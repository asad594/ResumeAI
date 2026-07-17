from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Float, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    resume_id = Column(Integer, ForeignKey("resumes.id"), nullable=False)
    ats_score = Column(Float, nullable=True)
    ats_details = Column(JSON, nullable=True)
    missing_skills = Column(JSON, nullable=True)
    matched_skills = Column(JSON, nullable=True)
    partial_skills = Column(JSON, nullable=True)
    match_percentage = Column(Float, nullable=True)
    suggestions = Column(JSON, nullable=True)
    job_match = Column(JSON, nullable=True)
    job_description = Column(Text, nullable=True)
    status = Column(String(50), default="completed")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    @property
    def overall_score(self) -> float:
        return self.ats_score or 0.0

    @property
    def breakdown(self) -> dict:
        if not self.ats_details:
            return {}
        return self.ats_details.get("breakdown", {})

    @property
    def category_suggestions(self) -> list:
        if not self.ats_details:
            return []
        return self.ats_details.get("category_suggestions", [])

    @property
    def job_matching_not_available(self) -> bool:
        return self.job_description is None

    user = relationship("User", back_populates="analyses")
    resume = relationship("Resume", back_populates="analyses")
