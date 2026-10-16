import sys
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional

# Ensure broken torchvision op (RuntimeError: operator torchvision::nms does not exist)
# does not crash transformers/sentence-transformers in this text NLP environment.
if "torchvision" not in sys.modules:
    sys.modules["torchvision"] = None

BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BACKEND_DIR.parent

class Settings(BaseSettings):
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL_NAME: str = "gemini-2.0-flash"
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"
    RELEVANCE_THRESHOLD: float = 0.20
    MAX_CONTEXT_CHUNKS: int = 4
    MAX_HISTORY_MESSAGES: int = 6
    MAX_OUTPUT_TOKENS: int = 512
    KPGU_BASE_URL: str = "https://www.kpgu.ac.in/"

    # Canonical Absolute Paths
    BASE_DIR: str = str(BACKEND_DIR)
    DATA_RAW_DIR: str = str(BACKEND_DIR / "data" / "raw")
    DATA_PROCESSED_DIR: str = str(BACKEND_DIR / "data" / "processed")
    VECTOR_STORE_DIR: str = str(BACKEND_DIR / "vector_store")
    VECTOR_INDEX_PATH: str = str(BACKEND_DIR / "vector_store" / "faiss_index.bin")
    METADATA_PATH: str = str(BACKEND_DIR / "vector_store" / "metadata.json")
    DATABASE_PATH: str = str(BACKEND_DIR / "kpgu_assistant.db")

    # Root mirror paths
    ROOT_DATA_RAW_DIR: str = str(PROJECT_ROOT / "data" / "raw")
    ROOT_DATA_PROCESSED_DIR: str = str(PROJECT_ROOT / "data" / "processed")
    ROOT_VECTOR_STORE_DIR: str = str(PROJECT_ROOT / "vector_store")
    ROOT_VECTOR_INDEX_PATH: str = str(PROJECT_ROOT / "vector_store" / "faiss_index.bin")
    ROOT_METADATA_PATH: str = str(PROJECT_ROOT / "vector_store" / "metadata.json")

    class Config:
        env_file = str(BACKEND_DIR / ".env")
        env_file_encoding = 'utf-8'
        extra = "allow"

settings = Settings()