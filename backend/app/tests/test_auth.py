def test_login_success(client):
    res = client.post("/api/auth/login", json={"email": "agent@complaints.io", "password": "agent123"})
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["name"] == "Testing Agent"

def test_login_invalid(client):
    res = client.post("/api/auth/login", json={"email": "agent@complaints.io", "password": "wrongpassword"})
    assert res.status_code == 401

def test_current_user(client, auth_headers):
    res = client.get("/api/auth/me", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["email"] == "agent@complaints.io"
    assert res.json()["role"] == "ADMIN"

def test_rbac_admin_allowed(client, auth_headers):
    # Testing Agent has role ADMIN, so admin route should succeed
    res = client.get("/api/auth/admin/users", headers=auth_headers)
    assert res.status_code == 200
    assert isinstance(res.json(), list)

def test_rbac_customer_forbidden(client):
    # Register customer
    reg_res = client.post("/api/auth/register", json={
        "name": "Customer User",
        "email": "cust@example.com",
        "password": "customerpass",
        "role": "CUSTOMER"
    })
    assert reg_res.status_code == 200
    assert reg_res.json()["role"] == "CUSTOMER"

    # Login as customer
    login_res = client.post("/api/auth/login", json={"email": "cust@example.com", "password": "customerpass"})
    token = login_res.json()["access_token"]
    cust_headers = {"Authorization": f"Bearer {token}"}

    # Attempt to access ADMIN-only route -> Should get 403 Forbidden!
    forbidden_res = client.get("/api/auth/admin/users", headers=cust_headers)
    assert forbidden_res.status_code == 403
    assert "Access denied" in forbidden_res.json()["detail"]
