from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime


class ResumeResponse(BaseModel):
    id: int
    filename: str
    original_filename: str
    file_type: str
    file_size: int
    extracted_data: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ResumeUploadResponse(BaseModel):
    id: int
    filename: str
    message: str


class AnalysisCreate(BaseModel):
    resume_id: int
    job_description: Optional[str] = None


class ATSScore(BaseModel):
    overall: float
    formatting: float
    keywords: float
    experience: float
    education: float
    skills: float


class AnalysisResponse(BaseModel):
    id: int
    resume_id: int
    ats_score: Optional[float] = None
    ats_details: Optional[Dict[str, float]] = None
    missing_skills: Optional[List[str]] = None
    matched_skills: Optional[List[str]] = None
    partial_skills: Optional[List[str]] = None
    match_percentage: Optional[float] = None
    suggestions: Optional[List[Dict[str, Any]]] = None
    job_match: Optional[Dict[str, Any]] = None
    job_description: Optional[str] = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class HistoryResponse(BaseModel):
    analyses: List[AnalysisResponse]
    total: int
    page: int
    per_page: int


class JobDescriptionCreate(BaseModel):
    title: str
    company: Optional[str] = None
    description: str


class JobDescriptionResponse(BaseModel):
    id: int
    title: str
    company: Optional[str] = None
    description: str
    saved: int
    created_at: datetime

    class Config:
        from_attributes = True


class AnalyticsResponse(BaseModel):
    total_analyses: int
    average_ats_score: float
    most_common_skills: List[Dict[str, Any]]
    weekly_activity: List[Dict[str, Any]]
    score_distribution: Dict[str, int]


class JobMatchResult(BaseModel):
    similarity_score: float
    recommended_roles: List[Dict[str, Any]]
