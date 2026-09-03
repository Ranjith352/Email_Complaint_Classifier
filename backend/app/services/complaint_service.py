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

        # 3. Confidence-Based Routing & Human Review Decision
        # Thresholds:
        # - confidence >= 0.85: Automatically route
        # - confidence 0.60 - 0.84: Route but mark review_required = true
        # - confidence < 0.60: Do not automatically finalize department. Require human review.
        ai_confidence = float(ai_res.get("confidence", ai_res.get("cat_confidence", 0.90)))

        if ai_confidence >= 0.85:
            review_required = False
            dept_id, team_id, dept_name = routing_service.route_complaint(
                db=db,
                department_name=ai_res["department_name"],
                team_name=ai_res["team_name"],
                text_content=complaint_in.get_description()
            )

            # Lifecycle Event 4: Automatically Routed to Department
            lifecycle_service.transition_status(
                db=db,
                complaint=complaint,
                new_status="ROUTED",
                actor="AI_ENGINE",
                description=f"Routed to {dept_name or ai_res['department_name'] or 'General Triage'} (Automatically routed, Confidence: {ai_confidence:.2f} >= 0.85)",
                event_metadata={"department_id": dept_id, "department_name": dept_name, "confidence": ai_confidence}
            )

            # Lifecycle Event 5: Assigned to Team (if matched)
            team_label = ai_res.get("team_name")
            if team_label and team_id:
                lifecycle_service.record_event(
                    db=db,
                    complaint_id=complaint.id,
                    event_type="TEAM_ASSIGNED",
                    actor="AI_ENGINE",
                    description=f"Assigned to {team_label}",
                    event_metadata={"team_id": team_id, "team_name": team_label}
                )

            # Intelligent Agent Assignment
            assigned_agent = assignment_service.select_best_agent(
                db=db,
                department_id=dept_id,
                team_id=team_id,
                required_skills=[ai_res.get("category", "").lower()]
            )
            agent_id = assigned_agent.id if assigned_agent else None

            if assigned_agent:
                lifecycle_service.transition_status(
                    db=db,
                    complaint=complaint,
                    new_status="ASSIGNED",
                    actor="AI_ENGINE",
                    description=f"Assigned to {assigned_agent.name}",
                    event_metadata={"agent_id": assigned_agent.id, "agent_name": assigned_agent.name}
                )
            else:
                # If no suitable agent exists: Route to the team queue. Do not lose the complaint.
                team_display = team_label or dept_name or "General"
                lifecycle_service.record_event(
                    db=db,
                    complaint_id=complaint.id,
                    event_type="ENQUEUED_IN_TEAM_QUEUE",
                    actor="ASSIGNMENT_ENGINE",
                    description=f"No suitable agent available matching criteria. Routed to {team_display} queue. Ticket preserved without loss.",
                    event_metadata={"department_id": dept_id, "team_id": team_id, "queue": f"{team_display} Queue"}
                )

        elif 0.60 <= ai_confidence < 0.85:
            # Provisional routing: route to suggested department/team, but flag for human review
            review_required = True
            dept_id, team_id, dept_name = routing_service.route_complaint(
                db=db,
                department_name=ai_res["department_name"],
                team_name=ai_res["team_name"],
                text_content=complaint_in.get_description()
            )

            lifecycle_service.transition_status(
                db=db,
                complaint=complaint,
                new_status="ROUTED",
                actor="AI_ENGINE",
                description=f"Provisional routing to {dept_name or ai_res['department_name']} (Confidence: {ai_confidence:.2f}). Human review required.",
                event_metadata={"department_id": dept_id, "department_name": dept_name, "confidence": ai_confidence, "review_required": True}
            )

            team_label = ai_res.get("team_name")
            if team_label and team_id:
                lifecycle_service.record_event(
                    db=db,
                    complaint_id=complaint.id,
                    event_type="TEAM_ASSIGNED",
                    actor="AI_ENGINE",
                    description=f"Assigned to {team_label} (Provisional)",
                    event_metadata={"team_id": team_id, "team_name": team_label}
                )

            assigned_agent = assignment_service.select_best_agent(
                db=db,
                department_id=dept_id,
                team_id=team_id,
                required_skills=[ai_res.get("category", "").lower()]
            )
            agent_id = assigned_agent.id if assigned_agent else None

            if assigned_agent:
                lifecycle_service.transition_status(
                    db=db,
                    complaint=complaint,
                    new_status="ASSIGNED",
                    actor="AI_ENGINE",
                    description=f"Assigned to {assigned_agent.name} (Pending Review)",
                    event_metadata={"agent_id": assigned_agent.id, "agent_name": assigned_agent.name}
                )
            else:
                team_display = team_label or dept_name or "General"
                lifecycle_service.record_event(
                    db=db,
                    complaint_id=complaint.id,
                    event_type="ENQUEUED_IN_TEAM_QUEUE",
                    actor="ASSIGNMENT_ENGINE",
                    description=f"No suitable agent available matching criteria. Routed to {team_display} queue (Provisional). Ticket preserved without loss.",
                    event_metadata={"department_id": dept_id, "team_id": team_id, "queue": f"{team_display} Queue"}
                )

        else:
            # Low Confidence (< 0.60): Do NOT automatically finalize the department.
            review_required = True
            dept_id = None
            team_id = None
            agent_id = None

            lifecycle_service.record_event(
                db=db,
                complaint_id=complaint.id,
                event_type="ROUTING_HELD_FOR_REVIEW",
                actor="AI_ENGINE",
                description=f"Low confidence ({ai_confidence:.2f} < 0.60). Department not finalized. Human review required.",
                event_metadata={
                    "confidence": ai_confidence,
                    "suggested_category": ai_res.get("category"),
                    "suggested_department": ai_res.get("department_name")
                }
            )

        # 4. SLA Deadline
        sla_deadline = sla_service.calculate_deadline(ai_res["urgency"])

        # 5. Update Complaint with enriched AI analytics & review flags
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
        complaint.ai_confidence = ai_confidence
        complaint.review_required = review_required
        complaint.reviewed_by = None
        complaint.reviewed_at = None
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
            predicted_category=ai_res.get("category", "General"),
            category_confidence=ai_res.get("cat_confidence", ai_res.get("confidence", 0.90)),
            predicted_dept=ai_res.get("department_name", "General Support"),
            dept_confidence=ai_res.get("cat_confidence", ai_res.get("confidence", 0.90)),
            urgency=ai_res.get("urgency", "MEDIUM"),
            urgency_score=ai_res.get("urgency_score", 50.0),
            sentiment=ai_res.get("sentiment", "NEUTRAL"),
            sentiment_score=ai_res.get("sentiment_score", 0.0),
            emotion=ai_res.get("emotion", "NEUTRAL"),
            emotion_score=ai_res.get("emotion_score", 0.85),
            execution_time_ms=ai_res.get("execution_time_ms", 10.0)
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

    def review_complaint(
        self,
        db: Session,
        complaint: Complaint,
        department_id: Optional[int] = None,
        team_id: Optional[int] = None,
        assigned_agent_id: Optional[int] = None,
        reviewer_name: str = "Support Lead",
        notes: Optional[str] = None
    ) -> Complaint:
        """Completes human review for a complaint, updating review_required, reviewed_by, reviewed_at, and department."""
        complaint.review_required = False
        complaint.reviewed_by = reviewer_name
        complaint.reviewed_at = datetime.utcnow()

        if department_id is not None:
            complaint.department_id = department_id
        if team_id is not None:
            complaint.team_id = team_id
        if assigned_agent_id is not None:
            complaint.assigned_agent_id = assigned_agent_id

        # If department was unfinalized and is now finalized, transition to ROUTED
        if complaint.department_id and complaint.status in ("NEW", "AI_ANALYZED"):
            lifecycle_service.transition_status(
                db=db,
                complaint=complaint,
                new_status="ROUTED",
                actor=reviewer_name,
                description=f"Department finalized by {reviewer_name}: {notes or 'Human review approved'}",
                event_metadata={"department_id": complaint.department_id, "team_id": complaint.team_id}
            )
        else:
            lifecycle_service.record_event(
                db=db,
                complaint_id=complaint.id,
                event_type="HUMAN_REVIEW_COMPLETED",
                actor=reviewer_name,
                description=f"Human review completed by {reviewer_name}: {notes or 'Approved'}"
            )

        db.commit()
        db.refresh(complaint)
        return complaint

complaint_service = ComplaintService()
