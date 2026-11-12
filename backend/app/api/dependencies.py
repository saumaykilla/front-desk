from app.services.guest_booking_service import GuestBookingService


def get_guest_booking_service() -> GuestBookingService:
    return GuestBookingService()
