import os
import time
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

key = os.getenv("OPENAI_API_KEY")
base_url = os.getenv("OPENAI_BASE_URL")
model = os.getenv("OPENAI_MODEL")

AI_SYSTEM_PROMPT = """You are a professional resume editor. Your ONLY job is to improve the text quality of resume content.

RULES - You MUST follow these exactly:
1. ONLY correct: grammar, spelling, punctuation, sentence structure
2. ONLY improve: weak bullet points, action verbs, ATS keywords, readability, professional tone. DIVERSIFY action verbs: Do not repeat the same action verb (like "Developed" or "Built") across different bullet points. Use a variety of strong, professional Software Engineering action verbs such as: Engineered, Architected, Implemented, Spearheaded, Optimized, Formulated, Orchestrated, Designed, Devised, Automated, Modernized, Refactored.
3. NEVER change: the meaning, facts, dates, names, companies, skills, or any factual content
4. NEVER add: fake information, new skills, new projects, new experience, new certifications
5. NEVER remove: any user content, sections, or information
6. Keep the same line structure - one corrected line per original line
7. Return ONLY the corrected text, nothing else

You will receive numbered lines of resume text. Return the corrected version with the SAME line numbers.
Format your response as a JSON object with a single key "corrections", containing a list of objects with "line_num" and "corrected" fields."""

numbered_lines = [
    "0: BAD RESUME",
    "1: Ali Khan",
    "2: Karachi",
    "3: 03001234567",
    "4: alikhan123@gmail.com",
    "5: About Me",
    "6: I am a computer science student. I like programming and I want to get a software engineering job. I am hardworking and I can learn new things. I can work under pressure and I like teamwork.",
    "7: Education",
    "8: BS Computer Science",
    "9: ABC University",
    "10: 2022 - Present",
    "11: CGPA: 3.1",
    "12: Skills",
    "13: C++",
    "14: Java",
    "15: Python",
    "16: HTML",
    "17: CSS",
    "18: JavaScript",
    "19: SQL",
    "20: Git",
    "21: Projects",
    "22: Library Management System",
    "23: Developed a library system.",
    "24: Used Java."
]

prompt = f"""Correct the following resume text lines from "BAD RESUME.docx".
Fix grammar, spelling, punctuation, improve action verbs and professional tone.
DO NOT change any factual content, names, dates, companies, or skills.
DO NOT add or remove any information.
Return a JSON object with a single key "corrections", containing a list of objects like {{"line_num": 0, "corrected": "corrected text"}}.
Only return the JSON object, nothing else.

Lines to correct:
{"\n".join(numbered_lines)}"""

client = OpenAI(api_key=key, base_url=base_url)
print(f"Calling model {model}...")
start_time = time.time()
try:
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": AI_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0.3,
        max_tokens=4000
    )
    elapsed = time.time() - start_time
    print(f"Call finished in {elapsed:.2f} seconds.")
    print("Response raw text:")
    print(response.choices[0].message.content)
except Exception as e:
    elapsed = time.time() - start_time
    print(f"Call failed in {elapsed:.2f} seconds. Error: {e}")
