from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from email.utils import parsedate_to_datetime
from typing import Any
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

import httpx

from app.core.config import MewsPropertySettings
from app.schemas.guest_booking import GuestBookingLookupRequest

PROPERTY_TIMEZONE = ZoneInfo("America/New_York")
MEWS_CLIENT_NAME = "Front Desk Agent 0.1.0"
MEWS_PAGE_SIZE = 1000
MEWS_RESERVATIONS_PATH = "/api/connector/v1/reservations/getAll/2023-06-06"
MEWS_CUSTOMERS_PATH = "/api/connector/v1/customers/getAll"
MEWS_COMPANIONSHIPS_PATH = "/api/connector/v1/companionships/getAll"


class MewsUnavailable(Exception):
    """Mews could not provide a valid response for a lookup."""


@dataclass(frozen=True)
class BookingCandidate:
    reservation_id: str
    guest_names: tuple[str, ...]
    check_in_date: date
    state: str


def _utc_interval(local_date: date) -> dict[str, str]:
    start_local = datetime.combine(local_date, time.min, tzinfo=PROPERTY_TIMEZONE)
    end_local = datetime.combine(local_date + timedelta(days=1), time.min, tzinfo=PROPERTY_TIMEZONE)
    start_utc = start_local.astimezone(timezone.utc)
    end_utc = end_local.astimezone(timezone.utc)
    return {
        "StartUtc": start_utc.isoformat(timespec="seconds").replace("+00:00", "Z"),
        "EndUtc": end_utc.isoformat(timespec="seconds").replace("+00:00", "Z"),
    }


def _parse_retry_after(value: str | None) -> float:
    if value is None:
        return 0.5
    try:
        return max(0.0, min(float(value), 30.0))
    except ValueError:
        try:
            retry_at = parsedate_to_datetime(value)
            if retry_at.tzinfo is None:
                retry_at = retry_at.replace(tzinfo=timezone.utc)
            return max(0.0, min((retry_at - datetime.now(timezone.utc)).total_seconds(), 30.0))
        except (TypeError, ValueError, OverflowError):
            return 0.5


