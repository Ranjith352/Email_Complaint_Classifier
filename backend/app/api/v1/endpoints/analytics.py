from datetime import datetime, timedelta
from collections import Counter
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.complaint import Complaint
from app.models.organization import Department, Agent, Team
from app.models.operations import AuditLog
from app.services.sla_service import sla_service
from app.services.insights_service import insights_service

router = APIRouter()


def _get_correction_complaint_ids(db: Session) -> set:
    """Finds IDs of complaints that experienced manual human corrections in audit logs."""
    correction_actions = [
        "Department Changed", "Team Changed", "Priority Changed",
        "Agent Assigned", "Response Edited", "Status Changed"
    ]
    corrected_ids = set()
    try:
        rows = db.query(AuditLog.entity_id).filter(
            AuditLog.action.in_(correction_actions)
        ).all()
        for r in rows:
            if r[0]:
                corrected_ids.add(str(r[0]))
    except Exception:
        pass
    return corrected_ids


def _calculate_base_metrics(complaints: List[Complaint], db: Session, total_enterprise: Optional[int] = None) -> Dict[str, Any]:
    """Calculates common foundational analytics metrics across a set of complaints."""
    total = len(complaints)
    open_cases = [c for c in complaints if (c.status or "").upper() not in ("RESOLVED", "CLOSED")]
    resolved_cases = [c for c in complaints if (c.status or "").upper() in ("RESOLVED", "CLOSED")]
    critical_cases = [
        c for c in complaints
        if (c.urgency or "").title() == "Critical" or (c.priority or "").upper() in ("P1", "CRITICAL")
    ]

    # SLA metrics evaluation
    sla_breaches = 0
    sla_compliant = 0
    sla_approaching = 0

    resolved_with_dates = 0
    total_res_hours = 0.0

    for c in complaints:
        m = sla_service.get_sla_metrics(c)
        if m.get("is_breached"):
            sla_breaches += 1
        elif m.get("warning_level") in ("WARNING", "CRITICAL_WARNING"):
            sla_approaching += 1
        else:
            sla_compliant += 1

        if (c.status or "").upper() in ("RESOLVED", "CLOSED") and c.resolved_at and c.created_at:
            resolved_with_dates += 1
            dur = (c.resolved_at - c.created_at).total_seconds() / 3600.0
            total_res_hours += dur

    avg_res_time = round(total_res_hours / resolved_with_dates, 1) if resolved_with_dates else 0.0
    sla_compliance_rate = round(((total - sla_breaches) / total * 100), 1) if total else 100.0
    resolution_rate = round((len(resolved_cases) / total * 100), 1) if total else 0.0

    # AI Auto-routing Rate & Confidence
    auto_routed = len([c for c in complaints if (c.ai_status or "").upper() == "COMPLETED" and c.department_id])
    ai_routing_rate = round((auto_routed / total * 100), 1) if total else 0.0

    confidences = [c.ai_confidence for c in complaints if c.ai_confidence is not None]
    avg_confidence = round((sum(confidences) / len(confidences) * 100), 1) if confidences else 0.0

    # Duplicate Rate
    duplicate_count = len([c for c in complaints if c.is_duplicate or (c.duplicate_status or "NONE").upper() != "NONE"])
    duplicate_rate = round((duplicate_count / total * 100), 1) if total else 0.0

    # Human Review Rate
    human_review_count = len([c for c in complaints if c.review_required])
    human_review_rate = round((human_review_count / total * 100), 1) if total else 0.0

    # Human Correction Rate
    corrected_ids = _get_correction_complaint_ids(db)
    corrected_count = len([
        c for c in complaints
        if str(c.id) in corrected_ids or str(c.complaint_number) in corrected_ids or (c.reviewed_by and c.review_required)
    ])
    human_correction_rate = round((corrected_count / total * 100), 1) if total else 0.0

    return {
        "total_complaints": total,
        "open_complaints": len(open_cases),
        "resolved_complaints": len(resolved_cases),
        "critical_complaints": len(critical_cases),
        "resolution_rate": resolution_rate,
        "average_resolution_time": avg_res_time,
        "average_resolution_time_hours": avg_res_time,
        "sla_compliance": sla_compliance_rate,
        "sla_compliance_rate": sla_compliance_rate,
        "sla_breaches": sla_breaches,
        "sla_compliant": sla_compliant,
        "sla_approaching": sla_approaching,
        "duplicate_rate": duplicate_rate,
        "duplicate_count": duplicate_count,
        "ai_routing_rate": ai_routing_rate,
        "auto_routed_count": auto_routed,
        "ai_confidence": avg_confidence,
        "human_review_rate": human_review_rate,
        "human_review_count": human_review_count,
        "human_correction_rate": human_correction_rate,
        "human_correction_count": corrected_count
    }


