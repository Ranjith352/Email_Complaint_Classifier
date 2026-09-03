from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, Boolean, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class ComplaintPrediction(Base):
    __tablename__ = "complaint_predictions"

    id = Column(Integer, primary_key=True, index=True)
    complaint_id = Column(Integer, ForeignKey("complaints.id", ondelete="CASCADE"), nullable=False)
    model_name = Column(String(100), nullable=False)
    model_version = Column(String(50), default="1.0.0")
    
    predicted_category = Column(String(100), nullable=False)
    category_confidence = Column(Float, nullable=False)
    
    predicted_dept = Column(String(100), nullable=False)
    dept_confidence = Column(Float, nullable=False)
    
    urgency = Column(String(50), nullable=False)
    urgency_score = Column(Float, default=0.5)
    
    sentiment = Column(String(50), nullable=False)
    sentiment_score = Column(Float, default=0.0)
    
    emotion = Column(String(50), nullable=False)
    emotion_score = Column(Float, default=0.5)
    
    execution_time_ms = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

class ComplaintEntity(Base):
    __tablename__ = "complaint_entities"

    id = Column(Integer, primary_key=True, index=True)
    complaint_id = Column(Integer, ForeignKey("complaints.id", ondelete="CASCADE"), nullable=False)
    entity_type = Column(String(50), nullable=False)  # TRANSACTION_ID, ORDER_ID, AMOUNT, DATE, EMAIL, ACCOUNT_NUMBER
    entity_value = Column(String(255), nullable=False)
    confidence = Column(Float, default=0.90)
    start_char = Column(Integer, nullable=True)
    end_char = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    complaint = relationship("Complaint", back_populates="entities")

class AIResponse(Base):
    """Stores LLM generation records for human-in-the-loop review and audit."""
    __tablename__ = "ai_responses"

    id = Column(Integer, primary_key=True, index=True)
    complaint_id = Column(Integer, ForeignKey("complaints.id", ondelete="CASCADE"), nullable=False)
    provider = Column(String(50), nullable=False)  # ollama, groq, heuristic_fallback
    model = Column(String(100), nullable=False)
    prompt_tokens = Column(Integer, default=0)
    response_tokens = Column(Integer, default=0)
    response_type = Column(String(50), nullable=False)  # SUMMARY, RECOMMENDATION, DRAFT_REPLY, RAG_EXPLANATION
    content = Column(Text, nullable=False)
    
    # Human Approval (Human-in-the-loop)
    is_approved = Column(Boolean, default=False)
    approved_by = Column(String(255), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    feedback_score = Column(Integer, nullable=True)  # 1 to 5
    
    created_at = Column(DateTime, default=datetime.utcnow)

class ModelVersion(Base):
    """Tracks deployed NLP and Generative AI model metadata."""
    __tablename__ = "model_versions"

    id = Column(Integer, primary_key=True, index=True)
    task_name = Column(String(100), unique=True, nullable=False)  # classification, sentiment, ner, embeddings, llm
    model_name = Column(String(100), nullable=False)
    version = Column(String(50), default="1.0.0")
    provider = Column(String(50), default="local")
    is_active = Column(Boolean, default=True)
    accuracy_score = Column(Float, nullable=True)
    description = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
