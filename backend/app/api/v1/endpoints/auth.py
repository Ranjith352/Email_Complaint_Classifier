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

# Example RBAC Protected Routes
@router.get("/admin/users", dependencies=[Depends(require_roles("ADMIN", "MANAGER"))])
def list_all_users_admin(db: Session = Depends(get_db)):
    """Only accessible to ADMIN and MANAGER roles."""
    return db.query(User).all()
