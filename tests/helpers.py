from fastapi.testclient import TestClient


def register(client: TestClient, email: str, name: str = "Rudra") -> dict:
    response = client.post(
        "/api/users/register",
        json={"name": name, "email": email, "password": "secret123", "mobile": "9988776655"},
    )
    assert response.status_code == 201, response.text
    return response.json()


def login(client: TestClient, email: str, password: str = "secret123") -> str:
    response = client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}
