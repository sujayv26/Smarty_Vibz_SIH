from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum as SQLEnum, Boolean, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class ConfidenceLevel(str, enum.Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class ReviewStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    CORRECTED = "CORRECTED"
    REJECTED = "REJECTED"
    NEW_ACTIVITY_CREATED = "NEW_ACTIVITY_CREATED"


class DecisionType(str, enum.Enum):
    AUTO_MATCH = "AUTO_MATCH"
    APPROVED = "APPROVED"
    CORRECTED = "CORRECTED"
    REJECTED = "REJECTED"
    NEW_ACTIVITY_CREATED = "NEW_ACTIVITY_CREATED"


class ActorType(str, enum.Enum):
    SYSTEM = "SYSTEM"
    PLANNER = "PLANNER"


class ConfidenceResult(Base):
    __tablename__ = "confidence_results"

    id = Column(Integer, primary_key=True, index=True)
    progress_event_id = Column(Integer, ForeignKey("progress_events.id"), nullable=False, index=True)
    proposed_activity_id = Column(Integer, ForeignKey("schedule_activities.id"), nullable=True)
    confidence_score = Column(Float, nullable=False)
    confidence_level = Column(SQLEnum(ConfidenceLevel), nullable=False)
    decision = Column(SQLEnum(DecisionType), nullable=False)
    score_gap = Column(Float, nullable=True)
    exact_identifier_strength = Column(Float, nullable=True)
    fuzzy_similarity = Column(Float, nullable=True)
    semantic_similarity = Column(Float, nullable=True)
    discipline_compatibility = Column(Float, nullable=True)
    context_compatibility = Column(Float, nullable=True)
    temporal_compatibility = Column(Float, nullable=True)
    missing_information_penalty = Column(Float, nullable=True)
    candidate_ambiguity_penalty = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    progress_event = relationship("ProgressEvent")
    proposed_activity = relationship("ScheduleActivity")


class PlannerReview(Base):
    __tablename__ = "planner_reviews"

    id = Column(Integer, primary_key=True, index=True)
    progress_event_id = Column(Integer, ForeignKey("progress_events.id"), nullable=False, index=True)
    proposed_activity_id = Column(Integer, ForeignKey("schedule_activities.id"), nullable=True)
    final_activity_id = Column(Integer, ForeignKey("schedule_activities.id"), nullable=True)
    new_activity_id = Column(Integer, ForeignKey("schedule_activities.id"), nullable=True)
    confidence_score = Column(Float, nullable=False)
    confidence_level = Column(SQLEnum(ConfidenceLevel), nullable=False)
    status = Column(SQLEnum(ReviewStatus), default=ReviewStatus.PENDING, nullable=False)
    top_candidates_json = Column(Text, nullable=True)
    score_breakdown_json = Column(Text, nullable=True)
    matching_reasons_json = Column(Text, nullable=True)
    reviewer_note = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    progress_event = relationship("ProgressEvent")
    proposed_activity = relationship("ScheduleActivity", foreign_keys=[proposed_activity_id])
    final_activity = relationship("ScheduleActivity", foreign_keys=[final_activity_id])
    new_activity = relationship("ScheduleActivity", foreign_keys=[new_activity_id])


class AuditRecord(Base):
    __tablename__ = "audit_records"

    id = Column(Integer, primary_key=True, index=True)
    progress_event_id = Column(Integer, ForeignKey("progress_events.id"), nullable=False, index=True)
    proposed_activity_id = Column(Integer, ForeignKey("schedule_activities.id"), nullable=True)
    final_activity_id = Column(Integer, ForeignKey("schedule_activities.id"), nullable=True)
    new_activity_id = Column(Integer, ForeignKey("schedule_activities.id"), nullable=True)
    confidence_score = Column(Float, nullable=False)
    confidence_level = Column(SQLEnum(ConfidenceLevel), nullable=False)
    decision = Column(SQLEnum(DecisionType), nullable=False)
    reviewer_note = Column(Text, nullable=True)
    actor_type = Column(SQLEnum(ActorType), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    progress_event = relationship("ProgressEvent")
    proposed_activity = relationship("ScheduleActivity", foreign_keys=[proposed_activity_id])
    final_activity = relationship("ScheduleActivity", foreign_keys=[final_activity_id])
    new_activity = relationship("ScheduleActivity", foreign_keys=[new_activity_id])