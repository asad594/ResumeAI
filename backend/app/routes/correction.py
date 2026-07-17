from fastapi import APIRouter, Depends, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from app.core.database import get_db
from app.core.deps import get_current_user
from app.services.correction_service import CorrectionService
from app.models.user import User

router = APIRouter(prefix="/correction", tags=["Correction"])


class ChangeDetail(BaseModel):
    original: str
    corrected: str


class CorrectionResult(BaseModel):
    corrected_pdf: Optional[str] = None
    corrected_docx: Optional[str] = None
    changes: List[ChangeDetail]
    total_lines: int
    changed_lines: int
    message: str


@router.post("/correct", response_model=CorrectionResult)
async def correct_resume(
    resume_id: int = Query(..., description="ID of the resume to correct"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = CorrectionService(db)
    result = await service.correct_resume(resume_id, current_user.id)
    return CorrectionResult(
        corrected_pdf=result.get("corrected_pdf"),
        corrected_docx=result.get("corrected_docx"),
        changes=[ChangeDetail(**c) for c in result.get("changes", [])],
        total_lines=result.get("total_lines", 0),
        changed_lines=result.get("changed_lines", 0),
        message=f"Resume corrected successfully. {result.get('changed_lines', 0)} lines improved.",
    )


@router.get("/download/{filename}")
async def download_corrected(
    filename: str,
    current_user: User = Depends(get_current_user),
):
    service = CorrectionService(None)
    file_path = service.download_corrected_file(filename)

    media_type = "application/pdf" if filename.endswith(".pdf") else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type=media_type,
    )


@router.get("/preview/{filename}")
async def preview_corrected(
    filename: str,
    current_user: User = Depends(get_current_user),
):
    service = CorrectionService(None)
    file_path = service.download_corrected_file(filename)

    return FileResponse(
        path=file_path,
        media_type="application/pdf" if filename.endswith(".pdf") else "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )
