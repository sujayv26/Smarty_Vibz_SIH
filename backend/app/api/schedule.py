from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.schedule_service import validate_schedule_excel, insert_schedule_activities, get_all_activities
from app.schemas.schedule import ScheduleActivityResponse, ScheduleUploadResponse

router = APIRouter(prefix="/schedule", tags=["Schedule"])

@router.post("/upload", response_model=ScheduleUploadResponse)
async def upload_schedule(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="Only .xlsx files are supported")
    
    try:
        valid_rows, errors = validate_schedule_excel(file.file)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    inserted = insert_schedule_activities(db, valid_rows)
    
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