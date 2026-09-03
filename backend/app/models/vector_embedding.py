from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey
from backend.app.core.database import Base

class KnowledgeItem(Base):
    """Knowledge base article or historical complaint embedding for RAG retrieval."""
    __tablename__ = "knowledge_items"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    category = Column(String(100), index=True, nullable=False)
    department = Column(String(100), index=True, nullable=False)
    problem_summary = Column(Text, nullable=False)
    solution_steps = Column(Text, nullable=False)
    
    # Store embedding as JSON list of floats for universal compatibility (Postgres/SQLite)
    embedding = Column(JSON, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
