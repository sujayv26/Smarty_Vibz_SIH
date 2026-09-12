from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.confidence_service import evaluate_confidence
from app.schemas.confidence import ConfidenceEvaluationResponse

router = APIRouter(prefix="/confidence", tags=["Confidence"])


@router.post("/evaluate/{progress_event_id}", response_model=ConfidenceEvaluationResponse)
async def evaluate_confidence_endpoint(progress_event_id: int, db: Session = Depends(get_db)):
    try:
        result = evaluate_confidence(db, progress_event_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Confidence evaluation failed: {str(e)}")