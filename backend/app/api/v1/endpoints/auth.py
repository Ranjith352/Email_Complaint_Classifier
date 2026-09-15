from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import (
    verify_password, get_password_hash, create_access_token,
    get_current_user, require_roles
)
from app.models.user import User, UserRole
from app.schemas.auth import Token, LoginRequest, UserCreate, UserResponse

router = APIRouter()

@router.post("/login", response_model=Token)
def login(creds: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == creds.email).first()
    if not user or not verify_password(creds.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    
    access_token = create_access_token(subject=user.id, role=user.role)
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

@router.post("/register", response_model=UserResponse)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    valid_roles = [r.value for r in UserRole]
    normalized_role = user_in.role.upper()
    if normalized_role not in valid_roles:
        normalized_role = UserRole.AGENT.value

    user = User(
        name=user_in.name,
        email=user_in.email,
        password_hash=get_password_hash(user_in.password),
        role=normalized_role,
        department_id=user_in.department_id,
        team_id=user_in.team_id,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.get("/me", response_model=UserResponse)
def get_current_user_profile(user: User = Depends(get_current_user)):
    return user

# RBAC: ADMIN User Management
@router.get("/admin/users", dependencies=[Depends(require_roles("ADMIN"))], response_model=List[UserResponse])
@router.get("/users", dependencies=[Depends(require_roles("ADMIN"))], response_model=List[UserResponse])
def list_all_users_admin(db: Session = Depends(get_db)):
    """Only accessible to ADMIN role."""
    return db.query(User).order_by(User.id.asc()).all()

@router.put("/users/{user_id}/role", dependencies=[Depends(require_roles("ADMIN"))], response_model=UserResponse)
def update_user_role_admin(user_id: int, new_role: str, db: Session = Depends(get_db)):
    """Allows ADMIN to reassign roles (CUSTOMER, AGENT, MANAGER, ADMIN)."""
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    norm_role = new_role.upper()
    if norm_role not in [r.value for r in UserRole]:
        raise HTTPException(status_code=400, detail=f"Invalid role '{new_role}'")
    target_user.role = norm_role
    db.commit()
    db.refresh(target_user)
    return target_user
