from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON, ForeignKey
from app.core.database import Base

class SLARule(Base):
    __tablename__ = "sla_rules"

    id = Column(Integer, primary_key=True, index=True)
    department_id = Column(Integer, ForeignKey("departments.id", ondelete="CASCADE"), nullable=True)
    priority_level = Column(String(50), nullable=False)  # P1, P2, P3, P4
    urgency_level = Column(String(50), nullable=False)   # Critical, High, Medium, Low
    max_response_hours = Column(Integer, default=2)
    max_resolution_hours = Column(Integer, default=24)
    escalation_email = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    recipient_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    department_id = Column(Integer, ForeignKey("departments.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(String(50), default="INFO")  # SLA_WARNING, CRITICAL_TICKET, ASSIGNMENT, RESOLUTION
    is_read = Column(Boolean, default=False)
    link_url = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class EmailMessage(Base):
    __tablename__ = "email_messages"

    id = Column(Integer, primary_key=True, index=True)
    complaint_id = Column(Integer, ForeignKey("complaints.id", ondelete="SET NULL"), nullable=True)
    message_id = Column(String(255), unique=True, index=True, nullable=False)
    thread_id = Column(String(255), nullable=True)
    direction = Column(String(20), default="INBOUND")  # INBOUND, OUTBOUND
    sender = Column(String(255), nullable=False)
    recipient = Column(String(255), nullable=False)
    subject = Column(String(500), nullable=False)
    body_text = Column(Text, nullable=True)
    body_html = Column(Text, nullable=True)
    received_at = Column(DateTime, default=datetime.utcnow)

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action = Column(String(100), nullable=False)  # CREATE_COMPLAINT, ROUTE_DEPT, ASSIGN_AGENT, APPROVE_RESPONSE, RESOLVE, UPDATE_SETTINGS
    entity_type = Column(String(50), nullable=False)  # COMPLAINT, AI_RESPONSE, USER, SLA_RULE
    entity_id = Column(String(100), nullable=True)
    ip_address = Column(String(50), nullable=True)
    details_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
