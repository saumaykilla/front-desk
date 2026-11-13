"""Front-desk conversation agent definition."""

from datetime import datetime
from zoneinfo import ZoneInfo

from livekit.agents import Agent

from config.settings import Settings
from prompts import load_system_prompt
from tools import load_tools
from tools.booking_client import BookingBackendClient


class FrontDeskAgent(Agent):
    """Conversation agent. It does not own reservations or PMS access."""

    def __init__(self, settings: Settings, property_id: str | None) -> None:
        local_date = datetime.now(ZoneInfo("America/New_York")).date()
        self._backend_client = BookingBackendClient(
            settings.backend_api_url,
            settings.backend_api_token,
        )
        super().__init__(
            instructions=load_system_prompt(local_date=local_date.isoformat()),
            tools=list(load_tools(property_id=property_id, backend_client=self._backend_client)),
        )

    async def on_exit(self) -> None:
        await self._backend_client.aclose()
        await super().on_exit()
