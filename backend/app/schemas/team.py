from typing import List, Optional
from pydantic import BaseModel, ConfigDict

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

    model_config = ConfigDict(from_attributes=True)
