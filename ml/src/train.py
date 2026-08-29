"""
Trains and compares three models for RUL prediction, in increasing order
of complexity, and saves the best one (by NASA score) plus the scaler
and feature list for the API to use at inference time.

Models compared:
  1. Linear Regression        - baseline, tells us if the problem is
                                 even roughly linear
  2. Random Forest Regressor  - strong tabular baseline, handles
                                 nonlinearity + feature interactions
  3. Gradient Boosting        - typically the best tabular performer;
                                 this is the sklearn stand-in for
                                 XGBoost/LightGBM (drop-in upgrade if
                                 you have internet: `pip install xgboost`
                                 and swap in xgboost.XGBRegressor with
                                 the same .fit/.predict interface)

Run: python src/train.py
"""
import os
import json
import joblib
import numpy as np
import pandas as pd

from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import GroupKFold

from features import (
    load_raw, load_rul, add_rul_labels_train, build_feature_set,
    get_last_cycle_per_unit, RUL_CAP
)
from scoring import nasa_score, rmse, mae

BASE = os.path.dirname(__file__)
RAW_DIR = os.path.join(BASE, "..", "data", "raw")
MODEL_DIR = os.path.join(BASE, "..", "models")
os.makedirs(MODEL_DIR, exist_ok=True)


def cross_validate(model, X, y, groups, n_splits=2):
    """GroupKFold so that rows from the same engine never appear in both
    train and validation folds -- otherwise the model 'cheats' by seeing
    near-identical rows (adjacent cycles) from the same unit in both
    splits, which inflates validation scores unrealistically."""
    gkf = GroupKFold(n_splits=n_splits)
    scores = []
    for train_idx, val_idx in gkf.split(X, y, groups):
        model.fit(X[train_idx], y.iloc[train_idx])
        preds = model.predict(X[val_idx])
        preds = np.clip(preds, 0, None)
        scores.append(rmse(y.iloc[val_idx], preds))
    return float(np.mean(scores)), float(np.std(scores))


def main():
    print("Loading data...")
    train_raw = load_raw(os.path.join(RAW_DIR, "train_FD001.txt"))
    test_raw = load_raw(os.path.join(RAW_DIR, "test_FD001.txt"))
    rul_true = load_rul(os.path.join(RAW_DIR, "RUL_FD001.txt"))

    train_raw = add_rul_labels_train(train_raw)
    train_feat, feature_cols = build_feature_set(train_raw)
    test_feat, _ = build_feature_set(test_raw)
    test_last = get_last_cycle_per_unit(test_feat, feature_cols)

    X_train_raw = train_feat[feature_cols].values
    y_train = train_feat["RUL"]
    groups = train_feat["unit_number"].values

    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train_raw)

    X_test = scaler.transform(test_last[feature_cols].values)
    y_test = test_last.merge(rul_true, on="unit_number")["RUL_y"] if "RUL_y" in \
        test_last.merge(rul_true, on="unit_number").columns else \
        rul_true.set_index("unit_number").loc[test_last["unit_number"], "RUL"].values

    candidates = {
        "LinearRegression": LinearRegression(),
        "RandomForest": RandomForestRegressor(
            n_estimators=60, max_depth=10, min_samples_leaf=5,
            n_jobs=-1, random_state=42
        ),
        "GradientBoosting": GradientBoostingRegressor(
            n_estimators=60, max_depth=3, learning_rate=0.1,
            subsample=0.8, random_state=42
        ),
    }

    print("\n5-fold GroupKFold cross-validation (RMSE, lower is better):")
    cv_results = {}
    for name, model in candidates.items():
        mean_rmse, std_rmse = cross_validate(model, X_train, y_train, groups)
        cv_results[name] = {"cv_rmse_mean": mean_rmse, "cv_rmse_std": std_rmse}
        print(f"  {name:20s}  RMSE = {mean_rmse:6.2f} +/- {std_rmse:.2f}")

    print("\nFitting final models on full training set, scoring on held-out test set...")
    results = {}
    fitted = {}
    for name, model in candidates.items():
        model.fit(X_train, y_train)
        preds = np.clip(model.predict(X_test), 0, RUL_CAP)
        results[name] = {
            "test_rmse": rmse(y_test, preds),
            "test_mae": mae(y_test, preds),
            "nasa_score": nasa_score(y_test, preds),
            **cv_results[name],
        }
        fitted[name] = model
        print(f"  {name:20s}  test RMSE={results[name]['test_rmse']:.2f}  "
              f"MAE={results[name]['test_mae']:.2f}  "
              f"NASA score={results[name]['nasa_score']:.1f}")

    best_name = min(results, key=lambda n: results[n]["nasa_score"])
    best_model = fitted[best_name]
    print(f"\nBest model by NASA score: {best_name}")

    joblib.dump(best_model, os.path.join(MODEL_DIR, "rul_model.joblib"))
    joblib.dump(scaler, os.path.join(MODEL_DIR, "scaler.joblib"))

    if hasattr(best_model, "feature_importances_"):
        importances = dict(zip(feature_cols, best_model.feature_importances_.tolist()))
        top10 = dict(sorted(importances.items(), key=lambda x: -x[1])[:10])
    else:
        top10 = {}

    metadata = {
        "best_model": best_name,
        "feature_cols": feature_cols,
        "rul_cap": RUL_CAP,
        "results": results,
        "top_features": top10,
    }
    with open(os.path.join(MODEL_DIR, "metadata.json"), "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"\nSaved model, scaler, and metadata to {MODEL_DIR}")


if __name__ == "__main__":
    main()
