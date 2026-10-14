from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_page_health_and_assets():
    assert "DEPLOYMENT PLAYGROUND" in client.get("/").text
    assert client.get("/static/app.js").status_code == 200
    assert client.get("/static/style.css").status_code == 200
    response = client.get("/health")
    assert response.json()["status"] == "ok"
    assert response.headers["cache-control"] == "no-store"
    assert client.get("/docs").status_code == 200
    assert client.get("/missing-page").status_code == 404


def test_metadata_is_runtime_and_allowlisted(monkeypatch):
    monkeypatch.setenv("APP_VERSION", "test-version")
    monkeypatch.setenv("DEMO_REGION", "test-region")
    monkeypatch.setenv("SECRET_SENTINEL", "must-not-leak")
    data = client.get("/api/info").json()
    assert data["version"] == "test-version"
    assert data["region"] == "test-region"
    assert "must-not-leak" not in str(data)
    assert set(data) == {"name", "version", "region", "framework"}


def test_greeting_and_validation():
    assert "파도" in client.get("/api/hello", params={"name": "파도"}).json()["message"]
    assert client.get("/api/hello", params={"name": "x" * 101}).status_code == 422
    assert client.post("/api/echo", json={"message": "안녕"}).json() == {"message": "안녕", "length": 2}
    for payload in [{}, {"message": ""}, {"message": "x" * 501}]:
        assert client.post("/api/echo", json=payload).status_code == 422
