from typing import List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class IncidentBase(BaseModel):
    title: str
    description: Optional[str] = None
    department_name: str = "IT"
    department_id: Optional[int] = None
    severity: str = "HIGH"  # HIGH, CRITICAL, MEDIUM, LOW
    status: str = "DETECTED"  # DETECTED, ACKNOWLEDGED, INVESTIGATING, RESOLVED
    affected_count: int = 0
    complaint_ids: List[int] = []
    sample_complaints: List[str] = []

class IncidentResponse(IncidentBase):
    id: int
    incident_number: str
    detected_at: datetime
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class IncidentDetectRequest(BaseModel):
    window_hours: int = 24
    min_complaints: int = 3
    similarity_threshold: float = 0.65

class IncidentAcknowledgeRequest(BaseModel):
    manager_name: str = "Manager"
    notes: Optional[str] = None

class IncidentResolveRequest(BaseModel):
    manager_name: str = "Manager"
    resolution_notes: str = "Incident resolved and services restored."

class IncidentDetectionResponse(BaseModel):
    detected: bool
    incidents: List[IncidentResponse] = []
    total_detected: int = 0
    scanned_complaints: int = 0
    window_hours: int = 24

