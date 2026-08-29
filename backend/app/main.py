import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.schemas import TrajectoryRequest, PredictionResponse, ModelInfo
from app.inference import get_predictor

app = FastAPI(
    title="Predictive Maintenance API",
    description="RUL (Remaining Useful Life) prediction for turbofan engines, "
                 "based on NASA C-MAPSS schema sensor data.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/model-info", response_model=ModelInfo)
def model_info():
    try:
        predictor = get_predictor()
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    return {
        "best_model": predictor.metadata["best_model"],
        "rul_cap": predictor.metadata["rul_cap"],
        "results": predictor.metadata["results"],
        "top_features": predictor.metadata["top_features"],
    }


@app.post("/api/predict", response_model=PredictionResponse)
def predict(payload: TrajectoryRequest):
    try:
        predictor = get_predictor()
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))

    readings = [r.model_dump() for r in payload.readings]
    unit_number = readings[-1]["unit_number"]

    try:
        result = predictor.predict(unit_number, readings)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return result


@app.get("/api/sample-fleet")
def sample_fleet():
    """Returns a small fleet of sample engine trajectories (from the
    generated test set) so the frontend has something to demo against
    without requiring the user to hand-craft sensor readings."""
    sample_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "ml", "data", "sample_fleet.json"
    )
    if not os.path.exists(sample_path):
        raise HTTPException(
            status_code=404,
            detail="Sample fleet not generated yet. Run ml/src/export_sample_fleet.py",
        )
    with open(sample_path) as f:
        return json.load(f)
