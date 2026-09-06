from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.schedule_service import validate_schedule_excel, insert_schedule_activities, get_all_activities
from app.schemas.schedule import ScheduleActivityResponse, ScheduleUploadResponse
from app.core.auth import get_current_user
from app.models.project import Project
import io

router = APIRouter(prefix="/schedule", tags=["Schedule"])

@router.post("/upload", response_model=ScheduleUploadResponse)
async def upload_schedule(
    file: UploadFile = File(...),
    project_id: int = Query(None, description="Project ID to associate the schedule with"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    if not file.filename.endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="Only .xlsx files are supported")
    
    # Determine project_id
    if project_id is None:
        # Use the first project for the user's organization
        project = db.query(Project).filter(Project.organization_id == current_user.organization_id).first()
        if not project:
            raise HTTPException(status_code=400, detail="No project found for your organization. Please create a project first or specify project_id.")
        project_id = project.id
    else:
        # Verify the project belongs to the user's organization
        project = db.query(Project).filter(Project.id == project_id, Project.organization_id == current_user.organization_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found or access denied")
    
    try:
        content = await file.read()
        file_bytes = io.BytesIO(content)
        valid_rows, errors = validate_schedule_excel(file_bytes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    inserted = insert_schedule_activities(db, valid_rows, current_user.organization_id, project_id)
    
    return ScheduleUploadResponse(
        total_rows=len(valid_rows) + len(errors),
        inserted_rows=inserted,
        failed_rows=len(errors),
        errors=errors
    )

@router.get("/activities", response_model=list[ScheduleActivityResponse])
async def get_activities(db: Session = Depends(get_db)):
    activities = get_all_activities(db)
    return activities