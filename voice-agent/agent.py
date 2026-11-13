"""Canonical LiveKit Agents entrypoint for the front-desk assistant."""

from livekit.agents import AgentServer, JobContext, cli

from config.property_context import property_from_job_metadata
from config.settings import get_settings
from session import start_session

settings = get_settings()
server = AgentServer(log_level=settings.log_level.lower())


@server.rtc_session(agent_name=settings.agent_name)
async def entrypoint(ctx: JobContext) -> None:
    property_id = property_from_job_metadata(ctx.job.metadata)
    await start_session(ctx, get_settings(), property_id)


if __name__ == "__main__":
    cli.run_app(server)
