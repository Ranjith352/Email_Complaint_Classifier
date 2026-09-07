from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.incident import (
    IncidentResponse, IncidentDetectRequest, IncidentAcknowledgeRequest,
    IncidentResolveRequest, IncidentDetectionResponse
)
from app.services.incident_service import incident_service

router = APIRouter()

@router.get("/active", response_model=List[IncidentResponse])
def get_active_incidents(db: Session = Depends(get_db)):
    """Retrieves all active incidents currently requiring management attention."""
    return incident_service.get_active_incidents(db)

@router.post("/detect", response_model=IncidentDetectionResponse)
def run_incident_detection(
    req: IncidentDetectRequest = IncidentDetectRequest(),
    db: Session = Depends(get_db)
):
    """Triggers an automated semantic incident detection scan across recent complaints."""
    return incident_service.detect_incidents(
        db=db,
        window_hours=req.window_hours,
        min_complaints=req.min_complaints,
        similarity_threshold=req.similarity_threshold
    )

@router.get("/", response_model=List[IncidentResponse])
def list_incidents(
    status: Optional[str] = None,
    severity: Optional[str] = None,
    department_name: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Lists incidents with optional filtering by status, severity, or department."""
    return incident_service.get_all_incidents(
        db=db,
        status=status,
        severity=severity,
        department_name=department_name,
        limit=limit
    )

@router.get("/{incident_id}", response_model=IncidentResponse)
def get_incident(incident_id: int, db: Session = Depends(get_db)):
    """Retrieves detailed information for a specific incident."""
    inc = incident_service.get_all_incidents(db=db)
    target = next((i for i in inc if i.id == incident_id), None)
    if not target:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")
    return target

@router.post("/{incident_id}/acknowledge", response_model=IncidentResponse)
def acknowledge_incident(
    incident_id: int,
    req: IncidentAcknowledgeRequest = IncidentAcknowledgeRequest(),
    db: Session = Depends(get_db)
):
    """Allows a manager to acknowledge an incident."""
    try:
        return incident_service.acknowledge_incident(
            db=db,
            incident_id=incident_id,
            manager_name=req.manager_name,
            notes=req.notes
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/{incident_id}/resolve", response_model=IncidentResponse)
def resolve_incident(
    incident_id: int,
    req: IncidentResolveRequest = IncidentResolveRequest(),
    db: Session = Depends(get_db)
):
    """Allows a manager to mark an incident as resolved."""
    try:
        return incident_service.resolve_incident(
            db=db,
            incident_id=incident_id,
            manager_name=req.manager_name,
            resolution_notes=req.resolution_notes
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
