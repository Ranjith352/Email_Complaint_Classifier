from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, JSON, Float
from sqlalchemy.orm import relationship, synonym
from app.core.database import Base

class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    code = Column(String(20), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    email = Column(String(255), nullable=True)
    lead_name = Column(String(255), nullable=True)
    keywords = Column(JSON, default=list, nullable=True)  # Dynamic routing keywords stored in DB
    sla_hours = Column(Integer, default=24)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 1-to-Many: Each department has multiple teams
    teams = relationship("Team", back_populates="department", cascade="all, delete-orphan")
    agents = relationship("Agent", back_populates="department")

class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    department_id = Column(Integer, ForeignKey("departments.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False, index=True)
    code = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)
    keywords = Column(JSON, default=list, nullable=True)  # Dynamic sub-category keywords for routing
    lead_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    department = relationship("Department", back_populates="teams")
    agents = relationship("Agent", back_populates="team", cascade="all, delete-orphan")

class Agent(Base):
    __tablename__ = "agents"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id", ondelete="SET NULL"), nullable=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id", ondelete="SET NULL"), nullable=True, index=True)
    skills = Column(JSON, default=list, nullable=True)  # e.g. ["billing", "refunds", "vip", "network"]
    availability = Column(Boolean, default=True, nullable=False)  # Online / Available for assignment
    current_workload = Column(Integer, default=0, nullable=False)  # Active tickets currently assigned
    max_workload = Column(Integer, default=10, nullable=False)  # Max concurrent capacity
    performance_score = Column(Float, default=95.0, nullable=False)  # Historical rating (0-100)
    average_resolution_time = Column(Float, default=4.0, nullable=False)  # Historical avg resolution in hours
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
