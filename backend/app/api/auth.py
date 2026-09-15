from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.core.security import (
    verify_password, get_password_hash, create_access_token,
    get_current_user, require_roles
)
from app.models.user import User, UserRole
from app.schemas.auth import Token, LoginRequest, UserCreate, UserResponse

router = APIRouter()

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    """Register a new enterprise user."""
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    valid_roles = [r.value for r in UserRole]
    normalized_role = user_in.role.upper() if user_in.role else UserRole.AGENT.value
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

@router.post("/login", response_model=Token)
def login(creds: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate user and issue JWT access token."""
    user = db.query(User).filter(User.email == creds.email).first()
    if not user or not verify_password(creds.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    access_token = create_access_token(subject=user.id, role=user.role)
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

@router.get("/me", response_model=UserResponse)
def get_current_user_profile(user: User = Depends(get_current_user)):
    """Retrieve profile of the currently authenticated user."""
    return user

@router.get("/admin/users", dependencies=[Depends(require_roles("ADMIN"))], response_model=List[UserResponse])
@router.get("/users", dependencies=[Depends(require_roles("ADMIN"))], response_model=List[UserResponse])
def list_all_users_admin(db: Session = Depends(get_db)):
    """Admin endpoint to list all platform users."""
    return db.query(User).order_by(User.id.asc()).all()

@router.put("/users/{user_id}/role", dependencies=[Depends(require_roles("ADMIN"))], response_model=UserResponse)
def update_user_role_admin(user_id: int, new_role: str, db: Session = Depends(get_db)):
    """Admin endpoint to update user roles."""
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    norm_role = new_role.upper()
    if norm_role not in [r.value for r in UserRole]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid role '{new_role}'")
    target_user.role = norm_role
    db.commit()
    db.refresh(target_user)
    return target_user
