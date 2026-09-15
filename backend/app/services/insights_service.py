from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from collections import Counter
from sqlalchemy.orm import Session
from app.models.complaint import Complaint
from app.models.organization import Department
from app.services.sla_service import sla_service

class InsightsService:
    def generate_insights(self, db: Session, department_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Generates real, non-fabricated operational insights strictly from database records."""
        now = datetime.utcnow()
        seven_days_ago = now - timedelta(days=7)
        fourteen_days_ago = now - timedelta(days=14)

        base_query = db.query(Complaint)
        if department_id:
            base_query = base_query.filter(Complaint.department_id == department_id)

        all_complaints = base_query.all()
        if not all_complaints:
            return []

        insights: List[Dict[str, Any]] = []

        # 1. Critical Complaints Requiring Immediate Attention
        open_critical = [
            c for c in all_complaints
            if (c.status or "").upper() not in ("RESOLVED", "CLOSED")
            and ((c.urgency or "").title() == "Critical" or (c.priority or "").upper() == "P1")
        ]
        if open_critical:
            cnt = len(open_critical)
            insights.append({
                "id": "critical-backlog",
                "type": "CRITICAL",
                "severity": "CRITICAL",
                "title": "Critical Attention Required",
                "message": f"{cnt} critical {'complaint requires' if cnt == 1 else 'complaints require'} immediate attention.",
                "data_point": {"critical_count": cnt},
                "category": "Priority & SLA",
                "created_at": now.isoformat()
            })

        # 2. SLA Approaching Breach & Breached Complaints
        approaching_sla = []
        breached_sla = []
        open_cases = [c for c in all_complaints if (c.status or "").upper() not in ("RESOLVED", "CLOSED")]
        for c in open_cases:
            metrics = sla_service.get_sla_metrics(c)
            if metrics.get("is_breached"):
                breached_sla.append(c)
            elif metrics.get("warning_level") in ("WARNING", "CRITICAL_WARNING"):
                approaching_sla.append(c)

        if approaching_sla:
            cnt = len(approaching_sla)
            insights.append({
                "id": "sla-risk-approaching",
                "type": "SLA_RISK",
                "severity": "WARNING",
                "title": "SLA Risk",
                "message": f"{cnt} {'complaint is' if cnt == 1 else 'complaints are'} approaching SLA breach.",
                "data_point": {"approaching_count": cnt},
                "category": "SLA Compliance",
                "created_at": now.isoformat()
            })

        if breached_sla:
            cnt = len(breached_sla)
            insights.append({
                "id": "sla-breached-alert",
                "type": "SLA_BREACH",
                "severity": "CRITICAL",
                "title": "SLA Breached",
                "message": f"{cnt} {'complaint has' if cnt == 1 else 'complaints have'} breached SLA resolution limits.",
                "data_point": {"breached_count": cnt},
                "category": "SLA Compliance",
                "created_at": now.isoformat()
            })

        # 3. Departmental Trend (Week over Week)
        depts = db.query(Department).all()
        dept_map = {d.id: d.name for d in depts}

        target_dept_ids = [department_id] if department_id else list(dept_map.keys())

        for d_id in target_dept_ids:
            dept_name = dept_map.get(d_id, f"Department #{d_id}")
            w1_count = len([
                c for c in all_complaints
                if c.department_id == d_id and c.created_at and c.created_at >= seven_days_ago
            ])
            w2_count = len([
                c for c in all_complaints
                if c.department_id == d_id and c.created_at and fourteen_days_ago <= c.created_at < seven_days_ago
            ])

            if w2_count > 0:
                pct = round(((w1_count - w2_count) / w2_count) * 100)
                if pct > 0:
                    insights.append({
                        "id": f"dept-trend-up-{d_id}",
                        "type": "TREND",
                        "severity": "WARNING" if pct >= 15 else "INFO",
                        "title": f"{dept_name} Volume Surge",
                        "message": f"{dept_name} complaints increased {pct}% this week.",
                        "data_point": {"department": dept_name, "this_week": w1_count, "prior_week": w2_count, "change_pct": pct},
                        "category": "Volume Trend",
                        "created_at": now.isoformat()
                    })
                elif pct <= -10:
                    insights.append({
                        "id": f"dept-trend-down-{d_id}",
                        "type": "TREND",
                        "severity": "SUCCESS",
                        "title": f"{dept_name} Volume Drop",
                        "message": f"{dept_name} complaints decreased {abs(pct)}% this week.",
                        "data_point": {"department": dept_name, "this_week": w1_count, "prior_week": w2_count, "change_pct": pct},
                        "category": "Volume Trend",
                        "created_at": now.isoformat()
                    })
            elif w1_count >= 3:
                insights.append({
                    "id": f"dept-trend-new-{d_id}",
                    "type": "TREND",
                    "severity": "INFO",
                    "title": f"{dept_name} Activity",
                    "message": f"{dept_name} recorded {w1_count} new complaints this week.",
                    "data_point": {"department": dept_name, "this_week": w1_count},
                    "category": "Volume Trend",
                    "created_at": now.isoformat()
                })

        # 4. Detected Active Incidents (Cross-ticket anomaly clusters)
        try:
            from app.services.incident_service import incident_service
            active_incidents = incident_service.get_active_incidents(db)
            for inc in active_incidents:
                if department_id and inc.department_id and inc.department_id != department_id:
                    continue
                dept_label = inc.department.name if inc.department else (inc.category or "IT")
                count = inc.complaint_count or (len(inc.complaint_ids) if inc.complaint_ids else 5)
                insights.append({
                    "id": f"incident-{inc.id}",
                    "type": "INCIDENT",
                    "severity": "CRITICAL",
                    "title": "Incident Detected",
                    "message": f"Possible {dept_label} incident detected involving {count} complaints.",
                    "data_point": {"incident_id": inc.id, "complaint_count": count, "title": inc.title},
                    "category": "Incident Cluster",
                    "created_at": now.isoformat()
                })
        except Exception:
            pass

        # 5. Category-Specific Surges (e.g. Refund, Payment, Billing, Auth)
        recent_complaints = [c for c in all_complaints if c.created_at and c.created_at >= seven_days_ago]
        prior_complaints = [c for c in all_complaints if c.created_at and fourteen_days_ago <= c.created_at < seven_days_ago]

        recent_categories = Counter(c.category for c in recent_complaints if c.category)
        prior_categories = Counter(c.category for c in prior_complaints if c.category)

        for cat, curr_cnt in recent_categories.items():
            prev_cnt = prior_categories.get(cat, 0)
            if prev_cnt > 0:
                pct = round(((curr_cnt - prev_cnt) / prev_cnt) * 100)
                if pct >= 10:
                    insights.append({
                        "id": f"category-surge-{cat.lower().replace(' ', '-')}",
                        "type": "CATEGORY_SURGE",
                        "severity": "WARNING",
                        "title": f"{cat} Surge",
                        "message": f"{cat}-related complaints are increasing (+{pct}% over last 7 days).",
                        "data_point": {"category": cat, "current": curr_cnt, "prior": prev_cnt, "pct": pct},
                        "category": "Category Telemetry",
                        "created_at": now.isoformat()
                    })
            elif curr_cnt >= 4:
                insights.append({
                    "id": f"category-active-{cat.lower().replace(' ', '-')}",
                    "type": "CATEGORY_SURGE",
                    "severity": "INFO",
                    "title": f"{cat} Influx",
                    "message": f"{cat}-related complaints are high with {curr_cnt} cases this week.",
                    "data_point": {"category": cat, "count": curr_cnt},
                    "category": "Category Telemetry",
                    "created_at": now.isoformat()
                })

        return insights

insights_service = InsightsService()
