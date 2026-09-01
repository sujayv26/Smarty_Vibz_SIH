from pydantic import BaseModel, field_validator
from datetime import date
from typing import Optional, Literal, List
from enum import Enum


class MatchCategory(str, Enum):
    EXACT_MATCH = "EXACT_MATCH"
    FUZZY_WORDING = "FUZZY_WORDING"
    AMBIGUOUS_TAG = "AMBIGUOUS_TAG"
    MISSING_FIELDS = "MISSING_FIELDS"
    NO_MATCH = "NO_MATCH"
    MULTI_DISCIPLINE = "MULTI_DISCIPLINE"


class ComponentScores(BaseModel):
    exact: float = 0.0
    semantic: float = 0.0
    fuzzy: float = 0.0
    discipline: float = 0.0
    context: float = 0.0
    temporal: float = 0.0


class MatchedActivity(BaseModel):
    activity_id: int
    activity_code: str
    activity_name: str
    discipline: str
    wbs: str
    planned_start: date
    planned_finish: date
    final_score: float
    component_scores: ComponentScores
    reasons: List[str]


class MatchingResult(BaseModel):
    progress_event_id: int
    top_matches: List[MatchedActivity]


class BenchmarkReport(BaseModel):
    progress_event_id: int
    expected_activity_code: Optional[str] = None
    category: MatchCategory
    top1_match: Optional[str] = None
    top3_matches: List[str]
    top1_correct: bool
    top3_correct: bool
    final_scores: List[float]


class BenchmarkSummary(BaseModel):
    total_reports: int
    top1_accuracy: float
    top3_accuracy: float
    category_results: dict
    reports: List[BenchmarkReport]


class MatchingRunRequest(BaseModel):
    progress_event_id: int


class MatchingRunResponse(BaseModel):
    progress_event_id: int
    top_matches: List[MatchedActivity]


class BenchmarkRequest(BaseModel):
    pass


class BenchmarkResponse(BaseModel):
    summary: BenchmarkSummary