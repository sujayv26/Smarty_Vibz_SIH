from pydantic import BaseModel
from datetime import date
from typing import List, Dict, Any, Optional


class DisciplineStats(BaseModel):
    discipline: str
    total_activities: int
    completed_activities: int
    in_progress_activities: int
    not_started_activities: int
    planned_duration_days: int
    actual_duration_days: Optional[int] = None
    variance_days: Optional[int] = None
    variance_pct: Optional[float] = None
    productivity_index: Optional[float] = None
    delay_events: int
    delay_days: int
    delay_categories: Dict[str, int]


class DisciplineSummaryResponse(BaseModel):
    disciplines: List[DisciplineStats]
    period_weeks: int


class DelayCategoryStats(BaseModel):
    category: str
    count: int
    total_days: int
    avg_days: float
    critical_path_count: int


class DelayPatternsResponse(BaseModel):
    by_category: List[DelayCategoryStats]
    by_discipline: Dict[str, Dict[str, int]]
    top_causes: List[Dict[str, Any]]
    total_delay_events: int
    total_delay_days: int
    period_weeks: int


class BenchmarkActivityType(BaseModel):
    activity_type: str
    unit: str
    planned_quantity: Optional[float] = None
    actual_quantity: Optional[float] = None
    planned_duration_days: Optional[float] = None
    actual_duration_days: Optional[float] = None
    productivity_rate: Optional[float] = None
    sample_size: int
    period_start: Optional[str] = None
    period_end: Optional[str] = None


class DisciplineBenchmark(BaseModel):
    discipline: str
    activity_types: List[BenchmarkActivityType]
    avg_productivity_rate: float
    total_planned_quantity: float
    total_actual_quantity: float
    total_planned_duration: float
    total_actual_duration: float
    sample_size: int


class BenchmarksResponse(BaseModel):
    benchmarks: List[DisciplineBenchmark]
    project_id: int


class WeeklyVariance(BaseModel):
    week_start: str
    planned_days: int
    actual_days: int
    variance_days: int
    variance_pct: float
    completed_count: int
    delay_events: int


class VarianceTrendResponse(BaseModel):
    trend: List[WeeklyVariance]
    period_weeks: int


class MatchingQualityResponse(BaseModel):
    total_reviews: int
    auto_commit_rate: float
    review_rate: float
    correction_rate: float
    rejection_rate: float
    new_activity_rate: float
    avg_confidence: float
    period_weeks: int


class ConfidenceDistributionResponse(BaseModel):
    distribution: Dict[str, float]
    counts: Dict[str, int]
    total: int
    period_weeks: int