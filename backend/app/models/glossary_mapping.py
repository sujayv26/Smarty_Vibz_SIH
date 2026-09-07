from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class GlossaryMapping(Base):
    __tablename__ = "glossary_mappings"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True, index=True)
    source_term = Column(String, nullable=False)
    standardized_term = Column(String, nullable=False)
    discipline = Column(String, nullable=True)
    context = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    organization = relationship("Organization", backref="glossary_mappings")
    project = relationship("Project", backref="glossary_mappings")
    creator = relationship("User", backref="glossary_mappings")

    __table_args__ = (
        Index("ix_glossary_mappings_org_term", "organization_id", "source_term"),
        Index("ix_glossary_mappings_project_term", "project_id", "source_term"),
    )