import sqlite3
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient
import pytest

from gateway.app import main as gateway_main


client = TestClient(gateway_main.app)


@pytest.fixture(autouse=True)
def isolated_account_database(tmp_path, monkeypatch):
    monkeypatch.setattr(
        gateway_main.user_store,
        "DATABASE_PATH",
        str(tmp_path / "accounts.sqlite3"),
    )


def demo_credentials():
    return {
        "username": gateway_main.DEMO_USERNAME,
        "password": gateway_main.DEMO_PASSWORD,
    }


def test_demo_token_accepts_valid_credentials_and_documents_links():
    response = client.post("/auth/demo-token", json=demo_credentials())

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["_links"]["tasks"]["href"] == "/api/tasks"
    assert body["_links"]["categories"]["href"] == "/api/categories"


def test_demo_token_rejects_invalid_credentials():
    response = client.post(
        "/auth/demo-token",
        json={**demo_credentials(), "password": "senha-incorreta"},
    )

    assert response.status_code == 401


def test_user_can_register_and_password_is_stored_as_scrypt_hash():
    response = client.post(
        "/auth/register",
        json={"username": "new.student", "email": "new.student@example.com", "password": "Safe-password-42"},
    )

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["user"]["username"] == "new.student"
    assert body["access_token"]
    with sqlite3.connect(gateway_main.user_store.DATABASE_PATH) as connection:
        row = connection.execute(
            "SELECT email, password_hash FROM users WHERE username = ?",
            ("new.student",),
        ).fetchone()
    assert row[0] == "new.student@example.com"
    password_hash = row[1]
    assert gateway_main.user_store.authenticate_user("NEW.STUDENT", "Safe-password-42") == "new.student"
    assert gateway_main.user_store.authenticate_user("new.student", "incorrecta") is None
    assert password_hash.startswith("scrypt$")
    assert "Safe-password-42" not in password_hash


def test_registration_rejects_duplicate_normalized_username():
    first = client.post(
        "/auth/register",
        json={"username": "BrunoAluno", "email": "bruno@example.com", "password": "Safe-password-42"},
    )
    duplicate = client.post(
        "/auth/register",
        json={"username": "brunoaluno", "email": "other@example.com", "password": "Other-password-52"},
    )

    assert first.status_code == 201
    assert duplicate.status_code == 409


def test_registration_rejects_duplicate_email_ignoring_case():
    first = client.post(
        "/auth/register",
        json={"username": "first-user", "email": "shared@example.com", "password": "Safe-password-42"},
    )
    duplicate = client.post(
        "/auth/register",
        json={"username": "second-user", "email": "SHARED@example.com", "password": "Other-password-52"},
    )

    assert first.status_code == 201
    assert duplicate.status_code == 409


def test_registration_validates_username_and_password_length():
    response = client.post(
        "/auth/register",
        json={"username": "ab", "email": "not-an-email", "password": "short"},
    )

    assert response.status_code == 422


def test_registration_requires_a_valid_email_address():
    response = client.post(
        "/auth/register",
        json={"username": "valid-user", "email": "not-an-email", "password": "Safe-password-42"},
    )

    assert response.status_code == 422


def test_new_account_gets_token_for_current_user_endpoint():
    registration = client.post(
        "/auth/register",
        json={"username": "profile.student", "email": "profile@example.com", "password": "Safe-password-42"},
    )
    headers = {"Authorization": f"Bearer {registration.json()['access_token']}"}

    response = client.get("/auth/me", headers=headers)

    assert registration.status_code == 201
    assert response.status_code == 200
    assert response.json() == {"user": {"username": "profile.student"}}


def test_protected_routes_reject_missing_and_invalid_tokens():
    for route in ("/api/tasks", "/api/categories"):
        for headers in ({}, {"Authorization": "Bearer token-invalido"}):
            response = client.get(route, headers=headers)
            assert response.status_code == 401


def test_valid_token_can_access_protected_services_and_openapi_documents_bearer():
    token_response = client.post("/auth/token", json=demo_credentials())
    headers = {"Authorization": f"Bearer {token_response.json()['access_token']}"}
    tasks = [{"id": 3, "title": "Estudar", "category_id": "estudo", "completed": False}]
    categories = [{"id": "estudo", "name": "Estudo"}]

    with patch("gateway.app.main.call_service", new_callable=AsyncMock) as call_service:
        call_service.side_effect = [tasks, categories]
        tasks_response = client.get("/api/tasks", headers=headers)
        categories_response = client.get("/api/categories", headers=headers)

    assert tasks_response.status_code == 200
    assert tasks_response.json()["data"][0]["title"] == "Estudar"
    assert tasks_response.json()["data"][0]["_links"]["self"]["href"] == "/api/tasks/3"
    assert categories_response.status_code == 200
    assert categories_response.json()["data"][0]["id"] == "estudo"
    assert call_service.await_count == 2

    schema = client.get("/openapi.json").json()
    assert schema["components"]["securitySchemes"]["HTTPBearer"]["scheme"] == "bearer"
    assert schema["paths"]["/api/tasks"]["get"]["security"]
    assert "/auth/register" in schema["paths"]
    assert "/auth/token" in schema["paths"]
