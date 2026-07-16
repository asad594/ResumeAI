import pytest
from io import BytesIO


def test_upload_resume_pdf(client, auth_headers):
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
BT /F1 12 Tf 100 700 Td (John Doe) Tj ET
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
    response = client.post("/api/v1/resumes/upload", files=files, headers=auth_headers)
    assert response.status_code == 201
    assert "id" in response.json()


def test_get_resumes(client, auth_headers):
    response = client.get("/api/v1/resumes/", headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_upload_invalid_file_type(client, auth_headers):
    files = {"file": ("resume.txt", BytesIO(b"test"), "text/plain")}
    response = client.post("/api/v1/resumes/upload", files=files, headers=auth_headers)
    assert response.status_code == 415


def test_delete_resume(client, auth_headers):
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
BT /F1 12 Tf 100 700 Td (John Doe) Tj ET
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
    upload_response = client.post("/api/v1/resumes/upload", files=files, headers=auth_headers)
    resume_id = upload_response.json()["id"]

    response = client.delete(f"/api/v1/resumes/{resume_id}", headers=auth_headers)
    assert response.status_code == 200
