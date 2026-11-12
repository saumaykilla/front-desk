from fastapi import APIRouter, Depends

from app.api.dependencies import get_guest_booking_service
from app.core.security import require_agent_token
from app.schemas.guest_booking import GuestBookingLookupRequest, GuestBookingLookupResponse
from app.services.guest_booking_service import GuestBookingService

router = APIRouter(
    prefix="/guest-bookings",
    tags=["guest-bookings"],
    dependencies=[Depends(require_agent_token)],
)


@router.post("/lookup", response_model=GuestBookingLookupResponse)
async def lookup_guest_booking(
    request: GuestBookingLookupRequest,
    service: GuestBookingService = Depends(get_guest_booking_service),
) -> GuestBookingLookupResponse:
    return await service.lookup(request)
