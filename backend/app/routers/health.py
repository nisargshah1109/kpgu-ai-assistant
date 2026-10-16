from fastapi import APIRouter
from app.db import SessionLocal
from app.Models import Base
import logging

router = APIRouter()

@router.get("/health")
async def health_check():
    """
    Health check endpoint.
    """
    try:
        from sqlalchemy import text
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        db_status = "healthy"
    except Exception as e:
        logging.error(f"Database health check failed: {e}")
        db_status = "unhealthy"

    # Check Gemini API key (we can't actually call the API without making a request, but we can check if the key is set)
    import os
    gemini_key = os.getenv("GEMINI_API_KEY")
    gemini_status = "configured" if gemini_key and gemini_key != "your_api_key_here" else "not configured"

    # Check FAISS index (we'll check if the index file exists)
    import os
    faiss_index_path = "vector_store/faiss_index.bin"
    faiss_status = "available" if os.path.exists(faiss_index_path) else "not available"

    return {
        "status": "healthy" if db_status == "healthy" and gemini_status == "configured" and faiss_status == "available" else "degraded",
        "database": db_status,
        "gemini": gemini_status,
        "vector_store": faiss_status
    }