class MewsConnectorClient:
    def __init__(
        self,
        property_settings: MewsPropertySettings,
        *,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        parsed = urlparse(property_settings.api_url)
        if (
            parsed.scheme not in {"https", "http"}
            or not parsed.netloc
            or parsed.path not in {"", "/"}
            or parsed.username is not None
            or parsed.password is not None
            or parsed.query
            or parsed.fragment
        ):
            raise MewsUnavailable("Mews API base URL is not configured correctly")
        if parsed.scheme != "https" and parsed.hostname not in {"localhost", "127.0.0.1"}:
            raise MewsUnavailable("Mews API must use HTTPS")
        self._settings = property_settings
        self._http_client = http_client

    async def find_bookings(self, request: GuestBookingLookupRequest) -> list[BookingCandidate]:
        if self._http_client is not None:
            return await self._find_bookings(request)
        async with httpx.AsyncClient(timeout=httpx.Timeout(10.0, connect=3.0)) as client:
            self._http_client = client
            try:
                return await self._find_bookings(request)
            finally:
                self._http_client = None

    async def _find_bookings(self, request: GuestBookingLookupRequest) -> list[BookingCandidate]:
        filters: dict[str, Any] = {
            "ScheduledStartUtc": _utc_interval(request.check_in_date),
            "States": ["Confirmed", "Started"],
        }
        if request.booking_reference is None:
            reservations = await self._get_all(MEWS_RESERVATIONS_PATH, filters, "Reservations")
        else:
            reservations_by_id: dict[str, dict[str, Any]] = {}
            for number_filter in ("Numbers", "ChannelNumbers"):
                results = await self._get_all(
                    MEWS_RESERVATIONS_PATH,
                    {**filters, number_filter: [request.booking_reference]},
                    "Reservations",
                )
                for reservation in results:
                    reservation_id = self._required_string(reservation, "Id")
                    reservations_by_id.setdefault(reservation_id, reservation)
            reservations = list(reservations_by_id.values())
        reservations = [
            reservation
            for reservation in reservations
            if reservation.get("State") in {"Confirmed", "Started"}
            and self._scheduled_date(reservation) == request.check_in_date
        ]
        if not reservations:
            return []

        reservation_ids = [self._required_string(row, "Id") for row in reservations]
        customer_ids: set[str] = set()
        for reservation in reservations:
            if reservation.get("AccountType") == "Customer":
                customer_ids.add(self._required_string(reservation, "AccountId"))
            elif reservation.get("AccountType") != "Company":
                raise MewsUnavailable("Mews reservation account type is invalid")

        companion_customer_ids = await self._get_companion_customer_ids(reservation_ids)
        for linked_customer_ids in companion_customer_ids.values():
            customer_ids.update(linked_customer_ids)
        customers = await self._get_customers(sorted(customer_ids)) if customer_ids else {}

        candidates: list[BookingCandidate] = []
        for reservation in reservations:
            reservation_id = self._required_string(reservation, "Id")
            linked_ids = set(companion_customer_ids.get(reservation_id, set()))
            if reservation.get("AccountType") == "Customer":
                linked_ids.add(self._required_string(reservation, "AccountId"))
            names = tuple(
                sorted(
                    {
                        self._customer_name(customers[customer_id])
                        for customer_id in linked_ids
                        if customer_id in customers
                    },
                    key=str.casefold,
                )
            )
            candidates.append(
                BookingCandidate(
                    reservation_id=reservation_id,
                    guest_names=names,
                    check_in_date=self._scheduled_date(reservation),
                    state=self._required_string(reservation, "State"),
                )
            )
        return candidates

    async def _get_companion_customer_ids(
        self,
        reservation_ids: list[str],
    ) -> dict[str, set[str]]:
        result: dict[str, set[str]] = {}
        for offset in range(0, len(reservation_ids), MEWS_PAGE_SIZE):
            batch = reservation_ids[offset : offset + MEWS_PAGE_SIZE]
            rows = await self._get_all(
                MEWS_COMPANIONSHIPS_PATH,
                {
                    "ReservationIds": batch,
                    "Extent": {"Customers": False, "Reservations": False, "ReservationGroups": False},
                },
                "Companionships",
            )
            for row in rows:
                reservation_id = self._required_string(row, "ReservationId")
                customer_id = self._required_string(row, "CustomerId")
                if reservation_id in batch:
                    result.setdefault(reservation_id, set()).add(customer_id)
        return result

    async def _get_customers(self, customer_ids: list[str]) -> dict[str, dict[str, Any]]:
        customers: dict[str, dict[str, Any]] = {}
        for offset in range(0, len(customer_ids), MEWS_PAGE_SIZE):
            batch = customer_ids[offset : offset + MEWS_PAGE_SIZE]
            rows = await self._get_all(
                MEWS_CUSTOMERS_PATH,
                {
                    "CustomerIds": batch,
                    "Extent": {"Customers": True, "Addresses": False},
                },
                "Customers",
            )
            for row in rows:
                customer_id = self._required_string(row, "Id")
                customers[customer_id] = row
        return customers

    async def _get_all(
        self,
        path: str,
        filters: dict[str, Any],
        result_key: str,
    ) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        cursor: str | None = None
        seen_cursors: set[str] = set()
        while True:
            limitation: dict[str, Any] = {"Count": MEWS_PAGE_SIZE}
            if cursor is not None:
                limitation["Cursor"] = cursor
            payload = await self._post(path, {**filters, "Limitation": limitation})
            page = payload.get(result_key)
            if not isinstance(page, list) or any(not isinstance(row, dict) for row in page):
                raise MewsUnavailable("Mews returned an invalid lookup response")
            items.extend(page)
            next_cursor = payload.get("Cursor")
            if next_cursor is None or next_cursor == "":
                return items
            if not isinstance(next_cursor, str) or next_cursor in seen_cursors:
                raise MewsUnavailable("Mews returned an invalid pagination cursor")
            seen_cursors.add(next_cursor)
            cursor = next_cursor

    async def _post(self, path: str, filters: dict[str, Any]) -> dict[str, Any]:
        payload = {
            "ClientToken": self._settings.client_token,
            "AccessToken": self._settings.access_token,
            "Client": MEWS_CLIENT_NAME,
            **filters,
        }
        client = self._http_client
        if client is None:
            raise MewsUnavailable("Mews client is not available")
        for attempt in range(2):
            try:
                response = await client.post(f"{self._settings.api_url}{path}", json=payload)
            except (httpx.TimeoutException, httpx.NetworkError, httpx.RemoteProtocolError) as exc:
                raise MewsUnavailable("Mews is temporarily unavailable") from exc
            if response.status_code == 429 and attempt == 0:
                await asyncio.sleep(_parse_retry_after(response.headers.get("Retry-After")))
                continue
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                raise MewsUnavailable("Mews rejected or could not complete the lookup") from exc
            try:
                result = response.json()
            except (json.JSONDecodeError, ValueError) as exc:
                raise MewsUnavailable("Mews returned invalid JSON") from exc
            if not isinstance(result, dict):
                raise MewsUnavailable("Mews returned an invalid lookup response")
            return result
        raise MewsUnavailable("Mews rate limit persisted after retry")

    @staticmethod
    def _scheduled_date(reservation: dict[str, Any]) -> date:
        value = MewsConnectorClient._required_string(reservation, "ScheduledStartUtc")
        try:
            scheduled = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise MewsUnavailable("Mews returned an invalid reservation date") from exc
        if scheduled.tzinfo is None:
            raise MewsUnavailable("Mews returned a reservation date without a timezone")
        return scheduled.astimezone(PROPERTY_TIMEZONE).date()

    @staticmethod
    def _customer_name(customer: dict[str, Any]) -> str:
        parts = [customer.get("FirstName"), customer.get("LastName"), customer.get("SecondLastName")]
        name = " ".join(part.strip() for part in parts if isinstance(part, str) and part.strip())
        if not name:
            raise MewsUnavailable("Mews returned a customer without a usable name")
        return name

    @staticmethod
    def _required_string(payload: dict[str, Any], key: str) -> str:
        value = payload.get(key)
        if not isinstance(value, str) or not value.strip():
            raise MewsUnavailable("Mews returned an invalid lookup response")
        return value.strip()
