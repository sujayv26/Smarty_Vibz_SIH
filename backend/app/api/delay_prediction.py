from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.services.ml_delay_service import DelayPredictionService
from app.models.delay_prediction import DelayPrediction, ModelTrainingRun
from app.models.wbs_node import WBSNode
from app.schemas.delay_prediction import (
    DelayPredictionResponse,
    DelayPredictionListResponse,
    TrainingRunResponse,
    TrainingRunListResponse,
    TriggerTrainingRequest,
    TriggerTrainingResponse,
    PredictRequest,
)

router = APIRouter(prefix="/delay-predictions", tags=["ML Delay Prediction"])


def get_service(db: Session = Depends(get_db), model_version: str = "v1") -> DelayPredictionService:
    return DelayPredictionService(db, model_version)


@router.get("/project/{project_id}", response_model=DelayPredictionListResponse)
async def get_delay_predictions(
    project_id: int,
    risk_level: Optional[str] = Query(None, description="Filter by risk level"),
    model_version: str = Query("v1", description="Model version"),
    db: Session = Depends(get_db),
    service: DelayPredictionService = Depends(get_service),
):
    """Get all delay predictions for a project."""
    query = db.query(DelayPrediction).join(
        WBSNode, DelayPrediction.wbs_node_id == WBSNode.id
    ).filter(
        DelayPrediction.project_id == project_id,
        DelayPrediction.model_version == model_version,
    )
    
    if risk_level:
        query = query.filter(DelayPrediction.risk_level == risk_level)
    
    predictions = query.order_by(
        DelayPrediction.delay_probability.desc(),
        DelayPrediction.expected_delay_days.desc()
    ).all()
    
    # Enrich with WBS node data
    enriched = []
    for pred in predictions:
        response = DelayPredictionResponse.model_validate(pred)
        if pred.wbs_node:
            response.activity_code = pred.wbs_node.activity_code
            response.activity_name = pred.wbs_node.activity_name
            response.discipline = pred.wbs_node.discipline
            response.wbs = pred.wbs_node.wbs
            response.planned_start = str(pred.wbs_node.planned_start) if pred.wbs_node.planned_start else None
            response.planned_finish = str(pred.wbs_node.planned_finish) if pred.wbs_node.planned_finish else None
            response.actual_start = str(pred.wbs_node.actual_start) if pred.wbs_node.actual_start else None
        enriched.append(response)
    
    high_risk = sum(1 for p in enriched if p.risk_level in ("HIGH", "CRITICAL"))
    critical_risk = sum(1 for p in enriched if p.risk_level == "CRITICAL")
    
    # Get last training run
    training_run = service.get_latest_training_run(project_id)
    last_training = training_run.completed_at if training_run else None
    
    return DelayPredictionListResponse(
        predictions=enriched,
        total=len(enriched),
        high_risk_count=high_risk,
        critical_risk_count=critical_risk,
        model_version=model_version,
        last_training_date=last_training,
    )


@router.get("/project/{project_id}/watchlist", response_model=DelayPredictionListResponse)
async def get_risk_watchlist(
    project_id: int,
    model_version: str = Query("v1", description="Model version"),
    limit: int = Query(20, description="Max items in watchlist"),
    db: Session = Depends(get_db),
):
    """Get ranked watchlist of at-risk activities (high/medium risk only)."""
    query = db.query(DelayPrediction).join(
        WBSNode, DelayPrediction.wbs_node_id == WBSNode.id
    ).filter(
        DelayPrediction.project_id == project_id,
        DelayPrediction.model_version == model_version,
        DelayPrediction.risk_level.in_(["MEDIUM", "HIGH", "CRITICAL"]),
    ).order_by(
        DelayPrediction.risk_level.desc(),
        DelayPrediction.delay_probability.desc(),
        DelayPrediction.expected_delay_days.desc()
    ).limit(limit)
    
    predictions = query.all()
    
    enriched = []
    for pred in predictions:
        response = DelayPredictionResponse.model_validate(pred)
        if pred.wbs_node:
            response.activity_code = pred.wbs_node.activity_code
            response.activity_name = pred.wbs_node.activity_name
            response.discipline = pred.wbs_node.discipline
            response.wbs = pred.wbs_node.wbs
            response.planned_start = str(pred.wbs_node.planned_start) if pred.wbs_node.planned_start else None
            response.planned_finish = str(pred.wbs_node.planned_finish) if pred.wbs_node.planned_finish else None
            response.actual_start = str(pred.wbs_node.actual_start) if pred.wbs_node.actual_start else None
        enriched.append(response)
    
    high_risk = sum(1 for p in enriched if p.risk_level in ("HIGH", "CRITICAL"))
    critical_risk = sum(1 for p in enriched if p.risk_level == "CRITICAL")
    
    training_run = db.query(ModelTrainingRun).filter(
        ModelTrainingRun.model_version == model_version,
        ModelTrainingRun.project_id == project_id
    ).order_by(ModelTrainingRun.started_at.desc()).first()
    
    return DelayPredictionListResponse(
        predictions=enriched,
        total=len(enriched),
        high_risk_count=high_risk,
        critical_risk_count=critical_risk,
        model_version=model_version,
        last_training_date=training_run.completed_at if training_run else None,
    )


