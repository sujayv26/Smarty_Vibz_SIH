from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.progress_service import extract_and_store_progress, get_all_progress_events
from app.services.excel_progress_service import validate_excel_progress, process_excel_progress
from app.schemas.progress import ProgressExtractRequest, ProgressExtractResponse, ProgressEventResponse

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