import os
import json
import uuid
import pymupdf
from docx import Document
from sqlalchemy.orm import Session
from openai import OpenAI
from app.models.resume import Resume
from app.core.exceptions import NotFoundException, BadRequestException
from app.core.config import settings
from loguru import logger


FONT_MAP = {
    "arial": "helv",
    "helvetica": "helv",
    "calibri": "helv",
    "segoe ui": "helv",
    "open sans": "helv",
    "roboto": "helv",
    "lato": "helv",
    "montserrat": "helv",
    "times new roman": "tiro",
    "times": "tiro",
    "georgia": "tiro",
    "garamond": "tiro",
    "palatino": "tiro",
    "courier new": "cour",
    "courier": "cour",
    "consolas": "cour",
    "monaco": "cour",
}

AI_SYSTEM_PROMPT = """You are a professional resume editor. Your ONLY job is to improve the text quality of resume content.

RULES - You MUST follow these exactly:
1. ONLY correct: grammar, spelling, punctuation, sentence structure
2. ONLY improve: weak bullet points, action verbs, ATS keywords, readability, professional tone
3. NEVER change: the meaning, facts, dates, names, companies, skills, or any factual content
4. NEVER add: fake information, new skills, new projects, new experience, new certifications
5. NEVER remove: any user content, sections, or information
6. Keep the same line structure - one corrected line per original line
7. Return ONLY the corrected text, nothing else

You will receive numbered lines of resume text. Return the corrected version with the SAME line numbers.
Format your response as a JSON array of objects with "line_num" and "corrected" fields."""