# =====================================================================
# 1. GET /api/analytics/overview
# =====================================================================
@router.get("/overview")
def get_analytics_overview(
    department_id: Optional[int] = Query(None, description="Optional department filter"),
    db: Session = Depends(get_db)
):
    """
    Returns global executive overview metrics calculating:
    - Total complaints
    - Resolution rate
    - Average resolution time
    - SLA compliance
    - Duplicate rate
    - AI routing rate
    - Human review rate
    - Human correction rate
    """
    query = db.query(Complaint)
    if department_id:
        query = query.filter(Complaint.department_id == department_id)
    complaints = query.all()

    base = _calculate_base_metrics(complaints, db)

    # Ingestion trends (past 7 days)
    now = datetime.utcnow()
    date_created = Counter()
    date_resolved = Counter()
    for c in complaints:
        if c.created_at:
            date_created[c.created_at.strftime("%b %d")] += 1
        if c.resolved_at:
            date_resolved[c.resolved_at.strftime("%b %d")] += 1

    past_7_days = [(now - timedelta(days=i)).strftime("%b %d") for i in range(6, -1, -1)]
    trends = [
        {
            "date": d,
            "created": date_created.get(d, 0),
            "resolved": date_resolved.get(d, 0)
        }
        for d in past_7_days
    ]

    return {
        "total_complaints": base["total_complaints"],
        "open_complaints": base["open_complaints"],
        "resolved_complaints": base["resolved_complaints"],
        "critical_complaints": base["critical_complaints"],
        "resolution_rate": base["resolution_rate"],
        "average_resolution_time": base["average_resolution_time"],
        "sla_compliance": base["sla_compliance"],
        "duplicate_rate": base["duplicate_rate"],
        "ai_routing_rate": base["ai_routing_rate"],
        "ai_confidence": base["ai_confidence"],
        "human_review_rate": base["human_review_rate"],
        "human_correction_rate": base["human_correction_rate"],
        "trends": trends
    }


# =====================================================================
# 2. GET /api/analytics/departments
# =====================================================================
@router.get("/departments")
def get_analytics_departments(
    db: Session = Depends(get_db)
):
    """
    Returns department workload and performance analytics across all organizational units.
    Calculates:
    - Department workload distribution
    - Total complaints per department
    - Open, resolved, critical complaints
    - Workload percentage of total enterprise volume
    - Active agent count and resolution turnaround
    """
    complaints = db.query(Complaint).all()
    total_enterprise = len(complaints)
    departments = db.query(Department).all()
    agents = db.query(Agent).filter(Agent.is_active == True).all()

    dept_agent_count = Counter(a.department_id for a in agents)

    dept_complaints_map = {}
    for d in departments:
        dept_complaints_map[d.id] = []

    unassigned_dept_complaints = []
    for c in complaints:
        if c.department_id in dept_complaints_map:
            dept_complaints_map[c.department_id].append(c)
        else:
            unassigned_dept_complaints.append(c)

    department_workload = []
    for d in departments:
        d_comps = dept_complaints_map.get(d.id, [])
        d_base = _calculate_base_metrics(d_comps, db)
        workload_pct = round((d_base["total_complaints"] / total_enterprise * 100), 1) if total_enterprise else 0.0

        department_workload.append({
            "department_id": d.id,
            "department_name": d.name,
            "code": d.code,
            "total_complaints": d_base["total_complaints"],
            "open_complaints": d_base["open_complaints"],
            "resolved_complaints": d_base["resolved_complaints"],
            "critical_complaints": d_base["critical_complaints"],
            "workload_percentage": workload_pct,
            "active_agents_count": dept_agent_count.get(d.id, 0),
            "average_resolution_time": d_base["average_resolution_time"],
            "sla_compliance": d_base["sla_compliance"]
        })

    # Sort departments by workload descending
    department_workload.sort(key=lambda x: x["total_complaints"], reverse=True)

    return {
        "total_enterprise_complaints": total_enterprise,
        "department_count": len(departments),
        "department_workload": department_workload
    }


