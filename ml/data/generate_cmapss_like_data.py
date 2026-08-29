"""
Generates a synthetic dataset that matches the NASA C-MAPSS Turbofan Engine
Degradation Simulation dataset schema exactly (FD001 format):

    unit_number, time_in_cycles, op_setting_1..3, sensor_1..21

WHY THIS FILE EXISTS
---------------------
This sandbox has no internet access, so the real NASA C-MAPSS dataset
(https://data.nasa.gov/dataset/C-MAPSS-Jet-Engine-Simulated-Data/ff5v-kuh6)
could not be downloaded. This script generates data with the identical
schema, column count, and degradation-curve statistical shape (piecewise
linear degradation + sensor noise + operating-condition drift), so the
entire pipeline (feature engineering -> training -> evaluation -> API)
is real and runs end-to-end.

TO USE THE REAL DATASET INSTEAD:
1. Download train_FD001.txt / test_FD001.txt / RUL_FD001.txt from:
   https://www.kaggle.com/datasets/behrad3d/nasa-cmaps
   (mirrors the official NASA archive, same schema)
2. Drop them into ml/data/raw/
3. In train.py, set USE_SYNTHETIC = False

Everything downstream (feature engineering, models, API, frontend)
works unmodified either way because the schema matches exactly.
"""
import numpy as np
import pandas as pd
import os

np.random.seed(42)

SENSOR_COLS = [f"sensor_{i}" for i in range(1, 22)]
OP_SETTING_COLS = [f"op_setting_{i}" for i in range(1, 4)]
COLUMNS = ["unit_number", "time_in_cycles"] + OP_SETTING_COLS + SENSOR_COLS

# Sensors known (from published CMAPSS analyses) to trend strongly with
# degradation vs. those that are flat/uninformative -- we replicate that
# structure so feature-selection work in the notebook is meaningful.
TRENDING_SENSORS = {2, 3, 4, 7, 8, 9, 11, 12, 13, 14, 15, 17, 20, 21}
FLAT_SENSORS = set(range(1, 22)) - TRENDING_SENSORS


def simulate_unit(unit_id: int, base_life: int) -> pd.DataFrame:
    n_cycles = base_life + np.random.randint(-15, 15)
    n_cycles = max(n_cycles, 120)
    cycles = np.arange(1, n_cycles + 1)

    # health index: 1.0 (healthy) -> 0.0 (failure), nonlinear degradation
    # (degrades slowly at first, accelerates near end of life)
    t = cycles / n_cycles
    health = 1 - t**2.2

    op1 = np.random.normal(20, 3, n_cycles).clip(0, 42)
    op2 = np.random.normal(0.6, 0.1, n_cycles).clip(0, 1)
    op3 = np.full(n_cycles, 100.0)

    data = {
        "unit_number": unit_id,
        "time_in_cycles": cycles,
        "op_setting_1": op1,
        "op_setting_2": op2,
        "op_setting_3": op3,
    }

    for s in range(1, 22):
        base = np.random.uniform(400, 600)
        noise = np.random.normal(0, 0.4, n_cycles)
        if s in TRENDING_SENSORS:
            direction = 1 if s % 2 == 0 else -1
            magnitude = np.random.uniform(15, 45)
            drift = direction * magnitude * (1 - health)
            values = base + drift + noise
        else:
            values = base + noise * 0.5
        data[f"sensor_{s}"] = values

    return pd.DataFrame(data)


def generate(n_units: int, mean_life: int, seed_offset: int = 0) -> pd.DataFrame:
    np.random.seed(42 + seed_offset)
    frames = []
    for uid in range(1, n_units + 1):
        life = int(np.random.normal(mean_life, 25))
        frames.append(simulate_unit(uid, life))
    return pd.concat(frames, ignore_index=True)


def split_train_test(df: pd.DataFrame, test_fraction: float = 0.3):
    """Train gets full run-to-failure trajectories. Test gets trajectories
    truncated at a random point before failure (this matches the real
    CMAPSS test-set design, where the true RUL is what you must predict)."""
    unit_ids = df["unit_number"].unique()
    np.random.shuffle(unit_ids)
    n_test = int(len(unit_ids) * test_fraction)
    test_ids = set(unit_ids[:n_test])

    train_df = df[~df["unit_number"].isin(test_ids)].copy()

    test_frames = []
    true_rul = {}
    for uid in test_ids:
        unit_df = df[df["unit_number"] == uid]
        max_cycle = unit_df["time_in_cycles"].max()
        cutoff = np.random.randint(int(max_cycle * 0.3), int(max_cycle * 0.85))
        truncated = unit_df[unit_df["time_in_cycles"] <= cutoff]
        test_frames.append(truncated)
        true_rul[uid] = max_cycle - cutoff

    test_df = pd.concat(test_frames, ignore_index=True)
    rul_df = pd.DataFrame(
        {"unit_number": list(true_rul.keys()), "RUL": list(true_rul.values())}
    ).sort_values("unit_number").reset_index(drop=True)

    # re-index test unit numbers to 1..N (matches CMAPSS convention)
    remap = {uid: i + 1 for i, uid in enumerate(sorted(test_ids))}
    test_df["unit_number"] = test_df["unit_number"].map(remap)
    rul_df["unit_number"] = rul_df["unit_number"].map(remap)
    rul_df = rul_df.sort_values("unit_number").reset_index(drop=True)

    return train_df, test_df, rul_df


if __name__ == "__main__":
    out_dir = os.path.join(os.path.dirname(__file__), "raw")
    os.makedirs(out_dir, exist_ok=True)

    full_df = generate(n_units=160, mean_life=200)
    train_df, test_df, rul_df = split_train_test(full_df, test_fraction=0.25)

    train_df[COLUMNS].to_csv(
        os.path.join(out_dir, "train_FD001.txt"), sep=" ", header=False, index=False
    )
    test_df[COLUMNS].to_csv(
        os.path.join(out_dir, "test_FD001.txt"), sep=" ", header=False, index=False
    )
    rul_df[["RUL"]].to_csv(
        os.path.join(out_dir, "RUL_FD001.txt"), sep=" ", header=False, index=False
    )

    print(f"train units: {train_df['unit_number'].nunique()}, rows: {len(train_df)}")
    print(f"test units:  {test_df['unit_number'].nunique()}, rows: {len(test_df)}")
    print(f"Saved to {out_dir}")
