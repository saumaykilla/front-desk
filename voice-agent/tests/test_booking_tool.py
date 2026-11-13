import pytest
from datetime import date
from inspect import signature
import httpx

from config.property_context import property_from_job_metadata
from config.settings import Settings
from prompts import load_system_prompt
from tools import make_find_guest_booking_tool
from tools.booking_client import BookingBackendClient, BookingBackendUnavailable


class FakeBackendClient:
    def __init__(self, result=None, error=None):
        self.result = result or {"outcome": "matched", "matches": []}
        self.error = error
        self.requests = []

    async def lookup_booking(self, **kwargs):
        self.requests.append(kwargs)
        if self.error:
            raise self.error
        return self.result


def test_property_is_allowlisted_from_livekit_job_metadata() -> None:
    assert property_from_job_metadata('{"property":"nolita"}') == "nolita"
    assert property_from_job_metadata('{"property":"nap_york"}') == "nap_york"
    assert property_from_job_metadata('{"property":"other"}') is None
    assert property_from_job_metadata("not-json") is None
    assert property_from_job_metadata(None) is None


@pytest.mark.anyio
async def test_tool_injects_property_without_exposing_it_as_a_model_argument() -> None:
    backend = FakeBackendClient()
    tool = make_find_guest_booking_tool("nap_york", backend)

    result = await tool._func(
        None,
        check_in_date="2026-11-12",
        full_name="Jordan Lee",
    )

    assert result["outcome"] == "matched"
    assert backend.requests == [
        {
            "property_id": "nap_york",
            "full_name": "Jordan Lee",
            "booking_reference": None,
            "check_in_date": date(2026, 11, 12),
        }
    ]
    assert "property_id" not in signature(tool._func).parameters
    assert "property" not in signature(tool._func).parameters


@pytest.mark.anyio
async def test_missing_property_and_backend_failure_never_claim_no_match() -> None:
    backend = FakeBackendClient(error=BookingBackendUnavailable())
    no_property_tool = make_find_guest_booking_tool(None, backend)
    unavailable_tool = make_find_guest_booking_tool("nolita", backend)

    missing_property = await no_property_tool._func(
        None,
        check_in_date="2026-11-12",
        booking_reference="00042",
    )
    backend_failure = await unavailable_tool._func(
        None,
        check_in_date="2026-11-12",
        booking_reference="00042",
    )

    assert missing_property["outcome"] == "unavailable"
    assert backend_failure["outcome"] == "unavailable"
    assert backend.requests[0]["property_id"] == "nolita"


def test_prompt_includes_current_new_york_date_for_today_lookup() -> None:
    assert "Current property-local date (America/New_York): 2026-11-12" in load_system_prompt(
        local_date="2026-11-12"
    )


@pytest.mark.anyio
async def test_backend_client_sends_bearer_and_only_returns_whitelisted_fields(monkeypatch) -> None:
    observed = {}

    class FakeAsyncClient:
        def __init__(self, **_kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return None

        async def aclose(self):
            return None

        async def post(self, url, *, json, headers):
            observed.update({"url": url, "payload": json, "headers": headers})
            return httpx.Response(
                200,
                request=httpx.Request("POST", url),
                json={
                    "outcome": "matched",
                    "matches": [
                        {
                            "guest_name": "Jordan Lee",
                            "check_in_date": "2026-11-12",
                            "state": "Started",
                            "reservation_id": "must-not-be-returned",
                        }
                    ],
                },
            )

    monkeypatch.setattr("tools.booking_client.httpx.AsyncClient", FakeAsyncClient)
    client = BookingBackendClient("https://backend.example.test", "shared-secret")

    result = await client.lookup_booking(
        property_id="nolita",
        full_name="Jordan Lee",
        booking_reference=None,
        check_in_date=date(2026, 11, 12),
    )
    await client.aclose()

    assert observed["url"] == "https://backend.example.test/guest-bookings/lookup"
    assert observed["headers"] == {"Authorization": "Bearer shared-secret"}
    assert observed["payload"]["property"] == "nolita"
    assert result == {
        "outcome": "matched",
        "matches": [
            {
                "guest_name": "Jordan Lee",
                "check_in_date": "2026-11-12",
                "state": "Started",
            }
        ],
    }
