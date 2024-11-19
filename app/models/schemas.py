from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, Integer, String, DateTime, Float, Text, Enum, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class ScrapingTask(Base):
    __tablename__ = "scraping_tasks"

    id = Column(Integer, primary_key=True)
    url = Column(String(500), nullable=False, index=True)
    status = Column(String(50), default="pending", index=True)  # pending, in_progress, completed, failed
    last_run = Column(DateTime, nullable=True)
    next_run = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    success_count = Column(Integer, default=0)
    fail_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    updated_at = Column(DateTime, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())

    # Relationships
    scraped_links = relationship("ScrapedLink", back_populates="task", cascade="all, delete-orphan")
    progress = relationship("ScrapingProgress", back_populates="task", uselist=False, cascade="all, delete-orphan")
    scholarships = relationship("Scholarship", back_populates="task", cascade="all, delete-orphan")

class ScrapedLink(Base):
    __tablename__ = "scraped_links"

    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey("scraping_tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    text = Column(String(500))
    url = Column(String(500), index=True)
    classification = Column(String(50), index=True)  # scholarship, irrelevant
    found_at = Column(DateTime, default=lambda: datetime.utcnow())
    processed = Column(Boolean, default=False, index=True)  # Track if the link has been processed

    # Relationship
    task = relationship("ScrapingTask", back_populates="scraped_links")

class ScrapingProgress(Base):
    __tablename__ = "scraping_progress"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("scraping_tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(50), index=True)  # in_progress, completed, failed
    total_links = Column(Integer, default=0)
    processed_links = Column(Integer, default=0)
    scholarships_found = Column(Integer, default=0)
    start_time = Column(DateTime, default=lambda: datetime.utcnow())
    end_time = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    processing_duration = Column(Float, nullable=True)  # Duration in seconds
    last_update = Column(DateTime, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())

    # Relationship
    task = relationship("ScrapingTask", back_populates="progress")

class Scholarship(Base):
    __tablename__ = "scholarships"

    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey("scraping_tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(500), index=True)
    amount = Column(String(100))
    deadline = Column(DateTime, nullable=True, index=True)
    field_of_study = Column(String(200), index=True)
    level_of_study = Column(String(100), index=True)
    eligibility_criteria = Column(Text)
    application_url = Column(String(500))
    source_url = Column(String(500), index=True)
    location_of_study = Column(String(200))
    
    # AI processing fields
    ai_summary = Column(Text, nullable=True)
    confidence_score = Column(Float, nullable=True, index=True)
    last_updated = Column(DateTime, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())
    
    # Additional fields for better tracking
    amount_normalized_min = Column(Float, nullable=True)
    amount_normalized_max = Column(Float, nullable=True)
    amount_type = Column(String(50), nullable=True)  # fixed, range, unknown
    is_renewable = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.utcnow())

    # Relationship
    task = relationship("ScrapingTask", back_populates="scholarships")