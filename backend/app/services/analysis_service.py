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
        self.client = None
        if settings.OPENAI_API_KEY:
            kwargs = {"api_key": settings.OPENAI_API_KEY}
            if settings.OPENAI_BASE_URL:
                kwargs["base_url"] = settings.OPENAI_BASE_URL
            self.client = OpenAI(**kwargs)

    async def _evaluate_resume_with_llm(self, raw_text: str, job_description: Optional[str] = None) -> dict:
        if not self.client:
            return {}

        prompt = f"""
        Analyze the following resume text. Evaluate the language and quality, and score each category from 0 to 100:
        1. "grammar": Grammar, spelling, punctuation, and typos.
        2. "action_verbs": Use of strong, professional action verbs instead of weak ones (e.g., "engineered" instead of "worked on").
        3. "metrics": Presence and quality of quantifiable results, percentages, and numbers (e.g., "improved speed by 30%").
        4. "formatting_readability": Readability, structure, flow, and professional tone.
        
        Provide constructive suggestions for improvement if any of these scores are below 90.
        For each suggestion, provide:
        - "type": one of "grammar", "action_verbs", "metrics", "formatting"
        - "severity": "high", "medium", or "low"
        - "title": a short title
        - "description": a specific description of what to improve based on the resume text
        - "category": a category name (e.g., "Quality", "Language", "Impact", "Format")

        CRITICAL REQUIREMENT:
        The output MUST be a valid JSON object. Inside the JSON string fields (like "description"), any double quotes (") MUST be escaped as \\" and backslashes (\\) MUST be escaped as \\\\. Single quotes (') do not need to be escaped, but do not use unescaped double quotes inside values.

        Format your response as a valid JSON object with the following structure:
        {{
            "scores": {{
                "grammar": 95,
                "action_verbs": 80,
                "metrics": 60,
                "formatting_readability": 85
            }},
            "suggestions": [
                {{
                    "type": "metrics",
                    "severity": "medium",
                    "title": "Add Quantifiable Metrics",
                    "description": "While you describe your work well, consider adding percentages or numbers to demonstrate impact.",
                    "category": "Impact"
                }}
            ]
        }}
        
        Resume text to analyze:
        ---
        {raw_text}
        ---
        """

        try:
            response = self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a professional resume auditor that outputs valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.2,
            )
            content = response.choices[0].message.content.strip()
            
            if content.startswith("```"):
                content = content.split("\n", 1)[1]
                if content.endswith("```"):
                    content = content[:-3]
                content = content.strip()

            return json.loads(content)
        except Exception as e:
            logger.error(f"Failed to evaluate resume with LLM: {e}")
            return {}

    async def create_analysis(self, user_id: int, data: AnalysisCreate) -> Analysis:
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
        
        # Call Gemini to dynamically evaluate the resume text
        llm_eval = await self._evaluate_resume_with_llm(raw_text, data.job_description)
        
        suggestions = []
        # Add basic section checks
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

        if llm_eval and "scores" in llm_eval:
            # Integrate dynamic suggestions from LLM
            suggestions.extend(llm_eval.get("suggestions", []))
            
            # Incorporate dynamic scores into details
            llm_scores = llm_eval["scores"]
            grammar_score = llm_scores.get("grammar", 100)
            action_verbs_score = llm_scores.get("action_verbs", 100)
            metrics_score = llm_scores.get("metrics", 100)
            
            ats_score["grammar"] = grammar_score
            ats_score["action_verbs"] = action_verbs_score
            ats_score["metrics"] = metrics_score
            
            # Blend readability into formatting
            if "formatting_readability" in llm_scores:
                ats_score["formatting"] = round((ats_score["formatting"] + llm_scores["formatting_readability"]) / 2, 1)
            
            # Recalculate overall score with language quality included (30% weight)
            language_score = (grammar_score * 0.4 + action_verbs_score * 0.3 + metrics_score * 0.3)
            base_overall = ats_score.get("overall", 0)
            overall_score = round(base_overall * 0.7 + language_score * 0.3, 1)
            ats_score["overall"] = overall_score
        else:
            # Fallback to static suggestions
            suggestions.extend(self._generate_suggestions(extracted, ats_score))

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
