from __future__ import annotations

import unicodedata
from collections.abc import Callable
from typing import Protocol

from app.core.config import MewsPropertySettings, Settings, get_settings
from app.integrations.mews.client import BookingCandidate, MewsConnectorClient, MewsUnavailable
from app.schemas.guest_booking import (
    GuestBookingLookupRequest,
    GuestBookingLookupResponse,
    GuestBookingMatch,
    LookupOutcome,
)


class BookingGateway(Protocol):
    async def find_bookings(self, request: GuestBookingLookupRequest) -> list[BookingCandidate]: ...


def normalize_guest_name(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value)
    return " ".join(normalized.casefold().split())


class GuestBookingService:
    def __init__(
        self,
        settings: Settings | None = None,
        gateway_factory: Callable[[MewsPropertySettings], BookingGateway] | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._gateway_factory = gateway_factory or MewsConnectorClient

    async def lookup(self, request: GuestBookingLookupRequest) -> GuestBookingLookupResponse:
        property_settings = self._settings.mews_property(request.property)
        if property_settings is None:
            return GuestBookingLookupResponse(outcome=LookupOutcome.UNAVAILABLE)

        try:
            candidates = await self._gateway_factory(property_settings).find_bookings(request)
        except MewsUnavailable:
            return GuestBookingLookupResponse(outcome=LookupOutcome.UNAVAILABLE)

        if request.full_name is not None:
            expected_name = normalize_guest_name(request.full_name)
            selected = []
            for candidate in candidates:
                matched_name = next(
                    (name for name in candidate.guest_names if normalize_guest_name(name) == expected_name),
                    None,
                )
                if matched_name is not None:
                    selected.append((candidate, matched_name))
        else:
            selected = [
                (candidate, candidate.guest_names[0] if candidate.guest_names else None)
                for candidate in candidates
            ]

        unique: dict[str, tuple[BookingCandidate, str | None]] = {}
        for candidate, matched_name in selected:
            unique.setdefault(candidate.reservation_id, (candidate, matched_name))

        matches = [
            GuestBookingMatch(
                guest_name=name,
                check_in_date=candidate.check_in_date,
                state=candidate.state,
            )
            for candidate, name in unique.values()
        ]
        if not matches:
            return GuestBookingLookupResponse(outcome=LookupOutcome.NO_MATCH)
        if len(matches) > 1:
            if request.booking_reference is not None:
                matches = [
                    GuestBookingMatch(
                        guest_name=None,
                        check_in_date=match.check_in_date,
                        state=match.state,
                    )
                    for match in matches
                ]
            return GuestBookingLookupResponse(outcome=LookupOutcome.AMBIGUOUS, matches=matches)
        return GuestBookingLookupResponse(outcome=LookupOutcome.MATCHED, matches=matches)
