import pytest


def test_register_user(client):
    response = client.post("/api/v1/auth/register", json={
        "email": "new@example.com",
        "username": "newuser",
        "password": "password123",
        "full_name": "New User",
    })
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["user"]["email"] == "new@example.com"


def test_register_duplicate_email(client, registered_user):
    response = client.post("/api/v1/auth/register", json={
        "email": "test@example.com",
        "username": "different",
        "password": "password123",
    })
    assert response.status_code == 409


def test_login_success(client, registered_user):
    response = client.post("/api/v1/auth/login", json={
        "email": "test@example.com",
        "password": "password123",
    })
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_login_wrong_password(client, registered_user):
    response = client.post("/api/v1/auth/login", json={
        "email": "test@example.com",
        "password": "wrongpassword",
    })
    assert response.status_code == 400


def test_get_me(client, auth_headers):
    response = client.get("/api/v1/auth/me", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["email"] == "test@example.com"


def test_update_me(client, auth_headers):
    response = client.put("/api/v1/auth/me", json={
        "full_name": "Updated Name"
    }, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["full_name"] == "Updated Name"


def test_unauthorized_access(client):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 403


def test_refresh_token(client, registered_user):
    refresh_token = registered_user["refresh_token"]
    response = client.post("/api/v1/auth/refresh", json={
        "refresh_token": refresh_token
    })
    assert response.status_code == 200
    assert "access_token" in response.json()
