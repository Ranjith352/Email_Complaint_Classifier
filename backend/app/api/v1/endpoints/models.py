from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.intelligence import ModelVersion

router = APIRouter()

class ModelVersionResponse(BaseModel):
    id: int
    model_name: str
    version: str
    accuracy: Optional[float] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1_score: Optional[float] = None
    training_date: Optional[datetime] = None
    dataset_version: Optional[str] = None
    is_active: bool
    description: Optional[str] = None

    class Config:
        from_attributes = True

@router.get("/", response_model=List[ModelVersionResponse])
def list_model_versions(db: Session = Depends(get_db)):
    """List all registered ML model versions."""
    return db.query(ModelVersion).order_by(ModelVersion.id.asc()).all()

@router.get("/active", response_model=List[ModelVersionResponse])
def get_active_models(db: Session = Depends(get_db)):
    """Expose the active models through the API."""
    return db.query(ModelVersion).filter(ModelVersion.is_active == True).all()

@router.post("/{model_id}/activate", response_model=ModelVersionResponse)
def activate_model(model_id: int, db: Session = Depends(get_db)):
    """Set model version as active."""
    m = db.query(ModelVersion).filter(ModelVersion.id == model_id).first()
    if not m:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model version not found")
    
    base_name = m.model_name.split("(")[0].strip()
    for other in db.query(ModelVersion).all():
        if base_name in other.model_name and other.id != m.id:
            other.is_active = False
    m.is_active = True
    db.commit()
    db.refresh(m)
    return m
