from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class NotificationResponse(BaseModel):
    id: int
    title: str
    message: str
    notification_type: str
    is_read: bool
    link_url: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class AuditLogResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    action: str
    entity_type: str
    entity_id: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

# --- Configurable Routing Rules Schemas ---

class RoutingRuleBase(BaseModel):
    trigger_keyword: str
    department_name: str
    team_name: Optional[str] = None
    priority_override: Optional[str] = None
    sla_hours: Optional[int] = None
    description: Optional[str] = None
    is_active: bool = True

class RoutingRuleCreate(RoutingRuleBase):
    pass

class RoutingRuleUpdate(BaseModel):
    trigger_keyword: Optional[str] = None
    department_name: Optional[str] = None
    team_name: Optional[str] = None
    priority_override: Optional[str] = None
    sla_hours: Optional[int] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class RoutingRuleResponse(RoutingRuleBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
