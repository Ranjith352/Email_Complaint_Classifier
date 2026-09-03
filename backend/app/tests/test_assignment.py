import pytest
from app.services.assignment_service import assignment_service
from app.models.organization import Department, Team, Agent

def test_assignment_7_factors(db):
    dept = Department(name="Finance Ops Test", code="FOPTST")
    db.add(dept)
    db.commit()
    db.refresh(dept)

    t_refund = Team(department_id=dept.id, name="Refund Team", code="FOP-REF")
    t_bill = Team(department_id=dept.id, name="Billing Team", code="FOP-BIL")
    db.add_all([t_refund, t_bill])
    db.commit()
    db.refresh(t_refund)
    db.refresh(t_bill)

    # 1. Unavailable agent -> Must be skipped even with high skills
    agent_offline = Agent(
        name="Offline Specialist",
        email="offline@test.com",
        department_id=dept.id,
        team_id=t_refund.id,
        skills=["refund", "chargeback"],
        availability=False,
        current_workload=0,
        max_workload=10,
        performance_score=99.0,
        average_resolution_time=1.0,
        is_active=True
    )

    # 2. Agent at maximum capacity (current_workload == max_workload) -> Must be skipped
    agent_maxed = Agent(
        name="Overloaded Specialist",
        email="overloaded@test.com",
        department_id=dept.id,
        team_id=t_refund.id,
        skills=["refund"],
        availability=True,
        current_workload=10,
        max_workload=10,
        performance_score=98.0,
        average_resolution_time=2.0,
        is_active=True
    )

    # 3. Candidate A: Correct team, has required skill "chargeback", good performance
    agent_expert = Agent(
        name="Expert Refund Agent",
        email="expert@test.com",
        department_id=dept.id,
        team_id=t_refund.id,
        skills=["refund", "chargeback", "vip"],
        availability=True,
        current_workload=2,
        max_workload=10,
        performance_score=95.0,
        average_resolution_time=2.5,
        is_active=True
    )

    # 4. Candidate B: Different team (Billing), no "chargeback" skill
    agent_other = Agent(
        name="Billing Agent",
        email="billing@test.com",
        department_id=dept.id,
        team_id=t_bill.id,
        skills=["invoice"],
        availability=True,
        current_workload=1,
        max_workload=10,
        performance_score=80.0,
        average_resolution_time=5.0,
        is_active=True
    )

    db.add_all([agent_offline, agent_maxed, agent_expert, agent_other])
    db.commit()

    # Request assignment for Refund Team with required skill "chargeback"
    chosen = assignment_service.select_best_agent(
        db,
        department_id=dept.id,
        team_id=t_refund.id,
        required_skills=["chargeback"]
    )

    # Must select agent_expert: correct department, correct team, matching skill, available, under max capacity
    assert chosen is not None
    assert chosen.id == agent_expert.id
    assert chosen.name == "Expert Refund Agent"
    assert chosen.current_workload == 3  # Workload incremented by 1
