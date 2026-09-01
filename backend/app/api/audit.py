from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.confidence_service import get_audit_trail
from app.schemas.confidence import AuditTrailResponse, AuditRecordResponse

router = APIRouter(prefix="/audit", tags=["Audit Trail"])


@router.get("/{progress_event_id}", response_model=AuditTrailResponse)
async def get_audit_trail_endpoint(progress_event_id: int, db: Session = Depends(get_db)):
    try:
        audit_records = get_audit_trail(db, progress_event_id)
        return AuditTrailResponse(
            progress_event_id=progress_event_id,
            audit_records=[
                AuditRecordResponse(
                    id=record.id,
                    progress_event_id=record.progress_event_id,
                    proposed_activity_id=record.proposed_activity_id,
                    final_activity_id=record.final_activity_id,
                    new_activity_id=record.new_activity_id,
                    confidence_score=record.confidence_score,
                    confidence_level=record.confidence_level.value,
                    decision=record.decision.value,
                    reviewer_note=record.reviewer_note,
                    actor_type=record.actor_type.value,
                    created_at=record.created_at,
                )
                for record in audit_records
            ],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Audit retrieval failed: {str(e)}")