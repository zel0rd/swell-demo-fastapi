from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_page_health_and_assets():
    assert "생각이 문장이 되는 곳" in client.get("/").text
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


def test_analysis_counts_unicode_and_repeated_words():
    response = client.post("/api/analyze", json={"text": "파도 파도. 생각!\n\nHello hello?"})
    assert response.status_code == 200
    data = response.json()
    assert data["words"] == 5
    assert data["sentences"] == 3
    assert data["paragraphs"] == 2
    assert {x["word"]: x["count"] for x in data["keywords"]} == {"파도": 2, "hello": 2, "생각": 1}
    assert data["reading_seconds"] == 2
    assert response.headers["cache-control"] == "no-store"
    assert "text" not in data


def test_analysis_rejects_empty_or_oversize_input():
    for value in ["", "   ", "x" * 20001]:
        assert client.post("/api/analyze", json={"text": value}).status_code == 422
    assert client.post("/api/analyze", json={}).status_code == 422