# =====================================================================
# 3. GET /api/analytics/categories
# =====================================================================
@router.get("/categories")
def get_analytics_categories(
    department_id: Optional[int] = Query(None, description="Optional department filter"),
    db: Session = Depends(get_db)
):
    """
    Returns category distribution and subcategory breakdown for incoming complaints.
    Calculates:
    - Category distribution (counts & percentages)
    - Open vs resolved counts per category
    - Subcategories distribution
    """
    query = db.query(Complaint)
    if department_id:
        query = query.filter(Complaint.department_id == department_id)
    complaints = query.all()
    total = len(complaints)

    cat_counter = Counter()
    cat_open = Counter()
    cat_resolved = Counter()
    cat_critical = Counter()
    cat_subcats = {}

    for c in complaints:
        cat = c.category or "General Inquiry"
        cat_counter[cat] += 1

        is_resolved = (c.status or "").upper() in ("RESOLVED", "CLOSED")
        if is_resolved:
            cat_resolved[cat] += 1
        else:
            cat_open[cat] += 1

        if (c.urgency or "").title() == "Critical" or (c.priority or "").upper() in ("P1", "CRITICAL"):
            cat_critical[cat] += 1

        if c.sub_category:
            if cat not in cat_subcats:
                cat_subcats[cat] = Counter()
            cat_subcats[cat][c.sub_category] += 1

    category_distribution = []
    for cat, count in cat_counter.most_common():
        pct = round((count / total * 100), 1) if total else 0.0
        sub_items = [
            {"subcategory": sub, "count": sub_count}
            for sub, sub_count in cat_subcats.get(cat, Counter()).most_common(5)
        ]

        category_distribution.append({
            "category": cat,
            "count": count,
            "percentage": pct,
            "open_count": cat_open.get(cat, 0),
            "resolved_count": cat_resolved.get(cat, 0),
            "critical_count": cat_critical.get(cat, 0),
            "subcategories": sub_items
        })

    return {
        "total_complaints": total,
        "category_distribution": category_distribution
    }


# =====================================================================
# 4. GET /api/analytics/sentiment
# =====================================================================
@router.get("/sentiment")
def get_analytics_sentiment(
    department_id: Optional[int] = Query(None, description="Optional department filter"),
    db: Session = Depends(get_db)
):
    """
    Returns customer sentiment distribution (Positive, Neutral, Negative).
    Calculates:
    - Sentiment distribution (counts & percentages)
    - Average AI confidence per sentiment
    - Open vs resolved volume per sentiment tier
    """
    query = db.query(Complaint)
    if department_id:
        query = query.filter(Complaint.department_id == department_id)
    complaints = query.all()
    total = len(complaints)

    sent_counts = {"Positive": 0, "Neutral": 0, "Negative": 0}
    sent_open = {"Positive": 0, "Neutral": 0, "Negative": 0}
    sent_resolved = {"Positive": 0, "Neutral": 0, "Negative": 0}
    sent_confs = {"Positive": [], "Neutral": [], "Negative": []}

    for c in complaints:
        raw_s = (c.sentiment or "Neutral").title()
        s = raw_s if raw_s in sent_counts else "Neutral"
        sent_counts[s] += 1

        is_res = (c.status or "").upper() in ("RESOLVED", "CLOSED")
        if is_res:
            sent_resolved[s] += 1
        else:
            sent_open[s] += 1

        if c.ai_confidence is not None:
            sent_confs[s].append(c.ai_confidence)

    sentiment_distribution = []
    for s in ["Positive", "Neutral", "Negative"]:
        cnt = sent_counts[s]
        pct = round((cnt / total * 100), 1) if total else 0.0
        confs = sent_confs[s]
        avg_conf = round((sum(confs) / len(confs) * 100), 1) if confs else 90.0

        sentiment_distribution.append({
            "sentiment": s,
            "count": cnt,
            "percentage": pct,
            "average_confidence": avg_conf,
            "open_count": sent_open[s],
            "resolved_count": sent_resolved[s]
        })

    return {
        "total_complaints": total,
        "sentiment_distribution": sentiment_distribution
    }


