import json, joblib, numpy as np, pandas as pd, os
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score
from xgboost import XGBClassifier

FLOOD_CSV  = Path("/app/data/csvs/flood/flood_cleaned.csv")
MODELS_DIR = Path("/app/data/models")
MODELS_DIR.mkdir(parents=True, exist_ok=True)

# FIX: jrc_perm_water added — strongest static predictor
FEATURES = [
    "precip_1d", "precip_3d", "NDVI", "NDWI",
    "jrc_perm_water",
    "landcover", "elevation", "slope", "upstream_area", "TWI",
    "saturation_idx", "rain_burst_ratio",
    "topo_flood_potential", "veg_absorption",
]
TARGET = "target"


def train():
    print(f"🚀 Loading Cleaned Dataset: {FLOOD_CSV}")

    if not FLOOD_CSV.exists():
        print(f"❌ Error: {FLOOD_CSV} not found. Run the cleaning pipeline first!")
        return

    df = pd.read_csv(FLOOD_CSV, usecols=FEATURES + [TARGET])

    neg   = (df[TARGET] == 0).sum()
    pos   = (df[TARGET] == 1).sum()
    ratio = neg / pos if pos > 0 else 1

    X = df[FEATURES]
    y = df[TARGET]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.1, stratify=y, random_state=42
    )

    print(f"📊 Dataset: {len(df):,} rows | Imbalance Ratio: {ratio:.1f}")

    # FIX: subsample + colsample_bytree added to prevent overfitting
    # FIX: min_child_weight=10 prevents splits on tiny flood clusters
    model = XGBClassifier(
        n_estimators=500,
        max_depth=6,
        learning_rate=0.05,
        scale_pos_weight=ratio,
        subsample=0.8,
        colsample_bytree=0.8,
        min_child_weight=10,
        tree_method="hist",
        device="cuda" if os.path.exists("/usr/local/cuda") else "cpu",
        random_state=42,
    )

    print("🏋️  Training on 1M rows (with Early Stopping)...")
    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        early_stopping_rounds=50,
        verbose=50,
    )

    y_pred  = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]
    auc     = float(roc_auc_score(y_test, y_proba))

    print("\n" + "="*30)
    print("      FINAL RESULTS")
    print("="*30)
    print(f"AUC-ROC: {auc:.4f}")
    print(classification_report(y_test, y_pred))

    joblib.dump(model, MODELS_DIR / "flood_model.pkl")

    # FIX: importance sort by score (x[1]), not by tuple (x)
    importance_scores = model.feature_importances_.tolist()
    importance_map = dict(sorted(
        zip(FEATURES, importance_scores),
        key=lambda x: x[1],
        reverse=True,
    ))

    # FIX: auc stored at top level so predict.py can read it directly
    meta = {
        "features":  FEATURES,
        "version":   "1.1.0-engineered",
        "auc":       auc,
        "n_samples": len(df),
        "importance": importance_map,
        "metrics":   {"auc": auc},
    }

    with open(MODELS_DIR / "flood_features.json", "w") as f:
        json.dump(meta, f, indent=2)

    print(f"\n✅ Model saved to {MODELS_DIR}")


if __name__ == "__main__":
    train()