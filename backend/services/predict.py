import math
import json
import joblib
import numpy as np
from pathlib import Path

MODELS_DIR = Path("/app/data/models")

_flood_model    = None
_flood_features = None
_flood_meta     = None


def _load_flood_model():
    global _flood_model, _flood_features, _flood_meta

    model_path    = MODELS_DIR / "flood_model.pkl"
    features_path = MODELS_DIR / "flood_features.json"

    if not model_path.exists():
        raise RuntimeError(
            "Flood model not found. Run: "
            "docker exec climarisk_backend python services/train.py"
        )
    if not features_path.exists():
        raise RuntimeError("flood_features.json not found — retrain the model.")

    _flood_model = joblib.load(model_path)

    with open(features_path) as f:
        _flood_meta = json.load(f)

    _flood_features = _flood_meta["features"]

    import logging
    logging.getLogger("climarisk.predict").info(
        f"Flood model v{_flood_meta.get('version','?')} loaded — "
        f"features: {_flood_features} — "
        f"AUC: {_flood_meta.get('auc', '?')}"
    )


def get_flood_model():
    if _flood_model is None:
        _load_flood_model()
    return _flood_model, _flood_features, _flood_meta


def _geo_calibration(lat: float, lon: float) -> float:

    if -15 <= lat <= 25 and 90 <= lon <= 155:
        return 1.0

    if -10 <= lat <= 25 and 25 <= lon <= 90:
        return 0.80

    if -20 <= lat <= 20 and -85 <= lon <= -30:
        return 0.75

    if 15 <= lat <= 45 and -15 <= lon <= 60:
        return 0.25

    if 45 <= lat <= 70 and -15 <= lon <= 40:
        return 0.45

    if 25 <= lat <= 60 and -130 <= lon <= -60:
        return 0.45

    if 10 <= lat <= 35 and 10 <= lon <= 60:
        return 0.15

    if abs(lat) > 60:
        return 0.30

    return 0.55


def flood_probability(
    precip_1d:      float | None,
    precip_3d:      float | None,
    ndvi:           float | None,
    ndwi:           float | None,
    jrc_perm_water: float | None,
    landcover:      float | None,
    elevation:      float | None,
    slope:          float | None,
    upstream_area:  float | None,
    twi:            float | None,
    lat:            float = 0.0,
    lon:            float = 0.0,
) -> float:

    try:
        model, features, meta = get_flood_model()

        p1d   = max(0.0,   precip_1d      or 0.0)
        p3d   = max(0.0,   precip_3d      or 0.0)
        ndvi_ = max(-1.0,  min(ndvi       or 0.3,  1.0))
        ndwi_ = max(-1.0,  min(ndwi       or -0.1, 1.0))
        jrc   = float(max(0.0, min(jrc_perm_water or 0.0, 1.0)))
        lc    = float(landcover or 0.0)
        elev  = max(-50.0, min(elevation   or 50.0, 8000.0))
        slp   = max(0.0,   min(slope       or 1.0,  80.0))
        ua    = max(0.0,   upstream_area   or 0.0)
        twi_  = max(0.0,   min(twi         or 2.0,  15.0))

        saturation_idx       = p3d * twi_
        rain_burst_ratio     = min(p1d / (p3d + 1e-6), 3.0)
        topo_flood_potential = ua / (slp + 1.0)
        veg_absorption       = max(0.0, min(ndvi_, 1.0)) * (1.0 - max(0.0, min(ndwi_, 1.0)))

        feature_map = {
            "precip_1d":            p1d,
            "precip_3d":            p3d,
            "NDVI":                 ndvi_,
            "NDWI":                 ndwi_,
            "jrc_perm_water":       jrc,
            "landcover":            lc,
            "elevation":            elev,
            "slope":                slp,
            "upstream_area":        ua,
            "TWI":                  twi_,
            "saturation_idx":       saturation_idx,
            "rain_burst_ratio":     rain_burst_ratio,
            "topo_flood_potential": topo_flood_potential,
            "veg_absorption":       veg_absorption,
        }

        vector   = np.array([[feature_map[f] for f in features]])
        raw_prob = float(model.predict_proba(vector)[0][1])

        cal      = _geo_calibration(lat, lon)
        prob     = raw_prob * cal

        if p3d < 1.0 and jrc == 0.0:
            prob = min(prob, 0.15)


        if elev > 800:
            prob = prob * 0.20
        elif elev > 400:
            prob = prob * 0.45

        return round(max(0.01, min(prob, 0.99)), 4)

    except Exception as e:
        import logging
        logging.getLogger("climarisk.predict").warning(
            f"Flood model failed ({e}), using heuristic fallback"
        )
        return _flood_heuristic(precip_1d, precip_3d, twi, jrc_perm_water)


def _flood_heuristic(precip_1d, precip_3d, twi, jrc_perm_water) -> float:

    score = 0.05
    if precip_1d      and precip_1d      > 50:  score += 0.30
    if precip_3d      and precip_3d      > 100: score += 0.25
    if twi            and twi            > 8:   score += 0.20
    if jrc_perm_water and jrc_perm_water == 1:  score += 0.15
    return min(round(score, 4), 0.95)


def fire_probability(
    temperature_c:  float | None,
    humidity_pct:   float | None,
    wind_speed_kmh: float | None,
    rainfall_mm:    float | None,
    fwi:            float | None,
) -> float:

    temp = temperature_c  if temperature_c  is not None else 20.0
    rh   = humidity_pct   if humidity_pct   is not None else 50.0
    wind = wind_speed_kmh if wind_speed_kmh is not None else 10.0
    rain = rainfall_mm    if rainfall_mm    is not None else 0.0

    if fwi is not None and fwi > 0:
        return round(min(fwi / 50.0, 1.0), 4)

    ffmc_score  = max(0.0, (temp - rh / 5.0))
    wind_factor = math.exp(0.05039 * wind)
    isi         = wind_factor * (ffmc_score / 20.0)

    if rain > 10:   rain_penalty = 0.5
    elif rain > 5:  rain_penalty = 0.3
    elif rain > 1:  rain_penalty = 0.1
    else:           rain_penalty = 0.0

    drought   = max(0.0, (temp - 15) / 40.0) * max(0.0, (80 - rh) / 80.0)
    raw_score = (
        0.30 * min(isi / 20.0, 1.0)       +
        0.35 * drought                     +
        0.20 * min(temp / 45.0, 1.0)      +
        0.15 * max(0.0, (60 - rh) / 60.0)
    ) - rain_penalty

    return max(0.05, min(round(raw_score, 4), 0.95))