# =====================================================================
# 5. GET /api/analytics/emotions
# =====================================================================
@router.get("/emotions")
def get_analytics_emotions(
    department_id: Optional[int] = Query(None, description="Optional department filter"),
    db: Session = Depends(get_db)
):
    """
    Returns granular emotion distribution (Frustration, Anger, Anxiety, Neutral, etc.).
    Calculates:
    - Emotion distribution (counts & percentages)
    - Dominant sentiment correlation
    - Critical case count per emotion
    """
    query = db.query(Complaint)
    if department_id:
        query = query.filter(Complaint.department_id == department_id)
    complaints = query.all()
    total = len(complaints)

    emo_counter = Counter()
    emo_sentiments = {}
    emo_critical = Counter()

    for c in complaints:
        emo = (c.emotion or "Neutral").title()
        emo_counter[emo] += 1

        if emo not in emo_sentiments:
            emo_sentiments[emo] = Counter()
        emo_sentiments[emo][(c.sentiment or "Neutral").title()] += 1

        if (c.urgency or "").title() == "Critical" or (c.priority or "").upper() in ("P1", "CRITICAL"):
            emo_critical[emo] += 1

    emotion_distribution = []
    for emo, count in emo_counter.most_common():
        pct = round((count / total * 100), 1) if total else 0.0
        dom_sent = emo_sentiments.get(emo, Counter()).most_common(1)
        dominant_sentiment = dom_sent[0][0] if dom_sent else "Neutral"

        emotion_distribution.append({
            "emotion": emo,
            "count": count,
            "percentage": pct,
            "dominant_sentiment": dominant_sentiment,
            "critical_count": emo_critical.get(emo, 0)
        })

    return {
        "total_complaints": total,
        "emotion_distribution": emotion_distribution
    }


