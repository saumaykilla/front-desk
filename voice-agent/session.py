"""LiveKit session construction.

The Google realtime model is created only when a job starts. Importing this
module does not open a LiveKit or Google connection.

The session uses Google's Gemini Live API directly through the LiveKit Google
plugin. It does not fall back to LiveKit Inference.
"""

from livekit.agents import AgentSession, JobContext
from livekit.plugins import google

from front_desk_agent import FrontDeskAgent
from config.settings import Settings


def build_realtime_model(settings: Settings) -> google.realtime.RealtimeModel:
    if not settings.google_api_key.strip():
        raise ValueError("GOOGLE_API_KEY is required before creating a realtime model.")
    if not settings.google_realtime_model.strip():
        raise ValueError("GOOGLE_REALTIME_MODEL must not be blank.")

    return google.realtime.RealtimeModel(
        api_key=settings.google_api_key,
        api_version="v1beta",
        model=settings.google_realtime_model.strip(),
        vertexai=False,
        voice=settings.google_realtime_voice,
    )


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
