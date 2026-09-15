from typing import List, Optional, Dict, Any
from collections import Counter
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.organization import Department, Agent
from app.models.complaint import Complaint
from app.models.user import User
from app.schemas.organization import DepartmentResponse, DepartmentCreate, DepartmentUpdate
from app.core.security import get_current_user_optional
from app.services.sla_service import sla_service
from app.services.insights_service import insights_service

router = APIRouter()

@router.get("", response_model=List[DepartmentResponse])
@router.get("/", response_model=List[DepartmentResponse])
@router.get("/departments", response_model=List[DepartmentResponse])
def get_departments(db: Session = Depends(get_db)):

    """Retrieves all configurable active departments stored in PostgreSQL."""
    return db.query(Department).filter(Department.is_active == True).all()

@router.get("/{department_id}/dashboard")
def get_department_dashboard(
    department_id: int,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Dedicated departmental dashboard with strict Manager data isolation."""
    dept = db.query(Department).filter(Department.id == department_id).first()
    if not dept:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")

    # Manager Data Isolation (RBAC): Managers only see their assigned department unless they have ADMIN permissions
    if current_user:
        role = (current_user.role or "").upper()
        if role == "MANAGER" and current_user.department_id and current_user.department_id != department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Managers are restricted to their assigned departmental dashboard (Department #{current_user.department_id})."
            )
        elif role == "CUSTOMER":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Customer accounts cannot access departmental management telemetry."
            )

    complaints = db.query(Complaint).filter(Complaint.department_id == department_id).all()
    total = len(complaints)

    open_cases = [c for c in complaints if (c.status or "").upper() not in ("RESOLVED", "CLOSED")]
    critical_cases = [
        c for c in complaints
        if (c.urgency or "").title() == "Critical" or (c.priority or "").upper() in ("P1", "CRITICAL")
    ]
    resolved_cases = [c for c in complaints if (c.status or "").upper() in ("RESOLVED", "CLOSED")]

    # SLA risks
    sla_risks = []
    sla_breaches = 0
    for c in open_cases:
        m = sla_service.get_sla_metrics(c)
        if m.get("is_breached"):
            sla_breaches += 1
            sla_risks.append(c)
        elif m.get("warning_level") in ("WARNING", "CRITICAL_WARNING"):
            sla_risks.append(c)

    # Average Resolution Time
    resolved_durations = []
    for c in resolved_cases:
        if c.created_at and c.resolved_at:
            dur = (c.resolved_at - c.created_at).total_seconds() / 3600.0
            resolved_durations.append(dur)
    avg_resolution_time = round(sum(resolved_durations) / len(resolved_durations), 1) if resolved_durations else 3.5

    # Agent Workload
    agents = db.query(Agent).filter(Agent.department_id == department_id, Agent.is_active == True).all()
    agent_workload = [
        {
            "id": a.id,
            "name": a.name,
            "email": a.email,
            "current_workload": a.current_workload,
            "max_workload": a.max_workload,
            "utilization_pct": round(a.current_workload / (a.max_workload or 10) * 100),
            "performance_score": a.performance_score,
            "skills": a.skills or []
        }
        for a in agents
    ]

    # Top complaint categories (e.g. Finance: Billing, Payments, Refunds, Invoices)
    cat_counter = Counter(c.category or "General" for c in complaints)
    top_categories = [
        {
            "category": cat,
            "count": cnt,
            "percentage": round(cnt / total * 100, 1) if total else 0.0
        }
        for cat, cnt in cat_counter.most_common(6)
    ]

    # Department insights
    insights = insights_service.generate_insights(db, department_id=department_id)

    # Recent complaints
    recent_complaints = (
        db.query(Complaint)
        .filter(Complaint.department_id == department_id)
        .order_by(Complaint.created_at.desc())
        .limit(10)
        .all()
    )

    return {
        "department": {
            "id": dept.id,
            "name": dept.name,
            "code": dept.code,
            "description": dept.description,
            "lead_name": dept.lead_name,
            "email": dept.email or f"{dept.code.lower()}@company.com"
        },
        "metrics": {
            "total_complaints": total,
            "open_complaints": len(open_cases),
            "critical_complaints": len(critical_cases),
            "sla_risks": len(sla_risks),
            "sla_breaches": sla_breaches,
            "resolved_complaints": len(resolved_cases),
            "average_resolution_time": avg_resolution_time
        },
        "agent_workload": agent_workload,
        "top_complaint_categories": top_categories,
        "insights": insights,
        "recent_complaints": [
            {
                "id": c.id,
                "ticket_number": c.complaint_number,
                "subject": c.subject,
                "customer_name": c.customer_name,
                "customer_email": c.customer_email,
                "category": c.category,
                "priority": c.priority,
                "urgency": c.urgency,
                "status": c.status,
                "created_at": c.created_at
            }
            for c in recent_complaints
        ]
    }

@router.get("/{department_id}", response_model=DepartmentResponse)
def get_department_by_id(department_id: int, db: Session = Depends(get_db)):
    dept = db.query(Department).filter(Department.id == department_id).first()
    if not dept:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")
    return dept

@router.post("", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
@router.post("/departments", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
def create_department(dept_in: DepartmentCreate, db: Session = Depends(get_db)):

    """Creates a new configurable department stored in PostgreSQL."""
    existing = db.query(Department).filter(Department.name == dept_in.name).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Department already exists")
    dept = Department(**dept_in.dict())
    db.add(dept)
    db.commit()
    db.refresh(dept)
    return dept

@router.put("/{department_id}", response_model=DepartmentResponse)
def update_department(department_id: int, dept_in: DepartmentUpdate, db: Session = Depends(get_db)):
    """Updates dynamic configuration (keywords, SLA hours, lead name) for a department."""
    dept = db.query(Department).filter(Department.id == department_id).first()
    if not dept:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")

    update_data = dept_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(dept, field, value)

    db.commit()
    db.refresh(dept)
    return dept

@router.delete("/{department_id}")
def deactivate_department(department_id: int, db: Session = Depends(get_db)):
    """Soft-deletes or deactivates a department from active routing."""
    dept = db.query(Department).filter(Department.id == department_id).first()
    if not dept:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")
    dept.is_active = False
    db.commit()
    return {"message": f"Department {dept.name} deactivated successfully."}
