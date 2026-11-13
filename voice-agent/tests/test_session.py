import pytest

from config.settings import Settings
from session import build_realtime_model


GOOGLE_GEMINI_LIVE_MODEL = "gemini-3.8-live"


def test_google_realtime_model_uses_google_plugin_and_configured_values(monkeypatch) -> None:
    captured = {}

    def fake_realtime_model(**kwargs):
        captured.update(kwargs)
        return object()

    monkeypatch.setattr("session.google.realtime.RealtimeModel", fake_realtime_model)
    settings = Settings(
        google_api_key="google-key",
        google_realtime_model="gemini-test-live",
        google_realtime_voice="Aoede",
    )

    model = build_realtime_model(settings)

    assert model is not None
    assert captured == {
        "api_key": "google-key",
        "api_version": "v1beta",
        "model": "gemini-test-live",
        "vertexai": False,
        "voice": "Aoede",
    }


def test_default_model_is_google_gemini_api_model() -> None:
    assert Settings.model_fields["google_realtime_model"].default == GOOGLE_GEMINI_LIVE_MODEL


def test_google_realtime_model_requires_google_api_key() -> None:
    settings = Settings(google_api_key=" ")

    with pytest.raises(
        ValueError,
        match="GOOGLE_API_KEY is required before creating a realtime model",
    ):
        build_realtime_model(settings)


def test_google_realtime_model_requires_a_nonblank_model_id() -> None:
    settings = Settings(google_api_key="google-key", google_realtime_model=" ")

    with pytest.raises(ValueError, match="GOOGLE_REALTIME_MODEL must not be blank"):
        build_realtime_model(settings)