class CorrectionService:
    def __init__(self, db: Session):
        self.db = db
        self.corrected_dir = "uploads/corrected"
        os.makedirs(self.corrected_dir, exist_ok=True)
        self.openai_client = None
        if settings.OPENAI_API_KEY:
            kwargs = {"api_key": settings.OPENAI_API_KEY}
            if settings.OPENAI_BASE_URL:
                kwargs["base_url"] = settings.OPENAI_BASE_URL
            self.openai_client = OpenAI(**kwargs)

    async def correct_resume(self, resume_id: int, user_id: int) -> dict:
        resume = self.db.query(Resume).filter(
            Resume.id == resume_id, Resume.user_id == user_id
        ).first()
        if not resume:
            raise NotFoundException("Resume not found")

        if not os.path.exists(resume.file_path):
            raise NotFoundException("Resume file not found on server")

        file_ext = resume.file_type.lower()
        if file_ext not in ("pdf", "docx"):
            raise BadRequestException("Only PDF and DOCX files can be corrected")

        if not self.openai_client:
            raise BadRequestException("OpenAI API key is not configured. Set OPENAI_API_KEY in .env")

        try:
            if file_ext == "pdf":
                result = await self._correct_pdf(resume)
            else:
                result = await self._correct_docx(resume)

            return result
        except BadRequestException:
            raise
        except Exception as e:
            logger.error(f"Correction failed for resume {resume_id}: {e}")
            raise BadRequestException(f"Correction failed: {str(e)}")

    async def _correct_pdf(self, resume: Resume) -> dict:
        file_path = resume.file_path
        doc = pymupdf.open(file_path)

        all_lines = []
        page_line_map = []

        for page_num in range(len(doc)):
            page = doc[page_num]
            text_dict = page.get_text("dict", flags=pymupdf.TEXT_PRESERVE_WHITESPACE)

            lines_on_page = self._extract_pdf_lines(text_dict, page_num)
            for line_info in lines_on_page:
                idx = len(all_lines)
                page_line_map.append(line_info)
                all_lines.append({
                    "num": idx,
                    "text": line_info["text"],
                    "page": page_num,
                })

        if not all_lines:
            doc.close()
            raise BadRequestException("No text found in the PDF to correct")

        corrected_lines = await self._correct_text_batch(
            [l["text"] for l in all_lines],
            resume.original_filename,
        )

        changes = []
        for i, (original, corrected) in enumerate(zip(all_lines, corrected_lines)):
            if original["text"].strip() != corrected.strip():
                changes.append({
                    "original": original["text"],
                    "corrected": corrected,
                    "line_num": i,
                })

        output_name = f"corrected_{uuid.uuid4().hex}.pdf"
        output_path = os.path.join(self.corrected_dir, output_name)

        self._apply_pdf_corrections(doc, page_line_map, corrected_lines)
        doc.save(output_path)
        doc.close()

        return {
            "corrected_pdf": output_name,
            "corrected_docx": None,
            "changes": changes,
            "total_lines": len(all_lines),
            "changed_lines": len(changes),
        }

    async def _correct_docx(self, resume: Resume) -> dict:
        file_path = resume.file_path
        doc = Document(file_path)

        paragraphs_data = []
        for para_idx, para in enumerate(doc.paragraphs):
            if not para.text.strip():
                continue
            runs_text = []
            for run in para.runs:
                runs_text.append(run.text)
            full_text = "".join(runs_text)
            if full_text.strip():
                paragraphs_data.append({
                    "para_idx": para_idx,
                    "text": full_text,
                    "runs": [
                        {
                            "text": r.text,
                            "bold": r.bold,
                            "italic": r.italic,
                            "underline": r.underline,
                            "font_name": r.font.name if r.font else None,
                            "font_size": r.font.size.pt if r.font and r.font.size else None,
                            "font_color": str(r.font.color.rgb) if r.font and r.font.color and r.font.color.rgb else None,
                        }
                        for r in para.runs
                    ],
                })

        if not paragraphs_data:
            raise BadRequestException("No text found in the DOCX to correct")

        all_texts = [p["text"] for p in paragraphs_data]
        corrected_texts = await self._correct_text_batch(
            all_texts, resume.original_filename
        )

        changes = []
        for original, corrected in zip(paragraphs_data, corrected_texts):
            if original["text"].strip() != corrected.strip():
                changes.append({
                    "original": original["text"],
                    "corrected": corrected,
                    "para_idx": original["para_idx"],
                })

        output_name = f"corrected_{uuid.uuid4().hex}.docx"
        output_path = os.path.join(self.corrected_dir, output_name)

        self._apply_docx_corrections(doc, paragraphs_data, corrected_texts)
        doc.save(output_path)

        return {
            "corrected_pdf": None,
            "corrected_docx": output_name,
            "changes": changes,
            "total_lines": len(paragraphs_data),
            "changed_lines": len(changes),
        }

    def _extract_pdf_lines(self, text_dict: dict, page_num: int) -> list:
        lines = []
        for block in text_dict.get("blocks", []):
            if block.get("type") != 0:
                continue

            block_lines = block.get("lines", [])
            for line in block_lines:
                spans = line.get("spans", [])
                if not spans:
                    continue

                line_text = "".join(s["text"] for s in spans).strip()
                if not line_text:
                    continue

                first_span = spans[0]
                bbox = line["bbox"]

                font_name = first_span.get("font", "helv")
                font_size = first_span.get("size", 10)
                color_int = first_span.get("color", 0)
                flags = first_span.get("flags", 0)

                lines.append({
                    "text": line_text,
                    "page": page_num,
                    "bbox": bbox,
                    "font_name": font_name,
                    "font_size": font_size,
                    "color": color_int,
                    "flags": flags,
                    "spans": spans,
                    "is_bold": bool(flags & 2 ** 4),
                    "is_italic": bool(flags & 2 ** 1),
                })

        lines.sort(key=lambda l: (l["bbox"][1], l["bbox"][0]))
        return lines

    async def _correct_text_batch(self, texts: list, filename: str) -> list:
        if not self.openai_client:
            return texts

        batch_size = 30
        all_corrected = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            numbered_lines = []
            for j, text in enumerate(batch):
                numbered_lines.append(f"{j}: {text}")

            prompt = f"""Correct the following resume text lines from "{filename}".
Fix grammar, spelling, punctuation, improve action verbs and professional tone.
DO NOT change any factual content, names, dates, companies, or skills.
DO NOT add or remove any information.
Return a JSON array with objects like [{{"line_num": 0, "corrected": "corrected text"}}].
Only return the JSON array, nothing else.

Lines to correct:
{chr(10).join(numbered_lines)}"""

            try:
                response = self.openai_client.chat.completions.create(
                    model=settings.OPENAI_MODEL,
                    messages=[
                        {"role": "system", "content": AI_SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.3,
                    max_tokens=4000,
                )

                result_text = response.choices[0].message.content.strip()

                if result_text.startswith("```"):
                    result_text = result_text.split("\n", 1)[1]
                    if result_text.endswith("```"):
                        result_text = result_text[:-3]
                    result_text = result_text.strip()

                corrections = json.loads(result_text)

                corrected_batch = list(batch)
                for item in corrections:
                    idx = item.get("line_num", -1)
                    corrected_text = item.get("corrected", "")
                    if 0 <= idx < len(corrected_batch) and corrected_text:
                        corrected_batch[idx] = corrected_text

                all_corrected.extend(corrected_batch)

            except json.JSONDecodeError:
                logger.warning("AI response was not valid JSON, returning original text")
                all_corrected.extend(batch)
            except Exception as e:
                logger.error(f"AI correction batch failed: {e}")
                all_corrected.extend(batch)

        while len(all_corrected) < len(texts):
            all_corrected.append(texts[len(all_corrected)])

        return all_corrected[:len(texts)]

    def _apply_pdf_corrections(self, doc, page_line_map, corrected_lines):
        pages_to_process = {}
        for i, line_info in enumerate(page_line_map):
            page_num = line_info["page"]
            if page_num not in pages_to_process:
                pages_to_process[page_num] = []
            pages_to_process[page_num].append((i, line_info))

        for page_num, line_indices in pages_to_process.items():
            page = doc[page_num]

            for idx, line_info in line_indices:
                corrected_text = corrected_lines[idx]
                original_text = line_info["text"]

                if original_text.strip() == corrected_text.strip():
                    continue

                bbox = line_info["bbox"]
                rect = pymupdf.Rect(bbox)

                mapped_font = self._map_font(line_info["font_name"])
                font_size = line_info["font_size"]
                color_int = line_info["color"]

                r = ((color_int >> 16) & 0xFF) / 255.0
                g = ((color_int >> 8) & 0xFF) / 255.0
                b = (color_int & 0xFF) / 255.0

                page.add_redact_annot(
                    rect,
                    text=None,
                    fill=(1, 1, 1),
                )

            page.apply_redactions()

            for idx, line_info in line_indices:
                corrected_text = corrected_lines[idx]
                original_text = line_info["text"]

                if original_text.strip() == corrected_text.strip():
                    continue

                bbox = line_info["bbox"]
                mapped_font = self._map_font(line_info["font_name"])
                font_size = line_info["font_size"]
                color_int = line_info["color"]

                r = ((color_int >> 16) & 0xFF) / 255.0
                g = ((color_int >> 8) & 0xFF) / 255.0
                b = (color_int & 0xFF) / 255.0

                origin_x = bbox[0]
                origin_y = bbox[3] - 2

                try:
                    page.insert_text(
                        pymupdf.Point(origin_x, origin_y),
                        corrected_text,
                        fontname=mapped_font,
                        fontsize=font_size,
                        color=(r, g, b),
                    )
                except Exception as e:
                    logger.warning(f"Failed to insert text at page {line_info['page']}: {e}")
                    try:
                        page.insert_text(
                            pymupdf.Point(origin_x, origin_y),
                            corrected_text,
                            fontname="helv",
                            fontsize=font_size,
                            color=(r, g, b),
                        )
                    except Exception as e2:
                        logger.error(f"Fallback text insert also failed: {e2}")

    def _apply_docx_corrections(self, doc, paragraphs_data, corrected_texts):
        para_idx = 0
        for para in doc.paragraphs:
            if not para.text.strip():
                continue

            if para_idx >= len(paragraphs_data):
                break

            corrected_text = corrected_texts[para_idx]
            original_data = paragraphs_data[para_idx]
            para_idx += 1

            if original_data["text"].strip() == corrected_text.strip():
                continue

            runs = para.runs
            if not runs:
                para.text = corrected_text
                continue

            if len(runs) == 1:
                runs[0].text = corrected_text
                continue

            self._distribute_text_to_runs(runs, corrected_text, original_data["runs"])

    def _distribute_text_to_runs(self, runs, corrected_text, runs_meta):
        if not runs or not corrected_text:
            return

        total_original_len = sum(len(r.text) for r in runs)
        if total_original_len == 0:
            runs[0].text = corrected_text
            for r in runs[1:]:
                r.text = ""
            return

        remaining = corrected_text
        for i, run in enumerate(runs):
            if i == len(runs) - 1:
                run.text = remaining
            else:
                original_len = len(run.text)
                ratio = original_len / total_original_len
                chars_to_take = max(1, int(len(corrected_text) * ratio))

                split_point = self._find_best_split_point(remaining, chars_to_take)
                run.text = remaining[:split_point]
                remaining = remaining[split_point:]

    def _find_best_split_point(self, text, target_pos):
        if target_pos >= len(text):
            return len(text)

        best = target_pos
        for offset in range(min(5, target_pos)):
            for pos in [target_pos + offset, target_pos - offset]:
                if 0 <= pos <= len(text):
                    if pos < len(text) and text[pos] == " ":
                        return pos + 1
                    if pos > 0 and text[pos - 1] == " ":
                        return pos
                    best = pos

        return best

    def _map_font(self, font_name: str) -> str:
        if not font_name:
            return "helv"

        normalized = font_name.lower().strip()

        for key, mapped in FONT_MAP.items():
            if key in normalized:
                return mapped

        if "bold" in normalized and "italic" in normalized:
            return "hebi"
        if "bold" in normalized:
            return "hebo"
        if "italic" in normalized or "oblique" in normalized:
            return "heit"

        return "helv"

    def download_corrected_file(self, filename: str) -> str:
        file_path = os.path.join(self.corrected_dir, filename)
        if not os.path.exists(file_path):
            raise NotFoundException("Corrected file not found")
        return file_path

    def cleanup_old_files(self, max_age_hours: int = 24):
        import time
        now = time.time()
        cutoff = now - (max_age_hours * 3600)

        for filename in os.listdir(self.corrected_dir):
            filepath = os.path.join(self.corrected_dir, filename)
            if os.path.isfile(filepath) and os.path.getmtime(filepath) < cutoff:
                try:
                    os.remove(filepath)
                except Exception:
                    pass
