"""
Exports a handful of test-set engine trajectories (raw sensor readings,
not features) to JSON so the frontend can demo real predictions without
requiring the user to hand-type 21 sensor values.

Includes the true RUL alongside each unit purely for demo/comparison
purposes in the UI (labeled clearly as "actual" vs "predicted").
"""
import os
import json
import pandas as pd

from features import load_raw, load_rul

BASE = os.path.dirname(__file__)
RAW_DIR = os.path.join(BASE, "..", "data", "raw")
OUT_PATH = os.path.join(BASE, "..", "data", "sample_fleet.json")

READING_COLS = [
    "unit_number", "time_in_cycles", "op_setting_1", "op_setting_2", "op_setting_3",
    "sensor_2", "sensor_3", "sensor_4", "sensor_7", "sensor_8", "sensor_9",
    "sensor_11", "sensor_12", "sensor_13", "sensor_14", "sensor_15",
    "sensor_17", "sensor_20", "sensor_21",
]

N_SAMPLE_UNITS = 8


def main():
    test_df = load_raw(os.path.join(RAW_DIR, "test_FD001.txt"))
    rul_df = load_rul(os.path.join(RAW_DIR, "RUL_FD001.txt"))

    unit_ids = sorted(test_df["unit_number"].unique())[:N_SAMPLE_UNITS]

    fleet = []
    for uid in unit_ids:
        unit_data = test_df[test_df["unit_number"] == uid].sort_values("time_in_cycles")
        readings = unit_data[READING_COLS].tail(10).to_dict(orient="records")
        true_rul = int(rul_df.loc[rul_df["unit_number"] == uid, "RUL"].values[0])
        fleet.append({
            "unit_number": int(uid),
            "actual_rul": true_rul,
            "last_cycle": int(unit_data["time_in_cycles"].max()),
            "readings": readings,
        })

    with open(OUT_PATH, "w") as f:
        json.dump(fleet, f, indent=2)

    print(f"Exported {len(fleet)} sample units to {OUT_PATH}")


if __name__ == "__main__":
    main()
