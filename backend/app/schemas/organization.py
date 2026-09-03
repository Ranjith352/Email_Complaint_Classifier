from typing import List, Optional
from pydantic import BaseModel

class TeamBase(BaseModel):
    department_id: int
    name: str
    code: Optional[str] = None
    description: Optional[str] = None
    keywords: List[str] = []
    lead_name: Optional[str] = None

class TeamCreate(TeamBase):
    pass

class TeamUpdate(BaseModel):
    department_id: Optional[int] = None
    name: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None
    keywords: Optional[List[str]] = None
    lead_name: Optional[str] = None
    is_active: Optional[bool] = None

class TeamResponse(TeamBase):
    id: int
    is_active: bool

    class Config:
        from_attributes = True

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

    class Config:
        from_attributes = True

class AgentBase(BaseModel):
    name: str
    email: str
    department_id: Optional[int] = None
    team_id: Optional[int] = None
    skills: List[str] = []
    availability: bool = True
    current_workload: int = 0
    max_workload: int = 10
    performance_score: float = 95.0
    average_resolution_time: float = 4.0
    employee_id: Optional[str] = None

class AgentCreate(AgentBase):
    pass

class AgentUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    department_id: Optional[int] = None
    team_id: Optional[int] = None
    skills: Optional[List[str]] = None
    availability: Optional[bool] = None
    current_workload: Optional[int] = None
    max_workload: Optional[int] = None
    performance_score: Optional[float] = None
    average_resolution_time: Optional[float] = None
    is_active: Optional[bool] = None

class AgentResponse(AgentBase):
    id: int
    is_active: bool

    class Config:
        from_attributes = True
