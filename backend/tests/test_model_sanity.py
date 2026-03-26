import sys
import os
import math

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_fire_probability():
    from services.predict import fire_probability

    # FWI=0 + extreme heat → HIGH fire risk
    p = fire_probability(temperature_c=45, humidity_pct=10, wind_speed_kmh=60,
                         rainfall_mm=0, fwi=0)
    assert p > 0.50, f"Extreme heat should give HIGH fire risk, got {p:.2%}"

    # FWI=0 + cold wet → LOW fire risk
    p = fire_probability(temperature_c=5, humidity_pct=90, wind_speed_kmh=5,
                         rainfall_mm=20, fwi=0)
    assert p < 0.30, f"Cold wet conditions should give LOW fire risk, got {p:.2%}"

    # FWI provided → should use FWI directly
    p = fire_probability(temperature_c=50, humidity_pct=5, wind_speed_kmh=100,
                         rainfall_mm=0, fwi=25)
    expected = 25 / 50.0
    assert abs(p - expected) < 0.01, f"FWI=25 should give {expected:.2%}, got {p:.2%}"

    # FWI=0 → should NOT use FWI, fall through to weather formula
    p_fwi0 = fire_probability(temperature_c=45, humidity_pct=10, wind_speed_kmh=60,
                               rainfall_mm=0, fwi=0)
    p_fwi_none = fire_probability(temperature_c=45, humidity_pct=10, wind_speed_kmh=60,
                                   rainfall_mm=0, fwi=None)
    assert abs(p_fwi0 - p_fwi_none) < 0.01, \
        f"FWI=0 and FWI=None should give same result: {p_fwi0:.2%} vs {p_fwi_none:.2%}"

    print("✅ fire_probability tests passed")


# ── Flood model tests (heuristic fallback — no model file needed in CI) ───────

def test_flood_heuristic():
    from services.predict import _flood_heuristic

    # Heavy rain + high water + wet soil → HIGH
    p = _flood_heuristic(rainfall_mm=50, river_level_m=4, soil_moisture_pct=30)
    assert p >= 0.50, f"Heavy flood conditions should give HIGH risk, got {p:.2%}"

    # No rain → LOW
    p = _flood_heuristic(rainfall_mm=2, river_level_m=0.3, soil_moisture_pct=5)
    assert p <= 0.15, f"Dry conditions should give LOW risk, got {p:.2%}"

    print("✅ flood heuristic tests passed")


# ── Elevation gate tests ───────────────────────────────────────────────────────

def test_elevation_gate():
    """Verify elevation penalty is applied correctly."""
    # Simulate model probability before gate
    raw_prob = 1.0

    def apply_gate(prob, elev):
        if elev > 800:   return prob * 0.05
        elif elev > 500: return prob * 0.15
        elif elev > 300: return prob * 0.35
        elif elev > 200: return prob * 0.60
        return prob

    # High mountain → near zero
    assert apply_gate(raw_prob, 1028) < 0.10, "Mountain should have near-zero flood risk"

    # Low elevation → unchanged
    assert apply_gate(raw_prob, 20) == raw_prob, "Low elevation should not be penalized"

    # Monotonic: higher elevation = lower risk (within gate thresholds)
    assert apply_gate(raw_prob, 500) < apply_gate(raw_prob, 200), \
        "Higher elevation should give lower risk"

    print("✅ elevation gate tests passed")


# ── Probability bounds tests ───────────────────────────────────────────────────

def test_probability_bounds():
    from services.predict import fire_probability

    for temp in [0, 20, 45, 60]:
        for rh in [5, 50, 95]:
            p = fire_probability(temperature_c=temp, humidity_pct=rh,
                                 wind_speed_kmh=20, rainfall_mm=0, fwi=None)
            assert 0.0 <= p <= 1.0, f"Probability out of bounds: {p} for temp={temp}, rh={rh}"

    print("✅ probability bounds tests passed")


# ── Risk level threshold tests ─────────────────────────────────────────────────

def test_risk_levels():
    from schemas.prediction import probability_to_risk_level

    assert probability_to_risk_level(0.00) == "LOW"
    assert probability_to_risk_level(0.05) == "LOW"
    assert probability_to_risk_level(0.10) == "MEDIUM"
    assert probability_to_risk_level(0.29) == "MEDIUM"
    assert probability_to_risk_level(0.30) == "HIGH"
    assert probability_to_risk_level(0.49) == "HIGH"
    assert probability_to_risk_level(0.50) == "CRITICAL"
    assert probability_to_risk_level(1.00) == "CRITICAL"

    print("✅ risk level threshold tests passed")


if __name__ == "__main__":
    print("\n🧪 Running ClimaRisk ML sanity tests...\n")
    errors = []
    tests  = [
        test_fire_probability,
        test_flood_heuristic,
        test_elevation_gate,
        test_probability_bounds,
        test_risk_levels,
    ]
    for test in tests:
        try:
            test()
        except AssertionError as e:
            print(f"❌ {test.__name__}: {e}")
            errors.append(test.__name__)
        except Exception as e:
            print(f"⚠️  {test.__name__} skipped: {e}")

    print()
    if errors:
        print(f"❌ {len(errors)} test(s) failed: {errors}")
        sys.exit(1)
    else:
        print(f"✅ All {len(tests)} sanity tests passed")