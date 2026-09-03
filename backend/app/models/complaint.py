from datetime import datetime
from enum import Enum
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, Boolean, JSON, ForeignKey
from sqlalchemy.orm import relationship, synonym
from app.core.database import Base

class ComplaintSource(str, Enum):
    EMAIL = "EMAIL"
    WEB = "WEB"
    MANUAL = "MANUAL"

class ComplaintStatus(str, Enum):
    NEW = "NEW"
    AI_ANALYZING = "AI_ANALYZING"
    AI_ANALYZED = "AI_ANALYZED"
    ROUTED = "ROUTED"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    WAITING_FOR_CUSTOMER = "WAITING_FOR_CUSTOMER"
    ESCALATED = "ESCALATED"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"

class ComplaintEventType(str, Enum):
    COMPLAINT_RECEIVED = "COMPLAINT_RECEIVED"
    AI_ANALYSIS_STARTED = "AI_ANALYSIS_STARTED"
    AI_ANALYSIS_COMPLETED = "AI_ANALYSIS_COMPLETED"
    ROUTED = "ROUTED"
    ASSIGNED = "ASSIGNED"
    INVESTIGATION_STARTED = "INVESTIGATION_STARTED"
    WAITING_CUSTOMER = "WAITING_CUSTOMER"
    ESCALATED = "ESCALATED"
    RESOLUTION_COMPLETED = "RESOLUTION_COMPLETED"
    RESPONSE_APPROVED = "RESPONSE_APPROVED"
    RESPONSE_SENT = "RESPONSE_SENT"
    COMPLAINT_CLOSED = "COMPLAINT_CLOSED"

class Complaint(Base):
    __tablename__ = "complaints"

    id = Column(Integer, primary_key=True, index=True)
    complaint_number = Column(String(50), unique=True, index=True, nullable=False)
    customer_name = Column(String(255), nullable=True)
    customer_email = Column(String(255), index=True, nullable=False)
    subject = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    source = Column(String(50), default=ComplaintSource.WEB.value, index=True, nullable=False)  # EMAIL, WEB, MANUAL
    
    # Classification & Routing
    category = Column(String(100), index=True, nullable=False)
    sub_category = Column(String(100), nullable=True)
    department_id = Column(Integer, ForeignKey("departments.id", ondelete="SET NULL"), nullable=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id", ondelete="SET NULL"), nullable=True, index=True)
    assigned_agent_id = Column(Integer, ForeignKey("agents.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Priority & Intelligence Metrics
    sentiment = Column(String(50), default="Neutral", nullable=False)  # Positive, Neutral, Negative
    emotion = Column(String(50), default="Neutral", nullable=False)    # Frustration, Anger, Anxiety, Neutral, etc.
    urgency = Column(String(50), default="Medium", index=True, nullable=False)  # Critical, High, Medium, Low
    priority = Column(String(50), default="P3", index=True, nullable=False)     # P1, P2, P3, P4
    priority_score = Column(Float, default=50.0, nullable=False)       # 0.0 to 100.0
    ai_confidence = Column(Float, default=0.90, nullable=False)        # 0.0 to 1.0
    review_required = Column(Boolean, default=False, nullable=False)   # Human review flag
    ai_status = Column(String(50), default="COMPLETED", nullable=False) # COMPLETED, PROCESSING, FAILED
    status = Column(String(50), default=ComplaintStatus.NEW.value, index=True, nullable=False)  # Lifecycle Status Enum
    summary = Column(Text, nullable=True)                              # LLM generated concise summary

    # SLA & Escalation
    sla_deadline = Column(DateTime, nullable=True)
    is_escalated = Column(Boolean, default=False, nullable=False)
    
    # Similarity & Deduplication
    is_duplicate = Column(Boolean, default=False, nullable=False)
    duplicate_of_id = Column(Integer, ForeignKey("complaints.id", ondelete="SET NULL"), nullable=True)
    
    # Embeddings & Preprocessing
    cleaned_text = Column(Text, nullable=True)
    embedding = Column(JSON, nullable=True)  # 384-dimensional dense vector
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

    # Relationships
    department = relationship("Department")
    team = relationship("Team")
    assigned_agent = relationship("Agent")
    assignments = relationship("ComplaintAssignment", back_populates="complaint", cascade="all, delete-orphan")
    events = relationship("ComplaintEvent", back_populates="complaint", cascade="all, delete-orphan", order_by="ComplaintEvent.created_at.asc()")
    feedback = relationship("ComplaintFeedback", back_populates="complaint", cascade="all, delete-orphan")
    entities = relationship("ComplaintEntity", back_populates="complaint", cascade="all, delete-orphan")

    # Synonyms for transparent backwards compatibility
    ticket_number = synonym("complaint_number")
    body = synonym("description")
    priority_level = synonym("priority")

class ComplaintAssignment(Base):
    __tablename__ = "complaint_assignments"

    id = Column(Integer, primary_key=True, index=True)
    complaint_id = Column(Integer, ForeignKey("complaints.id", ondelete="CASCADE"), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id", ondelete="SET NULL"), nullable=True)
    team_id = Column(Integer, ForeignKey("teams.id", ondelete="SET NULL"), nullable=True)
    agent_id = Column(Integer, ForeignKey("agents.id", ondelete="SET NULL"), nullable=True)
    assigned_by = Column(String(100), default="AI_ENGINE")  # AI_ENGINE, SUPERVISOR, MANUAL
    assigned_at = Column(DateTime, default=datetime.utcnow)
    reason = Column(String(500), nullable=True)

    complaint = relationship("Complaint", back_populates="assignments")
    department = relationship("Department")
    team = relationship("Team")
    agent = relationship("Agent")

class ComplaintEvent(Base):
    __tablename__ = "complaint_events"

    id = Column(Integer, primary_key=True, index=True)
    complaint_id = Column(Integer, ForeignKey("complaints.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String(50), nullable=False, index=True)
    actor = Column(String(100), default="SYSTEM")
    description = Column(Text, nullable=False)
    event_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    complaint = relationship("Complaint", back_populates="events")
    notes = synonym("description")

class ComplaintFeedback(Base):
    __tablename__ = "complaint_feedback"

    id = Column(Integer, primary_key=True, index=True)
    complaint_id = Column(Integer, ForeignKey("complaints.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    is_category_correct = Column(Boolean, nullable=False)
    corrected_category = Column(String(100), nullable=True)
    is_sentiment_correct = Column(Boolean, nullable=False)
    rating = Column(Integer, default=5)  # 1-5 agent satisfaction with AI
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    complaint = relationship("Complaint", back_populates="feedback")
    user = relationship("User")
