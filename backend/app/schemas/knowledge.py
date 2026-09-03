from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

class KnowledgeDocumentCreate(BaseModel):
    title: str
    category: str
    document_type: str = "POLICY"
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

    class Config:
        from_attributes = True

class RAGQueryRequest(BaseModel):
    question: str
    category: Optional[str] = None
    limit: int = 3

class RAGQueryResponse(BaseModel):
    answer: str
    cited_documents: List[dict]
    provider: str
