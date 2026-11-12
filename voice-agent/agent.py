"""Front-desk voice agent definition."""

from livekit.agents import Agent

from prompts import load_system_prompt
from tools import load_tools


class FrontDeskAgent(Agent):
    """Conversation agent. It does not own reservations or PMS access."""

    def __init__(self) -> None:
        super().__init__(
            instructions=load_system_prompt(),
            tools=list(load_tools()),
        )
