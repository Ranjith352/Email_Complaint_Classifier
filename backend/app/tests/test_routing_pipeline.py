import pytest
from app.models.organization import Department, Team, Agent
from app.services.routing_service import routing_service

def test_user_exact_example_routing_flow(db):
    # User Specification:
    # Complaint: "I have been charged twice for my payment."
    # AI:
    # Category = Billing
    # Subcategory = Duplicate Payment
    # Department = Finance
    # Team = Payments
    # Then select an available Finance Payments agent.

    # 1. Setup Department
    fin_dept = db.query(Department).filter(Department.name == "Finance").first()
    if not fin_dept:
        fin_dept = Department(name="Finance", code="FIN", description="Finance & Billing", is_active=True)
        db.add(fin_dept)
        db.commit()
        db.refresh(fin_dept)

    # 2. Setup Payments Team under Finance
    pay_team = db.query(Team).filter(Team.department_id == fin_dept.id, Team.name == "Payments").first()
    if not pay_team:
        pay_team = Team(department_id=fin_dept.id, name="Payments", code="FIN-PAY", is_active=True)
        db.add(pay_team)
        db.commit()
        db.refresh(pay_team)

    # 3. Setup Available Finance Payments Agents with different workloads
    agent_busy = db.query(Agent).filter(Agent.email == "busy.payments@example.com").first()
    if not agent_busy:
        agent_busy = Agent(
            name="Alice Busy",
            email="busy.payments@example.com",
            department_id=fin_dept.id,
            team_id=pay_team.id,
            skills=["billing", "payments", "duplicate payment"],
            availability=True,
            current_workload=7,
            max_workload=10,
            is_active=True
        )
        db.add(agent_busy)

    agent_free = db.query(Agent).filter(Agent.email == "free.payments@example.com").first()
    if not agent_free:
        agent_free = Agent(
            name="Bob Free",
            email="free.payments@example.com",
            department_id=fin_dept.id,
            team_id=pay_team.id,
            skills=["billing", "payments", "duplicate payment"],
            availability=True,
            current_workload=1,
            max_workload=10,
            is_active=True
        )
        db.add(agent_free)

    db.commit()
    db.refresh(agent_free)
    initial_workload = agent_free.current_workload

    # 4. Execute Complete 8-Stage Routing Pipeline
    complaint_text = "I have been charged twice for my payment."
    result = routing_service.execute_routing_pipeline(db, complaint_text)

    # 5. Verify Stage 1 to 9 Assertions
    # Stage 1-3: AI Classification -> Category & Subcategory
    assert result["category"] == "Billing"
    assert result["subcategory"] == "Duplicate Payment"

    # Stage 4: Department
    assert result["department_name"] == "Finance"
    assert result["department_id"] == fin_dept.id

    # Stage 5: Team
    assert result["team_name"] == "Payments"
    assert result["team_id"] == pay_team.id

    # Stage 6: Required Skills
    assert "billing" in result["required_skills"]
    assert "payments" in result["required_skills"]

    # Stage 7 & 8: Available Agents & Workload
    assert result["available_agents_count"] >= 2

    # Stage 9: Assignment - Selects the available Finance Payments agent with lowest workload
    assert result["assigned_agent_id"] == agent_free.id
    assert result["assigned_agent_name"] == "Bob Free"
    assert result["assigned_agent_workload"] == initial_workload + 1

def test_stage_breakdown_flow(db):
    # Test skill derivation
    skills = routing_service.derive_required_skills("Billing", "Duplicate Payment", "Payments")
    assert "billing" in skills
    assert "payments" in skills
    assert "duplicate payment" in skills

    # Test classification helper
    meta = routing_service.classify_complaint("I have been charged twice for my payment.")
    assert meta["category"] == "Billing"
    assert meta["subcategory"] == "Duplicate Payment"
    assert meta["department"] == "Finance"
    assert meta["team"] == "Payments"
