from pydantic import BaseModel
from datetime import date, datetime
from typing import List, Optional, Dict, Any


class DelayPredictionResponse(BaseModel):
    id: int
    project_id: int
    wbs_node_id: int
    model_version: str
    delay_probability: float
    expected_delay_days: float
    confidence_score: float
    risk_level: str
    feature_importance: Optional[str] = None
    features_json: Optional[str] = None
    prediction_date: date
    valid_until: Optional[date] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    # Enriched data
    activity_code: Optional[str] = None
    activity_name: Optional[str] = None
    discipline: Optional[str] = None
    wbs: Optional[str] = None
    planned_start: Optional[str] = None
    planned_finish: Optional[str] = None
    actual_start: Optional[str] = None

    class Config:
        from_attributes = True


class DelayPredictionListResponse(BaseModel):
    predictions: List[DelayPredictionResponse]
    total: int
    high_risk_count: int
    critical_risk_count: int
    model_version: str
    last_training_date: Optional[datetime] = None


class TrainingRunResponse(BaseModel):
    id: int
    model_version: str
    project_id: Optional[int] = None
    train_samples: int
    test_samples: int
    auc_roc: Optional[float] = None
    auc_pr: Optional[float] = None
    mae_delay_days: Optional[float] = None
    rmse_delay_days: Optional[float] = None
    feature_importance: Optional[str] = None
    hyperparameters: Optional[str] = None
    feature_list: Optional[str] = None
    status: str
    error_message: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class TrainingRunListResponse(BaseModel):
    runs: List[TrainingRunResponse]
    total: int


class TriggerTrainingRequest(BaseModel):
    project_id: Optional[int] = None
    force_retrain: bool = False


class TriggerTrainingResponse(BaseModel):
    status: str
    message: str
    run_id: Optional[int] = None
    metrics: Optional[Dict[str, Any]] = None


class PredictRequest(BaseModel):
    project_id: int
    force_refresh: bool = False