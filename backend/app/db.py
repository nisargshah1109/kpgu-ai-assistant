from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings
import os

# SQLite database URL anchored to canonical absolute path
db_path_posix = settings.DATABASE_PATH.replace("\\", "/")
SQLALCHEMY_DATABASE_URL = f"sqlite:///{db_path_posix}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Function to create tables
def create_tables():
    # Explicitly import models so Base.metadata knows about all tables
    import app.Models  # noqa: F401
    Base.metadata.create_all(bind=engine)