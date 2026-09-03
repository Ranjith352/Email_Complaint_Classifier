from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.organization import Agent
from app.schemas.organization import AgentResponse, AgentCreate, AgentUpdate

router = APIRouter()

@router.get("/", response_model=List[AgentResponse])
def get_agents(
    department_id: Optional[int] = None,
    team_id: Optional[int] = None,
    availability: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """Lists agents with optional filters for department, team, and availability."""
    query = db.query(Agent).filter(Agent.is_active == True)
    if department_id is not None:
        query = query.filter(Agent.department_id == department_id)
    if team_id is not None:
        query = query.filter(Agent.team_id == team_id)
    if availability is not None:
        query = query.filter(Agent.availability == availability)
    return query.all()

@router.get("/{agent_id}", response_model=AgentResponse)
def get_agent_by_id(agent_id: int, db: Session = Depends(get_db)):
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    return agent

@router.post("/", response_model=AgentResponse)
def create_agent(agent_in: AgentCreate, db: Session = Depends(get_db)):
    """Creates a new agent with defined skills, availability, and capacity."""
    existing = db.query(Agent).filter(Agent.email == agent_in.email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Agent with this email already exists")

    agent = Agent(**agent_in.dict())
    db.add(agent)
    db.commit()
    db.refresh(agent)
    return agent

@router.put("/{agent_id}", response_model=AgentResponse)
def update_agent(agent_id: int, agent_in: AgentUpdate, db: Session = Depends(get_db)):
    """Updates agent attributes (workload, availability, performance score, skills)."""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")

    update_data = agent_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(agent, field, value)

    db.commit()
    db.refresh(agent)
    return agent

@router.delete("/{agent_id}")
def deactivate_agent(agent_id: int, db: Session = Depends(get_db)):
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    agent.is_active = False
    agent.availability = False
    db.commit()
    return {"message": f"Agent {agent.name} deactivated successfully."}
