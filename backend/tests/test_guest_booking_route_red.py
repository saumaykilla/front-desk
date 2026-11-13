from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import create_app


def test_guest_booking_lookup_rejects_missing_agent_token(monkeypatch) -> None:
    monkeypatch.setenv("AGENT_API_TOKEN", "expected-secret")
    get_settings.cache_clear()
    client = TestClient(create_app())

    response = client.post(
        "/guest-bookings/lookup",
        json={
            "property": "nolita",
            "booking_reference": "42",
            "check_in_date": "2026-11-12",
        },
    )

    assert response.status_code == 401
    get_settings.cache_clear()
