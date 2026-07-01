import json


def test_register_returns_400_for_missing_fields(client):
    response = client.post("/register", json={"name": "Alice"})
    assert response.status_code == 400
    assert response.json["error"].startswith("Missing")


def test_login_returns_400_for_malformed_json(client):
    response = client.post("/login", data="not-json", content_type="application/json")
    assert response.status_code == 400
    assert "JSON body required or malformed" in response.json["error"]


def test_login_returns_401_for_invalid_credentials(client):
    response = client.post("/login", json={"email": "noone@example.com", "password": "bad"})
    assert response.status_code == 401
    assert response.json["error"] == "Invalid credentials or unverified email"


def test_protected_profile_requires_jwt(client):
    response = client.get("/profile")
    assert response.status_code == 401
    assert response.json["msg"]


def test_role_protected_landlord_route_blocks_user(client, jwt_token):
    token = jwt_token(identity="1", role="user")
    response = client.get("/accommodations/landlord", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403
    assert response.json["error"] == "Forbidden"
