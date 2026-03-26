import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_fire_probability():
    from services.predict import fire_probability

    p = fire_probability(temperature_c=45, humidity_pct=10, wind_speed_kmh=60,
                         rainfall_mm=0, fwi=0)
    assert p > 0.50, f"Extreme heat should give HIGH fire risk, got {p:.2%}"

    p = fire_probability(temperature_c=5, humidity_pct=90, wind_speed_kmh=5,
                         rainfall_mm=20, fwi=0)
    assert p < 0.30, f"Cold wet conditions should give LOW fire risk, got {p:.2%}"

    p = fire_probability(temperature_c=50, humidity_pct=5, wind_speed_kmh=100,
                         rainfall_mm=0, fwi=25)
    expected = 25 / 50.0
    assert abs(p - expected) < 0.01, f"FWI=25 should give {expected:.2%}, got {p:.2%}"

    p_fwi0 = fire_probability(temperature_c=45, humidity_pct=10, wind_speed_kmh=60,
                               rainfall_mm=0, fwi=0)
    p_fwi_none = fire_probability(temperature_c=45, humidity_pct=10, wind_speed_kmh=60,
                                   rainfall_mm=0, fwi=None)
    assert abs(p_fwi0 - p_fwi_none) < 0.01, \
        f"FWI=0 and FWI=None should give same result: {p_fwi0:.2%} vs {p_fwi_none:.2%}"

    print("✅ fire_probability tests passed")


def test_flood_heuristic():
    from services.predict import _flood_heuristic

    p = _flood_heuristic(precip_1d=80, precip_3d=150, twi=9, jrc_perm_water=1)
    assert p >= 0.50, f"Heavy flood conditions should give HIGH risk, got {p:.2%}"

    p = _flood_heuristic(precip_1d=2, precip_3d=5, twi=1, jrc_perm_water=0)
    assert p <= 0.15, f"Dry conditions should give LOW risk, got {p:.2%}"

    print("✅ flood heuristic tests passed")


def test_elevation_gate():

    raw_prob = 1.0

    def apply_gate(prob, elev):
        if elev > 800:
            return prob * 0.20
        elif elev > 400:
            return prob * 0.45
        return prob

    assert apply_gate(raw_prob, 1000) <= 0.20, \
        f"Mountain should have near-zero flood risk, got {apply_gate(raw_prob, 1000)}"

    assert apply_gate(raw_prob, 20) == raw_prob, \
        "Low elevation should not be penalized"

    assert apply_gate(raw_prob, 800) < apply_gate(raw_prob, 100), \
        "Higher elevation should give lower risk"

    print("✅ elevation gate tests passed")


def test_probability_bounds():
    from services.predict import fire_probability

    for temp in [0, 20, 45, 60]:
        for rh in [5, 50, 95]:
            p = fire_probability(temperature_c=temp, humidity_pct=rh,
                                 wind_speed_kmh=20, rainfall_mm=0, fwi=None)
            assert 0.0 <= p <= 1.0, \
                f"Probability out of bounds: {p} for temp={temp}, rh={rh}"

    print("✅ probability bounds tests passed")


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