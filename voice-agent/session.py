"""LiveKit session construction.

The Google realtime model is created only when a job starts. Importing this
module does not open a LiveKit or Google connection.

The model id is omitted unless GOOGLE_REALTIME_MODEL is set, so the installed
livekit-plugins-google default is used. Do not hard-code a model id here.
"""

from livekit.agents import AgentSession, JobContext
from livekit.plugins import google

from agent import FrontDeskAgent
from config.settings import Settings


def build_realtime_model(settings: Settings) -> google.realtime.RealtimeModel:
    if not settings.google_api_key.strip():
        raise ValueError("GOOGLE_API_KEY is required before creating a realtime model.")

    model_kwargs: dict[str, str] = {
        "api_key": settings.google_api_key,
        "voice": settings.google_realtime_voice,
    }
    if settings.google_realtime_model.strip():
        model_kwargs["model"] = settings.google_realtime_model.strip()

    return google.realtime.RealtimeModel(**model_kwargs)


def build_session(settings: Settings) -> AgentSession:
    return AgentSession(llm=build_realtime_model(settings))


async def start_session(
    ctx: JobContext,
    settings: Settings,
    property_id: str | None,
) -> AgentSession:
    session = build_session(settings)
    await session.start(
        room=ctx.room,
        agent=FrontDeskAgent(settings=settings, property_id=property_id),
    )
    return session
