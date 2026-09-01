from pydantic import BaseModel, field_validator
from datetime import datetime, date
from typing import Optional, List, Literal
from app.matching.schemas import MatchedActivity, ComponentScores


ConfidenceLevel = Literal["HIGH", "MEDIUM", "LOW"]
ReviewStatus = Literal["PENDING", "APPROVED", "CORRECTED", "REJECTED", "NEW_ACTIVITY_CREATED"]
DecisionType = Literal["AUTO_MATCH", "APPROVED", "CORRECTED", "REJECTED", "NEW_ACTIVITY_CREATED", "REVIEW_REQUIRED"]
ActorType = Literal["SYSTEM", "PLANNER"]


class ConfidenceScoreBreakdown(BaseModel):
    exact_identifier_strength: float
    fuzzy_similarity: float
    semantic_similarity: float
    discipline_compatibility: float
    context_compatibility: float
    temporal_compatibility: float
    missing_information_penalty: float
    candidate_ambiguity_penalty: float


class ConfidenceEvaluationRequest(BaseModel):
    progress_event_id: int


class ProposedActivity(BaseModel):
    activity_id: int
    activity_code: str
    activity_name: str
    discipline: str


class ConfidenceEvaluationResponse(BaseModel):
    progress_event_id: int
    proposed_activity: Optional[ProposedActivity] = None
    confidence_score: float
    confidence_level: ConfidenceLevel
    decision: DecisionType
    requires_review: bool
    review_id: Optional[int] = None
    score_breakdown: Optional[ConfidenceScoreBreakdown] = None
    top_candidates: List[MatchedActivity] = []


class ReviewCandidate(BaseModel):
    activity_id: int
    activity_code: str
    activity_name: str
    discipline: str
    final_score: float
    component_scores: ComponentScores
    reasons: List[str]


class PlannerReviewResponse(BaseModel):
    review_id: int
    progress_event_id: int
    proposed_activity: Optional[ProposedActivity] = None
    confidence_score: float
    confidence_level: ConfidenceLevel
    status: ReviewStatus
    top_candidates: List[ReviewCandidate] = []
    score_breakdown: Optional[ConfidenceScoreBreakdown] = None
    matching_reasons: List[str] = []
    reviewer_note: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None


class PlannerReviewListResponse(BaseModel):
    reviews: List[PlannerReviewResponse]


class ReviewApproveRequest(BaseModel):
    reviewer_note: Optional[str] = None


class ReviewCorrectRequest(BaseModel):
    activity_id: int
    reviewer_note: Optional[str] = None

    @field_validator("activity_id")
    @classmethod
    def positive_id(cls, v):
        if v <= 0:
            raise ValueError("activity_id must be positive")
        return v


class ReviewRejectRequest(BaseModel):
    reviewer_note: Optional[str] = None


class CreateNewActivityRequest(BaseModel):
    activity_code: str
    activity_name: str
    discipline: str
    wbs: Optional[str] = None
    planned_start: Optional[date] = None
    planned_finish: Optional[date] = None
    reviewer_note: Optional[str] = None

    @field_validator("activity_code")
    @classmethod
    def non_empty_code(cls, v):
        if not v or not v.strip():
            raise ValueError("activity_code cannot be empty")
        return v.strip()

    @field_validator("activity_name")
    @classmethod
    def non_empty_name(cls, v):
        if not v or not v.strip():
            raise ValueError("activity_name cannot be empty")
        return v.strip()

    @field_validator("discipline")
    @classmethod
    def non_empty_discipline(cls, v):
        if not v or not v.strip():
            raise ValueError("discipline cannot be empty")
        return v.strip()


class AuditRecordResponse(BaseModel):
    id: int
    progress_event_id: int
    proposed_activity_id: Optional[int] = None
    final_activity_id: Optional[int] = None
    new_activity_id: Optional[int] = None
    confidence_score: float
    confidence_level: ConfidenceLevel
    decision: DecisionType
    reviewer_note: Optional[str] = None
    actor_type: ActorType
    created_at: datetime

    class Config:
        from_attributes = True


class AuditTrailResponse(BaseModel):
    progress_event_id: int
    audit_records: List[AuditRecordResponse]