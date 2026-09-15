from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from app.schemas.team import TeamResponse

class DepartmentBase(BaseModel):
    name: str
    code: str
    description: Optional[str] = None
    email: Optional[str] = None
    lead_name: Optional[str] = None
    keywords: List[str] = []
    sla_hours: int = 24

class DepartmentCreate(DepartmentBase):
    pass

class DepartmentUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None
    email: Optional[str] = None
    lead_name: Optional[str] = None
    keywords: Optional[List[str]] = None
    sla_hours: Optional[int] = None
    is_active: Optional[bool] = None

class DepartmentResponse(DepartmentBase):
    id: int
    is_active: bool
    teams: List[TeamResponse] = []

    model_config = ConfigDict(from_attributes=True)