# =====================================================================
# 6. GET /api/analytics/priority
# =====================================================================
@router.get("/priority")
def get_analytics_priority(
    department_id: Optional[int] = Query(None, description="Optional department filter"),
    db: Session = Depends(get_db)
):
    """
    Returns priority distribution (P1 Critical, P2 High, P3 Medium, P4 Low).
    Calculates:
    - Priority distribution (counts & percentages)
    - Target SLA hours
    - Open vs resolved counts
    - SLA breaches and compliance rate per priority tier
    """
    query = db.query(Complaint)
    if department_id:
        query = query.filter(Complaint.department_id == department_id)
    complaints = query.all()
    total = len(complaints)

    target_hours_map = {
        "P1": 2,
        "P2": 8,
        "P3": 24,
        "P4": 72
    }

    prio_counts = {"P1": 0, "P2": 0, "P3": 0, "P4": 0}
    prio_open = {"P1": 0, "P2": 0, "P3": 0, "P4": 0}
    prio_resolved = {"P1": 0, "P2": 0, "P3": 0, "P4": 0}
    prio_breaches = {"P1": 0, "P2": 0, "P3": 0, "P4": 0}

    for c in complaints:
        raw_p = (c.priority or "P3").upper()
        if raw_p in prio_counts:
            p = raw_p
        elif "1" in raw_p or "CRITICAL" in raw_p:
            p = "P1"
        elif "2" in raw_p or "HIGH" in raw_p:
            p = "P2"
        elif "4" in raw_p or "LOW" in raw_p:
            p = "P4"
        else:
            p = "P3"

        prio_counts[p] += 1
        is_res = (c.status or "").upper() in ("RESOLVED", "CLOSED")
        if is_res:
            prio_resolved[p] += 1
        else:
            prio_open[p] += 1

        m = sla_service.get_sla_metrics(c)
        if m.get("is_breached"):
            prio_breaches[p] += 1

    priority_distribution = []
    for p in ["P1", "P2", "P3", "P4"]:
        cnt = prio_counts[p]
        pct = round((cnt / total * 100), 1) if total else 0.0
        breaches = prio_breaches[p]
        compliance = round(((cnt - breaches) / cnt * 100), 1) if cnt else 100.0

        priority_distribution.append({
            "priority": p,
            "count": cnt,
            "percentage": pct,
            "target_sla_hours": target_hours_map.get(p, 24),
            "open_count": prio_open[p],
            "resolved_count": prio_resolved[p],
            "sla_breaches": breaches,
            "sla_compliance": compliance
        })

    return {
        "total_complaints": total,
        "priority_distribution": priority_distribution
    }


# =====================================================================
# 7. GET /api/analytics/sla
# =====================================================================
@router.get("/sla")
def get_analytics_sla(
    department_id: Optional[int] = Query(None, description="Optional department filter"),
    db: Session = Depends(get_db)
):
    """
    Returns comprehensive SLA compliance telemetry.
    Calculates:
    - Overall SLA compliance rate
    - Total breaches, approaching breach, and on track
    - Average resolution turnaround in hours
    - Compliance breakdown by priority and department
    """
    query = db.query(Complaint)
    if department_id:
        query = query.filter(Complaint.department_id == department_id)
    complaints = query.all()
    total = len(complaints)

    base = _calculate_base_metrics(complaints, db)

    # SLA by priority
    prio_total = Counter()
    prio_breaches = Counter()
    for c in complaints:
        p = (c.priority or "P3").upper()
        norm_p = "P1" if "1" in p else "P2" if "2" in p else "P4" if "4" in p else "P3"
        prio_total[norm_p] += 1
        m = sla_service.get_sla_metrics(c)
        if m.get("is_breached"):
            prio_breaches[norm_p] += 1

    compliance_by_priority = {
        p: round(((prio_total[p] - prio_breaches[p]) / prio_total[p] * 100), 1) if prio_total[p] else 100.0
        for p in ["P1", "P2", "P3", "P4"]
    }

    # SLA by department
    departments = db.query(Department).all()
    dept_map = {d.id: d.name for d in departments}
    dept_total = Counter()
    dept_breaches = Counter()

    for c in complaints:
        d_name = dept_map.get(c.department_id, "General Support")
        dept_total[d_name] += 1
        m = sla_service.get_sla_metrics(c)
        if m.get("is_breached"):
            dept_breaches[d_name] += 1

    compliance_by_department = [
        {
            "department": d_name,
            "total_complaints": dept_total[d_name],
            "breaches": dept_breaches[d_name],
            "compliance_rate": round(((dept_total[d_name] - dept_breaches[d_name]) / dept_total[d_name] * 100), 1)
        }
        for d_name in dept_total
    ]

    return {
        "total_complaints": total,
        "sla_compliance": base["sla_compliance"],
        "sla_breaches": base["sla_breaches"],
        "sla_approaching": base["sla_approaching"],
        "sla_compliant": base["sla_compliant"],
        "average_resolution_time": base["average_resolution_time"],
        "compliance_by_priority": compliance_by_priority,
        "compliance_by_department": compliance_by_department
    }


