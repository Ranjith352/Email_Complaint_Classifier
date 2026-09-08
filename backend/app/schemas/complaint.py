from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, EmailStr

class ComplaintCreate(BaseModel):
    subject: str
    description: Optional[str] = None
    body: Optional[str] = None
    customer_email: EmailStr
    customer_name: Optional[str] = None
    source: str = "WEB"  # EMAIL, WEB, MANUAL

    def get_description(self) -> str:
        return self.description or self.body or ""

class ComplaintUpdate(BaseModel):
    category: Optional[str] = None
    sub_category: Optional[str] = None
    department_id: Optional[int] = None
    team_id: Optional[int] = None
    assigned_agent_id: Optional[int] = None
    sentiment: Optional[str] = None
    emotion: Optional[str] = None
    urgency: Optional[str] = None
    priority: Optional[str] = None
    priority_score: Optional[float] = None
    ai_confidence: Optional[float] = None
    review_required: Optional[bool] = None
    ai_status: Optional[str] = None
    status: Optional[str] = None
    summary: Optional[str] = None

class AssignRequest(BaseModel):
    agent_id: Optional[int] = None
    team_id: Optional[int] = None
    department_id: Optional[int] = None
    reason: Optional[str] = None

class ResolveRequest(BaseModel):
    resolution_notes: str
    mark_as_policy_knowledge: bool = True
    actor: Optional[str] = "Support Agent"

class EscalateRequest(BaseModel):
    reason: str
    actor: Optional[str] = "Support Agent"

class GenerateCustomerResponseRequest(BaseModel):
    tone: Optional[str] = "Empathetic & Professional"
    instructions: Optional[str] = None

class EditResponseRequest(BaseModel):
    response_id: Optional[int] = None
    content: str

class ApproveResponseRequest(BaseModel):
    response_id: Optional[int] = None
    approved_by: Optional[str] = "Support Agent"

class SendResponseRequest(BaseModel):
    response_id: Optional[int] = None
    message: Optional[str] = None
    sender: Optional[str] = "Support Agent"

class StatusTransitionRequest(BaseModel):
    status: str
    actor: Optional[str] = None
    notes: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class FeedbackCreate(BaseModel):
    is_category_correct: bool
    corrected_category: Optional[str] = None
    is_sentiment_correct: bool
    rating: int = 5
    notes: Optional[str] = None

class FeedbackResponse(BaseModel):
    id: int
    complaint_id: int
    is_category_correct: bool
    corrected_category: Optional[str] = None
    is_sentiment_correct: bool
    rating: int
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class ComplaintEventResponse(BaseModel):
    id: int
    complaint_id: int
    event_type: str
    actor: str
    description: str
    event_metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    notes: Optional[str] = None

    class Config:
        from_attributes = True

class ComplaintEntityResponse(BaseModel):
    id: int
    complaint_id: int
    entity_type: str
    entity_value: str
    confidence: float
    start_char: Optional[int] = None
    end_char: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True

class ComplaintResponse(BaseModel):
    id: int
    complaint_number: str
    customer_name: Optional[str] = None
    customer_email: str
    subject: str
    description: str
    source: str
    category: str
    sub_category: Optional[str] = None
    department_id: Optional[int] = None
    team_id: Optional[int] = None
    assigned_agent_id: Optional[int] = None
    sentiment: str
    emotion: str
    urgency: str
    priority: str
    priority_score: float
    ai_confidence: float
    review_required: bool
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    ai_status: str
    status: str
    summary: Optional[str] = None
    sla_deadline: Optional[datetime] = None
    is_duplicate: bool = False
    duplicate_of_id: Optional[int] = None
    duplicate_similarity: float = 0.0
    duplicate_status: str = "NONE"
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None

    # Backward compatibility aliases
    ticket_number: Optional[str] = None
    body: Optional[str] = None
    priority_level: Optional[str] = None

    class Config:
        from_attributes = True

class ComplaintReviewRequest(BaseModel):
    department_id: Optional[int] = None
    team_id: Optional[int] = None
    assigned_agent_id: Optional[int] = None
    reviewer_name: str = "Support Lead"
    notes: Optional[str] = None

class ComplaintLinkRequest(BaseModel):
    target_complaint_id: int
    notes: Optional[str] = None
    actor: Optional[str] = "Support Agent"

class ComplaintMergeRequest(BaseModel):
    primary_complaint_id: int
    reason: Optional[str] = None
    actor: Optional[str] = "Support Agent"

class ComplaintIgnoreDuplicateRequest(BaseModel):
    reason: Optional[str] = None
    actor: Optional[str] = "Support Agent"

class DuplicateSearchResponse(BaseModel):
    complaint_id: int
    matched_complaint_id: Optional[int] = None
    similarity_score: float
    is_duplicate: bool
    display_warning: Optional[str] = None
    duplicate_status: str
    similar_complaints: List[Dict[str, Any]] = []
    baseline_tfidf: Optional[Dict[str, Any]] = None

class SemanticSearchResultItem(BaseModel):
    id: int
    ticket_number: str
    subject: str
    description: Optional[str] = None
    category: Optional[str] = None
    department_id: Optional[int] = None
    status: Optional[str] = None
    similarity_score: float
    is_duplicate: bool = False
    display_badge: Optional[str] = None

class SemanticSearchResponse(BaseModel):
    query: str
    total_results: int
    results: List[SemanticSearchResultItem] = []


