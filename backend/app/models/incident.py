from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey
from app.core.database import Base

class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    incident_number = Column(String(50), unique=True, index=True, nullable=False)
    title = Column(String(255), nullable=False)  # e.g. "Portal Authentication Failure"
    description = Column(Text, nullable=True)
    department_id = Column(Integer, ForeignKey("departments.id", ondelete="SET NULL"), nullable=True)
    department_name = Column(String(100), default="IT", nullable=False)  # e.g. "IT", "Finance"
    severity = Column(String(50), default="HIGH", nullable=False)  # HIGH, CRITICAL, MEDIUM, LOW
    status = Column(String(50), default="DETECTED", nullable=False)  # DETECTED, ACKNOWLEDGED, INVESTIGATING, RESOLVED
    affected_count = Column(Integer, default=0, nullable=False)
    complaint_ids = Column(JSON, default=list)  # list of complaint IDs
    sample_complaints = Column(JSON, default=list)  # list of sample strings
    detected_at = Column(DateTime, default=datetime.utcnow)
    acknowledged_by = Column(String(255), nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
    resolved_by = Column(String(255), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    resolution_notes = Column(Text, nullable=True)
