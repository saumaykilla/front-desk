import json
from datetime import date

import httpx
import pytest

from app.core.config import MewsPropertySettings
from app.integrations.mews.client import (
    MEWS_CLIENT_NAME,
    MEWS_RESERVATIONS_PATH,
    MewsConnectorClient,
    MewsUnavailable,
    _utc_interval,
)
from app.schemas.guest_booking import GuestBookingLookupRequest


def test_new_york_day_interval_accounts_for_daylight_saving_transition() -> None:
    assert _utc_interval(date(2026, 3, 8)) == {
        "StartUtc": "2026-03-08T05:00:00Z",
        "EndUtc": "2026-03-09T04:00:00Z",
    }


@pytest.mark.anyio
async def test_name_lookup_uses_scoped_reservations_and_minimal_customer_profiles() -> None:
    requests: list[httpx.Request] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        body = json.loads(request.content)
        assert body["ClientToken"] == "client-secret"
        assert body["AccessToken"] == "access-secret"
        assert body["Client"] == MEWS_CLIENT_NAME
        if request.url.path == MEWS_RESERVATIONS_PATH:
            assert body["ScheduledStartUtc"] == {
                "StartUtc": "2026-11-12T05:00:00Z",
                "EndUtc": "2026-11-13T05:00:00Z",
            }
            return httpx.Response(
                200,
                json={
                    "Reservations": [
                        {
                            "Id": "reservation-1",
                            "AccountId": "customer-1",
                            "AccountType": "Customer",
                            "State": "Started",
                            "ScheduledStartUtc": "2026-11-12T05:00:00Z",
                        }
                    ]
                },
            )
        if request.url.path.endswith("/companionships/getAll"):
            return httpx.Response(
                200,
                json={
                    "Companionships": [
                        {"ReservationId": "reservation-1", "CustomerId": "companion-2"}
                    ]
                },
            )
        if request.url.path.endswith("/customers/getAll"):
            assert body["CustomerIds"] == ["companion-2", "customer-1"]
            assert body["Extent"] == {
                "Customers": True,
                "Addresses": False,
            }
            return httpx.Response(
                200,
                json={
                    "Customers": [
                        {
                            "Id": "customer-1",
                            "FirstName": "Jordan",
                            "LastName": "Lee",
                        },
                        {
                            "Id": "companion-2",
                            "FirstName": "Morgan",
                            "LastName": "Doe",
                        },
                    ]
                },
            )
        raise AssertionError(f"Unexpected Mews operation: {request.url.path}")

    http_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    gateway = MewsConnectorClient(
        MewsPropertySettings("https://api.example.test", "client-secret", "access-secret"),
        http_client=http_client,
    )
    candidates = await gateway.find_bookings(
        GuestBookingLookupRequest(
            property="nolita",
            full_name="Jordan Lee",
            check_in_date="2026-11-12",
        )
    )
    await http_client.aclose()

    assert [candidate.guest_names for candidate in candidates] == [
        ("Jordan Lee", "Morgan Doe")
    ]
    assert candidates[0].check_in_date == date(2026, 11, 12)
    assert len(requests) == 3


@pytest.mark.anyio
async def test_booking_reference_searches_both_mews_number_filters() -> None:
    filters: list[str] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        if request.url.path == MEWS_RESERVATIONS_PATH:
            assert body["ScheduledStartUtc"] == {
                "StartUtc": "2026-11-12T05:00:00Z",
                "EndUtc": "2026-11-13T05:00:00Z",
            }
            assert body["States"] == ["Confirmed", "Started"]
            selected_filters = [key for key in ("Numbers", "ChannelNumbers") if key in body]
            assert len(selected_filters) == 1
            filters.extend(selected_filters)
            assert body[selected_filters[0]] == ["00042"]
            if selected_filters[0] == "ChannelNumbers":
                return httpx.Response(
                    200,
                    json={
                        "Reservations": [
                            {
                                "Id": "channel-match",
                                "AccountType": "Company",
                                "State": "Confirmed",
                                "ScheduledStartUtc": "2026-11-12T12:00:00Z",
                            }
                        ]
                    },
                )
            return httpx.Response(200, json={"Reservations": []})
        if request.url.path.endswith("/companionships/getAll"):
            return httpx.Response(200, json={"Companionships": []})
        raise AssertionError(f"Unexpected Mews operation: {request.url.path}")

    http_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    gateway = MewsConnectorClient(
        MewsPropertySettings("https://api.example.test", "client-secret", "access-secret"),
        http_client=http_client,
    )
    result = await gateway.find_bookings(
        GuestBookingLookupRequest(
            property="nap_york",
            booking_reference="00042",
            check_in_date="2026-11-12",
        )
    )
    await http_client.aclose()

    assert filters == ["Numbers", "ChannelNumbers"]
    assert [candidate.reservation_id for candidate in result] == ["channel-match"]


