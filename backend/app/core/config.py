from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Resume Analyzer"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"

    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/resume_analyzer"
    SECRET_KEY: str = "your-super-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    OPENROUTER_API_KEY: str = ""
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    OPENROUTER_MODEL: str = "google/gemini-2.5-flash"
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    MAX_FILE_SIZE_MB: int = 10
    ENVIRONMENT: str = "development"

    # ATS Scoring Thresholds
    ATS_SCORE_MAX: int = 100
    ATS_SCORE_FORMATTING_NAME: int = 20
    ATS_SCORE_FORMATTING_EMAIL: int = 20
    ATS_SCORE_FORMATTING_PHONE: int = 15
    ATS_SCORE_FORMATTING_LOCATION: int = 10
    ATS_SCORE_EXPERIENCE_MULTIPLIER: int = 15
    ATS_SCORE_PROJECT_MULTIPLIER: int = 20
    ATS_SCORE_PROJECT_FALLBACK_MAX: int = 95
    ATS_SCORE_EDUCATION_MULTIPLIER: int = 30
    ATS_SCORE_SKILLS_MULTIPLIER: int = 8
    
    ATS_SUGGESTION_FORMATTING_THRESHOLD: int = 80
    ATS_SUGGESTION_SKILLS_MIN: int = 5
    
    ATS_DISTRIBUTION_EXCELLENT: int = 80
    ATS_DISTRIBUTION_GOOD: int = 60
    ATS_DISTRIBUTION_AVERAGE: int = 40

    # ATS Static Score Weights
    ATS_WEIGHT_FORMATTING: float = 0.2
    ATS_WEIGHT_KEYWORDS: float = 0.25
    ATS_WEIGHT_EXPERIENCE: float = 0.25
    ATS_WEIGHT_EDUCATION: float = 0.15
    ATS_WEIGHT_SKILLS: float = 0.20

    # Project to experience fallback multiplier
    ATS_PROJECT_TO_EXPERIENCE_MULTIPLIER: float = 0.95

    # LLM dynamic evaluation defaults
    ATS_LLM_DEFAULT_GRAMMAR: int = 100
    ATS_LLM_DEFAULT_ACTION_VERBS: int = 100
    ATS_LLM_DEFAULT_METRICS: int = 100

    # LLM language score weights
    ATS_WEIGHT_LLM_GRAMMAR: float = 0.4
    ATS_WEIGHT_LLM_ACTION_VERBS: float = 0.3
    ATS_WEIGHT_LLM_METRICS: float = 0.3

    # Dynamic blending weights
    ATS_WEIGHT_BASE_OVERALL: float = 0.7
    ATS_WEIGHT_LANGUAGE_QUALITY: float = 0.3

    # Recommended roles similarity offsets
    ATS_ROLE_MATCH_SOFTWARE_ENGINEER_OFFSET: float = 10.0
    ATS_ROLE_MATCH_BACKEND_DEVELOPER_OFFSET: float = 5.0
    ATS_ROLE_MATCH_FULL_STACK_DEVELOPER_OFFSET: float = -5.0
    ATS_ROLE_MATCH_DATA_ENGINEER_OFFSET: float = -10.0
    # ATS Breakdown and Threshold Configurations
    ATS_BREAKDOWN_THRESHOLD: int = 75
    ATS_MAX_CATEGORY_SCORE: int = 100
    ATS_MIN_SKILLS: int = 8
    ATS_MIN_KEYWORDS: int = 5
    ATS_MIN_METRICS: int = 75
    ATS_MIN_ACTION_VERBS: int = 80

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
