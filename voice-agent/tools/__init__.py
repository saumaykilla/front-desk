from collections.abc import Sequence
from datetime import date
from typing import Any

from livekit.agents import RunContext, ToolError, function_tool

from config.property_context import SUPPORTED_PROPERTIES
from tools.booking_client import BookingBackendClient, BookingBackendUnavailable


def make_find_guest_booking_tool(
    property_id: str | None,
    backend_client: BookingBackendClient,
) -> Any:
    @function_tool()
    async def find_guest_booking(
        context: RunContext,
        check_in_date: str,
        full_name: str | None = None,
        booking_reference: str | None = None,
    ) -> dict[str, object]:
        """Find a current booking using a guest-confirmed full name or booking confirmation/reference number and check-in date."""

        del context
        if (full_name is None) == (booking_reference is None):
            raise ToolError("Provide either a guest full name or booking confirmation/reference number, not both.")
        if property_id not in SUPPORTED_PROPERTIES:
            return {"outcome": "unavailable", "matches": []}
        try:
            requested_date = date.fromisoformat(check_in_date)
            if requested_date.isoformat() != check_in_date:
                raise ValueError("date must use YYYY-MM-DD")
        except ValueError as exc:
            raise ToolError("Check-in date must use YYYY-MM-DD. Ask the guest to confirm the date.") from exc

        normalized_name = full_name.strip() if full_name is not None else None
        normalized_number = booking_reference.strip() if booking_reference is not None else None
        if normalized_name == "" or normalized_number == "":
            raise ToolError("The guest lookup detail is empty. Ask the guest to repeat it.")
        try:
            return await backend_client.lookup_booking(
                property_id=property_id,
                full_name=normalized_name,
                booking_reference=normalized_number,
                check_in_date=requested_date,
            )
        except BookingBackendUnavailable:
            return {"outcome": "unavailable", "matches": []}

    return find_guest_booking


def load_tools(
    property_id: str | None,
    backend_client: BookingBackendClient,
) -> Sequence[Any]:
    return (make_find_guest_booking_tool(property_id, backend_client),)
