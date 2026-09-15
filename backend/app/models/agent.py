from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON, Float
from sqlalchemy.orm import relationship, synonym
from app.db.database import Base

class Agent(Base):
    __tablename__ = "agents"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id", ondelete="SET NULL"), nullable=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id", ondelete="SET NULL"), nullable=True, index=True)
    skills = Column(JSON, default=list, nullable=True)
    availability = Column(Boolean, default=True, nullable=False)
    current_workload = Column(Integer, default=0, nullable=False)
    max_workload = Column(Integer, default=10, nullable=False)
    performance_score = Column(Float, default=95.0, nullable=False)
    average_resolution_time = Column(Float, default=4.0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    employee_id = Column(String(50), unique=True, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    department = relationship("Department", back_populates="agents")
    team = relationship("Team", back_populates="agents")

    # Synonyms for transparent backwards compatibility
    full_name = synonym("name")
    is_online = synonym("availability")
    max_active_tickets = synonym("max_workload")
