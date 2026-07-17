import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.analysis import Analysis
from app.schemas.analysis import AnalysisResponse
from app.core.config import settings

# Connect to database
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

try:
    # Fetch latest analysis
    analysis = db.query(Analysis).order_by(Analysis.created_at.desc()).first()
    if analysis:
        # Convert to response schema
        resp = AnalysisResponse.model_validate(analysis)
        # Print serialized JSON
        print(json.dumps(resp.model_dump(), default=str, indent=2))
    else:
        print("No analysis records found.")
finally:
    db.close()
