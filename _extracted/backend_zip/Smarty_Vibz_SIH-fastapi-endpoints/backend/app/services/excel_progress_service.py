import pandas as pd
from datetime import date
from typing import Optional
from sqlalchemy.orm import Session
from app.models.progress import ProgressEvent
from app.schemas.progress import ProgressEventCreate, EventType
from app.services.extraction_service import get_extraction_provider

STATUS_TO_EVENT_TYPE = {
    "started": "START",
    "in progress": "PROGRESS",
    "inprogress": "PROGRESS",
    "completed": "COMPLETE",
    "complete": "COMPLETE",
    "delayed": "DELAY",
    "on hold": "HOLD",
    "hold": "HOLD",
}

REQUIRED_COLUMNS = ["date", "activity_description", "status"]

def validate_excel_progress(file) -> tuple[list[dict], list[dict]]:
    df = pd.read_excel(file, engine="openpyxl")
    
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    if df.empty:
        raise ValueError("Excel file is empty")
    
    valid_rows = []
    errors = []
    
    for idx, row in df.iterrows():
        row_num = idx + 2
        row_data = row.to_dict()
        row_errors = []
        
        if pd.isna(row_data.get("date")):
            row_errors.append("Missing required field: date")
        
        if pd.isna(row_data.get("activity_description")):
            row_errors.append("Missing required field: activity_description")
        
        event_date = None
        if not pd.isna(row_data.get("date")):
            try:
                event_date = pd.to_datetime(row_data["date"]).date()
            except Exception:
                row_errors.append("Invalid date format")
        
        status = str(row_data.get("status", "")).strip().lower() if not pd.isna(row_data.get("status")) else ""
        event_type = STATUS_TO_EVENT_TYPE.get(status, "PROGRESS")
        
        if row_errors:
            errors.append({"row": row_num, "errors": row_errors, "data": row_data})
        else:
            discipline = str(row_data.get("discipline", "")).strip() if not pd.isna(row_data.get("discipline")) else None
            equipment_tag = str(row_data.get("equipment_tag", "")).strip() if not pd.isna(row_data.get("equipment_tag")) else None
            location = str(row_data.get("location", "")).strip() if not pd.isna(row_data.get("location")) else None
            reported_by = str(row_data.get("reported_by", "")).strip() if not pd.isna(row_data.get("reported_by")) else None
            
            raw_text = f"{row_data['activity_description']}"
            if discipline:
                raw_text += f" (Discipline: {discipline})"
            if equipment_tag:
                raw_text += f" (Equipment: {equipment_tag})"
            if location:
                raw_text += f" (Location: {location})"
            if reported_by:
                raw_text += f" (Reported by: {reported_by})"
            
            valid_rows.append({
                "raw_text": raw_text,
                "activity_description": str(row_data["activity_description"]).strip(),
                "event_type": event_type,
                "event_date": event_date,
                "discipline": discipline,
                "equipment_tag": equipment_tag,
                "location": location,
                "reported_by": reported_by,
                "status": status,
            })
    
    return valid_rows, errors

def process_excel_progress(db: Session, valid_rows: list[dict], source_file: str) -> tuple[int, list[dict]]:
    provider = get_extraction_provider()
    inserted = 0
    row_errors = []
    
    for idx, row in enumerate(valid_rows):
        try:
            ai_extracted = provider.extract_progress(row["activity_description"])
            
            activity_reference = ai_extracted.activity_reference
            ai_equipment_tag = ai_extracted.equipment_tag
            ai_location = ai_extracted.location
            ai_discipline = ai_extracted.discipline
            
            equipment_tag = row["equipment_tag"] or ai_equipment_tag
            location = row["location"] or ai_location
            discipline = row["discipline"] or ai_discipline
            
            progress_event = ProgressEventCreate(
                raw_text=row["raw_text"],
                activity_reference=activity_reference,
                event_type=row["event_type"],
                event_date=row["event_date"],
                event_time=None,
                discipline=discipline,
                location=location,
                equipment_tag=equipment_tag,
                source_type="EXCEL",
                source_file=source_file,
                session_id=None
            )
            
            db_event = ProgressEvent(**progress_event.model_dump())
            db.add(db_event)
            inserted += 1
            
        except Exception as e:
            row_errors.append({"row": idx + 1, "errors": [str(e)], "data": row})
    
    db.commit()
    return inserted, row_errors

def get_all_progress_events(db: Session):
    return db.query(ProgressEvent).order_by(ProgressEvent.created_at.desc()).all()