@router.get("/{prediction_id}", response_model=DelayPredictionResponse)
async def get_delay_prediction(
    prediction_id: int,
    db: Session = Depends(get_db),
):
    """Get a specific delay prediction by ID."""
    pred = db.query(DelayPrediction).filter(DelayPrediction.id == prediction_id).first()
    if not pred:
        raise HTTPException(status_code=404, detail="Prediction not found")
    
    response = DelayPredictionResponse.model_validate(pred)
    if pred.wbs_node:
        response.activity_code = pred.wbs_node.activity_code
        response.activity_name = pred.wbs_node.activity_name
        response.discipline = pred.wbs_node.discipline
        response.wbs = pred.wbs_node.wbs
        response.planned_start = str(pred.wbs_node.planned_start) if pred.wbs_node.planned_start else None
        response.planned_finish = str(pred.wbs_node.planned_finish) if pred.wbs_node.planned_finish else None
        response.actual_start = str(pred.wbs_node.actual_start) if pred.wbs_node.actual_start else None
    
    return response


@router.post("/predict", response_model=DelayPredictionListResponse)
async def generate_predictions(
    request: PredictRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    service: DelayPredictionService = Depends(get_service),
):
    """Generate or refresh delay predictions for a project."""
    predictions = service.predict_for_project(request.project_id)
    
    enriched = []
    for pred in predictions:
        response = DelayPredictionResponse.model_validate(pred)
        if pred.wbs_node:
            response.activity_code = pred.wbs_node.activity_code
            response.activity_name = pred.wbs_node.activity_name
            response.discipline = pred.wbs_node.discipline
            response.wbs = pred.wbs_node.wbs
            response.planned_start = str(pred.wbs_node.planned_start) if pred.wbs_node.planned_start else None
            response.planned_finish = str(pred.wbs_node.planned_finish) if pred.wbs_node.planned_finish else None
            response.actual_start = str(pred.wbs_node.actual_start) if pred.wbs_node.actual_start else None
        enriched.append(response)
    
    high_risk = sum(1 for p in enriched if p.risk_level in ("HIGH", "CRITICAL"))
    critical_risk = sum(1 for p in enriched if p.risk_level == "CRITICAL")
    
    training_run = service.get_latest_training_run(request.project_id)
    
    return DelayPredictionListResponse(
        predictions=enriched,
        total=len(enriched),
        high_risk_count=high_risk,
        critical_risk_count=critical_risk,
        model_version="v1",
        last_training_date=training_run.completed_at if training_run else None,
    )


@router.post("/train", response_model=TriggerTrainingResponse)
async def trigger_training(
    request: TriggerTrainingRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Trigger model retraining (runs in background)."""
    # Check if training already in progress
    existing = db.query(ModelTrainingRun).filter(
        ModelTrainingRun.model_version == "v1",
        ModelTrainingRun.project_id == request.project_id,
        ModelTrainingRun.status == "in_progress"
    ).first()
    
    if existing and not request.force_retrain:
        return TriggerTrainingResponse(
            status="skipped",
            message="Training already in progress",
            run_id=existing.id,
        )
    
    # Create training run record
    training_run = ModelTrainingRun(
        model_version="v1",
        project_id=request.project_id,
        train_samples=0,
        test_samples=0,
        status="in_progress",
        started_at=datetime.utcnow(),
    )
    db.add(training_run)
    db.commit()
    db.refresh(training_run)
    
    # Run training in background
    def run_training():
        from app.database import SessionLocal
        db_session = SessionLocal()
        try:
            service = DelayPredictionService(db_session)
            result = service.train(request.project_id)
            training_run.status = result.get("status", "completed")
            training_run.train_samples = result.get("train_samples", 0)
            training_run.test_samples = result.get("test_samples", 0)
            training_run.auc_roc = result.get("auc_roc")
            training_run.auc_pr = result.get("auc_pr")
            training_run.mae_delay_days = result.get("mae_delay_days")
            training_run.rmse_delay_days = result.get("rmse_delay_days")
            training_run.feature_importance = result.get("feature_importance")
            training_run.error_message = result.get("error")
            training_run.completed_at = datetime.utcnow()
            db_session.commit()
        except Exception as e:
            training_run.status = "failed"
            training_run.error_message = str(e)
            training_run.completed_at = datetime.utcnow()
            db_session.commit()
        finally:
            db_session.close()
    
    background_tasks.add_task(run_training)
    
    return TriggerTrainingResponse(
        status="started",
        message="Training started in background",
        run_id=training_run.id,
    )


@router.get("/training-runs", response_model=TrainingRunListResponse)
async def get_training_runs(
    project_id: Optional[int] = Query(None),
    model_version: str = Query("v1"),
    db: Session = Depends(get_db),
):
    """Get training run history."""
    query = db.query(ModelTrainingRun).filter(
        ModelTrainingRun.model_version == model_version
    )
    if project_id:
        query = query.filter(ModelTrainingRun.project_id == project_id)
    
    runs = query.order_by(ModelTrainingRun.started_at.desc()).limit(50).all()
    return TrainingRunListResponse(runs=runs, total=len(runs))


@router.get("/training-runs/{run_id}", response_model=TrainingRunResponse)
async def get_training_run(
    run_id: int,
    db: Session = Depends(get_db),
):
    """Get a specific training run."""
    run = db.query(ModelTrainingRun).filter(ModelTrainingRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Training run not found")
    return run