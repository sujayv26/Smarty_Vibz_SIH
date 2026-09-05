from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.progress_service import extract_and_store_progress, get_all_progress_events
from app.services.excel_progress_service import validate_excel_progress, process_excel_progress
from app.schemas.progress import ProgressExtractRequest, ProgressExtractResponse, ProgressEventResponse
from app.models.progress import ProgressEvent
from app.models.ingestion_source import IngestionSource
from app.models.confidence import PlannerReview, ConfidenceResult, ReviewStatus, ConfidenceLevel
from datetime import datetime, timedelta
from sqlalchemy import desc

router = APIRouter(prefix="/progress", tags=["Progress"])

@router.post("/extract", response_model=ProgressExtractResponse)
async def extract_progress(request: ProgressExtractRequest, db: Session = Depends(get_db)):
    try:
        result = extract_and_store_progress(db, request.raw_text)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")

@router.post("/upload-excel")
async def upload_excel_progress(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="Only .xlsx files are supported")
    
    try:
        valid_rows, errors = validate_excel_progress(file.file)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    inserted, row_errors = process_excel_progress(db, valid_rows, file.filename)
    all_errors = errors + row_errors
    
    return {
        "total_rows": len(valid_rows) + len(errors),
        "extracted_events": inserted,
        "failed_rows": len(all_errors),
        "errors": all_errors
    }

@router.get("/events", response_model=list[ProgressEventResponse])
async def get_progress_events(db: Session = Depends(get_db)):
    events = get_all_progress_events(db)
    return events

@router.get("/inbound/recent", summary="Get recent inbound messages from all sources")
async def get_recent_inbound_messages(
    hours: int = Query(24, description="Hours to look back"),
    limit: int = Query(100, description="Maximum number of messages"),
    db: Session = Depends(get_db)
):
    """Get recent inbound messages from all ingestion sources for the live feed."""
    
    since = datetime.utcnow() - timedelta(hours=hours)
    events = db.query(ProgressEvent).filter(
        ProgressEvent.created_at >= since
    ).order_by(desc(ProgressEvent.created_at)).limit(limit).all()
    
    # Get source names
    sources = {s.id: s.code for s in db.query(IngestionSource).all()}
    
    return [
        {
            "id": e.id,
            "source": sources.get(e.ingestion_source_id, e.source_type),
            "from": "Field User",  # Would come from user relationship
            "text": e.raw_text[:200] + ("..." if len(e.raw_text) > 200 else ""),
            "time": _format_time_ago(e.created_at),
            "status": _get_event_status(e, db),
            "match": e.activity_reference,
            "event_type": e.event_type,
            "created_at": e.created_at,
        }
        for e in events
    ]


def _format_time_ago(dt: datetime) -> str:
    if not dt:
        return "unknown"
    now = datetime.utcnow()
    diff = now - dt.replace(tzinfo=None)
    if diff.total_seconds() < 60:
        return f"{int(diff.total_seconds())}s ago"
    if diff.total_seconds() < 3600:
        return f"{int(diff.total_seconds() / 60)}m ago"
    if diff.total_seconds() < 86400:
        return f"{int(diff.total_seconds() / 3600)}h ago"
    return f"{diff.days}d ago"


def _get_event_status(event: ProgressEvent, db: Session) -> str:
    # Check if there's a review
    review = db.query(PlannerReview).filter(
        PlannerReview.progress_event_id == event.id
    ).first()
    if review:
        if review.status == ReviewStatus.PENDING:
            return "review"
        elif review.status == ReviewStatus.APPROVED:
            return "matched"
        elif review.status in [ReviewStatus.CORRECTED, ReviewStatus.NEW_ACTIVITY_CREATED]:
            return "matched"
        elif review.status == ReviewStatus.REJECTED:
            return "rejected"
    
    # Check confidence result
    conf = db.query(ConfidenceResult).filter(
        ConfidenceResult.progress_event_id == event.id
    ).first()
    if conf:
        if conf.confidence_level == ConfidenceLevel.HIGH:
            return "matched"
        elif conf.confidence_level == ConfidenceLevel.MEDIUM:
            return "review"
        else:
            return "new-activity"
    
    return "processing"