import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.complaint import Complaint
from app.models.incident import Incident
from app.models.organization import Department
from app.ai.embeddings import embeddings_engine

logger = logging.getLogger(__name__)

class IncidentService:
    """Enterprise Incident Detection Engine.
    Detects potential common incidents when multiple semantically similar complaints
    arrive within a short time window.
    
    Example:
    Complaints:
      - "Portal is not working."
      - "Cannot login."
      - "Account access unavailable."
    Output:
      Potential Incident Detected
      Incident: Portal Authentication Failure
      Affected complaints: 50
      Department: IT
      Severity: HIGH
    """

    @staticmethod
    def _synthesize_incident_metadata(cluster: List[Complaint]) -> Dict[str, Any]:
        """Synthesizes the incident title, department, and severity from a cluster of complaints."""
        combined_text = " ".join([
            f"{c.subject or ''} {c.description or c.body or ''}" for c in cluster
        ]).lower()

        count = len(cluster)

        # 1. Determine Title & Department
        if any(w in combined_text for w in ["portal", "login", "log in", "auth", "password", "cannot login", "account access", "access unavailable"]):
            title = "Portal Authentication Failure"
            department = "IT"
        elif any(w in combined_text for w in ["deducted", "charged twice", "double charge", "duplicate payment", "billing", "fee", "refund"]):
            title = "Payment Gateway Double Deduction Incident"
            department = "Finance"
        elif any(w in combined_text for w in ["server", "outage", "crash", "crashed", "500", "503", "offline", "system down"]):
            title = "Core Infrastructure Outage"
            department = "IT"
        elif any(w in combined_text for w in ["hack", "hacked", "breach", "compromise", "phishing", "unauthorized"]):
            title = "Security Account Compromise Incident"
            department = "Security"
        elif any(w in combined_text for w in ["delivery", "shipping", "courier", "package", "transit", "lost parcel"]):
            title = "Logistics Delivery Disruption"
            department = "Logistics"
        else:
            # Fallback to category of the first complaint
            cat = cluster[0].category or "General"
            title = f"{cat} Operational Anomaly"
            department = cluster[0].category or "Operations"

        # 2. Determine Severity
        # If count >= 50 or high volume -> HIGH / CRITICAL
        has_critical = any(
            (c.urgency or "").upper() == "CRITICAL" or (c.priority or "").upper() in ["P1", "CRITICAL"]
            for c in cluster
        )
        if count >= 20:
            severity = "HIGH"
        elif count >= 5:
            severity = "HIGH"
        elif has_critical:
            severity = "HIGH"
        else:
            severity = "MEDIUM"

        description = (
            f"Automated incident detection detected {count} semantically related complaints "
            f"arriving in a short time window with symptoms matching '{title}'."
        )

        return {
            "title": title,
            "department_name": department,
            "severity": severity,
            "description": description
        }

    @staticmethod
    def detect_incidents(
        db: Session,
        window_hours: int = 24,
        min_complaints: int = 3,
        similarity_threshold: float = 0.65
    ) -> Dict[str, Any]:
        """Scans complaints within the sliding time window and groups semantically similar tickets
        into common operational incidents.
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=window_hours)
        
        # Query candidate complaints
        complaints = (
            db.query(Complaint)
            .filter(Complaint.created_at >= cutoff_time)
            .order_by(Complaint.created_at.desc())
            .all()
        )

        if not complaints:
            return {
                "detected": False,
                "incidents": [],
                "total_detected": 0,
                "scanned_complaints": 0,
                "window_hours": window_hours
            }

        # Cache dense embedding vectors
        embeddings_cache = {}
        for c in complaints:
            emb = c.embedding
            if not emb:
                txt = f"{c.subject or ''} {c.description or c.body or ''}"
                emb = embeddings_engine.get_embedding(txt)
                c.embedding = emb
            embeddings_cache[c.id] = emb

        # Semantic Clustering (Greedy Leader-Follower)
        clusters: List[List[Complaint]] = []

        for c in complaints:
            c_emb = embeddings_cache[c.id]
            assigned_cluster = None
            highest_sim = 0.0

            for cluster in clusters:
                # Compare against centroid/representative of the cluster
                rep_c = cluster[0]
                rep_emb = embeddings_cache[rep_c.id]
                sim = embeddings_engine.cosine_similarity(c_emb, rep_emb)

                if sim >= similarity_threshold and sim > highest_sim:
                    highest_sim = sim
                    assigned_cluster = cluster

            if assigned_cluster is not None:
                assigned_cluster.append(c)
            else:
                clusters.append([c])

        # Filter clusters meeting minimum volume threshold
        qualifying_clusters = [cl for cl in clusters if len(cl) >= min_complaints]
        detected_incidents: List[Incident] = []

        for cluster in qualifying_clusters:
            meta = IncidentService._synthesize_incident_metadata(cluster)
            complaint_ids = [c.id for c in cluster]
            samples = [c.subject or c.description or f"Complaint #{c.id}" for c in cluster[:5]]

            # Match Department if registered in organization table
            dept = db.query(Department).filter(
                or_(
                    Department.name.ilike(f"%{meta['department_name']}%"),
                    Department.code.ilike(f"%{meta['department_name']}%")
                )
            ).first()
            department_id = dept.id if dept else None

            # Check if active incident already exists
            existing = (
                db.query(Incident)
                .filter(
                    Incident.title == meta["title"],
                    Incident.status.in_(["DETECTED", "ACKNOWLEDGED", "INVESTIGATING"])
                )
                .first()
            )

            if existing:
                # Merge complaint IDs
                merged_ids = list(set((existing.complaint_ids or []) + complaint_ids))
                existing.affected_count = len(merged_ids)
                existing.complaint_ids = merged_ids
                existing.sample_complaints = samples
                existing.severity = meta["severity"]
                existing.department_name = meta["department_name"]
                if department_id:
                    existing.department_id = department_id
                existing.detected_at = datetime.utcnow()
                db.commit()
                db.refresh(existing)
                detected_incidents.append(existing)
            else:
                # Create new incident
                count_inc = db.query(Incident).count() + 1
                inc_num = f"INC-{datetime.utcnow().strftime('%Y%m%d')}-{count_inc:03d}"
                new_inc = Incident(
                    incident_number=inc_num,
                    title=meta["title"],
                    description=meta["description"],
                    department_name=meta["department_name"],
                    department_id=department_id,
                    severity=meta["severity"],
                    status="DETECTED",
                    affected_count=len(complaint_ids),
                    complaint_ids=complaint_ids,
                    sample_complaints=samples,
                    detected_at=datetime.utcnow()
                )
                db.add(new_inc)
                db.commit()
                db.refresh(new_inc)
                detected_incidents.append(new_inc)

        return {
            "detected": len(detected_incidents) > 0,
            "incidents": detected_incidents,
            "total_detected": len(detected_incidents),
            "scanned_complaints": len(complaints),
            "window_hours": window_hours
        }

    @staticmethod
    def get_active_incidents(db: Session) -> List[Incident]:
        """Retrieves all active incidents that have not yet been resolved."""
        return (
            db.query(Incident)
            .filter(Incident.status.in_(["DETECTED", "ACKNOWLEDGED", "INVESTIGATING"]))
            .order_by(Incident.detected_at.desc())
            .all()
        )

    @staticmethod
    def get_all_incidents(
        db: Session,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        department_name: Optional[str] = None,
        limit: int = 50
    ) -> List[Incident]:
        """Lists all incidents with optional filtering."""
        q = db.query(Incident)
        if status:
            q = q.filter(Incident.status == status.upper())
        if severity:
            q = q.filter(Incident.severity == severity.upper())
        if department_name:
            q = q.filter(Incident.department_name.ilike(f"%{department_name}%"))
        return q.order_by(Incident.detected_at.desc()).limit(limit).all()

    @staticmethod
    def acknowledge_incident(
        db: Session,
        incident_id: int,
        manager_name: str = "Manager",
        notes: Optional[str] = None
    ) -> Incident:
        """Manager acknowledges an ongoing incident."""
        incident = db.query(Incident).filter(Incident.id == incident_id).first()
        if not incident:
            raise ValueError(f"Incident {incident_id} not found")

        incident.status = "ACKNOWLEDGED"
        incident.acknowledged_by = manager_name
        incident.acknowledged_at = datetime.utcnow()
        if notes:
            incident.description = (incident.description or "") + f"\nManager Note: {notes}"

        db.commit()
        db.refresh(incident)
        return incident

    @staticmethod
    def resolve_incident(
        db: Session,
        incident_id: int,
        manager_name: str = "Manager",
        resolution_notes: str = "Incident resolved and services restored."
    ) -> Incident:
        """Manager marks an incident as resolved."""
        incident = db.query(Incident).filter(Incident.id == incident_id).first()
        if not incident:
            raise ValueError(f"Incident {incident_id} not found")

        incident.status = "RESOLVED"
        incident.resolved_by = manager_name
        incident.resolved_at = datetime.utcnow()
        incident.resolution_notes = resolution_notes

        db.commit()
        db.refresh(incident)
        return incident

incident_service = IncidentService()
