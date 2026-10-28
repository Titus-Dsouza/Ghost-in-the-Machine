"""Tests for the Ghost in the Machine Flask backend.

Tests use the Flask test client only — no network calls to Gemini are made.
The Gemini client is faked so the suite runs without an API key.
"""

import pytest

import app as app_module


@pytest.fixture
def client():
    app_module.app.testing = True
    return app_module.app.test_client()


def _no_gemini_key(monkeypatch):
    """Force the backend to behave as if no GEMINI_API_KEY is configured."""
    monkeypatch.setattr(app_module, "GEMINI_API_KEY", None)
    app_module._gemini_client = None


def _fake_gemini_client(monkeypatch, reply="Boo! I am a ghostly Gemini response."):
    """Install a fake Gemini client that returns a fixed reply."""

    class FakeResponse:
        text = reply

    class FakeModels:
        def generate_content(self, model, contents, config=None):
            return FakeResponse()

    class FakeClient:
        models = FakeModels()

    monkeypatch.setattr(app_module, "GEMINI_API_KEY", "test-key-123")
    app_module._gemini_client = None
    monkeypatch.setattr(app_module, "get_gemini_client", lambda: FakeClient())


# ---------------------------------------------------------------------------
# Frontend serving
# ---------------------------------------------------------------------------
def test_index_serves_html(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.content_type.startswith("text/html")
    body = response.data.decode("utf-8")
    assert "GHOST IN THE MACHINE" in body
    assert "/frontend/css/style.css" in body
    assert "/frontend/js/script.js" in body


def test_static_assets_served(client):
    for path in [
        "/frontend/css/style.css",
        "/frontend/js/script.js",
        "/frontend/images/ghost.svg",
        "/frontend/images/ghost-happy.svg",
        "/frontend/images/pumpkin.svg",
        "/frontend/images/bat.svg",
    ]:
        response = client.get(path)
        assert response.status_code == 200, f"{path} returned {response.status_code}"


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------
def test_health_without_key(client, monkeypatch):
    _no_gemini_key(monkeypatch)
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "ok"
    assert data["gemini_configured"] is False
    assert data["model"] is None


def test_health_with_key(client, monkeypatch):
    monkeypatch.setattr(app_module, "GEMINI_API_KEY", "test-key-123")
    app_module._gemini_client = None
    response = client.get("/api/health")
    data = response.get_json()
    assert data["gemini_configured"] is True
    assert data["model"] == "gemini-1.5-flash"
    # No secret values are leaked
    text = response.data.decode("utf-8")
    assert "AIza" not in text


# ---------------------------------------------------------------------------
# Chat validation
# ---------------------------------------------------------------------------
def test_chat_missing_message(client, monkeypatch):
    _no_gemini_key(monkeypatch)
    response = client.post("/api/chat", json={})
    assert response.status_code == 400
    assert "error" in response.get_json()


def test_chat_empty_message(client, monkeypatch):
    _no_gemini_key(monkeypatch)
    response = client.post("/api/chat", json={"message": "   "})
    assert response.status_code == 400
    assert "error" in response.get_json()


def test_chat_non_json(client, monkeypatch):
    _no_gemini_key(monkeypatch)
    response = client.post(
        "/api/chat", data="not json", content_type="application/json"
    )
    assert response.status_code == 400


# ---------------------------------------------------------------------------
# Missing key → clear error, never a faked AI success
# ---------------------------------------------------------------------------
def test_chat_without_key_returns_setup_error(client, monkeypatch):
    _no_gemini_key(monkeypatch)
    response = client.post("/api/chat", json={"message": "Hello ghost"})
    assert response.status_code == 503
    data = response.get_json()
    assert "error" in data
    assert "GEMINI_API_KEY" in data["error"]
    assert "response" not in data


def test_story_without_key_returns_setup_error(client, monkeypatch):
    _no_gemini_key(monkeypatch)
    response = client.post("/api/story")
    assert response.status_code == 503
    assert "error" in response.get_json()


# ---------------------------------------------------------------------------
# Happy path with faked Gemini
# ---------------------------------------------------------------------------
def test_chat_returns_gemini_response(client, monkeypatch):
    _fake_gemini_client(monkeypatch, reply="Beware the missing semicolon!")
    response = client.post(
        "/api/chat",
        json={"message": "Why is my code haunted?", "conversation": []},
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["response"] == "Beware the missing semicolon!"
    assert "error" not in data


def test_chat_sends_conversation_context(client, monkeypatch):
    captured = {}

    class FakeResponse:
        text = "Context acknowledged."

    class FakeModels:
        def generate_content(self, model, contents, config=None):
            captured["contents"] = contents
            return FakeResponse()

    class FakeClient:
        models = FakeModels()

    monkeypatch.setattr(app_module, "GEMINI_API_KEY", "test-key-123")
    app_module._gemini_client = None
    monkeypatch.setattr(app_module, "get_gemini_client", lambda: FakeClient())

    client.post(
        "/api/chat",
        json={
            "message": "Again?",
            "conversation": [
                {"role": "user", "content": "Hello"},
                {"role": "model", "content": "Hi there"},
            ],
        },
    )
    assert captured["contents"][-1] == {"role": "user", "parts": [{"text": "Again?"}]}
    roles = [c["role"] for c in captured["contents"]]
    assert roles == ["user", "model", "user"]


def test_clear_command(client, monkeypatch):
    _no_gemini_key(monkeypatch)
    response = client.post("/api/chat", json={"message": "/clear"})
    assert response.status_code == 200
    assert response.get_json()["response"] == "__CLEAR__"


def test_help_command(client, monkeypatch):
    _no_gemini_key(monkeypatch)
    response = client.post("/api/chat", json={"message": "/help"})
    assert response.status_code == 200
    assert "/story" in response.get_json()["response"]


def test_story_with_faked_gemini(client, monkeypatch):
    _fake_gemini_client(monkeypatch, reply="Once upon a midnight compile…")
    response = client.post("/api/story")
    assert response.status_code == 200
    data = response.get_json()
    assert data["story"] == "Once upon a midnight compile…"