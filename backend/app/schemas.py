from pydantic import BaseModel, Field
from typing import List, Optional


class SensorReading(BaseModel):
    """A single cycle's reading for one engine unit."""
    unit_number: int
    time_in_cycles: int
    op_setting_1: float
    op_setting_2: float
    op_setting_3: float = 100.0
    sensor_2: float
    sensor_3: float
    sensor_4: float
    sensor_7: float
    sensor_8: float
    sensor_9: float
    sensor_11: float
    sensor_12: float
    sensor_13: float
    sensor_14: float
    sensor_15: float
    sensor_17: float
    sensor_20: float
    sensor_21: float


class TrajectoryRequest(BaseModel):
    """A sequence of readings for one engine, most recent last.
    At least 1 reading required; up to the last 5 are used for
    rolling-window features (matches training window size)."""
    readings: List[SensorReading] = Field(..., min_length=1)


class PredictionResponse(BaseModel):
    unit_number: int
    predicted_rul: float
    risk_level: str
    risk_flag: bool
    model_used: str


class ModelInfo(BaseModel):
    best_model: str
    rul_cap: int
    results: dict
    top_features: dict
