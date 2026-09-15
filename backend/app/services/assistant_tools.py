import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func

from app.models.complaint import Complaint, ComplaintAssignment
from app.models.organization import Department, Team, Agent
from app.models.knowledge import KnowledgeDocument, KnowledgeChunk
from app.services.privacy_service import privacy_service
from app.services.llm_service import llm_service

logger = logging.getLogger(__name__)

class AssistantTools:
    """
    Controlled backend tools for AI Assistant.
    IMPORTANT SECURITY CONSTRAINT:
    Under NO circumstance does this allow arbitrary SQL execution.
    Only explicit, parameterized, type-safe operations are permitted.
    """

    @staticmethod
    def search_complaints(
        db: Session,
        query: Optional[str] = None,
        department: Optional[str] = None,
        priority: Optional[str] = None,
        status: Optional[str] = None,
        unresolved_only: bool = False,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Controlled search for complaints with multi-attribute filtering.
        Example: 'Show unresolved critical Finance complaints.'
        """
        q = db.query(Complaint)

        # Department filter (name or ID)
        if department:
            matched_depts = db.query(Department).filter(
                or_(
                    Department.name.ilike(f"%{department.strip()}%"),
                    Department.code.ilike(f"%{department.strip()}%")
                )
            ).all()
            if matched_depts:
                dept_ids = [d.id for d in matched_depts]
                q = q.filter(Complaint.department_id.in_(dept_ids))


        # Priority filter (e.g. Critical -> P1 or Critical)
        if priority:
            p_clean = priority.strip().upper()
            if p_clean in ("CRITICAL", "P1"):
                q = q.filter(or_(Complaint.priority.ilike("Critical"), Complaint.priority.ilike("P1")))
            elif p_clean in ("HIGH", "P2"):
                q = q.filter(or_(Complaint.priority.ilike("High"), Complaint.priority.ilike("P2")))
            elif p_clean in ("MEDIUM", "P3"):
                q = q.filter(or_(Complaint.priority.ilike("Medium"), Complaint.priority.ilike("P3")))
            elif p_clean in ("LOW", "P4"):
                q = q.filter(or_(Complaint.priority.ilike("Low"), Complaint.priority.ilike("P4")))
            else:
                q = q.filter(Complaint.priority.ilike(f"%{priority}%"))

        # Status / Unresolved filter
        if unresolved_only:
            q = q.filter(~Complaint.status.in_(["RESOLVED", "CLOSED"]))
        elif status:
            q = q.filter(Complaint.status.ilike(f"%{status.strip()}%"))

        # Free-text keyword search
        if query:
            q_term = f"%{query.strip().lower()}%"
            q = q.filter(
                or_(
                    Complaint.subject.ilike(q_term),
                    Complaint.description.ilike(q_term),
                    Complaint.ticket_number.ilike(q_term)
                )
            )

        results = q.order_by(Complaint.created_at.desc()).limit(min(limit, 50)).all()

        complaints_data = []
        for c in results:
            complaints_data.append({
                "id": c.id,
                "ticket_number": c.ticket_number,
                "subject": c.subject,
                "department": c.department.name if c.department else "Unassigned",
                "priority": c.priority,
                "status": c.status,
                "urgency": c.urgency,
                "sentiment": c.sentiment,
                "assigned_agent": c.assigned_agent.name if c.assigned_agent else "Unassigned",
                "created_at": c.created_at.isoformat() if c.created_at else None
            })

        return {
            "tool": "search_complaints",
            "total_found": len(complaints_data),
            "complaints": complaints_data
        }

    @staticmethod
    def get_complaint(
        db: Session,
        complaint_id: Optional[int] = None,
        ticket_number: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Retrieves a single complaint with details, masking unnecessary customer PII.
        Example: 'Summarize complaint CMP-10001.'
        """
        q = db.query(Complaint)
        if complaint_id:
            q = q.filter(Complaint.id == complaint_id)
        elif ticket_number:
            q = q.filter(Complaint.ticket_number == ticket_number.strip().upper())
        else:
            return {"error": "Either complaint_id or ticket_number must be specified."}

        c = q.first()
        if not c:
            return {"error": f"Complaint not found (ID: {complaint_id}, Ticket: {ticket_number})"}

        # Mask unnecessary customer info for privacy
        masked_cust = privacy_service.mask_customer_display(
            email=c.customer_email,
            phone=getattr(c, "customer_phone", None),
            name=c.customer_name
        )

        return {
            "tool": "get_complaint",
            "id": c.id,
            "ticket_number": c.ticket_number,
            "subject": c.subject,
            "description": c.description,
            "department": c.department.name if c.department else "Unassigned",
            "team": c.team.name if c.team else "Unassigned",
            "category": c.category or "General",
            "priority": c.priority,
            "status": c.status,
            "sentiment": c.sentiment,
            "urgency": c.urgency,
            "ai_confidence": c.ai_confidence,
            "ai_summary": getattr(c, "summary", None) or getattr(c, "ai_summary", None),
            "assigned_agent": c.assigned_agent.name if c.assigned_agent else "Unassigned",
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "customer": masked_cust
        }

    @staticmethod
    def find_similar_complaints(
        db: Session,
        complaint_id: Optional[int] = None,
        text: Optional[str] = None,
        limit: int = 5
    ) -> Dict[str, Any]:
        """
        Finds similar past complaints using TF-IDF / keyword similarity.
        Example: 'Find similar complaints.'
        """
        target_text = ""
        exclude_id = None
        if complaint_id:
            c = db.query(Complaint).filter(Complaint.id == complaint_id).first()
            if c:
                target_text = f"{c.subject} {c.description}"
                exclude_id = c.id
        elif text:
            target_text = text

        if not target_text:
            return {"tool": "find_similar_complaints", "similar_cases": []}

        # Query past candidates
        candidates = db.query(Complaint)
        if exclude_id:
            candidates = candidates.filter(Complaint.id != exclude_id)
        candidate_rows = candidates.order_by(Complaint.created_at.desc()).limit(100).all()

        if not candidate_rows:
            return {"tool": "find_similar_complaints", "similar_cases": []}

        from app.ai.duplicate_detector import TFIDFBaselineDuplicateDetector
        detector = TFIDFBaselineDuplicateDetector()
        candidate_texts = [f"{cr.subject} {cr.description}" for cr in candidate_rows]
        scores = detector.compute_similarity(target_text, candidate_texts)

        scored_results = []
        for cr, score in zip(candidate_rows, scores):
            if score > 0.15:
                scored_results.append({
                    "ticket_number": cr.ticket_number,
                    "subject": cr.subject,
                    "category": cr.category,
                    "status": cr.status,
                    "similarity_score": round(float(score), 4),
                    "department": cr.department.name if cr.department else "General"
                })

        scored_results.sort(key=lambda x: x["similarity_score"], reverse=True)
        return {
            "tool": "find_similar_complaints",
            "similar_cases": scored_results[:limit]
        }

    @staticmethod
    def search_knowledge_base(
        db: Session,
        query: str,
        department: Optional[str] = None,
        limit: int = 3
    ) -> Dict[str, Any]:
        """
        Searches company policies, SOPs, and knowledge documents.
        Example: 'What policy applies to this refund complaint?'
        """
        from app.ai.rag import rag_engine
        results = rag_engine.retrieve_relevant_policies(query, db, limit=limit, min_similarity=0.20)

        docs_formatted = []
        for r in results:
            docs_formatted.append({
                "title": r.get("title"),
                "document_type": r.get("document_type"),
                "similarity": r.get("similarity"),
                "key_clauses": r.get("content_snippet", "")[:350]
            })

        return {
            "tool": "search_knowledge_base",
            "query": query,
            "relevant_policies": docs_formatted
        }

    @staticmethod
    def get_customer_history(
        db: Session,
        customer_email: Optional[str] = None,
        customer_name: Optional[str] = None,
        complaint_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Where appropriate, allows authorized agents to view:
        - Previous complaints
        - Previous categories
        - Previous resolutions
        - Complaint frequency
        - Open complaints
        - Closed complaints
        Does not expose unnecessary customer information.
        """
        target_email = customer_email
        target_name = customer_name

        if complaint_id and not target_email:
            c = db.query(Complaint).filter(Complaint.id == complaint_id).first()
            if c:
                target_email = c.customer_email
                target_name = c.customer_name

        if not target_email and not target_name:
            return {"error": "Provide customer_email, customer_name, or complaint_id."}

        query = db.query(Complaint)
        if target_email:
            query = query.filter(Complaint.customer_email.ilike(target_email.strip()))
        elif target_name:
            query = query.filter(Complaint.customer_name.ilike(target_name.strip()))

        past_complaints = query.order_by(Complaint.created_at.desc()).all()

        total_count = len(past_complaints)
        open_count = sum(1 for c in past_complaints if c.status not in ("RESOLVED", "CLOSED"))
        closed_count = sum(1 for c in past_complaints if c.status in ("RESOLVED", "CLOSED"))

        categories = list({c.category for c in past_complaints if c.category})
        resolutions = []
        for c in past_complaints:
            if c.status in ("RESOLVED", "CLOSED"):
                resolutions.append({
                    "ticket_number": c.ticket_number,
                    "resolved_at": c.resolved_at.isoformat() if hasattr(c, "resolved_at") and c.resolved_at else None,
                    "category": c.category,
                    "subject": c.subject
                })

        # Calculate complaint frequency (e.g. complaints per 30 days)
        if past_complaints and len(past_complaints) > 1:
            first_date = past_complaints[-1].created_at or datetime.utcnow()
            last_date = past_complaints[0].created_at or datetime.utcnow()
            days_span = max((last_date - first_date).days, 1)
            frequency_desc = f"{total_count} complaints over {days_span} days ({round(total_count / (days_span / 30.0), 1)} / month)"
        else:
            frequency_desc = f"{total_count} complaint recorded"

        # Mask customer display
        masked_cust = privacy_service.mask_customer_display(
            email=target_email,
            name=target_name
        )

        return {
            "tool": "get_customer_history",
            "customer": masked_cust,
            "complaint_frequency": frequency_desc,
            "total_complaints": total_count,
            "open_complaints": open_count,
            "closed_complaints": closed_count,
            "previous_categories": categories,
            "previous_resolutions": resolutions[:5],
            "previous_complaints": [
                {
                    "ticket_number": c.ticket_number,
                    "subject": c.subject,
                    "category": c.category,
                    "status": c.status,
                    "priority": c.priority,
                    "created_at": c.created_at.isoformat() if c.created_at else None
                }
                for c in past_complaints[:10]
            ]
        }

    @staticmethod
    def get_department(
        db: Session,
        department_name: Optional[str] = None,
        department_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Retrieves department metrics, teams, and current load.
        """
        q = db.query(Department)
        if department_id:
            q = q.filter(Department.id == department_id)
        elif department_name:
            q = q.filter(Department.name.ilike(f"%{department_name.strip()}%"))
        else:
            depts = db.query(Department).all()
            return {
                "tool": "get_department",
                "departments": [{"id": d.id, "name": d.name, "code": d.code} for d in depts]
            }

        dept = q.first()
        if not dept:
            return {"error": f"Department '{department_name or department_id}' not found."}

        teams = [{"id": t.id, "name": t.name} for t in dept.teams] if dept.teams else []
        open_tickets = db.query(Complaint).filter(
            Complaint.department_id == dept.id,
            ~Complaint.status.in_(["RESOLVED", "CLOSED"])
        ).count()

        return {
            "tool": "get_department",
            "department_id": dept.id,
            "name": dept.name,
            "code": dept.code,
            "description": dept.description,
            "teams": teams,
            "open_complaints_count": open_tickets
        }

    @staticmethod
    def get_agent_workload(
        db: Session,
        department: Optional[str] = None,
        team: Optional[str] = None,
        agent_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Retrieves agent workloads, capacities, and availability.
        """
        q = db.query(Agent).filter(Agent.is_active == True)

        if department:
            dept_obj = db.query(Department).filter(Department.name.ilike(f"%{department.strip()}%")).first()
            if dept_obj:
                q = q.filter(Agent.department_id == dept_obj.id)

        if team:
            team_obj = db.query(Team).filter(Team.name.ilike(f"%{team.strip()}%")).first()
            if team_obj:
                q = q.filter(Agent.team_id == team_obj.id)

        if agent_name:
            q = q.filter(Agent.name.ilike(f"%{agent_name.strip()}%"))

        agents = q.all()
        workload_roster = []
        for a in agents:
            workload_roster.append({
                "agent_id": a.id,
                "name": a.name,
                "email": a.email,
                "department": a.department.name if a.department else "None",
                "current_workload": a.current_workload,
                "max_workload": a.max_workload,
                "utilization_pct": round((a.current_workload / max(a.max_workload, 1)) * 100, 1),
                "availability": a.availability
            })

        return {
            "tool": "get_agent_workload",
            "total_agents": len(workload_roster),
            "agents": workload_roster
        }

    @staticmethod
    async def generate_response(
        db: Session,
        complaint_id: Optional[int] = None,
        text: Optional[str] = None,
        tone: str = "Empathetic & Professional"
    ) -> Dict[str, Any]:
        """
        Generates an empathetic customer reply.
        Ensures PII is redacted before calling external LLMs.
        Prefers local Ollama for sensitive processing.
        """
        complaint_info = {}
        if complaint_id:
            c = db.query(Complaint).filter(Complaint.id == complaint_id).first()
            if c:
                complaint_info = {
                    "title": c.subject,
                    "sender_email": c.customer_email,
                    "department": c.department.name if c.department else "Customer Support",
                    "description": c.description,
                    "ticket_number": c.ticket_number
                }
        elif text:
            complaint_info = {
                "title": "Customer Inquiry",
                "sender_email": "customer@example.com",
                "department": "Customer Support",
                "description": text,
                "ticket_number": "CMP-AUTO"
            }

        # Privacy Check: Redact PII before LLM
        clean_desc, has_pii = privacy_service.mask_pii_for_external_llm(complaint_info.get("description", ""))
        complaint_info["description"] = clean_desc

        draft = await llm_service.generate_response_draft(complaint_info, tone=tone)
        return {
            "tool": "generate_response",
            "subject": draft.get("subject"),
            "body": draft.get("body"),
            "provider": draft.get("provider"),
            "privacy_sanitized": has_pii
        }

assistant_tools = AssistantTools()
