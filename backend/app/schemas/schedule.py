from pydantic import BaseModel, field_validator
from datetime import date, datetime
from typing import Optional

class ScheduleActivityBase(BaseModel):
    activity_code: str
    activity_name: str
    discipline: str
    wbs: str
    planned_start: date
    planned_finish: date

class ScheduleActivityCreate(ScheduleActivityBase):
    @field_validator("planned_finish")
    @classmethod
    def finish_after_start(cls, v, info):
        if info.data.get("planned_start") and v < info.data["planned_start"]:
            raise ValueError("planned_finish must be after planned_start")
        return v

class ScheduleActivityResponse(ScheduleActivityBase):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ScheduleUploadResponse(BaseModel):
    total_rows: int
    inserted_rows: int
    failed_rows: int
    errors: list[dict]