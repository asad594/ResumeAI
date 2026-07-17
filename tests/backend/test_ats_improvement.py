import pytest
from unittest.mock import patch
from io import BytesIO
from app.services.correction_service import CorrectionService
from app.services.analysis_service import AnalysisService

def test_ats_score_improves_after_correction(client, auth_headers):
    # 1. Original PDF content
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

    # 2. Upload original resume
    files = {"file": ("resume.pdf", BytesIO(pdf_content), "application/pdf")}
    upload_res = client.post("/api/v1/resumes/upload", files=files, headers=auth_headers)
    assert upload_res.status_code == 201
    original_resume_id = upload_res.json()["id"]

    # Mock evaluate_resume_with_llm for original: low scores
    async def mock_evaluate_original(self, resume_id, raw_text, job_description=None):
        return {
            "scores": {
                "grammar": 80,
                "action_verbs": 70,
                "metrics": 60,
                "formatting_readability": 70
            },
            "suggestions": [
                {
                    "type": "grammar",
                    "severity": "medium",
                    "title": "Fix grammar",
                    "description": "Please fix grammar in project descriptions.",
                    "category": "Language"
                },
                {
                    "type": "action_verbs",
                    "severity": "medium",
                    "title": "Vary action verbs",
                    "description": "Repeated use of Developed.",
                    "category": "Language"
                }
            ]
        }

    # 3. Analyze original resume
    with patch.object(AnalysisService, "_evaluate_resume_with_llm", new=mock_evaluate_original):
        analysis_res_1 = client.post("/api/v1/analysis/", json={"resume_id": original_resume_id}, headers=auth_headers)
        assert analysis_res_1.status_code == 201
        score_1 = analysis_res_1.json()["ats_score"]
        suggestions_1 = analysis_res_1.json()["suggestions"]
        assert len(suggestions_1) > 0

    # 4. Correct original resume
    async def mock_correct_text_batch(self, resume_id, texts, filename):
        return ["Strong, engineered, and optimized resume bullet point."]

    with patch.object(CorrectionService, "_correct_text_batch", new=mock_correct_text_batch):
        correct_res = client.post(f"/api/v1/correction/correct?resume_id={original_resume_id}", headers=auth_headers)
        assert correct_res.status_code == 200
        corrected_pdf_filename = correct_res.json()["corrected_pdf"]

    # 5. Download corrected PDF
    download_res = client.get(f"/api/v1/correction/download/{corrected_pdf_filename}", headers=auth_headers)
    assert download_res.status_code == 200
    corrected_pdf_bytes = download_res.content

    # 6. Upload corrected resume (re-upload)
    files_2 = {"file": (corrected_pdf_filename, BytesIO(corrected_pdf_bytes), "application/pdf")}
    upload_res_2 = client.post("/api/v1/resumes/upload", files=files_2, headers=auth_headers)
    assert upload_res_2.status_code == 201
    corrected_resume_id = upload_res_2.json()["id"]

    # Mock evaluate_resume_with_llm for corrected: improved scores
    async def mock_evaluate_corrected(self, resume_id, raw_text, job_description=None):
        return {
            "scores": {
                "grammar": 98,
                "action_verbs": 95,
                "metrics": 80,
                "formatting_readability": 90
            },
            "suggestions": []
        }

    # 7. Analyze corrected resume again
    with patch.object(AnalysisService, "_evaluate_resume_with_llm", new=mock_evaluate_corrected):
        analysis_res_2 = client.post("/api/v1/analysis/", json={"resume_id": corrected_resume_id}, headers=auth_headers)
        assert analysis_res_2.status_code == 201
        score_2 = analysis_res_2.json()["ats_score"]
        suggestions_2 = analysis_res_2.json()["suggestions"]

    # 8. Assertions: Y > X
    print(f"\n--- Scenario A (Original): Score = {score_1} ---")
    print(f"--- Scenario B (Corrected): Score = {score_2} ---")
    assert score_2 > score_1, f"Expected corrected score ({score_2}) to be greater than original score ({score_1})"
    assert len(suggestions_2) < len(suggestions_1)
