from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.team import Team
from app.schemas.team import TeamCreate, TeamUpdate, TeamResponse

router = APIRouter()

@router.get("", response_model=List[TeamResponse])
@router.get("/", response_model=List[TeamResponse])
def list_teams(department_id: int = None, db: Session = Depends(get_db)):
    """List operational teams, optionally filtered by department."""
    q = db.query(Team).filter(Team.is_active == True)
    if department_id:
        q = q.filter(Team.department_id == department_id)
    return q.all()

@router.get("/department/{department_id}", response_model=List[TeamResponse])
def list_teams_by_department(department_id: int, db: Session = Depends(get_db)):
    """List teams assigned to a specific department."""
    return db.query(Team).filter(Team.department_id == department_id, Team.is_active == True).all()

@router.get("/{team_id}", response_model=TeamResponse)
def get_team(team_id: int, db: Session = Depends(get_db)):
    """Retrieve details of a single team."""
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
    return team

@router.post("", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
def create_team(team_in: TeamCreate, db: Session = Depends(get_db)):
    """Create a new functional support team."""
    team = Team(**team_in.model_dump())
    db.add(team)
    db.commit()
    db.refresh(team)
    return team

@router.put("/{team_id}", response_model=TeamResponse)
def update_team(team_id: int, team_in: TeamUpdate, db: Session = Depends(get_db)):
    """Update team configuration."""
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
    
    update_data = team_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(team, field, value)
        
    db.commit()
    db.refresh(team)
    return team

@router.delete("/{team_id}")
def delete_team(team_id: int, db: Session = Depends(get_db)):
    """Deactivate a team."""
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
    team.is_active = False
    db.commit()
    return {"success": True, "message": f"Team '{team.name}' deactivated successfully"}
