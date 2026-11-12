"""Health endpoint tests."""

from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import create_app


def test_health_returns_ok(monkeypatch) -> None:
    monkeypatch.setenv("APP_NAME", "front-desk-backend")
    get_settings.cache_clear()
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "front-desk-backend",
    }
    get_settings.cache_clear()


def test_cors_origins_are_split_from_environment(monkeypatch) -> None:
    monkeypatch.setenv(
        "CORS_ALLOWED_ORIGINS",
        "http://localhost:3000, http://127.0.0.1:3000",
    )
    get_settings.cache_clear()

    settings = get_settings()

    assert settings.cors_origins == [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    get_settings.cache_clear()
