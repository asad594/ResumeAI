import pytest
from app.services.analysis_service import AnalysisService

@pytest.fixture
def service():
    # Provide None for db as these pure logic methods do not use it
    return AnalysisService(db=None)

def test_resume_only(service):
    """Scenario: Resume only (No JD supplied)."""
    extracted = {"skills": ["Python", "React"]}
    job_description = None
    
    score = service._calculate_ats_score(extracted, job_description)
    assert score["keywords"] is None
    
    analysis = service._analyze_skills(extracted, job_description)
    assert analysis["percentage"] is None
    assert analysis["matched"] == ["Python", "React"]

def test_resume_with_jd(service):
    """Scenario: Resume + JD (both provided, some matching)."""
    extracted = {"skills": ["Python", "Ruby"]}
    job_description = "We need Python and React developers."
    
    score = service._calculate_ats_score(extracted, job_description)
    assert score["keywords"] == 50  # 1 out of 2 matched
    
    analysis = service._analyze_skills(extracted, job_description)
    assert "python" in analysis["matched"]
    assert analysis["percentage"] > 0

def test_empty_jd(service):
    """Scenario: Empty JD (empty string). Should behave similarly to no JD, or handle gracefully without errors."""
    extracted = {"skills": ["Python", "React"]}
    job_description = ""
    
    score = service._calculate_ats_score(extracted, job_description)
    assert score["keywords"] is None
    
    analysis = service._analyze_skills(extracted, job_description)
    assert analysis["percentage"] is None

def test_empty_skills(service):
    """Scenario: Empty skills (JD provided but no skills in resume)."""
    extracted = {"skills": []}
    job_description = "We need Python and React developers."
    
    score = service._calculate_ats_score(extracted, job_description)
    assert score["keywords"] == 0
    assert score["skills"] == 0
    
    analysis = service._analyze_skills(extracted, job_description)
    assert analysis["percentage"] == 0
    assert "python" in analysis["missing"]

def test_partial_skill_match(service):
    """Scenario: Partial skill match."""
    extracted = {"skills": ["Python", "Ruby"]}
    job_description = "Looking for Python, React, and AWS."
    
    score = service._calculate_ats_score(extracted, job_description)
    assert score["keywords"] == 50
    
    analysis = service._analyze_skills(extracted, job_description)
    assert "python" in analysis["matched"]
    assert "ruby" not in analysis["matched"]
    assert "aws" in analysis["missing"] or "react" in analysis["missing"]

def test_full_skill_match(service):
    """Scenario: Full skill match."""
    extracted = {"skills": ["Python", "React", "AWS"]}
    job_description = "Looking for Python, React, and AWS."
    
    score = service._calculate_ats_score(extracted, job_description)
    assert score["keywords"] == 100
    
    analysis = service._analyze_skills(extracted, job_description)
    assert "python" in analysis["matched"]
    assert "react" in analysis["matched"]
    assert "aws" in analysis["matched"]
    assert analysis["percentage"] == 100.0