@pytest.mark.anyio
async def test_booking_reference_deduplicates_reservation_found_by_both_filters() -> None:
    reservation = {
        "Id": "same-reservation",
        "AccountType": "Company",
        "State": "Started",
        "ScheduledStartUtc": "2026-11-12T12:00:00Z",
    }

    async def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        if request.url.path == MEWS_RESERVATIONS_PATH:
            assert body.get("Numbers") == ["42"] or body.get("ChannelNumbers") == ["42"]
            return httpx.Response(200, json={"Reservations": [reservation]})
        if request.url.path.endswith("/companionships/getAll"):
            return httpx.Response(200, json={"Companionships": []})
        raise AssertionError(f"Unexpected Mews operation: {request.url.path}")

    http_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    gateway = MewsConnectorClient(
        MewsPropertySettings("https://api.example.test", "client-secret", "access-secret"),
        http_client=http_client,
    )
    candidates = await gateway.find_bookings(
        GuestBookingLookupRequest(
            property="nap_york",
            booking_reference="42",
            check_in_date="2026-11-12",
        )
    )
    await http_client.aclose()

    assert [candidate.reservation_id for candidate in candidates] == ["same-reservation"]


@pytest.mark.anyio
async def test_booking_reference_returns_unavailable_if_second_filter_fails() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        if "Numbers" in body:
            return httpx.Response(
                200,
                json={
                    "Reservations": [
                        {
                            "Id": "mews-number-match",
                            "AccountType": "Company",
                            "State": "Confirmed",
                            "ScheduledStartUtc": "2026-11-12T12:00:00Z",
                        }
                    ]
                },
            )
        return httpx.Response(503)

    http_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    gateway = MewsConnectorClient(
        MewsPropertySettings("https://api.example.test", "client-secret", "access-secret"),
        http_client=http_client,
    )
    with pytest.raises(MewsUnavailable):
        await gateway.find_bookings(
            GuestBookingLookupRequest(
                property="nap_york",
                booking_reference="42",
                check_in_date="2026-11-12",
            )
        )
    await http_client.aclose()


@pytest.mark.anyio
async def test_reservation_lookup_follows_mews_pagination_cursor() -> None:
    reservation_requests: list[dict[str, object]] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        if request.url.path == MEWS_RESERVATIONS_PATH:
            reservation_requests.append(body)
            if "Numbers" not in body:
                return httpx.Response(200, json={"Reservations": []})
            reservation_id = f"reservation-{len(reservation_requests)}"
            payload = {
                "Reservations": [
                    {
                        "Id": reservation_id,
                        "AccountType": "Company",
                        "State": "Started",
                        "ScheduledStartUtc": "2026-11-12T05:00:00Z",
                    }
                ]
            }
            if len(reservation_requests) == 1:
                payload["Cursor"] = "older-reservation-cursor"
            return httpx.Response(200, json=payload)
        if request.url.path.endswith("/companionships/getAll"):
            return httpx.Response(200, json={"Companionships": []})
        raise AssertionError(f"Unexpected Mews operation: {request.url.path}")

    http_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    gateway = MewsConnectorClient(
        MewsPropertySettings("https://api.example.test", "client-secret", "access-secret"),
        http_client=http_client,
    )
    candidates = await gateway.find_bookings(
        GuestBookingLookupRequest(
            property="nolita",
            booking_reference="42",
            check_in_date="2026-11-12",
        )
    )
    await http_client.aclose()

    assert len(candidates) == 2
    assert len(reservation_requests) == 3
    assert reservation_requests[1]["Limitation"] == {
        "Count": 1000,
        "Cursor": "older-reservation-cursor",
    }


@pytest.mark.anyio
async def test_mews_429_honors_retry_after_once(monkeypatch) -> None:
    attempts: dict[str, int] = {}
    delays: list[float] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        number_filter = "Numbers" if "Numbers" in body else "ChannelNumbers"
        attempts[number_filter] = attempts.get(number_filter, 0) + 1
        if number_filter == "Numbers" and attempts[number_filter] == 1:
            return httpx.Response(429, headers={"Retry-After": "0"})
        return httpx.Response(200, json={"Reservations": []})

    async def record_sleep(seconds: float) -> None:
        delays.append(seconds)

    monkeypatch.setattr("app.integrations.mews.client.asyncio.sleep", record_sleep)
    http_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    gateway = MewsConnectorClient(
        MewsPropertySettings("https://api.example.test", "client-secret", "access-secret"),
        http_client=http_client,
    )
    await gateway.find_bookings(
        GuestBookingLookupRequest(
            property="nolita",
            booking_reference="42",
            check_in_date="2026-11-12",
        )
    )
    await http_client.aclose()

    assert attempts == {"Numbers": 2, "ChannelNumbers": 1}
    assert delays == [0.0]


@pytest.mark.anyio
async def test_malformed_mews_json_is_unavailable() -> None:
    async def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=b"not-json")

    http_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    gateway = MewsConnectorClient(
        MewsPropertySettings("https://api.example.test", "client-secret", "access-secret"),
        http_client=http_client,
    )
    with pytest.raises(MewsUnavailable):
        await gateway.find_bookings(
            GuestBookingLookupRequest(
                property="nolita",
                booking_reference="42",
                check_in_date="2026-11-12",
            )
        )
    await http_client.aclose()


@pytest.mark.anyio
@pytest.mark.parametrize("status_code", [401, 403, 408, 429, 500, 503])
async def test_mews_http_failures_are_not_reported_as_no_match(status_code: int) -> None:
    async def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code, headers={"Retry-After": "0"})

    http_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    gateway = MewsConnectorClient(
        MewsPropertySettings("https://api.example.test", "client-secret", "access-secret"),
        http_client=http_client,
    )
    with pytest.raises(MewsUnavailable):
        await gateway.find_bookings(
            GuestBookingLookupRequest(
                property="nolita",
                booking_reference="42",
                check_in_date="2026-11-12",
            )
        )
    await http_client.aclose()
