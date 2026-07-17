import pytest
from unittest.mock import patch
import pymupdf
from io import BytesIO
from app.services.correction_service import CorrectionService

def test_pdf_correction_separates_highlights(client, auth_headers):
    # 1. Upload a PDF resume
    pdf_content = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>
endobj
4 0 obj
<< /Length 44 >>
stream
BT /F1 12 Tf 100 700 Td (Weak resume bullet point.) Tj ET
endstream
endobj
5 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>
endobj
xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000266 00000 n 
0000000360 00000 n 
trailer
<< /Size 6 /Root 1 0 R >>
startxref
438
%%EOF"""

    files = {"file": ("resume.pdf", BytesIO(pdf_content), "application/pdf")}
    upload_res = client.post("/api/v1/resumes/upload", files=files, headers=auth_headers)
    assert upload_res.status_code == 201
    resume_id = upload_res.json()["id"]

    # Mock correction batch to return corrected text
    async def mock_correct_text_batch(self, resume_id, texts, filename):
        return ["Strong resume bullet point."]

    with patch.object(CorrectionService, "_correct_text_batch", new=mock_correct_text_batch):
        # 2. Correct the resume
        correct_res = client.post(f"/api/v1/correction/correct?resume_id={resume_id}", headers=auth_headers)
        assert correct_res.status_code == 200
        data = correct_res.json()
        corrected_pdf = data["corrected_pdf"]
        assert corrected_pdf is not None

        # 3. Verify clean version downloaded
        download_res = client.get(f"/api/v1/correction/download/{corrected_pdf}", headers=auth_headers)
        assert download_res.status_code == 200
        
        # Verify clean PDF has NO highlights
        clean_doc = pymupdf.open(stream=download_res.content, filetype="pdf")
        clean_has_annots = False
        for page in clean_doc:
            if list(page.annots()):
                clean_has_annots = True
        assert not clean_has_annots
        clean_doc.close()

        # 4. Verify preview version has highlights
        preview_res = client.get(f"/api/v1/correction/preview/{corrected_pdf}", headers=auth_headers)
        assert preview_res.status_code == 200
        
        # Verify preview PDF DOES have highlights
        preview_doc = pymupdf.open(stream=preview_res.content, filetype="pdf")
        preview_has_annots = False
        for page in preview_doc:
            for annot in page.annots():
                if annot.type[1] == "Highlight":
                    preview_has_annots = True
        assert preview_has_annots
        preview_doc.close()


def test_clean_and_parse_json_valid():
    service = CorrectionService(None)
    valid_raw = '{"corrections": [{"line_num": 0, "corrected": "Hello"}]}'
    result = service.clean_and_parse_json(valid_raw)
    assert result == {"corrections": [{"line_num": 0, "corrected": "Hello"}]}


def test_clean_and_parse_json_markdown_wrapped():
    service = CorrectionService(None)
    markdown_raw = '```json\n{"corrections": [{"line_num": 1, "corrected": "World"}]}\n```'
    result = service.clean_and_parse_json(markdown_raw)
    assert result == {"corrections": [{"line_num": 1, "corrected": "World"}]}


def test_clean_and_parse_json_explanatory_text():
    service = CorrectionService(None)
    explanatory_raw = 'Here is the corrected resume JSON:\n{"corrections": [{"line_num": 2, "corrected": "Test"}]}\nI hope this helps!'
    result = service.clean_and_parse_json(explanatory_raw)
    assert result == {"corrections": [{"line_num": 2, "corrected": "Test"}]}


def test_clean_and_parse_json_truncated():
    service = CorrectionService(None)
    truncated_raw = '{"corrections": [{"line_num": 0, "corrected": "Hello"}, {"line_num": 1, "corrected": "World"}, {"line_num": 2'
    result = service.clean_and_parse_json(truncated_raw)
    assert result == {"corrections": [{"line_num": 0, "corrected": "Hello"}, {"line_num": 1, "corrected": "World"}]}


def test_clean_and_parse_json_invalid():
    service = CorrectionService(None)
    invalid_raw = 'This is not JSON at all'
    with pytest.raises(ValueError, match="Could not find valid JSON object boundaries"):
        service.clean_and_parse_json(invalid_raw)
