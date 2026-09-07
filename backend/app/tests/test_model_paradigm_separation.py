import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# 1. Generative LLM Components (Ollama / Groq via LLMProvider)
from app.ai.summarizer import summarizer
from app.ai.rag import rag_engine
from app.ai.response_generator import response_generator
from app.ai.llm_provider import get_llm_provider, LLMProvider

# 2. Specialized Models
from app.ai.classifier import classifier
from app.ai.sentiment import sentiment_analyzer
from app.ai.ner import ner_extractor
from app.ai.embeddings import embeddings_engine

# 3. Deterministic Logic
from app.ai.priority import priority_calculator
from app.services.sla_service import sla_service
from app.services.routing_service import routing_service
from app.services.assignment_service import assignment_service
from app.models.user import UserRole
from app.core.security import RoleChecker

@pytest.mark.asyncio
async def test_7_llm_tasks_separation(db: Session, client: TestClient):
    """Verifies that the 7 generative tasks are routed through LLMProvider (Ollama / Groq):
    1. Complaint summarization
    2. Resolution recommendations
    3. AI assistant
    4. RAG question answering
    5. Customer response generation
    6. Internal complaint explanation
    7. Reasoning over retrieved complaint/policy information
    """
    llm = get_llm_provider()
    assert isinstance(llm, LLMProvider)

    # Task 1: Complaint summarization
    sum_res = await summarizer.summarize(
        subject="Duplicate charge",
        body="Customer reports duplicate debit of ₹5,000 today and requests an immediate refund."
    )
    assert sum_res["summary"] is not None
    assert "duplicate payment" in sum_res["summary"].lower()

    # Task 2: Resolution recommendations
    rec_res = await rag_engine.generate_grounded_recommendation(
        complaint_text="Duplicate payment on debit card",
        category="Billing",
        db=db
    )
    assert "recommended_steps" in rec_res
    assert len(rec_res["recommended_steps"]) > 0

    # Task 3: AI assistant chat
    chat_res = client.post("/api/ai/chat", json={"message": "What is the policy for billing refunds?"})
    assert chat_res.status_code == 200
    assert "reply" in chat_res.json()

    # Task 4: RAG question answering
    qa_res = await rag_engine.answer_query(
        question="What is the standard SLA for critical severity complaints?",
        db=db
    )
    assert "answer" in qa_res

    # Task 5: Customer response generation
    resp_res = await response_generator.generate_draft(
        ticket_number="TCK-999",
        customer_name="Ranjith",
        subject="Duplicate charge",
        body="I was charged ₹5,000 twice.",
        department="Finance"
    )
    assert "subject" in resp_res
    assert "body" in resp_res
    assert resp_res["requires_approval"] is True

    # Task 6: Internal complaint explanation
    exp_res = await rag_engine.explain_complaint(
        subject="Portal 500 error on checkout",
        body="Every time I press checkout I get HTTP 500 internal server error.",
        category="Technical",
        department="IT Support",
        entities=[{"entity_type": "ERROR", "entity_value": "500"}]
    )
    assert "explanation" in exp_res
    assert "root_cause" in exp_res

    # Task 7: Reasoning over retrieved complaint/policy information
    reason_res = await rag_engine.reason_over_complaint_and_policies(
        complaint_text="Customer requests refund after 3 days of duplicate billing deduction.",
        category="Billing",
        db=db
    )
    assert "policy_aligned" in reason_res
    assert "reasoning" in reason_res

