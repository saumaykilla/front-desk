from datetime import date

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.config import Settings, get_settings
from app.integrations.mews.client import BookingCandidate
from app.api.dependencies import get_guest_booking_service
from app.main import create_app
from app.schemas.guest_booking import GuestBookingLookupRequest
from app.services.guest_booking_service import GuestBookingService, normalize_guest_name


def test_lookup_request_requires_exactly_one_search_key() -> None:
    with pytest.raises(ValidationError):
        GuestBookingLookupRequest(
            property="nolita",
            check_in_date="2026-11-12",
        )

    with pytest.raises(ValidationError):
        GuestBookingLookupRequest(
            property="nolita",
            full_name="Jordan Lee",
            booking_reference="00042",
            check_in_date="2026-11-12",
        )


def test_lookup_request_rejects_future_check_in_date() -> None:
    with pytest.raises(ValidationError):
        GuestBookingLookupRequest(
            property="nolita",
            booking_reference="42",
            check_in_date="2999-01-01",
        )


def test_lookup_request_preserves_booking_reference_and_rejects_unknown_property() -> None:
    request = GuestBookingLookupRequest(
        property="nap_york",
        booking_reference=" 00042-A ",
        check_in_date="2026-11-12",
    )

    assert request.booking_reference == "00042-A"
    with pytest.raises(ValidationError):
        GuestBookingLookupRequest(
            property="other",
            booking_reference="42",
            check_in_date="2026-11-12",
        )


def test_property_configuration_keeps_nolita_and_nap_york_tokens_separate() -> None:
    settings = Settings(
        mews_nolita_api_url="https://nolita.example.test",
        mews_nolita_client_token="nolita-client",
        mews_nolita_access_token="nolita-access",
        mews_nap_york_api_url="https://nap.example.test",
        mews_nap_york_client_token="nap-client",
        mews_nap_york_access_token="nap-access",
    )

    nolita = settings.mews_property(GuestBookingLookupRequest(
        property="nolita", booking_reference="1", check_in_date="2026-11-12"
    ).property)
    nap_york = settings.mews_property(GuestBookingLookupRequest(
        property="nap_york", booking_reference="1", check_in_date="2026-11-12"
    ).property)

    assert nolita is not None
    assert nap_york is not None
    assert (nolita.client_token, nolita.access_token) == ("nolita-client", "nolita-access")
    assert (nap_york.client_token, nap_york.access_token) == ("nap-client", "nap-access")


def test_name_normalization_ignores_case_and_repeated_whitespace() -> None:
    assert normalize_guest_name("  José   van der Lee ") == "josé van der lee"
    assert normalize_guest_name("JORDAN LEE") == "jordan lee"


class FakeGateway:
    def __init__(self, result):
        self.result = result

    async def find_bookings(self, request):
        return self.result


@pytest.mark.anyio
async def test_service_returns_matched_candidate_without_internal_reservation_id() -> None:
    service = GuestBookingService(
        settings=Settings(
            agent_api_token="agent-secret",
            mews_nolita_api_url="https://example.test",
            mews_nolita_client_token="client-token",
            mews_nolita_access_token="access-token",
        ),
        gateway_factory=lambda _property: FakeGateway(
            [
                BookingCandidate(
                    reservation_id="internal-id",
                    guest_names=("Jordan Lee",),
                    check_in_date=date(2026, 11, 12),
                    state="Started",
                )
            ]
        ),
    )
    request = GuestBookingLookupRequest(
        property="nolita",
        full_name="Jordan Lee",
        check_in_date="2026-11-12",
    )

    result = await service.lookup(request)

    assert result.outcome == "matched"
    assert result.matches[0].guest_name == "Jordan Lee"
    assert result.matches[0].check_in_date == date(2026, 11, 12)
    assert "internal-id" not in result.model_dump_json()


def test_lookup_route_requires_backend_bearer_token(monkeypatch) -> None:
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


def test_lookup_route_fails_closed_when_agent_token_is_not_configured(monkeypatch) -> None:
    monkeypatch.delenv("AGENT_API_TOKEN", raising=False)
    get_settings.cache_clear()
    client = TestClient(create_app())

    response = client.post(
        "/guest-bookings/lookup",
        json={
            "property": "nolita",
            "booking_reference": "42",
            "check_in_date": "2026-11-12",
        },
        headers={"Authorization": "Bearer arbitrary"},
    )

    assert response.status_code == 503
    get_settings.cache_clear()


def test_lookup_route_returns_minimal_authenticated_match(monkeypatch) -> None:
    monkeypatch.setenv("AGENT_API_TOKEN", "expected-secret")
    get_settings.cache_clear()
    service = GuestBookingService(
        settings=Settings(
            mews_nolita_api_url="https://example.test",
            mews_nolita_client_token="client-token",
            mews_nolita_access_token="access-token",
        ),
        gateway_factory=lambda _property: FakeGateway(
            [BookingCandidate("internal-id", ("Jordan Lee",), date(2026, 11, 12), "Started")]
        ),
    )
    application = create_app()
    application.dependency_overrides[get_guest_booking_service] = lambda: service
    client = TestClient(application)

    response = client.post(
        "/guest-bookings/lookup",
        json={
            "property": "nolita",
            "full_name": "Jordan Lee",
            "check_in_date": "2026-11-12",
        },
        headers={"Authorization": "Bearer expected-secret"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "outcome": "matched",
        "matches": [
            {
                "guest_name": "Jordan Lee",
                "check_in_date": "2026-11-12",
                "state": "Started",
            }
        ],
    }
    assert "internal-id" not in response.text
    application.dependency_overrides.clear()
    get_settings.cache_clear()


@pytest.mark.anyio
async def test_service_returns_ambiguous_when_name_matches_multiple_bookings() -> None:
    service = GuestBookingService(
        settings=Settings(
            mews_nolita_api_url="https://example.test",
            mews_nolita_client_token="client-token",
            mews_nolita_access_token="access-token",
        ),
        gateway_factory=lambda _property: FakeGateway(
            [
                BookingCandidate("one", ("Jordan Lee",), date(2026, 11, 12), "Confirmed"),
                BookingCandidate("two", ("Jordan Lee",), date(2026, 11, 12), "Started"),
            ]
        ),
    )
    request = GuestBookingLookupRequest(
        property="nolita",
        full_name=" jordan   lee ",
        check_in_date="2026-11-12",
    )

    result = await service.lookup(request)

    assert result.outcome == "ambiguous"
    assert len(result.matches) == 2


@pytest.mark.anyio
async def test_service_returns_no_match_for_different_normalized_name() -> None:
    service = GuestBookingService(
        settings=Settings(
            mews_nolita_api_url="https://example.test",
            mews_nolita_client_token="client-token",
            mews_nolita_access_token="access-token",
        ),
        gateway_factory=lambda _property: FakeGateway(
            [BookingCandidate("one", ("Jordan Lee",), date(2026, 11, 12), "Confirmed")]
        ),
    )

    result = await service.lookup(
        GuestBookingLookupRequest(
            property="nolita",
            full_name="Other Guest",
            check_in_date="2026-11-12",
        )
    )

    assert result.outcome == "no_match"
    assert result.matches == []


@pytest.mark.anyio
async def test_service_returns_unavailable_when_property_credentials_are_incomplete() -> None:
    service = GuestBookingService(
        settings=Settings(),
        gateway_factory=lambda _property: pytest.fail("Mews must not be called without credentials"),
    )

    result = await service.lookup(
        GuestBookingLookupRequest(
            property="nap_york",
            booking_reference="42",
            check_in_date="2026-11-12",
        )
    )

    assert result.outcome == "unavailable"
