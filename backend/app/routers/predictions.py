from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.engines.predictor import match_predictor

router = APIRouter()


class PredictRequest(BaseModel):
    team_a: str
    team_b: str
    as_of:  Optional[str] = "2026-06-21"


@router.post("/predict")
def predict_match(payload: PredictRequest):
    try:
        return match_predictor.predict(payload.team_a, payload.team_b, payload.as_of)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/predictions")
def get_all_predictions():
    return match_predictor.get_all_predictions()


@router.get("/accuracy")
def get_accuracy():
    return match_predictor.get_accuracy()
