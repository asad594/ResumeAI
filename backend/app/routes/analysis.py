from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.core.deps import get_current_user
from app.schemas.analysis import (
    AnalysisCreate, AnalysisResponse, HistoryResponse,
    AnalyticsResponse
)
from app.services.analysis_service import AnalysisService
from app.models.user import User

router = APIRouter(prefix="/analysis", tags=["Analysis"])


@router.post("/", response_model=AnalysisResponse, status_code=status.HTTP_201_CREATED)
async def create_analysis(
    data: AnalysisCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = AnalysisService(db)
    analysis = service.create_analysis(current_user.id, data)
    return AnalysisResponse.model_validate(analysis)


@router.get("/", response_model=HistoryResponse)
async def get_history(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = AnalysisService(db)
    result = service.get_user_analyses(current_user.id, page, per_page)
    return HistoryResponse(
        analyses=[AnalysisResponse.model_validate(a) for a in result["analyses"]],
        total=result["total"],
        page=result["page"],
        per_page=result["per_page"],
    )


@router.get("/analytics", response_model=AnalyticsResponse)
async def get_analytics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = AnalysisService(db)
    return service.get_analytics(current_user.id)


@router.get("/{analysis_id}", response_model=AnalysisResponse)
async def get_analysis(
    analysis_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = AnalysisService(db)
    analysis = service.get_by_id(analysis_id)
    return AnalysisResponse.model_validate(analysis)


@router.delete("/{analysis_id}")
async def delete_analysis(
    analysis_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = AnalysisService(db)
    service.delete(analysis_id, current_user.id)
    return {"message": "Analysis deleted successfully"}
