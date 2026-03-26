import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport


TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest_asyncio.fixture(scope="session")
async def app():
    import os
    os.environ["DATABASE_URL"]       = TEST_DATABASE_URL
    os.environ["SECRET_KEY"]         = "test-secret-key"
    os.environ["ALGORITHM"]          = "HS256"
    os.environ["ASYNC_DATABASE_URL"] = TEST_DATABASE_URL

    from main import app as _app
    return _app


@pytest_asyncio.fixture(scope="session")
async def client(app):
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as c:
        yield c



@pytest.mark.anyio
async def test_register_and_login(client):
    res = await client.post("/api/auth/register", json={
        "username": "testuser",
        "email":    "test@climarisk.com",
        "password": "testpass123",
    })
    assert res.status_code in (200, 201), f"Register failed: {res.text}"

    res = await client.post("/api/auth/token", data={
        "username": "testuser",
        "password": "testpass123",
    })
    assert res.status_code == 200, f"Login failed: {res.text}"
    assert "access_token" in res.json()


@pytest.mark.anyio
async def test_login_wrong_password(client):
    res = await client.post("/api/auth/token", data={
        "username": "testuser",
        "password": "wrongpassword",
    })
    assert res.status_code == 401


@pytest.mark.anyio
async def test_protected_endpoint_without_token(client):
    res = await client.get("/api/zones/")
    assert res.status_code == 401


@pytest.mark.anyio
async def test_health_endpoint(client):
    res = await client.get("/api/health")
    assert res.status_code == 200



async def _get_token(client) -> str:
    res = await client.post("/api/auth/token", data={
        "username": "testuser",
        "password": "testpass123",
    })
    return res.json().get("access_token", "")


async def _get_or_create_zone(client, headers) -> int:
    """Return first existing zone id, or create one."""
    zones = (await client.get("/api/zones/", headers=headers)).json()
    if zones:
        return zones[0]["id"]

    res = await client.post("/api/zones/", headers=headers, json={
        "name":      "Test Zone",
        "code":      "TZ-TEST",
        "latitude":  14.6928,
        "longitude": -17.4467,
        "region":    "Test Region",
    })
    assert res.status_code in (200, 201), f"Zone creation failed: {res.text}"
    return res.json()["id"]



@pytest.mark.anyio
async def test_flood_simulation_dry_run(client):

    headers  = {"Authorization": f"Bearer {await _get_token(client)}"}
    zone_id  = await _get_or_create_zone(client, headers)

    res = await client.post(
        f"/api/predictions/flood/{zone_id}/simulate",
        headers=headers,
        json={
            "precip_1d":      35.0,
            "precip_3d":      90.0,
            "elevation":      45.0,
            "TWI":            6.5,
            "slope":          2.5,
            "upstream_area":  3.8,
            "NDVI":           0.5,
            "NDWI":          -0.2,
            "jrc_perm_water": 0,
            "landcover":      40,
        }
    )
    assert res.status_code in (200, 201), f"Flood simulation failed: {res.text}"
    data = res.json()
    assert "probability" in data
    assert "risk_level"  in data
    assert data["risk_level"] in ("LOW", "MEDIUM", "HIGH", "CRITICAL")
    assert 0.0 <= data["probability"] <= 1.0
    assert data["id"] is None


@pytest.mark.anyio
async def test_fire_prediction_dry_run(client):

    from unittest.mock import patch, AsyncMock

    headers = {"Authorization": f"Bearer {await _get_token(client)}"}
    zone_id = await _get_or_create_zone(client, headers)

    mock_weather = {
        "temperature_c":  38.0,
        "humidity_pct":   15.0,
        "wind_speed_kmh": 45.0,
        "rainfall_mm":    0.0,
        "fwi":            None,
        "precip_1d": 0.0, "precip_3d": 0.0,
        "NDVI": 0.5, "NDWI": -0.2,
        "jrc_perm_water": 0.0, "landcover": 40.0,
        "elevation": 50.0, "slope": 2.5,
        "upstream_area": 3.8, "TWI": 4.0,
        "lat": 14.6928, "lon": -17.4467,
        "_daily_rain_mm": 0.0, "_et0": None,
    }

    with patch("services.weather.fetch_weather", new=AsyncMock(return_value=mock_weather)):
        res = await client.post(
            f"/api/predictions/fire/{zone_id}?dry_run=true",
            headers=headers,
        )

    assert res.status_code in (200, 201), f"Fire prediction failed: {res.text}"
    data = res.json()
    assert "probability" in data
    assert data["risk_level"] in ("LOW", "MEDIUM", "HIGH", "CRITICAL")
    assert data["id"] is None



def test_fire_high_temp_no_fwi():
    from services.predict import fire_probability
    p = fire_probability(temperature_c=45, humidity_pct=10,
                         wind_speed_kmh=60, rainfall_mm=0, fwi=None)
    assert p > 0.50, f"Expected HIGH fire risk, got {p:.2%}"


def test_fire_fwi_priority():
    from services.predict import fire_probability
    p = fire_probability(temperature_c=50, humidity_pct=5,
                         wind_speed_kmh=100, rainfall_mm=0, fwi=10)
    assert abs(p - 10/50) < 0.01, f"FWI=10 should give 20%, got {p:.2%}"


def test_fire_fwi_zero_uses_weather():
    from services.predict import fire_probability
    p_zero = fire_probability(temperature_c=45, humidity_pct=10,
                               wind_speed_kmh=60, rainfall_mm=0, fwi=0)
    p_none = fire_probability(temperature_c=45, humidity_pct=10,
                               wind_speed_kmh=60, rainfall_mm=0, fwi=None)
    assert abs(p_zero - p_none) < 0.01


def test_risk_level_mapping():
    from schemas.prediction import probability_to_risk_level
    assert probability_to_risk_level(0.05) == "LOW"
    assert probability_to_risk_level(0.15) == "MEDIUM"
    assert probability_to_risk_level(0.35) == "HIGH"
    assert probability_to_risk_level(0.75) == "CRITICAL"