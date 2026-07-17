import pytest
from unittest.mock import patch
from io import BytesIO
from app.services.analysis_service import AnalysisService
from app.services.correction_service import CorrectionService
from app.core.config import settings

# Dummy PDF helper
def make_dummy_pdf(text="Dummy PDF content."):
    return f"""%PDF-1.4
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
<< /Length {len(text) + 24} >>
stream
BT /F1 12 Tf 100 700 Td ({text}) Tj ET
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
%%EOF""".encode("utf-8")


def test_ats_breakdown_excellent(client, auth_headers):
    # 1. Upload resume
    pdf_content = make_dummy_pdf()
    files = {"file": ("resume.pdf", BytesIO(pdf_content), "application/pdf")}
    upload_res = client.post("/api/v1/resumes/upload", files=files, headers=auth_headers)
    assert upload_res.status_code == 201
    resume_id = upload_res.json()["id"]

    # 2. Mock resume extraction to return an excellent candidate profile
    mock_extracted = {
        "name": "John Doe",
        "email": "john.doe@example.com",
        "phone": "+1-555-0199",
        "location": "San Francisco, CA",
        "linkedin": "https://linkedin.com/in/johndoe",
        "skills": ["Python", "Docker", "Git", "FastAPI", "PostgreSQL", "React", "AWS", "Kubernetes", "Redis", "Linux"],
        "education": ["B.S. in Computer Science"],
        "experience": ["Senior Software Engineer at Tech Corp", "Software Engineer at Startup Co"],
        "projects": ["Personal Project A"],
        "certificates": ["AWS Solutions Architect"],
        "languages": ["English"],
        "raw_text": "John Doe. john.doe@example.com. +1-555-0199. linkedin.com/in/johndoe. San Francisco, CA. Python, Docker, Git. Senior Software Engineer at Tech Corp."
    }

    # 3. Mock LLM dynamic scores for high metrics
    async def mock_evaluate(self, resume_id, raw_text, job_description=None):
        return {
            "scores": {
                "grammar": 95,
                "action_verbs": 90,
                "metrics": 90,
                "formatting_readability": 95
            },
            "suggestions": []
        }

    with patch("app.services.resume_service.ResumeService._extract_data", return_value=mock_extracted), \
         patch.object(AnalysisService, "_evaluate_resume_with_llm", new=mock_evaluate):
        
        analysis_res = client.post("/api/v1/analysis/", json={"resume_id": resume_id}, headers=auth_headers)
        assert analysis_res.status_code == 201
        data = analysis_res.json()
        
        # Verify response attributes
        assert "overall_score" in data
        assert "breakdown" in data
        assert "category_suggestions" in data
        
        breakdown = data["breakdown"]
        assert len(breakdown) == 8
        for k in ["formatting", "contact_information", "skills", "experience", "keywords", "action_verbs", "grammar", "metrics"]:
            assert k in breakdown
            assert 0 <= breakdown[k] <= 100
            
        # Overall score verification
        assert data["overall_score"] == data["ats_score"]
        
        # With high scores, breakdown category suggestions should be minimal or empty
        for cat_sug in data["category_suggestions"]:
            assert cat_sug["score"] < settings.ATS_BREAKDOWN_THRESHOLD


