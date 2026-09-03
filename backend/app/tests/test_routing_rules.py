import pytest
from app.models.organization import Department, Team, RoutingRule
from app.services.routing_service import routing_service

@pytest.fixture(autouse=True)
def setup_routing_rules_environment(db):
    # Ensure departments and teams exist for tests
    dept_specs = [
        {"name": "Finance", "code": "FIN", "teams": ["Payments", "Refunds", "Billing"]},
        {"name": "IT", "code": "IT", "teams": ["Application Support", "Network Team", "Technical Support"]},
        {"name": "Security", "code": "SEC", "teams": ["Incident Response", "Threat Detection"]},
        {"name": "HR", "code": "HR", "teams": ["Payroll", "Employee Relations"]},
        {"name": "Logistics", "code": "LOG", "teams": ["Delivery & Tracking", "Warehousing"]},
        {"name": "Executive", "code": "EXEC", "teams": ["Rapid Response"]}
    ]

    for ds in dept_specs:
        dept = db.query(Department).filter(Department.name == ds["name"]).first()
        if not dept:
            dept = Department(name=ds["name"], code=ds["code"], is_active=True)
            db.add(dept)
            db.commit()
            db.refresh(dept)
        for t_name in ds["teams"]:
            team = db.query(Team).filter(Team.department_id == dept.id, Team.name == t_name).first()
            if not team:
                db.add(Team(department_id=dept.id, name=t_name, code=f"{dept.code}-{t_name[:4].upper()}", is_active=True))
    db.commit()

    # Seed the user's exact example rules if missing
    user_rules = [
        {"trigger_keyword": "Billing", "department_name": "Finance", "team_name": None},
        {"trigger_keyword": "Payment", "department_name": "Finance", "team_name": "Payments"},
        {"trigger_keyword": "Refund", "department_name": "Finance", "team_name": "Refunds"},
        {"trigger_keyword": "Login", "department_name": "IT", "team_name": "Application Support"},
        {"trigger_keyword": "Network", "department_name": "IT", "team_name": "Network Team"},
        {"trigger_keyword": "Security Breach", "department_name": "Security", "team_name": "Incident Response"},
        {"trigger_keyword": "Payroll", "department_name": "HR", "team_name": "Payroll"},
        {"trigger_keyword": "Leave", "department_name": "HR", "team_name": "Employee Relations"},
        {"trigger_keyword": "Delivery", "department_name": "Logistics", "team_name": "Delivery & Tracking"}
    ]
    for r in user_rules:
        existing = db.query(RoutingRule).filter(RoutingRule.trigger_keyword == r["trigger_keyword"]).first()
        if not existing:
            db.add(RoutingRule(**r, is_active=True))
    db.commit()

def test_crud_routing_rules_api(client, db):
    # 1. Create a new configurable routing rule via API
    new_rule_payload = {
        "trigger_keyword": "VIP Escalation",
        "department_name": "Executive",
        "team_name": "Rapid Response",
        "priority_override": "CRITICAL",
        "sla_hours": 2,
        "description": "VIP client escalations route to Executive / Rapid Response",
        "is_active": True
    }
    create_res = client.post("/api/routing-rules/", json=new_rule_payload)
    assert create_res.status_code == 201
    created_data = create_res.json()
    rule_id = created_data["id"]
    assert created_data["trigger_keyword"] == "VIP Escalation"
    assert created_data["department_name"] == "Executive"
    assert created_data["team_name"] == "Rapid Response"

    # 2. List all configurable routing rules
    list_res = client.get("/api/routing-rules/")
    assert list_res.status_code == 200
    rules = list_res.json()
    assert len(rules) >= 10
    assert any(r["trigger_keyword"] == "VIP Escalation" for r in rules)

    # 3. Update rule
    update_res = client.put(f"/api/routing-rules/{rule_id}", json={
        "sla_hours": 1,
        "description": "Updated ultra-urgent SLA"
    })
    assert update_res.status_code == 200
    assert update_res.json()["sla_hours"] == 1

    # 4. Delete rule
    del_res = client.delete(f"/api/routing-rules/{rule_id}")
    assert del_res.status_code == 200

    # Verify deleted
    get_res = client.get(f"/api/routing-rules/{rule_id}")
    assert get_res.status_code == 404

def test_exact_user_routing_rules_matching(db):
    # User's exact examples:
    # Billing -> Finance
    # Payment -> Finance / Payments
    # Refund -> Finance / Refunds
    # Login -> IT / Application Support
    # Network -> IT / Network
    # Security Breach -> Security
    # Payroll -> HR / Payroll
    # Leave -> HR / Employee Services
    # Delivery -> Logistics

    test_cases = [
        ("I have a question regarding my Billing statement", "Finance", None),
        ("Payment failed during processing", "Finance", "Payments"),
        ("I request a full Refund for this transaction", "Finance", "Refunds"),
        ("Cannot Login to my portal account", "IT", "Application Support"),
        ("Office Network connectivity is broken", "IT", "Network Team"),
        ("URGENT: Security Breach detected in user accounts", "Security", "Incident Response"),
        ("Discrepancy in my monthly Payroll deposit", "HR", "Payroll"),
        ("Submitting sick Leave request for next week", "HR", "Employee Relations"),
        ("Package Delivery arrived damaged and late", "Logistics", "Delivery & Tracking"),
    ]

    for text, expected_dept, expected_team in test_cases:
        dept_id, team_id, dept_name = routing_service.route_complaint(
            db=db,
            text_content=text
        )
        assert dept_name == expected_dept, f"Failed for '{text}': expected dept {expected_dept}, got {dept_name}"
        if expected_team:
            team = db.query(Team).filter(Team.id == team_id).first()
            assert team is not None, f"Team id {team_id} not found for '{text}'"
            assert team.name == expected_team, f"Failed for '{text}': expected team {expected_team}, got {team.name}"

def test_dynamic_runtime_rule_addition(client, db):
    # Create a dynamic custom rule at runtime in the database
    custom_rule = RoutingRule(
        trigger_keyword="Hardware Replacement",
        department_name="IT",
        team_name="Technical Support",
        is_active=True
    )
    db.add(custom_rule)
    db.commit()

    # Verify routing engine immediately honors the new database rule
    dept_id, team_id, dept_name = routing_service.route_complaint(
        db=db,
        text_content="My monitor broke, I need a Hardware Replacement immediately"
    )
    assert dept_name == "IT"
    team = db.query(Team).filter(Team.id == team_id).first()
    assert team.name == "Technical Support"
