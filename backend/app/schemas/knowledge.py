from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict

class SupportedDocumentType(BaseModel):
    type: str
    name: str
    category: str
    department: str
    description: str

class KnowledgeChunkResponse(BaseModel):
    id: int
    chunk_index: int
    chunk_text: str
    token_count: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class KnowledgeDocumentCreate(BaseModel):
    title: str
    category: Optional[str] = None
    document_type: str = "REFUND_POLICY"
    content_text: str
    department_id: Optional[int] = None

class KnowledgeDocumentResponse(BaseModel):
    id: int
    title: str
    category: str
    document_type: str
    chunk_text: str
    is_active: bool
    created_at: datetime
    chunk_count: Optional[int] = 1

    model_config = ConfigDict(from_attributes=True)

class KnowledgeDocumentDetailResponse(BaseModel):
    id: int
    title: str
    category: str
    document_type: str
    content_text: str
    is_active: bool
    created_at: datetime
    chunks: List[KnowledgeChunkResponse] = []

    model_config = ConfigDict(from_attributes=True)

class RAGQueryRequest(BaseModel):
    question: str
    category: Optional[str] = None
    document_type: Optional[str] = None
    limit: int = 4
    min_similarity: float = 0.35

class CitedChunk(BaseModel):
    chunk_id: Optional[int] = None
    document_id: int
    document_title: str
    document_type: str
    category: str
    chunk_index: int
    chunk_text: str
    similarity_score: float

class RAGQueryResponse(BaseModel):
    question: str
    answer: str
    grounded: bool
    cited_chunks: List[CitedChunk]
    provider: str
    confidence_score: float
