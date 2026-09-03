from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.complaint import Complaint, ComplaintAssignment, ComplaintEvent, ComplaintFeedback
from app.models.intelligence import ComplaintPrediction, ComplaintEntity, AIResponse
from app.schemas.complaint import ComplaintCreate
from app.ai.ai_orchestrator import ai_orchestrator
from app.services.routing_service import routing_service
from app.services.assignment_service import assignment_service
from app.services.sla_service import sla_service
from app.services.notification_service import notification_service
from app.services.audit_service import audit_service
from app.services.lifecycle_service import lifecycle_service
from app.repositories.complaint_repository import complaint_repository

class ComplaintService:
    @staticmethod
    async def process_and_create_complaint(db: Session, complaint_in: ComplaintCreate) -> Complaint:
        """Executes full 14-task AI triage, department routing, agent assignment, and lifecycle event logging."""
        total_count = complaint_repository.count(db) + 10001
        ticket_num = f"CMP-{total_count}"

        # Normalize Source (EMAIL, WEB, MANUAL)
        raw_source = (complaint_in.source or "WEB").upper()
        if "EMAIL" in raw_source:
            norm_source = "EMAIL"
        elif "MANUAL" in raw_source:
            norm_source = "MANUAL"
        else:
            norm_source = "WEB"

        # 1. Persist Initial Complaint in NEW status
        complaint = Complaint(
            complaint_number=ticket_num,
            customer_name=complaint_in.customer_name,
            customer_email=complaint_in.customer_email,
            subject=complaint_in.subject,
            description=complaint_in.get_description(),
            source=norm_source,
            category="Pending Classification",
            status="NEW"
        )
        db.add(complaint)
        db.flush()

        # Lifecycle Event 1: Complaint received
        lifecycle_service.record_event(
            db=db,
            complaint_id=complaint.id,
            event_type="COMPLAINT_RECEIVED",
            actor=norm_source,
            description="Complaint received",
            event_metadata={"source": norm_source, "customer_email": complaint.customer_email}
        )

        # Lifecycle Event 2: AI analysis started
        lifecycle_service.transition_status(
            db=db,
            complaint=complaint,
            new_status="AI_ANALYZING",
            actor="AI_ENGINE",
            description="AI analysis started"
        )

        # 2. Execute AI Pipeline
        ai_res = await ai_orchestrator.process_complaint_full(
            subject=complaint_in.subject,
            body=complaint_in.get_description(),
            customer_name=complaint_in.customer_name or "Valued Customer",
            ticket_number=ticket_num,
            db=db
        )

        # Lifecycle Event 3: AI analysis completed
        lifecycle_service.transition_status(
            db=db,
            complaint=complaint,
            new_status="AI_ANALYZED",
            actor="AI_ENGINE",
            description="AI analysis completed",
            event_metadata={
                "category": ai_res["category"],
                "confidence": ai_res.get("cat_confidence", 0.90),
                "urgency": ai_res["urgency"],
                "execution_time_ms": ai_res.get("execution_time_ms")
            }
        )

        # 3. Route Department and Team
        dept_id, team_id, dept_name = routing_service.route_complaint(
            db=db,
            department_name=ai_res["department_name"],
            team_name=ai_res["team_name"],
            text_content=complaint_in.get_description()
        )

        # Lifecycle Event 4: Routed to Department
        lifecycle_service.transition_status(
            db=db,
            complaint=complaint,
            new_status="ROUTED",
            actor="AI_ENGINE",
            description=f"Routed to {dept_name or ai_res['department_name'] or 'General Triage'}",
            event_metadata={"department_id": dept_id, "department_name": dept_name}
        )

        # Lifecycle Event 5: Assigned to Team (if matched)
        team_label = ai_res.get("team_name")
        if team_label:
            lifecycle_service.record_event(
                db=db,
                complaint_id=complaint.id,
                event_type="TEAM_ASSIGNED",
                actor="AI_ENGINE",
                description=f"Assigned to {team_label}",
                event_metadata={"team_id": team_id, "team_name": team_label}
            )

        # 4. Intelligent Agent Assignment (evaluating 7 business factors)
        assigned_agent = assignment_service.select_best_agent(
            db=db,
            department_id=dept_id,
            team_id=team_id,
            required_skills=[ai_res.get("category", "").lower()]
        )
        agent_id = assigned_agent.id if assigned_agent else None

        # Lifecycle Event 6: Assigned to Agent (if found)
        if assigned_agent:
            lifecycle_service.transition_status(
                db=db,
                complaint=complaint,
                new_status="ASSIGNED",
                actor="AI_ENGINE",
                description=f"Assigned to {assigned_agent.name}",
                event_metadata={"agent_id": assigned_agent.id, "agent_name": assigned_agent.name}
            )

        # 5. SLA Deadline
        sla_deadline = sla_service.calculate_deadline(ai_res["urgency"])

        # 6. Update Complaint with enriched AI analytics
        complaint.category = ai_res["category"]
        complaint.sub_category = ai_res["sub_category"]
        complaint.department_id = dept_id
        complaint.team_id = team_id
        complaint.assigned_agent_id = agent_id
        complaint.urgency = ai_res["urgency"]
        complaint.priority = ai_res["priority_level"]
        complaint.priority_score = ai_res["priority_score"]
        complaint.sentiment = ai_res["sentiment"]
        complaint.emotion = ai_res["emotion"]
        complaint.ai_confidence = ai_res.get("cat_confidence", 0.90)
        complaint.review_required = ai_res.get("review_required", False)
        complaint.ai_status = "COMPLETED"
        complaint.summary = ai_res.get("summary", "")
        complaint.sla_deadline = sla_deadline
        complaint.cleaned_text = ai_res["cleaned_text"]
        complaint.is_duplicate = ai_res["is_duplicate"]
        complaint.duplicate_of_id = ai_res["duplicate_of_id"]
        complaint.embedding = ai_res["embedding"]
        db.flush()

        # 6. Record Prediction
        db.add(ComplaintPrediction(
            complaint_id=complaint.id,
            model_name="AutoTriage-AI-Pipeline",
            predicted_category=ai_res["category"],
            category_confidence=ai_res["cat_confidence"],
            predicted_dept=ai_res["department_name"],
            dept_confidence=ai_res["cat_confidence"],
            urgency=ai_res["urgency"],
            urgency_score=ai_res["urgency_score"],
            sentiment=ai_res["sentiment"],
            sentiment_score=ai_res["sentiment_score"],
            emotion=ai_res["emotion"],
            emotion_score=ai_res["emotion_score"],
            execution_time_ms=ai_res["execution_time_ms"]
        ))

        # 7. Record Entities
        for ent in ai_res["entities"]:
            db.add(ComplaintEntity(
                complaint_id=complaint.id,
                entity_type=ent["entity_type"],
                entity_value=ent["entity_value"],
                confidence=ent["confidence"],
                start_char=ent.get("start_char"),
                end_char=ent.get("end_char")
            ))

        # 8. Record AI Draft Response & Summary
        db.add(AIResponse(
            complaint_id=complaint.id,
            provider=ai_res["draft_response"]["provider"],
            model="Configured-LLM",
            response_type="DRAFT_REPLY",
            content=ai_res["draft_response"]["body"],
            is_approved=False
        ))
        db.add(AIResponse(
            complaint_id=complaint.id,
            provider="AutoTriage-Summarizer",
            model="Summarizer-v1",
            response_type="SUMMARY",
            content=ai_res["summary"],
            is_approved=True
        ))

        # 9. Audit and Notifications
        db.add(ComplaintEvent(
            complaint_id=complaint.id,
            event_type="INGESTION",
            actor=complaint_in.source,
            notes=f"Ingested and triaged in {ai_res['execution_time_ms']}ms."
        ))

        if ai_res["urgency"] in ("Critical", "High"):
            notification_service.create_notification(
                db=db,
                title=f"{ai_res['urgency']} Priority Ticket: {ticket_num}",
                message=f"New complaint in {ai_res['department_name']} ({ai_res['category']}).",
                notification_type="CRITICAL_TICKET",
                department_id=dept_id,
                link_url=f"/complaints/{complaint.id}"
            )

        audit_service.log_event(
            db=db,
            action="CREATE_COMPLAINT",
            entity_type="COMPLAINT",
            entity_id=str(complaint.id),
            details={"ticket_number": ticket_num, "urgency": ai_res["urgency"]}
        )

        db.commit()
        db.refresh(complaint)
        return complaint

complaint_service = ComplaintService()
