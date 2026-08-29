"""
Loads the trained model/scaler once at startup and exposes a single
`predict_rul` function that mirrors the exact feature engineering used
in ml/src/features.py at training time. Keeping this logic in sync with
training is the most important correctness property of the service --
if the two drift apart, predictions silently become garbage.
"""
import os
import json
import joblib
import numpy as np
import pandas as pd

MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "ml", "models")

ROLLING_WINDOW = 5
ACTIVE_SENSORS = [
    "sensor_2", "sensor_3", "sensor_4", "sensor_7", "sensor_8", "sensor_9",
    "sensor_11", "sensor_12", "sensor_13", "sensor_14", "sensor_15",
    "sensor_17", "sensor_20", "sensor_21",
]
OP_SETTING_COLS = ["op_setting_1", "op_setting_2", "op_setting_3"]


class RULPredictor:
    def __init__(self):
        model_path = os.path.join(MODEL_DIR, "rul_model.joblib")
        scaler_path = os.path.join(MODEL_DIR, "scaler.joblib")
        meta_path = os.path.join(MODEL_DIR, "metadata.json")

        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"No trained model found at {model_path}. "
                f"Run `python ml/src/train.py` first."
            )

        self.model = joblib.load(model_path)
        self.scaler = joblib.load(scaler_path)
        with open(meta_path) as f:
            self.metadata = json.load(f)
        self.feature_cols = self.metadata["feature_cols"]
        self.rul_cap = self.metadata["rul_cap"]
        self.model_name = self.metadata["best_model"]

    def _build_features(self, readings: list[dict]) -> pd.DataFrame:
        """readings: list of dicts ordered oldest -> newest for ONE unit."""
        df = pd.DataFrame(readings).sort_values("time_in_cycles").reset_index(drop=True)

        roll_mean = df[ACTIVE_SENSORS].rolling(ROLLING_WINDOW, min_periods=1).mean()
        roll_std = df[ACTIVE_SENSORS].rolling(ROLLING_WINDOW, min_periods=1).std().fillna(0)
        roll_mean.columns = [f"{c}_rollmean" for c in ACTIVE_SENSORS]
        roll_std.columns = [f"{c}_rollstd" for c in ACTIVE_SENSORS]

        feat = pd.concat([df, roll_mean, roll_std], axis=1)
        return feat.tail(1)  # only the latest cycle is used for prediction

    def predict(self, unit_number: int, readings: list[dict]) -> dict:
        feat_row = self._build_features(readings)
        missing = [c for c in self.feature_cols if c not in feat_row.columns]
        if missing:
            raise ValueError(f"Missing required features: {missing}")

        X = feat_row[self.feature_cols].values
        X_scaled = self.scaler.transform(X)
        pred = float(self.model.predict(X_scaled)[0])
        pred = max(0.0, min(pred, self.rul_cap))

        if pred < 20:
            risk = "critical"
        elif pred < 50:
            risk = "warning"
        else:
            risk = "healthy"

        return {
            "unit_number": unit_number,
            "predicted_rul": round(pred, 1),
            "risk_level": risk,
            "risk_flag": pred < 20,
            "model_used": self.model_name,
        }


_predictor: RULPredictor | None = None


def get_predictor() -> RULPredictor:
    global _predictor
    if _predictor is None:
        _predictor = RULPredictor()
    return _predictor
