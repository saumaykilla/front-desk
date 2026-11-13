from datetime import date, datetime
from enum import Enum
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core.config import BookingProperty


class LookupOutcome(str, Enum):
    MATCHED = "matched"
    NO_MATCH = "no_match"
    AMBIGUOUS = "ambiguous"
    UNAVAILABLE = "unavailable"


class GuestBookingLookupRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    property: BookingProperty
    full_name: str | None = Field(default=None, max_length=200)
    booking_reference: str | None = Field(default=None, max_length=100)
    check_in_date: date

    @field_validator("check_in_date")
    @classmethod
    def reject_future_check_in_date(cls, value: date) -> date:
        today = datetime.now(ZoneInfo("America/New_York")).date()
        if value > today:
            raise ValueError("check_in_date cannot be in the future")
        return value

    @field_validator("full_name", "booking_reference")
    @classmethod
    def strip_lookup_value(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None

    @model_validator(mode="after")
    def require_one_lookup_key(self) -> "GuestBookingLookupRequest":
        if (self.full_name is None) == (self.booking_reference is None):
            raise ValueError("provide exactly one of full_name or booking_reference")
        return self


class GuestBookingMatch(BaseModel):
    guest_name: str | None
    check_in_date: date
    state: str


class GuestBookingLookupResponse(BaseModel):
    outcome: LookupOutcome
    matches: list[GuestBookingMatch] = Field(default_factory=list)