def test_ats_breakdown_poor_formatting_and_no_experience(client, auth_headers):
    # 1. Upload resume
    pdf_content = make_dummy_pdf()
    files = {"file": ("resume.pdf", BytesIO(pdf_content), "application/pdf")}
    upload_res = client.post("/api/v1/resumes/upload", files=files, headers=auth_headers)
    assert upload_res.status_code == 201
    resume_id = upload_res.json()["id"]

    # 2. Mock poor resume details: missing contact details and no experience
    mock_extracted = {
        "name": "Unknown",
        "email": "",
        "phone": "",
        "location": "",
        "linkedin": "",
        "skills": ["Java"],
        "education": [],
        "experience": [],
        "projects": [],
        "certificates": [],
        "languages": [],
        "raw_text": "Java Developer resume with no contacts."
    }

    async def mock_evaluate(self, resume_id, raw_text, job_description=None):
        return {
            "scores": {
                "grammar": 40,
                "action_verbs": 35,
                "metrics": 30,
                "formatting_readability": 40
            },
            "suggestions": []
        }

    with patch("app.services.resume_service.ResumeService._extract_data", return_value=mock_extracted), \
         patch.object(AnalysisService, "_evaluate_resume_with_llm", new=mock_evaluate):
         
        analysis_res = client.post("/api/v1/analysis/", json={"resume_id": resume_id}, headers=auth_headers)
        assert analysis_res.status_code == 201
        data = analysis_res.json()
        breakdown = data["breakdown"]
        
        # Formatting score and contact details should be low
        assert breakdown["contact_information"] == 0
        assert breakdown["formatting"] < settings.ATS_BREAKDOWN_THRESHOLD
        assert breakdown["experience"] == 0
        
        # Suggestions must exist for low categories
        categories_with_suggestions = [cs["category"] for cs in data["category_suggestions"]]
        assert "Contact Information" in categories_with_suggestions
        assert "Experience" in categories_with_suggestions
        
        # Contact information suggestions must point out missing name, email, phone, location
        contact_sugs = next(cs for cs in data["category_suggestions"] if cs["category"] == "Contact Information")["suggestions"]
        assert any("email" in s.lower() for s in contact_sugs)
        assert any("phone" in s.lower() for s in contact_sugs)
        assert any("location" in s.lower() for s in contact_sugs)


def test_ats_breakdown_projects_fallback(client, auth_headers):
    # 1. Upload resume
    pdf_content = make_dummy_pdf()
    files = {"file": ("resume.pdf", BytesIO(pdf_content), "application/pdf")}
    upload_res = client.post("/api/v1/resumes/upload", files=files, headers=auth_headers)
    assert upload_res.status_code == 201
    resume_id = upload_res.json()["id"]

    # 2. Mock resume: no experience, but has personal projects
    mock_extracted = {
        "name": "Jane Developer",
        "email": "jane@example.com",
        "phone": "+1-555-1234",
        "location": "Boston, MA",
        "linkedin": "",
        "skills": ["C++", "Python"],
        "education": ["M.S. in CS"],
        "experience": [],
        "projects": ["Project Alpha: compiler design", "Project Beta: database implementation", "Project Gamma"],
        "certificates": [],
        "languages": [],
        "raw_text": "Jane Developer. M.S. compiler design. Project Alpha, Beta, Gamma."
    }

    async def mock_evaluate(self, resume_id, raw_text, job_description=None):
        return {
            "scores": {
                "grammar": 90,
                "action_verbs": 85,
                "metrics": 80,
                "formatting_readability": 85
            },
            "suggestions": []
        }

    with patch("app.services.resume_service.ResumeService._extract_data", return_value=mock_extracted), \
         patch.object(AnalysisService, "_evaluate_resume_with_llm", new=mock_evaluate):
         
        analysis_res = client.post("/api/v1/analysis/", json={"resume_id": resume_id}, headers=auth_headers)
        assert analysis_res.status_code == 201
        data = analysis_res.json()
        breakdown = data["breakdown"]
        
        # Experience score should use projects fallback and be greater than 0
        assert breakdown["experience"] > 0


def test_ats_breakdown_low_metrics(client, auth_headers):
    # 1. Upload resume
    pdf_content = make_dummy_pdf()
    files = {"file": ("resume.pdf", BytesIO(pdf_content), "application/pdf")}
    upload_res = client.post("/api/v1/resumes/upload", files=files, headers=auth_headers)
    assert upload_res.status_code == 201
    resume_id = upload_res.json()["id"]

    # 2. Mock resume with low metrics score
    mock_extracted = {
        "name": "Alice Green",
        "email": "alice@example.com",
        "phone": "+1-555-5678",
        "location": "Seattle, WA",
        "linkedin": "",
        "skills": ["JavaScript", "React"],
        "education": ["B.A."],
        "experience": ["React dev doing frontend tasks without numbers"],
        "projects": [],
        "certificates": [],
        "languages": [],
        "raw_text": "Alice Green. frontend tasks."
    }

    async def mock_evaluate(self, resume_id, raw_text, job_description=None):
        return {
            "scores": {
                "grammar": 90,
                "action_verbs": 90,
                "metrics": 45, # Low metrics score
                "formatting_readability": 85
            },
            "suggestions": []
        }

    with patch("app.services.resume_service.ResumeService._extract_data", return_value=mock_extracted), \
         patch.object(AnalysisService, "_evaluate_resume_with_llm", new=mock_evaluate):
         
        analysis_res = client.post("/api/v1/analysis/", json={"resume_id": resume_id}, headers=auth_headers)
        assert analysis_res.status_code == 201
        data = analysis_res.json()
        
        # Metrics score should match
        assert data["breakdown"]["metrics"] == 45
        
        # Metrics suggestions should trigger
        categories_with_suggestions = [cs["category"] for cs in data["category_suggestions"]]
        assert "Metrics" in categories_with_suggestions


