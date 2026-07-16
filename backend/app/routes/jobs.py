from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/jobs", tags=["Saved Jobs"])


@router.get("/")
async def get_saved_jobs(current_user: User = Depends(get_current_user)):
    return {"jobs": [], "message": "Saved jobs retrieved"}


@router.post("/save")
async def save_job(
    title: str,
    description: str,
    company: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.models.job_description import JobDescription
    job = JobDescription(
        user_id=current_user.id,
        title=title,
        company=company,
        description=description,
        saved=1,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return {"id": job.id, "message": "Job saved successfully"}


@router.delete("/{job_id}")
async def delete_saved_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.models.job_description import JobDescription
    from app.core.exceptions import NotFoundException
    job = db.query(JobDescription).filter(
        JobDescription.id == job_id,
        JobDescription.user_id == current_user.id
    ).first()
    if not job:
        raise NotFoundException("Job not found")
    db.delete(job)
    db.commit()
    return {"message": "Job deleted successfully"}
