from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Literal


ImpactType = Literal["DIRECT", "PROPAGATED", "FLOAT_CONSUMED", "CRITICAL_PATH"]


class DelayImpactResponse(BaseModel):
    id: int
    project_id: int
    source_event_id: int
    source_wbs_node_id: Optional[int] = None
    impacted_wbs_node_id: int
    impact_type: ImpactType
    relationship_type: Optional[str] = None
    lag_days: int
    original_delay_days: int
    propagated_delay_days: int
    float_consumed_days: int
    remaining_float_days: Optional[int] = None
    is_critical_path: bool
    critical_path_exposure: bool
    path_depth: int
    computed_at: datetime

    # Related data (populated by service)
    source_activity_code: Optional[str] = None
    source_activity_name: Optional[str] = None
    impacted_activity_code: Optional[str] = None
    impacted_activity_name: Optional[str] = None
    impacted_discipline: Optional[str] = None
    impacted_wbs: Optional[str] = None
    impacted_planned_start: Optional[str] = None
    impacted_planned_finish: Optional[str] = None

    class Config:
        from_attributes = True


class DelayImpactListResponse(BaseModel):
    impacts: List[DelayImpactResponse]
    total_impacted_activities: int
    max_propagated_delay: int
    critical_path_impacts: int


class DelayImpactSummaryResponse(BaseModel):
    project_id: int
    total_delay_events: int
    total_impacted_activities: int
    critical_path_activities_at_risk: int
    max_delay_days: int
    recent_impacts: List[DelayImpactResponse]