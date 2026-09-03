from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserResponse"

class TokenPayload(BaseModel):
    sub: Optional[str] = None
    role: Optional[str] = None
    exp: Optional[int] = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str = "AGENT"  # ADMIN, MANAGER, AGENT, CUSTOMER
    department_id: Optional[int] = None
    team_id: Optional[int] = None

class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: str
    department_id: Optional[int] = None
    team_id: Optional[int] = None
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

Token.model_rebuild()
