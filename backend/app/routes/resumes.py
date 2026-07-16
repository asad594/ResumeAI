from fastapi import APIRouter, Depends, UploadFile, File, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.deps import get_current_user
from app.schemas.analysis import ResumeResponse, ResumeUploadResponse
from app.services.resume_service import ResumeService
from app.models.user import User

router = APIRouter(prefix="/resumes", tags=["Resumes"])


@router.post("/upload", response_model=ResumeUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = ResumeService(db)
    resume = await service.upload_resume(current_user.id, file)
    return ResumeUploadResponse(id=resume.id, filename=resume.original_filename, message="Resume uploaded successfully")


@router.get("/", response_model=List[ResumeResponse])
async def get_resumes(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = ResumeService(db)
    resumes = service.get_user_resumes(current_user.id)
    return [ResumeResponse.model_validate(r) for r in resumes]


@router.get("/{resume_id}", response_model=ResumeResponse)
async def get_resume(
    resume_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = ResumeService(db)
    resume = service.get_by_id(resume_id)
    return ResumeResponse.model_validate(resume)


@router.delete("/{resume_id}")
async def delete_resume(
    resume_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = ResumeService(db)
    service.delete(resume_id, current_user.id)
    return {"message": "Resume deleted successfully"}