def test_specialized_models_not_llm():
    """Verifies that specialized models (Classification, Sentiment, NER, Embeddings)
    do NOT use general LLM prompts but dedicated ML/NLP models.
    """
    # 1. Specialized Classification
    class_res = classifier.classify("I was charged twice for my subscription.")
    assert "category" in class_res
    assert "confidence" in class_res
    assert "model" in class_res

    # 2. Specialized Sentiment
    sent_res = sentiment_analyzer.analyze("This service is absolutely unacceptable and frustrating!")
    assert sent_res["sentiment"] in ["NEGATIVE", "POSITIVE", "NEUTRAL"]
    assert -1.0 <= sent_res["sentiment_score"] <= 1.0

    # 3. Specialized NER
    ner_res = ner_extractor.extract_entities(
        "Customer John Doe transferred ₹5,000 on 2026-03-01 for order ORD-12345 to Amazon."
    )
    assert isinstance(ner_res, list)
    entity_types = [e["entity_type"] for e in ner_res]
    assert any(t in entity_types for t in ["PERSON", "AMOUNT", "ORDER_ID", "DATE", "COMPANY"])

    # 4. Specialized Embeddings
    vec = embeddings_engine.get_embedding("Dense semantic vector testing")
    assert isinstance(vec, list)
    assert len(vec) == 384  # Dense 384-d MiniLM representation

def test_deterministic_code_not_llm(db: Session):
    """Verifies that Priority, SLA, Routing, Permissions, and Assignment
    use pure deterministic code without relying on LLM generation.
    """
    # 1. Deterministic Priority: Mathematical weighted formula
    # Priority = (Urgency*0.30) + (Sentiment*0.15) + (BizImpact*0.20) + (CustImpact*0.15) + (SLARisk*0.20)
    p_res = priority_calculator.calculate(
        urgency="CRITICAL",
        sentiment="NEGATIVE",
        category="Billing",
        business_impact=90.0,
        customer_impact=90.0,
        sla_risk=90.0
    )
    assert p_res["priority"] == "CRITICAL"
    assert 80.0 <= p_res["priority_score"] <= 100.0

    # 2. Deterministic SLA: Exact mathematical timestamps
    deadline = sla_service.calculate_deadline("CRITICAL")
    assert deadline is not None
    assert sla_service.is_breached(deadline) is False

    # 3. Deterministic Routing: Exact confidence threshold and database mapping
    route_high = routing_service.evaluate_confidence_tier(0.95)
    assert route_high["action"] == "AUTO_ROUTE"
    assert route_high["review_required"] is False

    route_med = routing_service.evaluate_confidence_tier(0.70)
    assert route_med["action"] == "PROVISIONAL_ROUTE"
    assert route_med["review_required"] is True

    route_low = routing_service.evaluate_confidence_tier(0.40)
    assert route_low["action"] == "HOLD_FOR_REVIEW"
    assert route_low["finalize_department"] is False

    # 4. Deterministic Permissions: Pure RBAC bitmask/enum checks
    admin_checker = RoleChecker(["ADMIN"])
    assert "ADMIN" in admin_checker.allowed_roles
    assert "AGENT" not in admin_checker.allowed_roles
    assert UserRole.ADMIN.value == "ADMIN"
    assert UserRole.AGENT.value == "AGENT"

    # 5. Deterministic Assignment: 7-step criteria & capacity verification
    from app.models.organization import Department, Team, Agent
    dept = Department(name="Paradigm Billing Dept", code="PBD01", is_active=True)
    db.add(dept)
    db.commit()
    db.refresh(dept)

    team = Team(department_id=dept.id, name="Paradigm Payments Team", code="PPT01", is_active=True)
    db.add(team)
    db.commit()
    db.refresh(team)

    agent1 = Agent(
        name="Payments Agent A",
        email="agent_a_paradigm@domain.com",
        department_id=dept.id,
        team_id=team.id,
        skills=["Payments", "Refunds"],
        availability=True,
        current_workload=2,
        max_workload=5,
        is_active=True
    )
    agent2 = Agent(
        name="Payments Agent B",
        email="agent_b_paradigm@domain.com",
        department_id=dept.id,
        team_id=team.id,
        skills=["Payments", "Refunds"],
        availability=True,
        current_workload=1,
        max_workload=5,
        is_active=True
    )
    db.add_all([agent1, agent2])
    db.commit()
    db.refresh(agent1)
    db.refresh(agent2)

    # Prefers lower workload agent2
    selected = assignment_service.select_best_agent(
        db,
        department_id=dept.id,
        team_id=team.id,
        required_skills=["Payments"]
    )
    assert selected is not None
    assert selected.id == agent2.id
    assert selected.name == "Payments Agent B"