# =====================================================================
# 8. GET /api/analytics/agents
# =====================================================================
@router.get("/agents")
def get_analytics_agents(
    department_id: Optional[int] = Query(None, description="Optional department filter"),
    db: Session = Depends(get_db)
):
    """
    Returns agent workload, utilization, and performance telemetry.
    Calculates:
    - Active assigned workload vs max capacity
    - Agent utilization rate
    - Resolved complaint counts and performance scores
    """
    agents_query = db.query(Agent).filter(Agent.is_active == True)
    if department_id:
        agents_query = agents_query.filter(Agent.department_id == department_id)
    agents = agents_query.all()

    departments = db.query(Department).all()
    dept_map = {d.id: d.name for d in departments}

    complaints_query = db.query(Complaint)
    if department_id:
        complaints_query = complaints_query.filter(Complaint.department_id == department_id)
    complaints = complaints_query.all()

    agent_assigned_count = Counter()
    agent_resolved_count = Counter()
    for c in complaints:
        if c.assigned_agent_id:
            agent_assigned_count[c.assigned_agent_id] += 1
            if (c.status or "").upper() in ("RESOLVED", "CLOSED"):
                agent_resolved_count[c.assigned_agent_id] += 1

    agent_workload = []
    for a in agents:
        max_wl = a.max_workload or 10
        util_rate = round((a.current_workload / max_wl * 100), 1)

        agent_workload.append({
            "agent_id": a.id,
            "agent_name": a.name,
            "department_id": a.department_id,
            "department_name": dept_map.get(a.department_id, "Support"),
            "current_workload": a.current_workload,
            "max_workload": max_wl,
            "utilization_rate": util_rate,
            "performance_score": a.performance_score or 4.8,
            "is_active": a.is_active,
            "assigned_complaints_count": agent_assigned_count.get(a.id, 0),
            "resolved_complaints_count": agent_resolved_count.get(a.id, 0)
        })

    # Sort by current workload descending
    agent_workload.sort(key=lambda x: x["current_workload"], reverse=True)

    return {
        "active_agent_count": len(agents),
        "agent_workload": agent_workload
    }


# =====================================================================
# 9. GET /api/analytics/ai-performance
# =====================================================================
@router.get("/ai-performance")
def get_analytics_ai_performance(
    department_id: Optional[int] = Query(None, description="Optional department filter"),
    db: Session = Depends(get_db)
):
    """
    Returns AI routing, confidence, review, and human correction telemetry.
    Calculates:
    - AI auto-routing rate
    - Mean AI classification confidence
    - Human review rate
    - Human correction rate
    - Duplicate detection rate
    - Confidence score distribution
    """
    query = db.query(Complaint)
    if department_id:
        query = query.filter(Complaint.department_id == department_id)
    complaints = query.all()
    total = len(complaints)

    base = _calculate_base_metrics(complaints, db)

    # Confidence brackets
    brackets = {
        ">=90% (High)": 0,
        "80-89% (Solid)": 0,
        "70-79% (Moderate)": 0,
        "<70% (Low)": 0
    }

    for c in complaints:
        conf = (c.ai_confidence or 0.85) * 100
        if conf >= 90:
            brackets[">=90% (High)"] += 1
        elif conf >= 80:
            brackets["80-89% (Solid)"] += 1
        elif conf >= 70:
            brackets["70-79% (Moderate)"] += 1
        else:
            brackets["<70% (Low)"] += 1

    confidence_distribution = [
        {
            "tier": k,
            "count": v,
            "percentage": round((v / total * 100), 1) if total else 0.0
        }
        for k, v in brackets.items()
    ]

    return {
        "total_complaints": total,
        "ai_routing_rate": base["ai_routing_rate"],
        "ai_confidence": base["ai_confidence"],
        "duplicate_rate": base["duplicate_rate"],
        "human_review_rate": base["human_review_rate"],
        "human_correction_rate": base["human_correction_rate"],
        "confidence_distribution": confidence_distribution
    }


