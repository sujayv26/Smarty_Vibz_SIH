from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.xer.service import XERImportService, get_relationships
from app.models.xer import ExternalSchedule, ScheduleRelationship
from app.models.schedule import ScheduleActivity
from typing import Optional
from datetime import date
import io

router = APIRouter(prefix="/schedule", tags=["Schedule"])


@router.post("/import/p6", summary="Import Primavera P6 XER schedule")
async def import_p6_schedule(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    if not file.filename.endswith(".xer"):
        raise HTTPException(status_code=400, detail="Only .xer files are supported")

    try:
        content = await file.read()
        content_str = content.decode("utf-8", errors="replace")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read file: {str(e)}")

    service = XERImportService(db)
    try:
        result = service.import_xer(content_str, file.filename)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"XER parsing failed: {str(e)}")

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
            "external_activity_id": a.external_activity_id,
            "source_format": a.source_format,
        }
        for a in activities
    ]