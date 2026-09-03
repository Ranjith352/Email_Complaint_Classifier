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
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None

class ComplaintReviewRequest(BaseModel):
    department_id: Optional[int] = None
    team_id: Optional[int] = None
    assigned_agent_id: Optional[int] = None
    reviewer_name: str = "Support Lead"
    notes: Optional[str] = None

    # Backward compatibility aliases
    ticket_number: Optional[str] = None
    body: Optional[str] = None
    priority_level: Optional[str] = None

    class Config:
        from_attributes = True
