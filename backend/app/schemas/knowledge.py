from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field

class SupportedDocumentType(BaseModel):
    type: str
    name: str
    category: str
    department: str
    description: str

class ChunkEmbeddingResponse(BaseModel):
    id: int
    chunk_id: int
    document_id: int
    model_name: str
    dimension: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class KnowledgeChunkResponse(BaseModel):
    id: int
    chunk_index: int
    chunk_text: str
    token_count: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class KnowledgeDocumentCreate(BaseModel):
    title: Optional[str] = None
    document_name: Optional[str] = None
    category: Optional[str] = None
    document_type: str = "REFUND_POLICY"
    department: Optional[str] = None
    content_text: str
    uploaded_by: Optional[str] = "Admin"
    department_id: Optional[int] = None

class KnowledgeDocumentUpdate(BaseModel):
    title: Optional[str] = None
    document_name: Optional[str] = None
    category: Optional[str] = None
    document_type: Optional[str] = None
    department: Optional[str] = None
    content_text: Optional[str] = None
    reindex: bool = True
    uploaded_by: Optional[str] = None

class KnowledgeDocumentResponse(BaseModel):
    id: int
    title: str
    document_name: Optional[str] = None
    category: str
    document_type: str
    department: str = "General"
    version: int = 1
    uploaded_by: str = "Admin"
    chunk_text: str
    is_active: bool
    created_at: datetime
    chunk_count: Optional[int] = 1

    model_config = ConfigDict(from_attributes=True)

    def __init__(self, **data):
        if "title" in data and not data.get("document_name"):
            data["document_name"] = data["title"]
        super().__init__(**data)

class KnowledgeDocumentDetailResponse(BaseModel):
    id: int
    title: str
    document_name: Optional[str] = None
    category: str
    document_type: str
    department: str = "General"
    version: int = 1
    uploaded_by: str = "Admin"
    content_text: str
    is_active: bool
    created_at: datetime
    chunks: List[KnowledgeChunkResponse] = []

    model_config = ConfigDict(from_attributes=True)

    def __init__(self, **data):
        if "title" in data and not data.get("document_name"):
            data["document_name"] = data["title"]
        super().__init__(**data)

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
    department: Optional[str] = "General"
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
