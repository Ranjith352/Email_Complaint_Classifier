from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.organization import Team, Department
from app.schemas.organization import TeamResponse, TeamCreate, TeamUpdate

router = APIRouter()

@router.get("/", response_model=List[TeamResponse])
def get_teams(department_id: Optional[int] = None, db: Session = Depends(get_db)):
    """Retrieves all active teams, optionally filtered by parent department_id."""
    query = db.query(Team).filter(Team.is_active == True)
    if department_id is not None:
        query = query.filter(Team.department_id == department_id)
    return query.all()

@router.get("/department/{department_id}", response_model=List[TeamResponse])
def get_teams_by_department(department_id: int, db: Session = Depends(get_db)):
    """Retrieves all active teams belonging to a specific department."""
    return db.query(Team).filter(
        Team.department_id == department_id,
        Team.is_active == True
    ).all()

@router.get("/{team_id}", response_model=TeamResponse)
def get_team_by_id(team_id: int, db: Session = Depends(get_db)):
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
    return team

@router.post("/", response_model=TeamResponse)
def create_team(team_in: TeamCreate, db: Session = Depends(get_db)):
    """Creates a new team under a configured department."""
    dept = db.query(Department).filter(Department.id == team_in.department_id).first()
    if not dept:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parent Department does not exist")

    team = Team(**team_in.dict())
    db.add(team)
    db.commit()
    db.refresh(team)
    return team

@router.put("/{team_id}", response_model=TeamResponse)
def update_team(team_id: int, team_in: TeamUpdate, db: Session = Depends(get_db)):
    """Updates team parameters (name, keywords, lead_name, department_id)."""
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")

    update_data = team_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(team, field, value)

    db.commit()
    db.refresh(team)
    return team

@router.delete("/{team_id}")
def deactivate_team(team_id: int, db: Session = Depends(get_db)):
    """Deactivates a team."""
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
    team.is_active = False
    db.commit()
    return {"message": f"Team {team.name} deactivated successfully."}
