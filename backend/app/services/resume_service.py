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
        linkedin = ""
        skills = []
        education = []
        experience = []
        projects = []
        certificates = []
        languages = []

        for line in lines:
            parts = [p.strip() for p in line.split("|")] if "|" in line else ([p.strip() for p in line.split("•")] if "•" in line else [line])
            for part in parts:
                part_lower = part.lower()
                if "@" in part and not email:
                    import re
                    email_match = re.search(r'[\w.+-]+@[\w-]+\.[\w.-]+', part)
                    if email_match:
                        email = email_match.group()
                if not phone and "@" not in part:
                    digits_count = sum(1 for c in part if c.isdigit())
                    if digits_count >= 7 and any(char in part for char in ["+", "(", "-", " "]):
                        phone = part
                if not location and "@" not in part and part != name:
                    if any(kw in part_lower for kw in ["city", "state", "country", "address", "location"]):
                        location = part
                    elif any(c in part_lower for c in ["pakistan", "india", "karachi", "lahore", "islamabad", "rawalpindi", "dubai", "london", "new york", "san francisco", "tokyo"]):
                        location = part
                if "linkedin.com" in part_lower and not linkedin:
                    linkedin = part

        header_mapping = {
            "skills": ["skills", "technical skills", "technologies", "skills & technologies", "skills and technologies", "proficiencies", "core competencies", "skills & tools", "technical proficiencies"],
            "education": ["education", "academic background", "academic profile", "academic history", "education & credentials", "academic credentials"],
            "experience": ["experience", "work experience", "employment history", "work history", "professional experience", "professional history", "employment", "relevant experience"],
            "projects": ["projects", "personal projects", "key projects", "academic projects", "featured projects"],
            "certificates": ["certifications", "certificates", "licenses", "credentials", "awards & certifications"],
            "languages": ["languages", "languages known", "foreign languages"]
        }

        current_section = None
        for line in lines:
            line_clean = line.strip()
            lower_clean = line_clean.lower().replace(":", "").replace(" - ", "").replace(" | ", "").strip()
            
            # Check if this line is a known section header
            found_section = None
            for section_key, headers in header_mapping.items():
                if lower_clean in headers:
                    found_section = section_key
                    break
            
            if found_section:
                current_section = found_section
            else:
                # Check if it looks like a generic section header to stop adding to previous section
                is_generic_header = False
                if len(line_clean) < 40 and any(c.isalpha() for c in line_clean):
                    is_all_caps = line_clean == line_clean.upper()
                    has_connector = any(conn in line_clean.lower() for conn in [" & ", " and ", " or "])
                    if (is_all_caps or has_connector) and not line_clean.startswith(("●", "•", "-", "*")):
                        is_generic_header = True
                
                if is_generic_header:
                    current_section = None
                elif current_section and line_clean:
                    if current_section == "skills":
                        # Split by commas and newlines to get individual skills
                        for part in line_clean.replace(",", "\n").split("\n"):
                            part_clean = part.strip().lstrip("•-*●▪▪◦ ").strip()
                            if part_clean:
                                skills.append(part_clean)
                    elif current_section == "education":
                        education.append(line_clean)
                    elif current_section == "experience":
                        experience.append(line_clean)
                    elif current_section == "projects":
                        projects.append(line_clean)
                    elif current_section == "certificates":
                        certificates.append(line_clean)
                    elif current_section == "languages":
                        languages.append(line_clean)

        return {
            "name": name,
            "email": email,
            "phone": phone,
            "location": location,
            "linkedin": linkedin,
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
