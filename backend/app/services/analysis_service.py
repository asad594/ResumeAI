import json
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from app.models.analysis import Analysis
from app.models.resume import Resume
from app.schemas.analysis import AnalysisCreate
from app.core.config import settings
from app.core.exceptions import NotFoundException, handle_llm_exception
from app.services.llm_service import LLMService
from loguru import logger


class AnalysisService:
    def __init__(self, db: Session):
        self.db = db
        self.llm_service = LLMService()

    async def _evaluate_resume_with_llm(self, resume_id: int, raw_text: str, job_description: Optional[str] = None) -> dict:
        if not self.llm_service.client:
            return {}

        prompt = f"""
        Analyze the following resume text. Evaluate the language and quality, and score each category from 0 to 100:
        1. "grammar": Grammar, spelling, punctuation, and typos.
        2. "action_verbs": Use of strong, professional Software Engineering action verbs instead of weak/repetitive ones (e.g., "engineered", "implemented", "architected" instead of "worked on", "helped", or repeating "developed").
        3. "metrics": Presence and quality of quantifiable results, percentages, and numbers (e.g., "improved speed by 30%"). NOTE: Do not assign an unfairly low score (e.g., below 75) to metrics if the resume is technically strong and well-written but simply lacks quantifiable numbers. Instead, assign a baseline metrics score of 75-80 if the descriptions are strong, and list metrics as a suggestion for further improvement.
        4. "formatting_readability": Readability, structure, flow, and professional tone.
        
        Provide at most 3-4 high-impact constructive suggestions in total for improvement if any of these scores are below 90. Keep suggestions concise to speed up generation time.
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
                "metrics": 75,
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

        import hashlib
        prompt_len = len(prompt)
        prompt_hash = hashlib.sha256(prompt.encode('utf-8')).hexdigest()
        first_1000 = prompt[:1000]
        logger.info(f"LLM REQUEST (Evaluation) - Resume ID: {resume_id}, Prompt Length: {prompt_len}, Prompt Hash: {prompt_hash}")
        logger.info(f"Prompt First 1000 characters:\n{first_1000}")

        try:
            content = await self.llm_service.generate_chat_completion(
                messages=[
                    {"role": "system", "content": "You are a professional resume auditor that outputs valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.2,
            )
            content = content.strip()
            
            if content.startswith("```"):
                content = content.split("\n", 1)[1]
                if content.endswith("```"):
                    content = content[:-3]
                content = content.strip()

            return json.loads(content)
        except Exception as e:
            raise handle_llm_exception(e)

    async def create_analysis(self, user_id: int, data: AnalysisCreate) -> Analysis:
        resume = self.db.query(Resume).filter(
            Resume.id == data.resume_id,
            Resume.user_id == user_id
        ).first()
        if not resume:
            raise NotFoundException("Resume not found")

        logger.info(f"ANALYSIS START - Resume ID: {resume.id}, User ID: {user_id}")
        extracted = resume.extracted_data or {}
        raw_text = extracted.get("raw_text", "")

        ats_score = self._calculate_ats_score(extracted, data.job_description)
        skills_analysis = self._analyze_skills(extracted, data.job_description)
        
        # Call Gemini to dynamically evaluate the resume text
        llm_eval = await self._evaluate_resume_with_llm(resume.id, raw_text, data.job_description)
        
        suggestions = []
        # Add basic section checks
        if ats_score.get("formatting", 0) < settings.ATS_SUGGESTION_FORMATTING_THRESHOLD:
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
        if len(skills) < settings.ATS_SUGGESTION_SKILLS_MIN:
            suggestions.append({
                "type": "skills",
                "severity": "high",
                "title": "Add More Skills",
                "description": "Include at least 8-12 relevant technical and soft skills to improve ATS matching.",
                "category": "Content"
            })

        grammar_score = settings.ATS_LLM_DEFAULT_GRAMMAR
        action_verbs_score = settings.ATS_LLM_DEFAULT_ACTION_VERBS
        metrics_score = settings.ATS_LLM_DEFAULT_METRICS

        if llm_eval and "scores" in llm_eval:
            # Integrate dynamic suggestions from LLM
            suggestions.extend(llm_eval.get("suggestions", []))
            
            # Incorporate dynamic scores into details
            llm_scores = llm_eval["scores"]
            grammar_score = llm_scores.get("grammar", settings.ATS_LLM_DEFAULT_GRAMMAR)
            action_verbs_score = llm_scores.get("action_verbs", settings.ATS_LLM_DEFAULT_ACTION_VERBS)
            metrics_score = llm_scores.get("metrics", settings.ATS_LLM_DEFAULT_METRICS)
            
            logger.info(f"DYNAMIC SCORING - Resume ID: {resume.id}, grammar: {grammar_score}, action_verbs: {action_verbs_score}, metrics: {metrics_score}")
            
            # Blend readability into formatting
            if "formatting_readability" in llm_scores:
                ats_score["formatting"] = round((ats_score["formatting"] + llm_scores["formatting_readability"]) / 2, 1)
            
            # Recalculate overall score with language quality included (30% weight)
            language_score = (
                grammar_score * settings.ATS_WEIGHT_LLM_GRAMMAR +
                action_verbs_score * settings.ATS_WEIGHT_LLM_ACTION_VERBS +
                metrics_score * settings.ATS_WEIGHT_LLM_METRICS
            )
            base_overall = ats_score.get("overall", 0)
            overall_score = round(
                base_overall * settings.ATS_WEIGHT_BASE_OVERALL +
                language_score * settings.ATS_WEIGHT_LANGUAGE_QUALITY,
                1
            )
            ats_score["overall"] = overall_score
            logger.info(f"DYNAMIC SCORING - Resume ID: {resume.id}, language_score: {language_score}, base_overall: {base_overall}, overall_score: {overall_score}")
        else:
            # Fallback to static suggestions
            suggestions.extend(self._generate_suggestions(extracted, ats_score))

        # Calculate category breakdown and suggestions
        breakdown, category_suggestions = self._calculate_breakdown_and_category_suggestions(
            extracted, ats_score, grammar_score, action_verbs_score, metrics_score, data.job_description
        )
        ats_score["breakdown"] = breakdown
        ats_score["category_suggestions"] = category_suggestions

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
        logger.info(f"ANALYSIS COMPLETE - Resume ID: {resume.id}, Score: {analysis.ats_score}")
        return analysis

    def _calculate_ats_score(self, extracted: dict, job_description: Optional[str] = None) -> dict:
        formatting_score = 0
        keywords_score = 0
        experience_score = 0
        education_score = 0
        skills_score = 0

        if extracted.get("name"):
            formatting_score += settings.ATS_SCORE_FORMATTING_NAME
        if extracted.get("email"):
            formatting_score += settings.ATS_SCORE_FORMATTING_EMAIL
        if extracted.get("phone"):
            formatting_score += settings.ATS_SCORE_FORMATTING_PHONE
        if extracted.get("location"):
            formatting_score += settings.ATS_SCORE_FORMATTING_LOCATION
        formatting_score = min(formatting_score, settings.ATS_SCORE_MAX)

        skills = extracted.get("skills", [])
        skills_score = min(len(skills) * settings.ATS_SCORE_SKILLS_MULTIPLIER, settings.ATS_SCORE_MAX)

        experience = extracted.get("experience", [])
        experience_score = min(len(experience) * settings.ATS_SCORE_EXPERIENCE_MULTIPLIER, settings.ATS_SCORE_MAX)

        projects = extracted.get("projects", [])
        projects_score = min(len(projects) * settings.ATS_SCORE_PROJECT_MULTIPLIER, settings.ATS_SCORE_MAX)

        if experience_score == 0 and projects_score > 0:
            experience_score = min(
                round(projects_score * settings.ATS_PROJECT_TO_EXPERIENCE_MULTIPLIER, 1),
                settings.ATS_SCORE_PROJECT_FALLBACK_MAX
            )

        education = extracted.get("education", [])
        education_score = min(len(education) * settings.ATS_SCORE_EDUCATION_MULTIPLIER, settings.ATS_SCORE_MAX)

        if job_description:
            if skills:
                job_lower = job_description.lower()
                matched = sum(1 for s in skills if s.lower() in job_lower)
                keywords_score = min(int((matched / max(len(skills), 1)) * 100), 100)
            else:
                keywords_score = 0
        else:
            keywords_score = None

        # For overall score calculation fallback
        keywords_score_for_calc = keywords_score if keywords_score is not None else skills_score

        overall = round(
            (
                formatting_score * settings.ATS_WEIGHT_FORMATTING +
                keywords_score_for_calc * settings.ATS_WEIGHT_KEYWORDS +
                experience_score * settings.ATS_WEIGHT_EXPERIENCE +
                education_score * settings.ATS_WEIGHT_EDUCATION +
                skills_score * settings.ATS_WEIGHT_SKILLS
            ),
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
            return {"missing": [], "matched": extracted.get("skills", []), "partial": [], "percentage": None}

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

        common_tech = ["python", "javascript", "typescript", "java", "react", "node", "aws", "docker", "kubernetes",
                       "sql", "mongodb", "redis", "graphql", "rest", "api", "git", "linux", "machine learning",
                       "data", "analytics", "agile", "scrum", "ci/cd", "terraform", "gcp", "azure"]
        for tech in common_tech:
            if tech in job_description.lower() and tech not in [s.lower() for s in resume_skills]:
                missing.append(tech)

        total = len(matched) + len(missing) + len(partial)
        percentage = round((len(matched) / max(total, 1)) * 100, 1) if total > 0 else 0

        return {
            "missing": list(set(missing)),
            "matched": matched,
            "partial": partial,
            "percentage": percentage,
        }

    def _generate_suggestions(self, extracted: dict, ats_score: dict) -> list:
        suggestions = []

        if not extracted.get("skills"):
            suggestions.append({
                "type": "skills",
                "severity": "high",
                "title": "No Skills Detected",
                "description": "We could not find a dedicated skills section in your resume. Please add a 'Skills' section listing your technical proficiencies (e.g. Python, SQL, Git) to help ATS parsers match your qualifications.",
                "category": "Content"
            })

        if ats_score.get("formatting", 0) < settings.ATS_SUGGESTION_FORMATTING_THRESHOLD:
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
        if len(skills) < settings.ATS_SUGGESTION_SKILLS_MIN:
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
            {"title": "Software Engineer", "match": min(similarity + settings.ATS_ROLE_MATCH_SOFTWARE_ENGINEER_OFFSET, 100)},
            {"title": "Backend Developer", "match": min(similarity + settings.ATS_ROLE_MATCH_BACKEND_DEVELOPER_OFFSET, 100)},
            {"title": "Full Stack Developer", "match": max(similarity + settings.ATS_ROLE_MATCH_FULL_STACK_DEVELOPER_OFFSET, 0)},
            {"title": "Data Engineer", "match": max(similarity + settings.ATS_ROLE_MATCH_DATA_ENGINEER_OFFSET, 0)},
            {"title": "AI/ML Engineer", "match": max(similarity + settings.ATS_ROLE_MATCH_AI_ML_ENGINEER_OFFSET, 0)},
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
            if score >= settings.ATS_DISTRIBUTION_EXCELLENT:
                distribution["excellent"] += 1
            elif score >= settings.ATS_DISTRIBUTION_GOOD:
                distribution["good"] += 1
            elif score >= settings.ATS_DISTRIBUTION_AVERAGE:
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

    def _calculate_breakdown_and_category_suggestions(
        self,
        extracted: dict,
        ats_score: dict,
        grammar_score: float,
        action_verbs_score: float,
        metrics_score: float,
        job_description: Optional[str] = None
    ) -> tuple[dict, list]:
        # 1. Contact Information calculation
        contact_info_score = 0
        name = extracted.get("name")
        if name and name != "Unknown":
            contact_info_score += 25
        if extracted.get("email"):
            contact_info_score += 25
        if extracted.get("phone"):
            contact_info_score += 25
        if extracted.get("location"):
            contact_info_score += 15
        if extracted.get("linkedin") or "linkedin.com" in extracted.get("raw_text", "").lower():
            contact_info_score += 10
            
        k_score = ats_score.get("keywords")
        keywords_final = round(min(k_score, settings.ATS_MAX_CATEGORY_SCORE)) if k_score is not None else None

        breakdown = {
            "formatting": round(min(ats_score.get("formatting", 0), settings.ATS_MAX_CATEGORY_SCORE)),
            "contact_information": round(min(contact_info_score, settings.ATS_MAX_CATEGORY_SCORE)),
            "skills": round(min(ats_score.get("skills", 0), settings.ATS_MAX_CATEGORY_SCORE)),
            "experience": round(min(ats_score.get("experience", 0), settings.ATS_MAX_CATEGORY_SCORE)),
            "keywords": keywords_final,
            "action_verbs": round(min(action_verbs_score, settings.ATS_MAX_CATEGORY_SCORE)),
            "grammar": round(min(grammar_score, settings.ATS_MAX_CATEGORY_SCORE)),
            "metrics": round(min(metrics_score, settings.ATS_MAX_CATEGORY_SCORE))
        }

        # 2. Build Category Suggestions based on score threshold
        category_suggestions = []
        threshold = settings.ATS_BREAKDOWN_THRESHOLD
        
        # Formatting Suggestions
        if breakdown["formatting"] < threshold:
            sugs = ["Ensure section headings are consistent.", "Improve spacing and layout structure."]
            category_suggestions.append({
                "category": "Formatting",
                "score": breakdown["formatting"],
                "suggestions": sugs
            })
            
        # Contact Information Suggestions
        if breakdown["contact_information"] < threshold:
            sugs = []
            if not name or name == "Unknown":
                sugs.append("Include your full name at the top of the resume.")
            if not extracted.get("email"):
                sugs.append("Add a professional email address.")
            if not extracted.get("phone"):
                sugs.append("Include a valid contact phone number.")
            if not extracted.get("location"):
                sugs.append("Include your location (city and state/country).")
            if not (extracted.get("linkedin") or "linkedin.com" in extracted.get("raw_text", "").lower()):
                sugs.append("Add your LinkedIn profile link to improve social credibility.")
            if not sugs:
                sugs = ["Check contact details formatting."]
            category_suggestions.append({
                "category": "Contact Information",
                "score": breakdown["contact_information"],
                "suggestions": sugs
            })
            
        # Skills Suggestions
        if breakdown["skills"] < threshold:
            sugs = []
            skills_count = len(extracted.get("skills", []))
            if skills_count < settings.ATS_MIN_SKILLS:
                sugs.append(f"Only {skills_count} skills detected. Include at least {settings.ATS_MIN_SKILLS} relevant technical skills.")
            
            # If we have missing tech from job description
            skills_analysis = self._analyze_skills(extracted, job_description)
            missing = skills_analysis.get("missing", [])
            if missing:
                tech_list = ", ".join(missing[:5])
                sugs.append(f"Missing critical tech/skills from job description: {tech_list}.")
            else:
                sugs.append("Include relevant frameworks, databases, and core libraries used.")
            category_suggestions.append({
                "category": "Skills",
                "score": breakdown["skills"],
                "suggestions": sugs
            })
            
        # Experience Suggestions
        if breakdown["experience"] < threshold:
            sugs = []
            exp_count = len(extracted.get("experience", []))
            if exp_count == 0:
                sugs.append("No professional work experience detected. Detail relevant project work, internships, or academic contributions in place of work history.")
            else:
                sugs.append("Describe specific responsibilities and achievements in your work history using the 'Action + Context + Result' formula.")
            category_suggestions.append({
                "category": "Experience",
                "score": breakdown["experience"],
                "suggestions": sugs
            })
            
        # Keywords Suggestions
        if breakdown["keywords"] is not None and (breakdown["keywords"] < settings.ATS_MIN_KEYWORDS * 10 or breakdown["keywords"] < threshold):
            sugs = ["Incorporate more industry-specific terminology.", "Align your technical stack description with keywords from target job descriptions."]
            category_suggestions.append({
                "category": "Keywords",
                "score": breakdown["keywords"],
                "suggestions": sugs
            })
            
        # Action Verbs Suggestions
        if breakdown["action_verbs"] < settings.ATS_MIN_ACTION_VERBS:
            sugs = ["Use strong, professional action verbs like 'engineered', 'implemented', 'designed'.", "Avoid repeating verbs like 'developed' or using passive verbs like 'worked on'."]
            category_suggestions.append({
                "category": "Action Verbs",
                "score": breakdown["action_verbs"],
                "suggestions": sugs
            })
            
        # Grammar Suggestions
        if breakdown["grammar"] < threshold:
            sugs = ["Proofread carefully to fix spelling mistakes and typos.", "Ensure correct use of capitalization and punctuation across all sections."]
            category_suggestions.append({
                "category": "Grammar",
                "score": breakdown["grammar"],
                "suggestions": sugs
            })
            
        # Metrics Suggestions
        if breakdown["metrics"] < settings.ATS_MIN_METRICS:
            sugs = ["Add quantifiable metrics (e.g. percentages, dollar values, time savings) to showcase your impact.", "Quantify the scale of the projects or teams you worked with."]
            category_suggestions.append({
                "category": "Metrics",
                "score": breakdown["metrics"],
                "suggestions": sugs
            })
            
        return breakdown, category_suggestions
