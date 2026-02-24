import os
from sqlalchemy import create_engine, Column, Integer, String, Float, Text, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
import json

DATABASE_URL = "sqlite:///./truthguard.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class ScanResult(Base):
    __tablename__ = "scans"

    id = Column(Integer, primary_key=True, index=True)
    scan_id = Column(String, unique=True, index=True, nullable=False) # e.g., TG-8924
    filename = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    verdict = Column(String, nullable=False)
    fake_probability = Column(Float, nullable=False)
    details_json = Column(Text, nullable=False) # Store the full API response as JSON string

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
