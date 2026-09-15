import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import create_access_token

client = TestClient(app)

@pytest.fixture
def auth_headers():
    token = create_access_token(subject=1, role="ADMIN")
    return {"Authorization": f"Bearer {token}"}

# =========================================================================
# 68. Test Authentication Endpoints
# =========================================================================

def test_auth_register_and_login():
    import uuid
    unique_email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    # Register
    reg_res = client.post("/api/auth/register", json={
        "name": "Alex Triage",
        "email": unique_email,
        "password": "Password123!",
        "role": "AGENT"
    })
    assert reg_res.status_code == 201
    assert reg_res.json()["email"] == unique_email

    # Login
    login_res = client.post("/api/auth/login", json={
        "email": unique_email,
        "password": "Password123!"
    })
    assert login_res.status_code == 200
    assert "access_token" in login_res.json()

    # Me
    token = login_res.json()["access_token"]
    me_res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    assert me_res.json()["email"] == unique_email

# =========================================================================
# 68. Test Complaints Endpoints
# =========================================================================

def test_complaint_crud_and_actions(auth_headers):
    # 1. POST /api/complaints
    create_res = client.post("/api/complaints", json={
        "subject": "System billing discrepancy error",
        "description": "Double billed for renewal invoice #9923.",
        "customer_email": "customer.test@example.com",
        "customer_name": "Test Customer"
    })
    assert create_res.status_code in (200, 201)
    comp_id = create_res.json()["id"]

    # 2. GET /api/complaints
    list_res = client.get("/api/complaints")
    assert list_res.status_code == 200
    assert any(c["id"] == comp_id for c in list_res.json())

    # 3. GET /api/complaints/{id}
    detail_res = client.get(f"/api/complaints/{comp_id}")
    assert detail_res.status_code == 200

    # 4. PUT /api/complaints/{id}
    put_res = client.put(f"/api/complaints/{comp_id}", json={
        "priority": "HIGH",
        "category": "Billing"
    })
    assert put_res.status_code == 200
    assert put_res.json()["priority"] == "HIGH"

    # 5. POST /api/complaints/{id}/assign
    assign_res = client.post(f"/api/complaints/{comp_id}/assign", json={
        "reason": "Routing to senior specialist"
    }, headers=auth_headers)
    assert assign_res.status_code == 200

    # 6. POST /api/complaints/{id}/reassign
    reassign_res = client.post(f"/api/complaints/{comp_id}/reassign", json={
        "reason": "Workload balancing"
    }, headers=auth_headers)
    assert reassign_res.status_code == 200

    # 7. POST /api/complaints/{id}/escalate
    esc_res = client.post(f"/api/complaints/{comp_id}/escalate", json={
        "reason": "Customer is waiting on urgent transaction unlock"
    })
    assert esc_res.status_code == 200

    # 8. POST /api/complaints/{id}/status
    status_res = client.post(f"/api/complaints/{comp_id}/status", json={
        "status": "IN_PROGRESS"
    })
    assert status_res.status_code == 200

    # 9. DELETE /api/complaints/{id}
    del_res = client.delete(f"/api/complaints/{comp_id}")
    assert del_res.status_code == 200
    assert del_res.json()["success"] is True

# =========================================================================
# 68. Test AI Endpoints
# =========================================================================

def test_ai_endpoints():
    # POST /api/ai/analyze
    analyze_res = client.post("/api/ai/analyze", json={
        "subject": "App crashes on login screen",
        "body": "Whenever I click submit, error 500 pops up immediately."
    })
    assert analyze_res.status_code == 200
    assert "classification" in analyze_res.json() or "category" in analyze_res.json() or "metadata" in analyze_res.json()

    # POST /api/ai/summarize
    sum_res = client.post("/api/ai/summarize", json={
        "text": "Customer contacted regarding prolonged outage during transaction settlement."
    })
    assert sum_res.status_code == 200
    assert "summary" in sum_res.json()

    # POST /api/ai/generate-response
    gen_res = client.post("/api/ai/generate-response", json={
        "subject": "Delay in refund processing",
        "body": "My refund was approved 5 days ago but hasn't arrived.",
        "department": "Finance"
    })
    assert gen_res.status_code == 200

    # POST /api/ai/similar
    sim_res = client.post("/api/ai/similar", json={
        "subject": "Login timeout issue",
        "body": "Cannot login to dashboard"
    })
    assert sim_res.status_code == 200
    assert "similar_complaints" in sim_res.json()

    # POST /api/ai/recommend-resolution
    rec_res = client.post("/api/ai/recommend-resolution", json={
        "complaint_text": "Customer requested full refund due to duplicate billing charges.",
        "category": "Billing"
    })
    assert rec_res.status_code == 200
    res_data = rec_res.json()
    assert "recommended_steps" in res_data or "recommendations" in res_data or "steps" in res_data


