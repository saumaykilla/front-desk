"""Readiness checks do not contact external services."""

import json

from livekit.agents import AgentServer

from config.settings import assess_readiness
from prompts import load_system_prompt
from tools import load_tools
from agent import entrypoint, server
from worker import main


def test_readiness_reports_every_missing_variable() -> None:
    report = assess_readiness({})

    assert report.ready is False
    assert report.livekit_connected is False
    assert report.google_connected is False
    assert report.missing == [
        "LIVEKIT_URL",
        "LIVEKIT_API_KEY",
        "LIVEKIT_API_SECRET",
        "GOOGLE_API_KEY",
        "BACKEND_API_URL",
        "BACKEND_API_TOKEN",
    ]


def test_readiness_is_ready_when_required_values_are_present() -> None:
    report = assess_readiness(
        {
            "LIVEKIT_URL": "wss://example.livekit.cloud",
            "LIVEKIT_API_KEY": "key",
            "LIVEKIT_API_SECRET": "secret",
            "GOOGLE_API_KEY": "google",
            "BACKEND_API_URL": "http://127.0.0.1:8000",
            "BACKEND_API_TOKEN": "agent-token",
        }
    )

    assert report.ready is True
    assert report.missing == []
    assert report.livekit_connected is False


def test_agent_module_exposes_canonical_livekit_entrypoint() -> None:
    assert isinstance(server, AgentServer)
    assert callable(entrypoint)


def test_blank_values_count_as_missing() -> None:
    report = assess_readiness(
        {
            "LIVEKIT_URL": "   ",
            "LIVEKIT_API_KEY": "key",
            "LIVEKIT_API_SECRET": "secret",
            "GOOGLE_API_KEY": "google",
            "BACKEND_API_URL": "http://127.0.0.1:8000",
            "BACKEND_API_TOKEN": "agent-token",
        }
    )

    assert report.missing == ["LIVEKIT_URL"]


def test_system_prompt_and_guest_booking_tool_are_registered() -> None:
    prompt = load_system_prompt()

    assert "confirm the spelling" in prompt
    assert "check-in date confirmed" in prompt

    class StubBackendClient:
        async def lookup_booking(self, **_kwargs):
            return {"outcome": "no_match", "matches": []}

    tools = load_tools("nolita", StubBackendClient())
    assert len(tools) == 1
    assert tools[0].id == "find_guest_booking"


def test_worker_exits_before_startup_when_credentials_are_missing(capsys, monkeypatch) -> None:
    monkeypatch.delenv("LIVEKIT_URL", raising=False)
    monkeypatch.delenv("LIVEKIT_API_KEY", raising=False)
    monkeypatch.delenv("LIVEKIT_API_SECRET", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("BACKEND_API_URL", raising=False)
    monkeypatch.delenv("BACKEND_API_TOKEN", raising=False)

    from config.settings import get_settings

    get_settings.cache_clear()
    exit_code = main([])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Missing required environment variables" in captured.err
    assert "No LiveKit or Google connection was attempted" in captured.err
    get_settings.cache_clear()


def test_readiness_command_prints_not_connected(capsys, monkeypatch) -> None:
    for name in (
        "LIVEKIT_URL",
        "LIVEKIT_API_KEY",
        "LIVEKIT_API_SECRET",
        "GOOGLE_API_KEY",
        "BACKEND_API_URL",
        "BACKEND_API_TOKEN",
    ):
        monkeypatch.setenv(name, "present")

    from config.settings import get_settings

    get_settings.cache_clear()
    exit_code = main(["readiness"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["ready"] is True
    assert payload["livekit_connected"] is False
    assert payload["google_connected"] is False
    get_settings.cache_clear()
