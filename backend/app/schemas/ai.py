from typing import List, Optional, Dict, Any
from pydantic import BaseModel

class SummarizeRequest(BaseModel):
    complaint_id: Optional[int] = None
    text: Optional[str] = None

class SummarizeResponse(BaseModel):
    summary: str
    key_points: List[str]
    detected_entities: Dict[str, Any]
    provider: str

class RecommendRequest(BaseModel):
    complaint_id: Optional[int] = None
    text: Optional[str] = None
    department: Optional[str] = None
    category: Optional[str] = None

class RAGItem(BaseModel):
    id: int
    title: str
    problem_summary: str
    solution_steps: str
    similarity_score: float

class RecommendResponse(BaseModel):
    recommended_steps: List[str]
    suggested_sub_department: Optional[str] = None
    similar_cases: List[RAGItem]
    confidence: float
    provider: str

class DraftResponseRequest(BaseModel):
    complaint_id: Optional[int] = None
    text: Optional[str] = None
    customer_name: Optional[str] = None
    tone: str = "Empathetic & Professional"

class DraftResponseResult(BaseModel):
    subject: str
    body: str
    provider: str

class ClassifyRequest(BaseModel):
    text: str

class ClassifyResult(BaseModel):
    category: str
    department: str
    sub_department: Optional[str] = None
    urgency: str
    sentiment: str
    confidence: float
    entities: Dict[str, Any]
