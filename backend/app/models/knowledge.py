from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship, synonym
from app.core.database import Base

class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), index=True, nullable=False)
    document_name = synonym("title")  # Synonym for transparent dual-naming (document_name & title)
    
    category = Column(String(100), index=True, nullable=False)
    document_type = Column(String(50), default="REFUND_POLICY", nullable=False)  # The 9 official types
    department = Column(String(100), default="General", nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id", ondelete="SET NULL"), nullable=True)
    
    version = Column(Integer, default=1, nullable=False)
    uploaded_by = Column(String(100), default="Admin", nullable=False)
    
    content_text = Column(Text, nullable=False)
    chunk_index = Column(Integer, default=0)
    chunk_text = Column(Text, nullable=False)
    
    # Optional document-level embedding for backward compatibility
    embedding = Column(JSON, nullable=True)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 1-to-many relationship to granular chunks stored separately
    chunks = relationship("KnowledgeChunk", back_populates="document", cascade="all, delete-orphan")
    # 1-to-many relationship to embeddings stored separately
    chunk_embeddings = relationship("ChunkEmbedding", back_populates="document", cascade="all, delete-orphan")


class KnowledgeChunk(Base):
    """Stores granular text chunks separately from document metadata and vector embeddings."""
    __tablename__ = "knowledge_chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("knowledge_documents.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_index = Column(Integer, default=0, nullable=False)
    chunk_text = Column(Text, nullable=False)
    token_count = Column(Integer, default=0)
    
    # Optional backward-compatible embedding field
    embedding = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    document = relationship("KnowledgeDocument", back_populates="chunks")
    # 1-to-1 relationship to dedicated ChunkEmbedding stored in separate table
    chunk_embedding = relationship("ChunkEmbedding", back_populates="chunk", uselist=False, cascade="all, delete-orphan")


class ChunkEmbedding(Base):
    """Stores vector embeddings separately from chunks and document text."""
    __tablename__ = "chunk_embeddings"

    id = Column(Integer, primary_key=True, index=True)
    chunk_id = Column(Integer, ForeignKey("knowledge_chunks.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    document_id = Column(Integer, ForeignKey("knowledge_documents.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # 384-dimensional dense semantic vector stored for pgvector indexing and cosine similarity
    embedding = Column(JSON, nullable=False)
    model_name = Column(String(100), default="all-MiniLM-L6-v2", nullable=False)
    dimension = Column(Integer, default=384, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    chunk = relationship("KnowledgeChunk", back_populates="chunk_embedding")
    document = relationship("KnowledgeDocument", back_populates="chunk_embeddings")
