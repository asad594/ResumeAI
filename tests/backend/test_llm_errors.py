import json
import pytest
import httpx
import openai
from unittest.mock import patch
from io import BytesIO
from app.services.analysis_service import AnalysisService
from app.services.correction_service import CorrectionService
from app.core.exceptions import LLMAPIException


def create_mock_response(status_code: int, json_body: dict = None, headers: dict = None) -> httpx.Response:
    request = httpx.Request("POST", "https://generativelanguage.googleapis.com/v1beta/openai/")
    response = httpx.Response(
        status_code=status_code,
        request=request,
        content=b"" if not json_body else json.dumps(json_body).encode("utf-8"),
        headers=headers,
    )
    return response


@pytest.fixture
def uploaded_resume_id(client, auth_headers):
    # Upload a dummy PDF resume
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
BT /F1 12 Tf 100 700 Td (Sample Resume text here.) Tj ET
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
    files = {"file": ("test_resume.pdf", BytesIO(pdf_content), "application/pdf")}
    res = client.post("/api/v1/resumes/upload", files=files, headers=auth_headers)
    assert res.status_code == 201
    return res.json()["id"]


def test_invalid_api_key_error(client, auth_headers, uploaded_resume_id):
    # Mock AuthenticationError
    mock_resp = create_mock_response(401, {"error": {"message": "API key not valid"}})
    exc = openai.AuthenticationError(
        message="Invalid API Key",
        response=mock_resp,
        body=mock_resp.json()
    )

    with patch("openai.resources.chat.completions.Completions.create", side_effect=exc):
        # 1. Test Analysis Endpoint
        res = client.post(
            "/api/v1/analysis/",
            json={"resume_id": uploaded_resume_id, "job_description": "SE Role"},
            headers=auth_headers,
        )
        assert res.status_code == 500
        data = res.json()
        assert data["detail"]["error_type"] == "invalid_api_key"
        assert "Invalid LLM API key" in data["detail"]["message"]

        # 2. Test Correction Endpoint
        res_corr = client.post(
            f"/api/v1/correction/correct?resume_id={uploaded_resume_id}",
            headers=auth_headers,
        )
        assert res_corr.status_code == 500
        data_corr = res_corr.json()
        assert data_corr["detail"]["error_type"] == "invalid_api_key"


def test_quota_exceeded_error(client, auth_headers, uploaded_resume_id):
    # Mock RateLimitError (Quota exceeded)
    mock_resp = create_mock_response(
        429, 
        {"error": {"message": "RESOURCE_EXHAUSTED", "status": "RESOURCE_EXHAUSTED"}}
    )
    exc = openai.RateLimitError(
        message="Quota exceeded",
        response=mock_resp,
        body=mock_resp.json()
    )

    with patch("openai.resources.chat.completions.Completions.create", side_effect=exc):
        res = client.post(
            "/api/v1/analysis/",
            json={"resume_id": uploaded_resume_id},
            headers=auth_headers,
        )
        assert res.status_code == 429
        data = res.json()
        assert data["detail"]["error_type"] == "quota_exceeded"
        assert "quota" in data["detail"]["message"].lower()


def test_rate_limiting_error(client, auth_headers, uploaded_resume_id):
    # Mock RateLimitError (standard RPM limit)
    mock_resp = create_mock_response(429, {"error": {"message": "Rate limit exceeded"}})
    exc = openai.RateLimitError(
        message="Rate limit exceeded",
        response=mock_resp,
        body=mock_resp.json()
    )

    with patch("openai.resources.chat.completions.Completions.create", side_effect=exc):
        res = client.post(
            "/api/v1/analysis/",
            json={"resume_id": uploaded_resume_id},
            headers=auth_headers,
        )
        assert res.status_code == 429
        data = res.json()
        assert data["detail"]["error_type"] == "rate_limiting"
        assert "rate limited" in data["detail"]["message"].lower()


def test_network_timeout_error(client, auth_headers, uploaded_resume_id):
    # Mock APITimeoutError
    req = httpx.Request("POST", "https://api.openai.com/v1/chat/completions")
    exc = openai.APITimeoutError(request=req)

    with patch("openai.resources.chat.completions.Completions.create", side_effect=exc):
        res = client.post(
            "/api/v1/analysis/",
            json={"resume_id": uploaded_resume_id},
            headers=auth_headers,
        )
        assert res.status_code == 504
        data = res.json()
        assert data["detail"]["error_type"] == "network_timeout"
        assert "timed out" in data["detail"]["message"].lower()


def test_internal_server_errors(client, auth_headers, uploaded_resume_id):
    # Mock InternalServerError
    mock_resp = create_mock_response(500, {"error": {"message": "Internal error"}})
    exc = openai.InternalServerError(
        message="Internal error",
        response=mock_resp,
        body=mock_resp.json()
    )

    with patch("openai.resources.chat.completions.Completions.create", side_effect=exc):
        res = client.post(
            "/api/v1/analysis/",
            json={"resume_id": uploaded_resume_id},
            headers=auth_headers,
        )
        assert res.status_code == 502
        data = res.json()
        assert data["detail"]["error_type"] == "internal_error"
        assert "internal error" in data["detail"]["message"].lower()


def test_invalid_model_name(client, auth_headers, uploaded_resume_id):
    # Mock NotFoundError for model name
    mock_resp = create_mock_response(404, {"error": {"message": "Model not found"}})
    exc = openai.NotFoundError(
        message="Model not found",
        response=mock_resp,
        body=mock_resp.json()
    )

    with patch("openai.resources.chat.completions.Completions.create", side_effect=exc):
        res = client.post(
            "/api/v1/analysis/",
            json={"resume_id": uploaded_resume_id},
            headers=auth_headers,
        )
        assert res.status_code == 400
        data = res.json()
        assert data["detail"]["error_type"] == "invalid_model_name"
        assert "model name is invalid" in data["detail"]["message"].lower()


def test_retry_after_header_extraction(client, auth_headers, uploaded_resume_id):
    # Mock RateLimitError with headers
    mock_resp = create_mock_response(
        429, 
        {"error": {"message": "Rate limit exceeded"}},
        headers={"retry-after": "45"}
    )
    exc = openai.RateLimitError(
        message="Rate limit exceeded",
        response=mock_resp,
        body=mock_resp.json()
    )

    with patch("openai.resources.chat.completions.Completions.create", side_effect=exc):
        res = client.post(
            "/api/v1/analysis/",
            json={"resume_id": uploaded_resume_id},
            headers=auth_headers,
        )
        assert res.status_code == 429
        data = res.json()
        assert data["detail"]["retry_after"] == 45


def test_retry_delay_body_extraction(client, auth_headers, uploaded_resume_id):
    # Mock RateLimitError with Google body structure retryDelay
    body_data = {
        "error": {
            "message": "RESOURCE_EXHAUSTED",
            "status": "RESOURCE_EXHAUSTED",
            "details": [
                {
                    "@type": "type.googleapis.com/google.rpc.RetryInfo",
                    "retryDelay": "23.5s"
                }
            ]
        }
    }
    mock_resp = create_mock_response(429, body_data)
    exc = openai.RateLimitError(
        message="Quota exceeded",
        response=mock_resp,
        body=mock_resp.json()
    )

    with patch("openai.resources.chat.completions.Completions.create", side_effect=exc):
        res = client.post(
            "/api/v1/analysis/",
            json={"resume_id": uploaded_resume_id},
            headers=auth_headers,
        )
        assert res.status_code == 429
        data = res.json()
        assert data["detail"]["retry_after"] == 23
