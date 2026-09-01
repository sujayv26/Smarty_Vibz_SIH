import pandas as pd
from datetime import date
from typing import Optional
from sqlalchemy.orm import Session
from app.models.schedule import ScheduleActivity
from app.schemas.schedule import ScheduleActivityCreate, ScheduleUploadResponse

REQUIRED_COLUMNS = ["activity_code", "activity_name", "discipline", "wbs", "planned_start", "planned_finish"]

def validate_schedule_excel(file) -> tuple[list[dict], list[dict]]:
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
        
        for col in REQUIRED_COLUMNS:
            if pd.isna(row_data.get(col)):
                row_errors.append(f"Missing required field: {col}")
        
        try:
            planned_start = pd.to_datetime(row_data.get("planned_start")).date() if not pd.isna(row_data.get("planned_start")) else None
            planned_finish = pd.to_datetime(row_data.get("planned_finish")).date() if not pd.isna(row_data.get("planned_finish")) else None
            
            if planned_start and planned_finish and planned_finish < planned_start:
                row_errors.append("planned_finish must be after planned_start")
        except Exception as e:
            row_errors.append(f"Invalid date format: {e}")
        
        if row_errors:
            errors.append({"row": row_num, "errors": row_errors, "data": row_data})
        else:
            valid_rows.append({
                "activity_code": str(row_data["activity_code"]).strip(),
                "activity_name": str(row_data["activity_name"]).strip(),
                "discipline": str(row_data["discipline"]).strip(),
                "wbs": str(row_data["wbs"]).strip(),
                "planned_start": planned_start,
                "planned_finish": planned_finish,
            })
    
    return valid_rows, errors

def insert_schedule_activities(db: Session, valid_rows: list[dict]) -> int:
    inserted = 0
    for row in valid_rows:
        existing = db.query(ScheduleActivity).filter(
            ScheduleActivity.activity_code == row["activity_code"]
        ).first()
        if existing:
            existing.activity_name = row["activity_name"]
            existing.discipline = row["discipline"]
            existing.wbs = row["wbs"]
            existing.planned_start = row["planned_start"]
            existing.planned_finish = row["planned_finish"]
        else:
            activity = ScheduleActivity(**row)
            db.add(activity)
            inserted += 1
    db.commit()
    return inserted

def get_all_activities(db: Session) -> list[ScheduleActivity]:
    return db.query(ScheduleActivity).order_by(ScheduleActivity.activity_code).all()