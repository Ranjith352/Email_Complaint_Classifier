import pytest
from app.services.routing_service import routing_service
from app.models.organization import Department, Team

def test_department_multiple_teams_routing(db):
    # 1. Setup Finance with 3 distinct teams as per user spec
    fin_dept = Department(
        name="Finance Test",
        code="FINTST",
        keywords=["refund", "billing", "invoice", "payment"]
    )
    db.add(fin_dept)
    db.commit()
    db.refresh(fin_dept)

    t_bill = Team(
        department_id=fin_dept.id,
        name="Billing Team",
        code="FIN-BILL",
        keywords=["invoice", "statement", "billing error"]
    )
    t_pay = Team(
        department_id=fin_dept.id,
        name="Payments Team",
        code="FIN-PAY",
        keywords=["payment gateway", "card charged", "processing fee"]
    )
    t_ref = Team(
        department_id=fin_dept.id,
        name="Refund Team",
        code="FIN-REF",
        keywords=["refund", "reimbursement", "chargeback"]
    )
    db.add_all([t_bill, t_pay, t_ref])
    db.commit()
    db.refresh(t_bill)
    db.refresh(t_pay)
    db.refresh(t_ref)

    # Verify 1-to-many relationship
    assert len(fin_dept.teams) == 3

    # 2. Test direct routing by team name
    dept_id, team_id, dept_name = routing_service.route_complaint(db, "Finance Test", "Refund Team")
    assert dept_id == fin_dept.id
    assert team_id == t_ref.id

    # 3. Test content-driven team routing via dynamic keywords
    d_id, t_id, _ = routing_service.route_complaint(
        db,
        department_name="Finance Test",
        text_content="I need an immediate refund for my cancelled order"
    )
    assert d_id == fin_dept.id
    assert t_id == t_ref.id

    # 4. Test IT department with Technical Support, Network Team, Application Support, Cybersecurity Team
    it_dept = Department(
        name="IT Test",
        code="ITTST",
        keywords=["server", "bug", "wifi", "security", "network"]
    )
    db.add(it_dept)
    db.commit()
    db.refresh(it_dept)

    it_teams = [
        Team(department_id=it_dept.id, name="Technical Support", code="IT-TECH", keywords=["hardware", "crash", "screen"]),
        Team(department_id=it_dept.id, name="Network Team", code="IT-NET", keywords=["network", "wifi", "vpn"]),
        Team(department_id=it_dept.id, name="Application Support", code="IT-APP", keywords=["software", "portal bug"]),
        Team(department_id=it_dept.id, name="Cybersecurity Team", code="IT-SEC", keywords=["phishing", "compromised", "hacked"])
    ]
    db.add_all(it_teams)
    db.commit()

    # Route network outage complaint
    it_id, net_team_id, _ = routing_service.route_complaint(
        db,
        department_name="IT Test",
        text_content="Our office VPN and wifi connection is completely down"
    )
    assert it_id == it_dept.id
    network_team = next(t for t in it_teams if t.name == "Network Team")
    assert net_team_id == network_team.id
