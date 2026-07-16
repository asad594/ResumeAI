import os
import uuid
import pdfplumber
from docx import Document
from sqlalchemy.orm import Session
from fastapi import UploadFile
from app.models.resume import Resume
from app.core.exceptions import InvalidFileTypeException, FileTooLargeException, NotFoundException
from app.core.config import settings
from loguru import logger


ALLOWED_TYPES = {".pdf", ".docx"}
MAX_SIZE_BYTES = settings.MAX_FILE_SIZE_MB * 1024 * 1024


class ResumeService:
    def __init__(self, db: Session):
        self.db = db
        self.upload_dir = "uploads/resumes"
        os.makedirs(self.upload_dir, exist_ok=True)

    async def upload_resume(self, user_id: int, file: UploadFile) -> Resume:
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in ALLOWED_TYPES:
            raise InvalidFileTypeException(list(ALLOWED_TYPES))

        content = await file.read()
        if len(content) > MAX_SIZE_BYTES:
            raise FileTooLargeException(settings.MAX_FILE_SIZE_MB)

        unique_name = f"{uuid.uuid4()}{ext}"
        file_path = os.path.join(self.upload_dir, unique_name)

        with open(file_path, "wb") as f:
            f.write(content)

        extracted_data = self._extract_data(file_path, ext)

        resume = Resume(
            user_id=user_id,
            filename=unique_name,
            original_filename=file.filename,
            file_path=file_path,
            file_type=ext.replace(".", ""),
            file_size=len(content),
            extracted_data=extracted_data,
        )
        self.db.add(resume)
        self.db.commit()
        self.db.refresh(resume)
        return resume

    def _extract_data(self, file_path: str, ext: str) -> dict:
        try:
            if ext == ".pdf":
                return self._extract_from_pdf(file_path)
            elif ext == ".docx":
                return self._extract_from_docx(file_path)
        except Exception as e:
            logger.error(f"Error extracting data: {e}")
            return {"raw_text": "Extraction failed"}

    def _extract_from_pdf(self, file_path: str) -> dict:
        text = ""
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"

        return self._parse_resume_text(text)

    def _extract_from_docx(self, file_path: str) -> dict:
        doc = Document(file_path)
        text = "\n".join([para.text for para in doc.paragraphs])
        return self._parse_resume_text(text)

    def _parse_resume_text(self, text: str) -> dict:
        lines = [line.strip() for line in text.split("\n") if line.strip()]

        name = lines[0] if lines else "Unknown"
        email = ""
        phone = ""
        location = ""
        skills = []
        education = []
        experience = []
        projects = []
        certificates = []
        languages = []

        for line in lines:
            lower = line.lower()
            if "@" in line and not email:
                import re
                email_match = re.search(r'[\w.+-]+@[\w-]+\.[\w.-]+', line)
                if email_match:
                    email = email_match.group()
            if any(c.isdigit() for c in line) and ("+" in line or "(" in line) and not phone:
                phone = line
            if any(kw in lower for kw in ["city", "state", "country", "address", "location"]) and not location:
                location = line

        sections = {
            "skills": ["skills", "technical skills", "technologies", "proficiencies"],
            "education": ["education", "academic", "degree", "university", "college"],
            "experience": ["experience", "work experience", "employment", "work history"],
            "projects": ["projects", "personal projects", "key projects"],
            "certificates": ["certifications", "certificates", "licenses"],
            "languages": ["languages", "foreign languages"],
        }

        current_section = None
        for line in lines:
            lower = line.lower().strip()
            for section_key, keywords in sections.items():
                if any(kw in lower for kw in keywords) and len(line) < 50:
                    current_section = section_key
                    break
            else:
                if current_section and line not in ["", " "]:
                    if current_section == "skills":
                        skill_items = [s.strip() for s in line.replace("•", "").replace("-", "").replace(",", "\n").split("\n") if s.strip()]
                        skills.extend(skill_items)
                    elif current_section == "education":
                        education.append(line)
                    elif current_section == "experience":
                        experience.append(line)
                    elif current_section == "projects":
                        projects.append(line)
                    elif current_section == "certificates":
                        certificates.append(line)
                    elif current_section == "languages":
                        languages.append(line)

        return {
            "name": name,
            "email": email,
            "phone": phone,
            "location": location,
            "skills": list(set(skills)) if skills else [],
            "education": education[:10],
            "experience": experience[:15],
            "projects": projects[:10],
            "certificates": certificates[:5],
            "languages": languages[:5],
            "raw_text": text[:5000],
        }

    def get_by_id(self, resume_id: int) -> Resume:
        resume = self.db.query(Resume).filter(Resume.id == resume_id).first()
        if not resume:
            raise NotFoundException("Resume not found")
        return resume

    def get_user_resumes(self, user_id: int) -> list:
        return self.db.query(Resume).filter(Resume.user_id == user_id).order_by(Resume.created_at.desc()).all()

    def delete(self, resume_id: int, user_id: int) -> None:
        resume = self.db.query(Resume).filter(Resume.id == resume_id, Resume.user_id == user_id).first()
        if not resume:
            raise NotFoundException("Resume not found")
        if os.path.exists(resume.file_path):
            os.remove(resume.file_path)
        self.db.delete(resume)
        self.db.commit()
