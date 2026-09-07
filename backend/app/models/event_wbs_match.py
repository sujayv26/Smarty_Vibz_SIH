from sqlalchemy import Column, Integer, String, DateTime, Text, Float, ForeignKey, Enum as SQLEnum, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class MatchType(str, enum.Enum):
    EXACT = "EXACT"
    FUZZY = "FUZZY"
    SEMANTIC = "SEMANTIC"
    CONTEXTUAL = "CONTEXTUAL"
    NEW_ACTIVITY = "NEW_ACTIVITY"


class EventWBSMatch(Base):
    __tablename__ = "event_wbs_matches"

    id = Column(Integer, primary_key=True, index=True)
    progress_event_id = Column(Integer, ForeignKey("progress_events.id"), nullable=False, index=True)
    wbs_node_id = Column(Integer, ForeignKey("wbs_nodes.id"), nullable=True, index=True)
    match_type = Column(SQLEnum(MatchType), nullable=False)
    confidence_score = Column(Float, nullable=False)
    progress_contribution_pct = Column(Float, nullable=True)
    score_breakdown_json = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    progress_event = relationship("ProgressEvent", backref="wbs_matches")
    wbs_node = relationship("WBSNode", backref="event_matches")

    __table_args__ = (
        Index("ix_event_wbs_matches_event_node", "progress_event_id", "wbs_node_id"),
    )