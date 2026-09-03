def test_departments_api(client):
    res = client.get("/api/departments/")
    assert res.status_code == 200
    assert isinstance(res.json(), list)

def test_configurable_department_crud(client):
    # 1. Create a new configurable department
    create_res = client.post("/api/departments/", json={
        "name": "Procurement Test",
        "code": "PROCTEST",
        "description": "Vendor and supply contracts",
        "keywords": ["supplier", "rfp", "vendor invoice"],
        "sla_hours": 18
    })
    assert create_res.status_code == 200
    dept_id = create_res.json()["id"]
    assert create_res.json()["name"] == "Procurement Test"
    assert create_res.json()["sla_hours"] == 18

    # 2. Update the department configuration
    update_res = client.put(f"/api/departments/{dept_id}", json={
        "sla_hours": 12,
        "lead_name": "New Procurement Lead"
    })
    assert update_res.status_code == 200
    assert update_res.json()["sla_hours"] == 12
    assert update_res.json()["lead_name"] == "New Procurement Lead"

    # 3. Fetch by ID
    get_res = client.get(f"/api/departments/{dept_id}")
    assert get_res.status_code == 200
    assert get_res.json()["code"] == "PROCTEST"

def test_teams_api(client):
    res = client.get("/api/teams/")
    assert res.status_code == 200
    assert isinstance(res.json(), list)

def test_agents_api(client):
    res = client.get("/api/agents/")
    assert res.status_code == 200
    assert isinstance(res.json(), list)

def test_analytics_api(client):
    res = client.get("/api/analytics/dashboard")
    assert res.status_code == 200
    data = res.json()
    assert "kpis" in data
    assert "department_volumes" in data

def test_knowledge_api(client):
    res = client.get("/api/knowledge/")
    assert res.status_code == 200
    assert isinstance(res.json(), list)
