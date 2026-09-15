from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from app.db.database import Base
from app.models.department import Department
from app.models.team import Team
from app.models.agent import Agent

class RoutingRule(Base):
    __tablename__ = "routing_rules"

    id = Column(Integer, primary_key=True, index=True)
    trigger_keyword = Column(String(100), unique=True, index=True, nullable=False)
    department_name = Column(String(100), nullable=False)
    team_name = Column(String(100), nullable=True)
    priority_override = Column(String(50), nullable=True)
    sla_hours = Column(Integer, nullable=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

__all__ = ["Department", "Team", "Agent", "RoutingRule"]
