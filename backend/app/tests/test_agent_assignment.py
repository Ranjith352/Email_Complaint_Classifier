import pytest
import uuid
from app.models.organization import Department, Team, Agent
from app.models.complaint import Complaint
from app.services.assignment_service import assignment_service

@pytest.fixture
def org_hierarchy(db):
    uid = uuid.uuid4().hex[:6]
    dept = Department(name=f"Customer Ops {uid}", code=f"C{uid[:3].upper()}", is_active=True)
    other_dept = Department(name=f"Engineering Ops {uid}", code=f"E{uid[:3].upper()}", is_active=True)
    db.add_all([dept, other_dept])
    db.commit()
    db.refresh(dept)
    db.refresh(other_dept)

    team_pay = Team(department_id=dept.id, name=f"Payments {uid}", code=f"P{uid[:3].upper()}", is_active=True)
    team_sub = Team(department_id=dept.id, name=f"Subscriptions {uid}", code=f"S{uid[:3].upper()}", is_active=True)
    db.add_all([team_pay, team_sub])
    db.commit()
    db.refresh(team_pay)
    db.refresh(team_sub)

    return {
        "dept": dept,
        "other_dept": other_dept,
        "team_pay": team_pay,
        "team_sub": team_sub,
        "uid": uid
    }

def test_verify_department_and_team(db, org_hierarchy):
    dept = org_hierarchy["dept"]
    other_dept = org_hierarchy["other_dept"]
    team_pay = org_hierarchy["team_pay"]
    uid = org_hierarchy["uid"]

    # 1. Agent in other department (Must not be selected)
    agent_other_dept = Agent(
        name=f"Other Dept Agent {uid}",
        email=f"other_{uid}@test.com",
        department_id=other_dept.id,
        team_id=None,
        skills=["payments"],
        availability=True,
        current_workload=0,
        max_workload=10,
        is_active=True
    )
    # 2. Agent in target department & team
    agent_target = Agent(
        name=f"Payments Agent {uid}",
        email=f"pay_{uid}@test.com",
        department_id=dept.id,
        team_id=team_pay.id,
        skills=["payments"],
        availability=True,
        current_workload=2,
        max_workload=10,
        is_active=True
    )
    db.add_all([agent_other_dept, agent_target])
    db.commit()

    chosen = assignment_service.select_best_agent(
        db=db,
        department_id=dept.id,
        team_id=team_pay.id,
        required_skills=["payments"]
    )
    assert chosen is not None
    assert chosen.id == agent_target.id

def test_verify_availability_and_max_workload(db, org_hierarchy):
    dept = org_hierarchy["dept"]
    team_pay = org_hierarchy["team_pay"]
    uid = org_hierarchy["uid"]

    # 1. Offline agent (availability=False)
    agent_offline = Agent(
        name=f"Offline Agent {uid}",
        email=f"offline_{uid}@example.com",
        department_id=dept.id,
        team_id=team_pay.id,
        skills=["payments"],
        availability=False,
        current_workload=0,
        max_workload=10,
        is_active=True
    )
    # 2. Inactive agent (is_active=False)
    agent_inactive = Agent(
        name=f"Inactive Agent {uid}",
        email=f"inactive_{uid}@example.com",
        department_id=dept.id,
        team_id=team_pay.id,
        skills=["payments"],
        availability=True,
        current_workload=0,
        max_workload=10,
        is_active=False
    )
    # 3. Maxed-out agent (current_workload == max_workload)
    agent_maxed = Agent(
        name=f"Maxed Agent {uid}",
        email=f"maxed_{uid}@example.com",
        department_id=dept.id,
        team_id=team_pay.id,
        skills=["payments"],
        availability=True,
        current_workload=10,
        max_workload=10,
        is_active=True
    )
    # 4. Valid available agent
    agent_available = Agent(
        name=f"Available Agent {uid}",
        email=f"avail_{uid}@example.com",
        department_id=dept.id,
        team_id=team_pay.id,
        skills=["payments"],
        availability=True,
        current_workload=5,
        max_workload=10,
        is_active=True
    )
    db.add_all([agent_offline, agent_inactive, agent_maxed, agent_available])
    db.commit()

    chosen = assignment_service.select_best_agent(
        db=db,
        department_id=dept.id,
        team_id=team_pay.id,
        required_skills=["payments"]
    )
    assert chosen is not None
    assert chosen.id == agent_available.id
    assert chosen.current_workload == 6  # Incremented from 5 to 6

def test_prefer_suitable_lower_workload_agents(db, org_hierarchy):
    dept = org_hierarchy["dept"]
    team_pay = org_hierarchy["team_pay"]
    uid = org_hierarchy["uid"]

    # Agent A has heavy load (8/10)
    agent_heavy = Agent(
        name=f"Heavy Load Agent {uid}",
        email=f"heavy_{uid}@example.com",
        department_id=dept.id,
        team_id=team_pay.id,
        skills=["payments", "billing"],
        availability=True,
        current_workload=8,
        max_workload=10,
        is_active=True
    )
    # Agent B has light load (1/10)
    agent_light = Agent(
        name=f"Light Load Agent {uid}",
        email=f"light_{uid}@example.com",
        department_id=dept.id,
        team_id=team_pay.id,
        skills=["payments", "billing"],
        availability=True,
        current_workload=1,
        max_workload=10,
        is_active=True
    )
    db.add_all([agent_heavy, agent_light])
    db.commit()

    # Criteria 7: Prefer suitable lower-workload agents
    chosen = assignment_service.select_best_agent(
        db=db,
        department_id=dept.id,
        team_id=team_pay.id,
        required_skills=["payments"]
    )
    assert chosen is not None
    assert chosen.id == agent_light.id
    assert chosen.name == f"Light Load Agent {uid}"
    assert chosen.current_workload == 2

def test_no_suitable_agent_routes_to_team_queue_do_not_lose(db, org_hierarchy):
    dept = org_hierarchy["dept"]
    team_pay = org_hierarchy["team_pay"]
    uid = org_hierarchy["uid"]

    # All agents in the team are completely overloaded or offline
    overloaded = Agent(
        name=f"Overloaded Only {uid}",
        email=f"overloaded_{uid}@example.com",
        department_id=dept.id,
        team_id=team_pay.id,
        skills=["payments"],
        availability=True,
        current_workload=10,
        max_workload=10,
        is_active=True
    )
    db.add(overloaded)
    db.commit()

    # Create complaint
    complaint = Complaint(
        complaint_number=f"TKT-QUEUE-{uid}",
        customer_email="user@test.com",
        subject="Charge issue",
        description="Double payment problem",
        category="Billing",
        status="NEW"
    )
    db.add(complaint)
    db.commit()
    db.refresh(complaint)

    # Assign or enqueue
    res = assignment_service.assign_to_agent_or_queue(
        db=db,
        complaint=complaint,
        department_id=dept.id,
        team_id=team_pay.id,
        required_skills=["payments"]
    )

    # Verification:
    # 1. No suitable agent exists
    assert res["assigned"] is False
    assert res["team_queue"] is True
    assert team_pay.name in res["queue_name"]

    # 2. Do not lose complaint - safely preserved in database
    db.refresh(complaint)
    assert complaint.id is not None
    assert complaint.department_id == dept.id
    assert complaint.team_id == team_pay.id
    assert complaint.assigned_agent_id is None
    assert complaint.status in ("ROUTED", "NEW")
