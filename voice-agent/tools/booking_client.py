"""Authenticated backend client for guest booking lookup."""

from __future__ import annotations

from datetime import date
from urllib.parse import urlparse

import httpx


class BookingBackendUnavailable(Exception):
    """The backend did not return a valid booking lookup response."""


class BookingBackendClient:
    def __init__(self, base_url: str, api_token: str) -> None:
        self._base_url = base_url.strip().rstrip("/")
        self._api_token = api_token.strip()
        self._http_client = httpx.AsyncClient(timeout=httpx.Timeout(10.0, connect=3.0))

    async def lookup_booking(
        self,
        *,
        property_id: str,
        full_name: str | None,
        confirmation_number: str | None,
        check_in_date: date,
    ) -> dict[str, object]:
        if not self._base_url or not self._api_token:
            raise BookingBackendUnavailable("Booking lookup is not configured")
        parsed = urlparse(self._base_url)
        if parsed.scheme not in {"https", "http"} or not parsed.netloc:
            raise BookingBackendUnavailable("Booking lookup is not configured")
        if parsed.scheme != "https" and parsed.hostname not in {"localhost", "127.0.0.1"}:
            raise BookingBackendUnavailable("Booking lookup is not configured")
        payload: dict[str, object] = {
            "property": property_id,
            "check_in_date": check_in_date.isoformat(),
        }
        if full_name is not None:
            payload["full_name"] = full_name
        if confirmation_number is not None:
            payload["confirmation_number"] = confirmation_number

        try:
            response = await self._http_client.post(
                f"{self._base_url}/guest-bookings/lookup",
                json=payload,
                headers={"Authorization": f"Bearer {self._api_token}"},
            )
            response.raise_for_status()
            result = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise BookingBackendUnavailable("Booking lookup is temporarily unavailable") from exc

        if not isinstance(result, dict) or result.get("outcome") not in {
            "matched",
            "no_match",
            "ambiguous",
            "unavailable",
        }:
            raise BookingBackendUnavailable("Booking lookup returned an invalid response")
        matches = result.get("matches", [])
        if not isinstance(matches, list) or any(not isinstance(match, dict) for match in matches):
            raise BookingBackendUnavailable("Booking lookup returned an invalid response")
        normalized_matches: list[dict[str, object]] = []
        for match in matches:
            guest_name = match.get("guest_name")
            state = match.get("state")
            check_in_date = match.get("check_in_date")
            if guest_name is not None and (
                not isinstance(guest_name, str) or len(guest_name) > 200 or not guest_name.strip()
            ):
                raise BookingBackendUnavailable("Booking lookup returned an invalid response")
            if state not in {"Confirmed", "Started"} or not isinstance(check_in_date, str):
                raise BookingBackendUnavailable("Booking lookup returned an invalid response")
            try:
                parsed_date = date.fromisoformat(check_in_date)
            except ValueError as exc:
                raise BookingBackendUnavailable("Booking lookup returned an invalid response") from exc
            if parsed_date.isoformat() != check_in_date:
                raise BookingBackendUnavailable("Booking lookup returned an invalid response")
            normalized_matches.append(
                {
                    "guest_name": guest_name,
                    "check_in_date": check_in_date,
                    "state": state,
                }
            )
        if result["outcome"] == "matched" and len(normalized_matches) != 1:
            raise BookingBackendUnavailable("Booking lookup returned an invalid response")
        if result["outcome"] == "no_match" and normalized_matches:
            raise BookingBackendUnavailable("Booking lookup returned an invalid response")
        if result["outcome"] == "ambiguous" and len(normalized_matches) < 2:
            raise BookingBackendUnavailable("Booking lookup returned an invalid response")
        if result["outcome"] == "unavailable" and normalized_matches:
            raise BookingBackendUnavailable("Booking lookup returned an invalid response")
        return {"outcome": result["outcome"], "matches": normalized_matches}

    async def aclose(self) -> None:
        await self._http_client.aclose()
