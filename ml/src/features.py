"""
Feature engineering for the C-MAPSS predictive maintenance pipeline.

Steps:
1. Load raw space-separated sensor logs
2. Label each training row with its Remaining Useful Life (RUL)
3. Drop sensors that carry no degradation signal (near-constant across life)
4. Add rolling-window statistics (mean/std) to capture trend, not just
   instantaneous reading -- this is the single biggest lever for RUL
   accuracy in published CMAPSS work
5. Clip training RUL at a ceiling (standard trick: a "healthy" engine's
   distance-to-failure is not linearly informative early in life, so
   capping the label prevents the model from being penalized for not
   predicting arbitrarily large numbers)
"""
import pandas as pd
import numpy as np
import os

SENSOR_COLS = [f"sensor_{i}" for i in range(1, 22)]
OP_SETTING_COLS = [f"op_setting_{i}" for i in range(1, 4)]
COLUMNS = ["unit_number", "time_in_cycles"] + OP_SETTING_COLS + SENSOR_COLS

# Determined by EDA (see notebooks/01_eda.ipynb): sensors with near-zero
# variance across the engine's life carry no useful degradation signal.
DROP_SENSORS = ["sensor_1", "sensor_5", "sensor_6", "sensor_10",
                 "sensor_16", "sensor_18", "sensor_19"]

RUL_CAP = 130
ROLLING_WINDOW = 5


def load_raw(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, sep=r"\s+", header=None, names=COLUMNS)
    return df


def load_rul(path: str) -> pd.DataFrame:
    rul = pd.read_csv(path, sep=r"\s+", header=None, names=["RUL"])
    rul["unit_number"] = rul.index + 1
    return rul


def add_rul_labels_train(df: pd.DataFrame) -> pd.DataFrame:
    """For training data we have full run-to-failure trajectories, so
    RUL at any cycle = (max cycle for that unit) - (current cycle)."""
    max_cycles = df.groupby("unit_number")["time_in_cycles"].transform("max")
    df = df.copy()
    df["RUL"] = max_cycles - df["time_in_cycles"]
    df["RUL"] = df["RUL"].clip(upper=RUL_CAP)
    return df


def add_rolling_features(df: pd.DataFrame, sensor_cols: list) -> pd.DataFrame:
    df = df.sort_values(["unit_number", "time_in_cycles"]).copy()
    grouped = df.groupby("unit_number")[sensor_cols]

    roll_mean = grouped.transform(
        lambda s: s.rolling(ROLLING_WINDOW, min_periods=1).mean()
    )
    roll_std = grouped.transform(
        lambda s: s.rolling(ROLLING_WINDOW, min_periods=1).std().fillna(0)
    )

    roll_mean.columns = [f"{c}_rollmean" for c in sensor_cols]
    roll_std.columns = [f"{c}_rollstd" for c in sensor_cols]

    return pd.concat([df, roll_mean, roll_std], axis=1)


def build_feature_set(df: pd.DataFrame):
    """Returns (X, feature_names) with dropped-sensor columns removed and
    rolling features added. Does NOT include RUL / identifier columns."""
    active_sensors = [c for c in SENSOR_COLS if c not in DROP_SENSORS]
    df_feat = add_rolling_features(df, active_sensors)

    feature_cols = (
        OP_SETTING_COLS
        + active_sensors
        + [f"{c}_rollmean" for c in active_sensors]
        + [f"{c}_rollstd" for c in active_sensors]
    )
    return df_feat, feature_cols


def get_last_cycle_per_unit(df_feat: pd.DataFrame, feature_cols: list) -> pd.DataFrame:
    """For test-set evaluation: we only get to see the truncated
    trajectory, and must predict RUL from the *last* observed cycle,
    exactly matching the real CMAPSS evaluation protocol."""
    last_rows = df_feat.sort_values("time_in_cycles").groupby("unit_number").tail(1)
    return last_rows.sort_values("unit_number").reset_index(drop=True)


if __name__ == "__main__":
    base = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
    train_raw = load_raw(os.path.join(base, "train_FD001.txt"))
    train_raw = add_rul_labels_train(train_raw)
    train_feat, feature_cols = build_feature_set(train_raw)
    print(f"Feature columns ({len(feature_cols)}): {feature_cols[:5]} ...")
    print(train_feat[feature_cols + ['RUL']].describe().T.head(10))
