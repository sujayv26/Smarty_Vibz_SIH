from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.xer.service import ScheduleImportService, XERImportService, get_relationships
from app.services.xer.mpp_parser import parse_mpp_content, MPPParseError
from app.services.xer.parser import parse_xer_content
from app.models.xer import ExternalSchedule, ScheduleRelationship
from app.models.schedule import ScheduleActivity
from app.models.progress import ProgressEvent
from app.services.confidence_service import get_review_by_id
from app.models.confidence import PlannerReview, ReviewStatus
from typing import Optional
from datetime import date
import io

router = APIRouter(prefix="/schedule", tags=["Schedule"])


@router.post("/import/p6", summary="Import Primavera P6 XER or MPP schedule")
async def import_p6_schedule(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    if not (file.filename.endswith(".xer") or file.filename.endswith(".mpp")):
        raise HTTPException(status_code=400, detail="Only .xer and .mpp files are supported")

    try:
        content = await file.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read file: {str(e)}")

    service = ScheduleImportService(db)

    if file.filename.endswith(".xer"):
        try:
            content_str = content.decode("utf-8", errors="replace")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to decode XER file: {str(e)}")

        try:
            parse_result = parse_xer_content(content_str)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"XER parsing failed: {str(e)}")

        result = service.import_schedule(parse_result, file.filename, "XER")
        return result

    elif file.filename.endswith(".mpp"):
        try:
            parse_result = parse_mpp_content(content)
        except MPPParseError as e:
            raise HTTPException(status_code=400, detail=f"MPP parsing failed: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"MPP parsing failed: {str(e)}")

        result = service.import_schedule(parse_result, file.filename, "MPP")
        return result


@router.get("/relationships", summary="Get schedule relationships")
async def get_schedule_relationships(
    external_schedule_id: Optional[int] = Query(None, description="Filter by external schedule ID"),
    db: Session = Depends(get_db)
):
    relationships = get_relationships(db, external_schedule_id)
    return [
        {
            "id": r.id,
            "external_schedule_id": r.external_schedule_id,
            "predecessor_activity_id": r.predecessor_activity_id,
            "predecessor_activity_code": r.predecessor.activity_code if r.predecessor else None,
            "successor_activity_id": r.successor_activity_id,
            "successor_activity_code": r.successor.activity_code if r.successor else None,
            "relationship_type": r.relationship_type,
            "lag": r.lag,
            "lag_unit": r.lag_unit,
            "created_at": r.created_at,
        }
        for r in relationships
    ]


@router.get("/external-schedules", summary="Get all imported external schedules")
async def get_external_schedules(db: Session = Depends(get_db)):
    schedules = db.query(ExternalSchedule).order_by(ExternalSchedule.imported_at.desc()).all()
    return [
        {
            "id": s.id,
            "external_schedule_id": s.external_schedule_id,
            "schedule_name": s.schedule_name,
            "source_filename": s.source_filename,
            "source_format": s.source_format,
            "imported_at": s.imported_at,
            "activity_count": s.activities.count(),
        }
        for s in schedules
    ]


@router.get("/external-schedules/{schedule_id}/activities", summary="Get activities for an external schedule")
async def get_external_schedule_activities(
    schedule_id: int,
    db: Session = Depends(get_db)
):
    ext_schedule = db.query(ExternalSchedule).filter(ExternalSchedule.id == schedule_id).first()
    if not ext_schedule:
        raise HTTPException(status_code=404, detail="External schedule not found")

    activities = ext_schedule.activities.all()
    return [
        {
            "id": a.id,
            "activity_code": a.activity_code,
            "activity_name": a.activity_name,
            "discipline": a.discipline,
            "wbs": a.wbs,
            "planned_start": a.planned_start,
            "planned_finish": a.planned_finish,
            "actual_start": a.actual_start,
            "actual_finish": a.actual_finish,
            "external_activity_id": a.external_activity_id,
            "source_format": a.source_format,
        }
        for a in activities
    ]


@router.post("/matches/{match_id}/resolve", summary="Resolve a schedule match and write back actuals")
async def resolve_schedule_match(
    match_id: int,
    db: Session = Depends(get_db)
):
    """Resolve a match (planner review) and write actual start/finish back to schedule activity."""
    review = get_review_by_id(db, match_id)
    if not review:
        raise HTTPException(status_code=404, detail=f"Match/review {match_id} not found")
    
    if review.status != ReviewStatus.PENDING:
        raise HTTPException(status_code=400, detail=f"Match {match_id} is not pending (status: {review.status.value})")
    
    if not review.proposed_activity_id:
        raise HTTPException(status_code=400, detail=f"Match {match_id} has no proposed activity")
    
    event = db.query(ProgressEvent).filter(ProgressEvent.id == review.progress_event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail=f"Progress event {review.progress_event_id} not found")
    
    activity = db.query(ScheduleActivity).filter(ScheduleActivity.id == review.proposed_activity_id).first()
    if not activity:
        raise HTTPException(status_code=404, detail=f"Activity {review.proposed_activity_id} not found")
    
    if event.event_type == "START" and not activity.actual_start:
        activity.actual_start = event.event_date
        db.add(activity)
    elif event.event_type == "COMPLETE" and not activity.actual_finish:
        activity.actual_finish = event.event_date
        db.add(activity)
    
    event.activity_reference = activity.activity_code
    db.add(event)
    
    review.status = ReviewStatus.APPROVED
    review.final_activity_id = review.proposed_activity_id
    review.completed_at = func.now()
    
    from app.models.confidence import AuditRecord, DecisionType, ActorType
    from sqlalchemy.sql import func
    audit = AuditRecord(
        progress_event_id=review.progress_event_id,
        proposed_activity_id=review.proposed_activity_id,
        final_activity_id=review.proposed_activity_id,
        confidence_score=review.confidence_score,
        confidence_level=review.confidence_level,
        decision=DecisionType.APPROVED,
        actor_type=ActorType.PLANNER,
    )
    db.add(audit)
    
    db.commit()
    db.refresh(review)
    db.refresh(activity)
    
    return {
        "match_id": match_id,
        "activity_id": activity.id,
        "activity_code": activity.activity_code,
        "actual_start": activity.actual_start,
        "actual_finish": activity.actual_finish,
        "status": "resolved",
    }