# =========================================================================
# 68. Test Departments, Teams, Agents
# =========================================================================

def test_departments_teams_agents():
    # GET /api/departments
    dept_res = client.get("/api/departments")
    assert dept_res.status_code == 200
    assert len(dept_res.json()) >= 1

    # POST /api/departments
    import uuid
    code = f"T{uuid.uuid4().hex[:4].upper()}"
    new_dept_res = client.post("/api/departments", json={
        "name": f"Operations Test {code}",
        "code": code,
        "description": "Test Department"
    })
    assert new_dept_res.status_code == 201
    d_id = new_dept_res.json()["id"]

    # PUT /api/departments/{id}
    put_dept = client.put(f"/api/departments/{d_id}", json={
        "description": "Updated Description"
    })
    assert put_dept.status_code == 200
    assert put_dept.json()["description"] == "Updated Description"

    # GET /api/teams
    teams_res = client.get("/api/teams")
    assert teams_res.status_code == 200

    # POST /api/teams
    new_team_res = client.post("/api/teams", json={
        "department_id": d_id,
        "name": f"Test Squad {code}",
        "code": f"SQD-{code}"
    })
    assert new_team_res.status_code == 201

    # GET /api/agents
    agents_res = client.get("/api/agents")
    assert agents_res.status_code == 200

    # POST /api/agents
    agent_email = f"agent_{uuid.uuid4().hex[:6]}@company.com"
    new_agent_res = client.post("/api/agents", json={
        "name": "Jane Specialist",
        "email": agent_email,
        "department_id": d_id
    })
    assert new_agent_res.status_code == 201

# =========================================================================
# 68. Test Gmail / Emails Endpoints
# =========================================================================

def test_emails_endpoints():
    status_res = client.get("/api/emails/status")
    assert status_res.status_code == 200

    sync_res = client.post("/api/emails/sync")
    assert sync_res.status_code == 200

# =========================================================================
# 68. Test Analytics Endpoints
# =========================================================================

def test_analytics_endpoints():
    endpoints = [
        "/api/analytics/overview",
        "/api/analytics/departments",
        "/api/analytics/categories",
        "/api/analytics/sentiment",
        "/api/analytics/priority",
        "/api/analytics/sla",
        "/api/analytics/agents",
        "/api/analytics/ai-performance"
    ]
    for ep in endpoints:
        res = client.get(ep)
        assert res.status_code == 200, f"Failed for {ep}: {res.text}"

# =========================================================================
# 68. Test Notifications & Knowledge Base
# =========================================================================

def test_notifications_and_knowledge():
    # GET /api/notifications
    notif_res = client.get("/api/notifications")
    assert notif_res.status_code == 200

    # POST /api/knowledge
    import uuid
    k_code = uuid.uuid4().hex[:6]
    k_create = client.post("/api/knowledge", json={
        "title": f"Refund Policy v2 {k_code}",
        "document_type": "POLICY",
        "department": "Finance",
        "content": "All eligible refund requests must be verified against transaction logs within 48 hours."
    })
    assert k_create.status_code == 201
    k_id = k_create.json()["id"]

    # GET /api/knowledge
    k_list = client.get("/api/knowledge")
    assert k_list.status_code == 200
    assert any(doc["id"] == k_id for doc in k_list.json())

    # DELETE /api/knowledge/{id}
    k_del = client.delete(f"/api/knowledge/{k_id}")
    assert k_del.status_code == 200
    assert k_del.json()["success"] is True

# =========================================================================
# 69. Test Standardized Error Handling
# =========================================================================

def test_standardized_error_handling():
    # 404 Not Found error format
    res = client.get("/api/complaints/999999")
    assert res.status_code == 404
    body = res.json()
    assert body["success"] is False
    assert body["error_code"] == "COMPLAINT_NOT_FOUND"
    assert "not found" in body["message"].lower()

    # 400 Bad Request error format
    dup_res = client.post("/api/auth/register", json={
        "name": "Duplicate Admin",
        "email": "admin@complaints.io",
        "password": "Password123!"
    })
    assert dup_res.status_code == 400
    dup_body = dup_res.json()
    assert dup_body["success"] is False
    assert dup_body["error_code"] in ("BAD_REQUEST", "RESOURCE_ALREADY_EXISTS")