def test_ats_breakdown_after_correction(client, auth_headers):
    # 1. Upload resume
    pdf_content = make_dummy_pdf("Weak bullet point description.")
    files = {"file": ("resume.pdf", BytesIO(pdf_content), "application/pdf")}
    upload_res = client.post("/api/v1/resumes/upload", files=files, headers=auth_headers)
    assert upload_res.status_code == 201
    original_resume_id = upload_res.json()["id"]

    # 2. Mock initial evaluation: low scores
    mock_original_extracted = {
        "name": "Bob Smith",
        "email": "bob@example.com",
        "phone": "+1-555-8888",
        "location": "Karachi",
        "linkedin": "",
        "skills": ["Git"],
        "education": ["Associate Degree"],
        "experience": ["Helped on things."],
        "projects": [],
        "certificates": [],
        "languages": [],
        "raw_text": "Bob Smith. helped on things."
    }

    async def mock_evaluate_original(self, resume_id, raw_text, job_description=None):
        return {
            "scores": {
                "grammar": 60,
                "action_verbs": 50,
                "metrics": 40,
                "formatting_readability": 60
            },
            "suggestions": []
        }

    # Analyze original
    with patch("app.services.resume_service.ResumeService._extract_data", return_value=mock_original_extracted), \
         patch.object(AnalysisService, "_evaluate_resume_with_llm", new=mock_evaluate_original):
        original_analysis_res = client.post("/api/v1/analysis/", json={"resume_id": original_resume_id}, headers=auth_headers)
        assert original_analysis_res.status_code == 201
        original_score = original_analysis_res.json()["ats_score"]

    # 3. Mock Correction Service output & corrected evaluation
    async def mock_correct_batch(self, resume_id, texts, filename):
        return ["Optimized server performance by 25% and engineered new robust REST APIs."]

    mock_corrected_extracted = {
        "name": "Bob Smith",
        "email": "bob@example.com",
        "phone": "+1-555-8888",
        "location": "Karachi",
        "linkedin": "",
        "skills": ["Git", "REST API"],
        "education": ["Associate Degree"],
        "experience": ["Optimized server performance by 25% and engineered new robust REST APIs."],
        "projects": [],
        "certificates": [],
        "languages": [],
        "raw_text": "Bob Smith. Optimized server performance by 25% and engineered new robust REST APIs."
    }

    async def mock_evaluate_corrected(self, resume_id, raw_text, job_description=None):
        return {
            "scores": {
                "grammar": 95,
                "action_verbs": 95,
                "metrics": 90,
                "formatting_readability": 90
            },
            "suggestions": []
        }

    # Mock batch correction and new evaluation execution
    with patch.object(CorrectionService, "_correct_text_batch", new=mock_correct_batch), \
         patch("app.services.resume_service.ResumeService._extract_data", return_value=mock_corrected_extracted), \
         patch.object(AnalysisService, "_evaluate_resume_with_llm", new=mock_evaluate_corrected):
         
        correct_res = client.post(f"/api/v1/correction/correct?resume_id={original_resume_id}", headers=auth_headers)
        assert correct_res.status_code == 200
        result = correct_res.json()
        
        # Verify corrected_analysis is returned and has higher score
        assert "corrected_analysis" in result
        corrected_analysis = result["corrected_analysis"]
        assert corrected_analysis is not None
        assert corrected_analysis["ats_score"] > original_score
        
        # Check breakdown improvements
        original_breakdown = original_analysis_res.json()["breakdown"]
        corrected_breakdown = corrected_analysis["breakdown"]
        
        assert corrected_breakdown["grammar"] > original_breakdown["grammar"]
        assert corrected_breakdown["action_verbs"] > original_breakdown["action_verbs"]
        assert corrected_breakdown["metrics"] > original_breakdown["metrics"]
