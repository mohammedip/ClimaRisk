"""
ClimaRisk ML Training Pipeline — v6
=====================================
Flood: MODIS dataset — retrained with ONLY weather API features
       precip_1d, precip_3d, soil_moisture, upstream_area (river proxy)
       These are exactly what Open-Meteo provides in real time.

Fire:  Canadian FWI formula (no ML — weather alone insufficient)
"""

import json
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.metrics import classification_report, roc_auc_score
from imblearn.over_sampling import SMOTE
from xgboost import XGBClassifier

FLOOD_CSV  = Path("/app/data/csvs/flood/flood.csv")
MODELS_DIR = Path("/app/data/models")
MODELS_DIR.mkdir(parents=True, exist_ok=True)


def train_flood():
    print("\n" + "="*60)
    print("🌊  FLOOD MODEL TRAINING v6 — Weather API features only")
    print("="*60)

    print("📄 Loading flood dataset...")
    df = pd.read_csv(FLOOD_CSV)
    print(f"   {len(df):,} rows loaded")

    # Only features available from Open-Meteo weather API
    FEATURES = [
        "precip_1d",      # rainfall last 24h (mm)      → rainfall_mm
        "precip_3d",      # rainfall last 72h (mm)      → _daily_rainfall_mm * 3
        "soil_moisture_0_to_1cm" if "soil_moisture_0_to_1cm" in df.columns else "TWI",  # soil moisture
        "upstream_area",  # watershed/river proxy        → river_level_m derived
    ]

    # Check which soil moisture column exists
    if "soil_moisture_0_to_1cm" in df.columns:
        soil_col = "soil_moisture_0_to_1cm"
    else:
        soil_col = "TWI"  # TWI is topographic wetness — best proxy for soil moisture
        print(f"   Using TWI as soil moisture proxy")

    FEATURES = ["precip_1d", "precip_3d", soil_col, "upstream_area"]
    TARGET   = "target"

    df = df[FEATURES + [TARGET]].dropna()
    print(f"   {len(df):,} rows after dropping nulls")
    print(f"   Class balance: {df[TARGET].value_counts().to_dict()}")
    print(f"   Features: {FEATURES}")

    X = df[FEATURES].values
    y = df[TARGET].values

    # 5-fold CV first
    print("\n📊 Running 5-fold cross-validation...")
    cv_model = XGBClassifier(
        n_estimators=300, max_depth=5, learning_rate=0.05,
        subsample=0.8, colsample_bytree=0.8, min_child_weight=3,
        reg_alpha=0.1, reg_lambda=1.0, random_state=42,
        n_jobs=-1, tree_method="hist", device="cuda",
    )
    skf    = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_auc = cross_val_score(cv_model, X, y, cv=skf, scoring="roc_auc")
    print(f"   CV AUC: {cv_auc.mean():.4f} ± {cv_auc.std():.4f}")

    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"   Train: {len(X_train):,}  Test: {len(X_test):,}")

    # SMOTE for imbalanced classes
    if y.mean() < 0.3:
        print(f"   ⚖️  Imbalanced ({y.mean():.1%}) — applying SMOTE...")
        smote = SMOTE(random_state=42)
        X_train, y_train = smote.fit_resample(X_train, y_train)
        print(f"   After SMOTE: {len(X_train):,} samples")

    print("🚀 Training XGBoost flood classifier...")
    model = XGBClassifier(
        n_estimators=500, max_depth=5, learning_rate=0.05,
        subsample=0.8, colsample_bytree=0.8, min_child_weight=3,
        reg_alpha=0.1, reg_lambda=1.0, eval_metric="logloss",
        early_stopping_rounds=30, random_state=42,
        n_jobs=-1, tree_method="hist", device="cuda",
    )
    model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=50)

    y_pred  = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]
    auc     = roc_auc_score(y_test, y_proba)

    print(f"\n📊 Flood Model Results:")
    print(f"   AUC-ROC: {auc:.4f}")
    print(f"   CV AUC:  {cv_auc.mean():.4f} ± {cv_auc.std():.4f}")
    print(classification_report(y_pred, y_test, target_names=["No Flood", "Flood"]))

    importance = dict(sorted(zip(FEATURES, model.feature_importances_.tolist()), key=lambda x: x[1], reverse=True))
    print("📈 Feature importance:")
    for feat, imp in importance.items():
        print(f"   {feat:<25} {imp:.4f}")

    joblib.dump(model, MODELS_DIR / "flood_model.pkl")
    with open(MODELS_DIR / "flood_features.json", "w") as f:
        json.dump({
            "features": FEATURES,
            "soil_col": soil_col,
            "importance": importance,
            "auc": auc,
            "cv_auc_mean": float(cv_auc.mean()),
            "cv_auc_std": float(cv_auc.std()),
            "version": "6.0.0"
        }, f, indent=2)

    print(f"\n✅ Flood model saved → {MODELS_DIR}/flood_model.pkl")
    return model, FEATURES, soil_col


if __name__ == "__main__":
    print("\n🌍 ClimaRisk ML Training Pipeline v6")
    print("="*60)
    print("Training flood model with weather-API-only features...")

    model, features, soil_col = train_flood()

    print("\n" + "="*60)
    print("✅ Flood model trained and saved!")
    print(f"   Features used: {features}")
    print(f"   Soil column:   {soil_col}")
    print("\nFire model: using Canadian FWI formula (no retraining needed)")
    print("\nNext: restart backend to load the new model.")