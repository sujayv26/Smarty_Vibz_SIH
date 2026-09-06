from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Date, Index, Text, Enum as SQLEnum, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class ModelVersion(str, enum.Enum):
    V1 = "v1"
    V2 = "v2"


class DelayPrediction(Base):
    __tablename__ = "delay_predictions"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    wbs_node_id = Column(Integer, ForeignKey("wbs_nodes.id"), nullable=False, index=True)
    model_version = Column(String, nullable=False, default="v1")
    
    # Predictions
    delay_probability = Column(Float, nullable=False)  # 0.0 to 1.0
    expected_delay_days = Column(Float, nullable=False)  # Expected magnitude
    confidence_score = Column(Float, nullable=False)  # Model confidence 0.0 to 1.0
    risk_level = Column(SQLEnum("LOW", "MEDIUM", "HIGH", "CRITICAL", name="risklevel"), nullable=False)
    
    # Feature importance (JSON string)
    feature_importance = Column(Text, nullable=True)
    
    # Metadata
    features_json = Column(Text, nullable=True)  # Input features used
    prediction_date = Column(Date, nullable=False)
    valid_until = Column(Date, nullable=True)  # When prediction expires
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    project = relationship("Project", backref="delay_predictions")
    wbs_node = relationship("WBSNode", backref="delay_predictions")

    __table_args__ = (
        Index("ix_delay_predictions_project_node", "project_id", "wbs_node_id", unique=True),
        Index("ix_delay_predictions_project_risk", "project_id", "risk_level"),
        Index("ix_delay_predictions_date", "prediction_date"),
    )


class ModelTrainingRun(Base):
    __tablename__ = "model_training_runs"

    id = Column(Integer, primary_key=True, index=True)
    model_version = Column(String, nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True, index=True)  # NULL = global model
    
    # Training metrics
    train_samples = Column(Integer, nullable=False)
    test_samples = Column(Integer, nullable=False)
    auc_roc = Column(Float, nullable=True)
    auc_pr = Column(Float, nullable=True)
    mae_delay_days = Column(Float, nullable=True)  # Mean absolute error for delay magnitude
    rmse_delay_days = Column(Float, nullable=True)
    
    # Feature importance (JSON)
    feature_importance = Column(Text, nullable=True)
    
    # Training config
    hyperparameters = Column(Text, nullable=True)
    feature_list = Column(Text, nullable=True)
    
    status = Column(String, nullable=False, default="completed")  # completed, failed, in_progress
    error_message = Column(Text, nullable=True)
    
    started_at = Column(DateTime(timezone=True), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    project = relationship("Project", backref="training_runs")

    __table_args__ = (
        Index("ix_training_runs_project_version", "project_id", "model_version"),
        Index("ix_training_runs_date", "started_at"),
    )