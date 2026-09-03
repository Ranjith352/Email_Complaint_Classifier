from datetime import datetime, timedelta
from collections import Counter
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.complaint import Complaint
from app.models.organization import Department

router = APIRouter()

@router.get("/dashboard")
def get_analytics_dashboard(db: Session = Depends(get_db)):
    complaints = db.query(Complaint).all()
    total = len(complaints)

    open_cases = len([c for c in complaints if c.status in ("New", "Assigned", "In Investigation", "Open")])
    resolved_cases = len([c for c in complaints if c.status == "Resolved"])
    critical_cases = len([c for c in complaints if c.urgency == "Critical"])
    p1_cases = len([c for c in complaints if c.priority_level == "P1"])

    resolution_rate = round((resolved_cases / total * 100), 1) if total else 0.0

    # SLA Compliance
    sla_met = 0
    resolved_with_dates = 0
    total_res_hours = 0.0
    for c in complaints:
        if c.status == "Resolved" and c.resolved_at and c.created_at:
            resolved_with_dates += 1
            duration = (c.resolved_at - c.created_at).total_seconds() / 3600.0
            total_res_hours += duration
            if c.sla_deadline and c.resolved_at <= c.sla_deadline:
                sla_met += 1
        elif c.status != "Resolved" and c.sla_deadline:
            if datetime.utcnow() <= c.sla_deadline:
                sla_met += 1

    sla_compliance = round((sla_met / total * 100), 1) if total else 100.0
    avg_res_time = round(total_res_hours / resolved_with_dates, 1) if resolved_with_dates else 3.8

    # Department volumes
    depts = db.query(Department).all()
    dept_map = {d.id: d.name for d in depts}
    dept_open = Counter()
    dept_resolved = Counter()
    dept_total = Counter()

    for c in complaints:
        name = dept_map.get(c.department_id, "Support")
        dept_total[name] += 1
        if c.status == "Resolved":
            dept_resolved[name] += 1
        else:
            dept_open[name] += 1

    department_volumes = [
        {
            "department": name,
            "count": dept_total[name],
            "open": dept_open[name],
            "resolved": dept_resolved[name]
        }
        for name in dept_total
    ]

    # Urgency Breakdown
    urg_counter = Counter(c.urgency for c in complaints)
    urgency_distributions = [
        {"urgency": u, "count": cnt, "percentage": round(cnt / total * 100, 1) if total else 0.0}
        for u, cnt in urg_counter.items()
    ]

    # Priority Breakdown
    prio_counter = Counter(c.priority_level for c in complaints)
    priority_distributions = [
        {"priority": p, "count": cnt} for p, cnt in prio_counter.items()
    ]

    # Emotion Breakdown
    emotion_breakdown = dict(Counter(c.emotion for c in complaints))

    # Trend points
    date_created = Counter()
    date_resolved = Counter()
    for c in complaints:
        d_str = c.created_at.strftime("%b %d") if c.created_at else "Today"
        date_created[d_str] += 1
        if c.resolved_at:
            r_str = c.resolved_at.strftime("%b %d")
            date_resolved[r_str] += 1

    all_dates = list(dict.fromkeys(list(date_created.keys()) + list(date_resolved.keys())))[-7:]
    trends = [
        {"date": d, "created": date_created.get(d, 0), "resolved": date_resolved.get(d, 0)}
        for d in all_dates
    ]

    return {
        "kpis": {
            "total_complaints": total,
            "open_cases": open_cases,
            "resolved_cases": resolved_cases,
            "critical_cases": critical_cases,
            "p1_cases": p1_cases,
            "resolution_rate": resolution_rate,
            "sla_compliance_rate": sla_compliance,
            "avg_resolution_hours": avg_res_time
        },
        "department_volumes": department_volumes,
        "urgency_distributions": urgency_distributions,
        "priority_distributions": priority_distributions,
        "emotion_breakdown": emotion_breakdown,
        "trends": trends
    }
