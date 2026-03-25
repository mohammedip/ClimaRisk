"""
ClimaRisk API Integration Tests
=================================
Tests for FastAPI endpoints using httpx async client.
Requires: pytest pytest-asyncio httpx

Run: cd backend && pytest tests/ -v
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Use in-memory SQLite for tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest_asyncio.fixture(scope="session")
async def app():
    """Create test app with in-memory database."""
    import os
    os.environ["DATABASE_URL"] = TEST_DATABASE_URL
    os.environ["SECRET_KEY"]   = "test-secret-key"
    os.environ["ALGORITHM"]    = "HS256"

    from main import app as _app
    return _app


@pytest_asyncio.fixture(scope="session")
async def client(app):
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as c:
        yield c


# ── Auth tests ─────────────────────────────────────────────────────────────────

@pytest.mark.anyio
async def test_register_and_login(client):
    """Test user registration and JWT login."""
    # Register
    res = await client.post("/api/auth/register", json={
        "username": "testuser",
        "email":    "test@climarisk.com",
        "password": "testpass123",
    })
    assert res.status_code in (200, 201), f"Register failed: {res.text}"

    # Login
    res = await client.post("/api/auth/token", data={
        "username": "testuser",
        "password": "testpass123",
    })
    assert res.status_code == 200, f"Login failed: {res.text}"
    data = res.json()
    assert "access_token" in data
    return data["access_token"]


@pytest.mark.anyio
async def test_login_wrong_password(client):
    """Invalid credentials should return 401."""
    res = await client.post("/api/auth/token", data={
        "username": "testuser",
        "password": "wrongpassword",
    })
    assert res.status_code == 401


@pytest.mark.anyio
async def test_protected_endpoint_without_token(client):
    """Accessing protected endpoint without token should return 401."""
    res = await client.get("/api/zones/")
    assert res.status_code == 401


# ── Health test ────────────────────────────────────────────────────────────────

@pytest.mark.anyio
async def test_health_endpoint(client):
    """Health endpoint should return 200."""
    res = await client.get("/api/health")
    assert res.status_code == 200


# ── Prediction tests (dry_run — no DB required) ───────────────────────────────

@pytest.mark.anyio
async def test_flood_prediction_dry_run(client):
    """Flood prediction dry_run should return probability without saving."""
    # Get token first
    res = await client.post("/api/auth/token", data={
        "username": "testuser",
        "password": "testpass123",
    })
    token = res.json().get("access_token", "")
    headers = {"Authorization": f"Bearer {token}"}

    # Create a zone first
    res = await client.post("/api/zones/", headers=headers, json={
        "name":      "Test Zone",
        "code":      "TZ-TEST",
        "latitude":  14.6928,
        "longitude": -17.4467,
        "region":    "Test Region",
    })
    if res.status_code not in (200, 201):
        pytest.skip("Zone creation failed — skipping prediction test")

    zone_id = res.json()["id"]

    # Run flood prediction in dry_run mode
    res = await client.post(
        "/api/predictions/flood?dry_run=true",
        headers=headers,
        json={
            "zone_id":           zone_id,
            "rainfall_mm":       35.0,
            "river_level_m":     3.5,
            "soil_moisture_pct": 28.0,
        }
    )
    assert res.status_code in (200, 201), f"Flood prediction failed: {res.text}"
    data = res.json()
    assert "probability" in data
    assert "risk_level" in data
    assert data["risk_level"] in ("LOW", "MEDIUM", "HIGH", "CRITICAL")
    assert 0.0 <= data["probability"] <= 1.0
    assert data["id"] is None  # dry_run should not save


@pytest.mark.anyio
async def test_fire_prediction_dry_run(client):
    """Fire prediction dry_run should return probability without saving."""
    res = await client.post("/api/auth/token", data={
        "username": "testuser",
        "password": "testpass123",
    })
    token = res.json().get("access_token", "")
    headers = {"Authorization": f"Bearer {token}"}

    # Get first available zone
    zones_res = await client.get("/api/zones/", headers=headers)
    if not zones_res.json():
        pytest.skip("No zones available")

    zone_id = zones_res.json()[0]["id"]

    res = await client.post(
        "/api/predictions/fire?dry_run=true",
        headers=headers,
        json={
            "zone_id":       zone_id,
            "temperature_c": 38.0,
            "humidity_pct":  15.0,
            "wind_speed_kmh":45.0,
            "fwi":           0,
        }
    )
    assert res.status_code in (200, 201), f"Fire prediction failed: {res.text}"
    data = res.json()
    assert "probability" in data
    assert data["risk_level"] in ("LOW", "MEDIUM", "HIGH", "CRITICAL")
    assert data["id"] is None


# ── Prediction logic tests (no HTTP) ──────────────────────────────────────────

def test_fire_high_temp_no_fwi():
    """High temp, low humidity, no FWI → HIGH fire risk."""
    from services.predict import fire_probability
    p = fire_probability(
        temperature_c=45, humidity_pct=10,
        wind_speed_kmh=60, rainfall_mm=0, fwi=None
    )
    assert p > 0.50, f"Expected HIGH fire risk, got {p:.2%}"


def test_fire_fwi_priority():
    """When FWI > 0 is provided, it takes priority over weather."""
    from services.predict import fire_probability
    p = fire_probability(
        temperature_c=50, humidity_pct=5,
        wind_speed_kmh=100, rainfall_mm=0, fwi=10
    )
    assert abs(p - 10/50) < 0.01, f"FWI=10 should give 20%, got {p:.2%}"


def test_fire_fwi_zero_uses_weather():
    """FWI=0 should fall through to weather formula."""
    from services.predict import fire_probability
    p_zero = fire_probability(
        temperature_c=45, humidity_pct=10,
        wind_speed_kmh=60, rainfall_mm=0, fwi=0
    )
    p_none = fire_probability(
        temperature_c=45, humidity_pct=10,
        wind_speed_kmh=60, rainfall_mm=0, fwi=None
    )
    assert abs(p_zero - p_none) < 0.01


def test_risk_level_mapping():

    from schemas.prediction import probability_to_risk_level
    assert probability_to_risk_level(0.05) == "LOW"
    assert probability_to_risk_level(0.15) == "MEDIUM"
    assert probability_to_risk_level(0.35) == "HIGH"
    assert probability_to_risk_level(0.75) == "CRITICAL"