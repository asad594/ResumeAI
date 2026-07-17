from fastapi import APIRouter, Depends, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from app.core.database import get_db
from app.core.deps import get_current_user
from app.services.correction_service import CorrectionService
from app.models.user import User
from loguru import logger

router = APIRouter(prefix="/correction", tags=["Correction"])


class ChangeDetail(BaseModel):
    original: str
    corrected: str


class DiffItem(BaseModel):
    original: str
    corrected: str
    changed: bool


from app.schemas.analysis import AnalysisResponse

class CorrectionResult(BaseModel):
    corrected_pdf: Optional[str] = None
    corrected_docx: Optional[str] = None
    changes: List[ChangeDetail]
    full_diff: Optional[List[DiffItem]] = None
    total_lines: int
    changed_lines: int
    message: str
    corrected_analysis: Optional[AnalysisResponse] = None


@router.post("/correct", response_model=CorrectionResult)
async def correct_resume(
    resume_id: int = Query(..., description="ID of the resume to correct"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    logger.info(f"CORRECTION START - Resume ID: {resume_id}, User ID: {current_user.id}")
    service = CorrectionService(db)
    result = await service.correct_resume(resume_id, current_user.id)
    logger.info(f"CORRECTION COMPLETE - Resume ID: {resume_id}, Changed: {result.get('changed_lines', 0)} / {result.get('total_lines', 0)} lines")
    return CorrectionResult(
        corrected_pdf=result.get("corrected_pdf"),
        corrected_docx=result.get("corrected_docx"),
        changes=[ChangeDetail(**c) for c in result.get("changes", [])],
        full_diff=[DiffItem(**d) for d in result.get("full_diff", [])] if "full_diff" in result else None,
        total_lines=result.get("total_lines", 0),
        changed_lines=result.get("changed_lines", 0),
        message=f"Resume corrected successfully. {result.get('changed_lines', 0)} lines improved.",
        corrected_analysis=AnalysisResponse.model_validate(result["corrected_analysis"]) if "corrected_analysis" in result and result["corrected_analysis"] else None,
    )


@router.get("/download/{filename}")
async def download_corrected(
    filename: str,
    current_user: User = Depends(get_current_user),
):
    logger.info(f"DOWNLOAD START - Filename: {filename}, User ID: {current_user.id}")
    service = CorrectionService(None)
    file_path = service.download_corrected_file(filename)
    logger.info(f"DOWNLOAD COMPLETE - File path served: {file_path}")

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
    logger.info(f"PREVIEW START - Filename: {filename}, User ID: {current_user.id}")
    import os
    service = CorrectionService(None)
    
    preview_filename = filename
    if filename.startswith("corrected_"):
        highlighted_filename = filename.replace("corrected_", "highlighted_", 1)
        possible_path = os.path.join(service.corrected_dir, highlighted_filename)
        if os.path.exists(possible_path):
            preview_filename = highlighted_filename

    file_path = service.download_corrected_file(preview_filename)
    logger.info(f"PREVIEW COMPLETE - File path served: {file_path}")

    return FileResponse(
        path=file_path,
        media_type="application/pdf" if preview_filename.endswith(".pdf") else "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )
