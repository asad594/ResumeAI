import json
from typing import Dict, List, Any, Optional
from openai import OpenAI
from sqlalchemy.orm import Session
from app.models.analysis import Analysis
from app.models.resume import Resume
from app.schemas.analysis import AnalysisCreate
from app.core.config import settings
from app.core.exceptions import NotFoundException
from loguru import logger


class AnalysisService:
    def __init__(self, db: Session):
        self.db = db
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None

    def create_analysis(self, user_id: int, data: AnalysisCreate) -> Analysis:
        resume = self.db.query(Resume).filter(
            Resume.id == data.resume_id,
            Resume.user_id == user_id
        ).first()
        if not resume:
            raise NotFoundException("Resume not found")

        extracted = resume.extracted_data or {}
        raw_text = extracted.get("raw_text", "")

        ats_score = self._calculate_ats_score(extracted, data.job_description)
        skills_analysis = self._analyze_skills(extracted, data.job_description)
        suggestions = self._generate_suggestions(extracted, ats_score)
        job_match = self._calculate_job_match(extracted, data.job_description)

        analysis = Analysis(
            user_id=user_id,
            resume_id=data.resume_id,
            ats_score=ats_score.get("overall", 0),
            ats_details=ats_score,
            missing_skills=skills_analysis.get("missing", []),
            matched_skills=skills_analysis.get("matched", []),
            partial_skills=skills_analysis.get("partial", []),
            match_percentage=skills_analysis.get("percentage", 0),
            suggestions=suggestions,
            job_match=job_match,
            job_description=data.job_description,
            status="completed",
        )
        self.db.add(analysis)
        self.db.commit()
        self.db.refresh(analysis)
        return analysis

    def _calculate_ats_score(self, extracted: dict, job_description: Optional[str] = None) -> dict:
        formatting_score = 0
        keywords_score = 0
        experience_score = 0
        education_score = 0
        skills_score = 0

        if extracted.get("name"):
            formatting_score += 20
        if extracted.get("email"):
            formatting_score += 20
        if extracted.get("phone"):
            formatting_score += 15
        if extracted.get("location"):
            formatting_score += 10
        formatting_score = min(formatting_score, 100)

        skills = extracted.get("skills", [])
        skills_score = min(len(skills) * 8, 100)

        experience = extracted.get("experience", [])
        experience_score = min(len(experience) * 15, 100)

        education = extracted.get("education", [])
        education_score = min(len(education) * 30, 100)

        if job_description and skills:
            job_lower = job_description.lower()
            matched = sum(1 for s in skills if s.lower() in job_lower)
            keywords_score = min(int((matched / max(len(skills), 1)) * 100), 100)
        else:
            keywords_score = skills_score

        overall = round(
            (formatting_score * 0.2 + keywords_score * 0.25 + experience_score * 0.25 + education_score * 0.15 + skills_score * 0.2),
            1
        )

        return {
            "overall": overall,
            "formatting": formatting_score,
            "keywords": keywords_score,
            "experience": experience_score,
            "education": education_score,
            "skills": skills_score,
        }

    def _analyze_skills(self, extracted: dict, job_description: Optional[str] = None) -> dict:
        if not job_description:
            return {"missing": [], "matched": extracted.get("skills", []), "partial": [], "percentage": 100}

        resume_skills = set(s.lower() for s in extracted.get("skills", []))
        job_words = set(w.lower() for w in job_description.split() if len(w) > 3)

        matched = []
        missing = []
        partial = []

        for skill in resume_skills:
            if skill in job_description.lower():
                matched.append(skill)
            elif any(w in skill for w in job_words):
                partial.append(skill)
            else:
                missing.append(skill)

        common_tech = ["python", "javascript", "typescript", "java", "react", "node", "aws", "docker", "kubernetes",
                       "sql", "mongodb", "redis", "graphql", "rest", "api", "git", "linux", "machine learning",
                       "data", "analytics", "agile", "scrum", "ci/cd", "terraform", "gcp", "azure"]
        for tech in common_tech:
            if tech in job_description.lower() and tech not in [s.lower() for s in resume_skills]:
                missing.append(tech)

        total = len(matched) + len(missing) + len(partial)
        percentage = round((len(matched) / max(total, 1)) * 100, 1) if total > 0 else 100

        return {
            "missing": list(set(missing)),
            "matched": matched,
            "partial": partial,
            "percentage": percentage,
        }

    def _generate_suggestions(self, extracted: dict, ats_score: dict) -> list:
        suggestions = []

        if ats_score.get("formatting", 0) < 80:
            suggestions.append({
                "type": "formatting",
                "severity": "high",
                "title": "Improve Resume Formatting",
                "description": "Add missing sections like contact information, professional summary, and ensure consistent formatting throughout.",
                "category": "Format"
            })

        if not extracted.get("experience"):
            suggestions.append({
                "type": "experience",
                "severity": "high",
                "title": "Add Work Experience",
                "description": "Include detailed work experience with specific job titles, companies, dates, and achievements.",
                "category": "Content"
            })

        if not extracted.get("education"):
            suggestions.append({
                "type": "education",
                "severity": "medium",
                "title": "Add Education Details",
                "description": "Include your educational background with degrees, institutions, and graduation dates.",
                "category": "Content"
            })

        skills = extracted.get("skills", [])
        if len(skills) < 5:
            suggestions.append({
                "type": "skills",
                "severity": "high",
                "title": "Add More Skills",
                "description": "Include at least 8-12 relevant technical and soft skills to improve ATS matching.",
                "category": "Content"
            })

        suggestions.extend([
            {
                "type": "metrics",
                "severity": "medium",
                "title": "Add Quantifiable Metrics",
                "description": "Include numbers and percentages to demonstrate impact (e.g., 'Increased revenue by 25%', 'Managed team of 10').",
                "category": "Impact"
            },
            {
                "type": "action_verbs",
                "severity": "medium",
                "title": "Use Stronger Action Verbs",
                "description": "Replace weak verbs like 'helped' or 'worked on' with strong ones like 'engineered', 'orchestrated', 'spearheaded'.",
                "category": "Language"
            },
            {
                "type": "keywords",
                "severity": "high",
                "title": "Optimize for Keywords",
                "description": "Include industry-specific keywords and phrases that match the job description to pass ATS filters.",
                "category": "ATS"
            },
            {
                "type": "summary",
                "severity": "medium",
                "title": "Add Professional Summary",
                "description": "Include a compelling 2-3 line professional summary at the top highlighting your key qualifications.",
                "category": "Content"
            },
            {
                "type": "bullet_points",
                "severity": "low",
                "title": "Improve Bullet Points",
                "description": "Start each bullet point with a strong action verb and keep them concise (1-2 lines each).",
                "category": "Format"
            },
            {
                "type": "grammar",
                "severity": "medium",
                "title": "Grammar and Spelling",
                "description": "Proofread carefully for grammar, spelling, and punctuation errors. Use tools like Grammarly for extra checking.",
                "category": "Quality"
            },
        ])

        return suggestions

    def _calculate_job_match(self, extracted: dict, job_description: Optional[str] = None) -> dict:
        if not job_description:
            return {"similarity_score": 0, "recommended_roles": []}

        resume_text = " ".join([
            " ".join(extracted.get("skills", [])),
            " ".join(extracted.get("experience", [])),
            " ".join(extracted.get("education", [])),
        ]).lower()

        job_lower = job_description.lower()

        overlap_words = set()
        resume_words = set(resume_text.split())
        job_words = set(job_lower.split())
        overlap_words = resume_words.intersection(job_words)

        similarity = min(round(len(overlap_words) / max(len(job_words), 1) * 100, 1), 100)

        roles = [
            {"title": "Software Engineer", "match": min(similarity + 10, 100)},
            {"title": "Backend Developer", "match": min(similarity + 5, 100)},
            {"title": "Full Stack Developer", "match": max(similarity - 5, 0)},
            {"title": "Data Engineer", "match": max(similarity - 10, 0)},
            {"title": "AI/ML Engineer", "match": max(similarity - 15, 0)},
        ]
        roles.sort(key=lambda x: x["match"], reverse=True)

        return {
            "similarity_score": similarity,
            "recommended_roles": roles[:5],
        }

    def get_by_id(self, analysis_id: int) -> Analysis:
        analysis = self.db.query(Analysis).filter(Analysis.id == analysis_id).first()
        if not analysis:
            raise NotFoundException("Analysis not found")
        return analysis

    def get_user_analyses(self, user_id: int, page: int = 1, per_page: int = 10) -> dict:
        total = self.db.query(Analysis).filter(Analysis.user_id == user_id).count()
        analyses = (
            self.db.query(Analysis)
            .filter(Analysis.user_id == user_id)
            .order_by(Analysis.created_at.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )
        return {"analyses": analyses, "total": total, "page": page, "per_page": per_page}

    def delete(self, analysis_id: int, user_id: int) -> None:
        analysis = self.db.query(Analysis).filter(
            Analysis.id == analysis_id,
            Analysis.user_id == user_id
        ).first()
        if not analysis:
            raise NotFoundException("Analysis not found")
        self.db.delete(analysis)
        self.db.commit()

    def get_analytics(self, user_id: int) -> dict:
        analyses = self.db.query(Analysis).filter(Analysis.user_id == user_id).all()

        total = len(analyses)
        avg_score = round(sum(a.ats_score or 0 for a in analyses) / max(total, 1), 1)

        all_skills = []
        for a in analyses:
            if a.matched_skills:
                all_skills.extend(a.matched_skills)

        skill_counts = {}
        for s in all_skills:
            skill_counts[s] = skill_counts.get(s, 0) + 1

        top_skills = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        most_common = [{"skill": s, "count": c} for s, c in top_skills]

        weekly = []
        from datetime import datetime, timedelta
        for i in range(6, -1, -1):
            day = datetime.utcnow() - timedelta(days=i)
            day_str = day.strftime("%Y-%m-%d")
            count = sum(1 for a in analyses if a.created_at and a.created_at.strftime("%Y-%m-%d") == day_str)
            weekly.append({"date": day_str, "count": count})

        distribution = {"excellent": 0, "good": 0, "average": 0, "poor": 0}
        for a in analyses:
            score = a.ats_score or 0
            if score >= 80:
                distribution["excellent"] += 1
            elif score >= 60:
                distribution["good"] += 1
            elif score >= 40:
                distribution["average"] += 1
            else:
                distribution["poor"] += 1

        return {
            "total_analyses": total,
            "average_ats_score": avg_score,
            "most_common_skills": most_common,
            "weekly_activity": weekly,
            "score_distribution": distribution,
        }