# =====================================================================
# Legacy / Existing Endpoints for Compatibility
# =====================================================================
@router.get("/insights")
def get_ai_insights(
    department_id: Optional[int] = Query(None, description="Optional department filter for insights"),
    db: Session = Depends(get_db)
):
    """Returns data-driven, strictly non-fabricated AI operational insights from actual database data."""
    return {
        "insights": insights_service.generate_insights(db, department_id=department_id)
    }


@router.get("/dashboard")
def get_analytics_dashboard(
    department_id: Optional[int] = Query(None, description="Optional department filter"),
    db: Session = Depends(get_db)
):
    query = db.query(Complaint)
    if department_id:
        query = query.filter(Complaint.department_id == department_id)
    complaints = query.all()
    total = len(complaints)

    base = _calculate_base_metrics(complaints, db)

    kpis = {
        "total_complaints": base["total_complaints"],
        "open_complaints": base["open_complaints"],
        "critical_complaints": base["critical_complaints"],
        "resolved_complaints": base["resolved_complaints"],
        "sla_breaches": base["sla_breaches"],
        "avg_resolution_hours": base["average_resolution_time"],
        "ai_auto_routing_rate": base["ai_routing_rate"],
        "ai_confidence": base["ai_confidence"],
        "duplicate_complaints": base["duplicate_count"],
        "human_review_required": base["human_review_count"],
        "duplicate_rate": base["duplicate_rate"],
        "human_review_rate": base["human_review_rate"],
        "human_correction_rate": base["human_correction_rate"],
        # backward-compatible aliases
        "open_cases": base["open_complaints"],
        "resolved_cases": base["resolved_complaints"],
        "critical_cases": base["critical_complaints"],
        "p1_cases": base["critical_complaints"],
        "resolution_rate": base["resolution_rate"],
        "sla_compliance_rate": base["sla_compliance"]
    }

    # Complaints over time
    now = datetime.utcnow()
    date_created = Counter()
    date_resolved = Counter()
    date_critical = Counter()

    for c in complaints:
        if c.created_at:
            d_str = c.created_at.strftime("%b %d")
            date_created[d_str] += 1
            if (c.urgency or "").title() == "Critical" or (c.priority or "").upper() in ("P1", "CRITICAL"):
                date_critical[d_str] += 1
        if c.resolved_at:
            r_str = c.resolved_at.strftime("%b %d")
            date_resolved[r_str] += 1

    past_7_days = [(now - timedelta(days=i)).strftime("%b %d") for i in range(6, -1, -1)]
    complaints_over_time = [
        {
            "date": d,
            "created": date_created.get(d, 0),
            "resolved": date_resolved.get(d, 0),
            "critical": date_critical.get(d, 0)
        }
        for d in past_7_days
    ]

    # Complaints by department
    depts = db.query(Department).all()
    dept_map = {d.id: d.name for d in depts}
    dept_open = Counter()
    dept_resolved = Counter()
    dept_total = Counter()

    for c in complaints:
        name = dept_map.get(c.department_id, "Customer Support")
        dept_total[name] += 1
        if (c.status or "").upper() in ("RESOLVED", "CLOSED"):
            dept_resolved[name] += 1
        else:
            dept_open[name] += 1

    complaints_by_department = [
        {
            "department": name,
            "count": dept_total[name],
            "open": dept_open[name],
            "resolved": dept_resolved[name]
        }
        for name in (list(dept_total.keys()) or ["Finance", "IT", "Customer Support", "Security", "Operations"])
    ]

    # Complaints by category
    cat_counter = Counter(c.category or "General Inquiry" for c in complaints)
    complaints_by_category = [
        {
            "category": cat,
            "count": cnt,
            "percentage": round(cnt / total * 100, 1) if total else 0.0
        }
        for cat, cnt in cat_counter.most_common(8)
    ]

    # Priority distribution
    prio_map = {"P1": 0, "P2": 0, "P3": 0, "P4": 0}
    for c in complaints:
        p = (c.priority or "P3").upper()
        if p in prio_map:
            prio_map[p] += 1
        elif "1" in p:
            prio_map["P1"] += 1
        elif "2" in p:
            prio_map["P2"] += 1
        elif "4" in p:
            prio_map["P4"] += 1
        else:
            prio_map["P3"] += 1

    priority_distribution = [
        {"priority": p, "count": prio_map[p], "percentage": round(prio_map[p] / total * 100, 1) if total else 0.0}
        for p in ["P1", "P2", "P3", "P4"]
    ]

    # Sentiment distribution
    sent_map = {"Positive": 0, "Neutral": 0, "Negative": 0}
    for c in complaints:
        s = (c.sentiment or "Neutral").title()
        if s in sent_map:
            sent_map[s] += 1
        else:
            sent_map["Neutral"] += 1

    sentiment_distribution = [
        {"sentiment": s, "count": sent_map[s], "percentage": round(sent_map[s] / total * 100, 1) if total else 0.0}
        for s in ["Positive", "Neutral", "Negative"]
    ]

    # Emotion distribution
    emotion_counter = Counter((c.emotion or "Neutral").title() for c in complaints)
    emotion_distribution = [
        {"emotion": emo, "count": cnt, "percentage": round(cnt / total * 100, 1) if total else 0.0}
        for emo, cnt in emotion_counter.most_common(6)
    ]

    # Resolution time distribution
    bucket_counts = {
        "<2 hours": 0,
        "2-8 hours": 0,
        "8-24 hours": 0,
        "24-48 hours": 0,
        ">48 hours": 0
    }
    for c in complaints:
        if (c.status or "").upper() in ("RESOLVED", "CLOSED") and c.resolved_at and c.created_at:
            h = (c.resolved_at - c.created_at).total_seconds() / 3600.0
            if h < 2:
                bucket_counts["<2 hours"] += 1
            elif h < 8:
                bucket_counts["2-8 hours"] += 1
            elif h < 24:
                bucket_counts["8-24 hours"] += 1
            elif h < 48:
                bucket_counts["24-48 hours"] += 1
            else:
                bucket_counts[">48 hours"] += 1
        else:
            bucket_counts["2-8 hours"] += 1

    resolution_time = [
        {"bucket": k, "count": v} for k, v in bucket_counts.items()
    ]

    # SLA compliance
    sla_compliance = [
        {"name": "Compliant", "value": base["sla_compliant"], "color": "#10b981"},
        {"name": "Approaching Breach", "value": base["sla_approaching"], "color": "#f59e0b"},
        {"name": "Breached", "value": base["sla_breaches"], "color": "#ef4444"}
    ]

    # Agent workload
    agents_query = db.query(Agent).filter(Agent.is_active == True)
    if department_id:
        agents_query = agents_query.filter(Agent.department_id == department_id)
    agents = agents_query.all()

    agent_workload = [
        {
            "agent_name": a.name,
            "department": dept_map.get(a.department_id, "Support"),
            "current_workload": a.current_workload,
            "max_workload": a.max_workload,
            "utilization_rate": round(a.current_workload / (a.max_workload or 10) * 100),
            "performance_score": a.performance_score,
            "is_active": a.is_active
        }
        for a in agents[:10]
    ]

    insights = insights_service.generate_insights(db, department_id=department_id)

    return {
        "kpis": kpis,
        "charts": {
            "complaints_over_time": complaints_over_time,
            "complaints_by_department": complaints_by_department,
            "complaints_by_category": complaints_by_category,
            "priority_distribution": priority_distribution,
            "sentiment_distribution": sentiment_distribution,
            "emotion_distribution": emotion_distribution,
            "resolution_time": resolution_time,
            "sla_compliance": sla_compliance,
            "agent_workload": agent_workload
        },
        "insights": insights,
        "department_volumes": complaints_by_department,
        "urgency_distributions": [
            {"urgency": u, "count": cnt} for u, cnt in Counter(c.urgency for c in complaints).items()
        ],
        "priority_distributions": priority_distribution,
        "emotion_breakdown": dict(Counter(c.emotion for c in complaints)),
        "trends": complaints_over_time
    }
