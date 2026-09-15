from typing import List, Optional
from pydantic import BaseModel, ConfigDict

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

    model_config = ConfigDict(from_attributes=True)
