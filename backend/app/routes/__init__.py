from fastapi import APIRouter
from app.routes import auth, resumes, analysis, jobs, correction

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(resumes.router)
api_router.include_router(analysis.router)
api_router.include_router(jobs.router)
api_router.include_router(correction.router)
