"""LiveKit worker entry point.

`python worker.py` validates local configuration and then starts the LiveKit
Agents worker. It does not report a successful LiveKit or Google connection.
The framework health server reports connection status only after `cli.run_app`
is running with valid LiveKit credentials.
"""

import json
import logging
import sys

from dotenv import load_dotenv
from livekit.agents import AgentServer, JobContext, cli

from config.settings import assess_readiness, get_settings
from session import start_session

load_dotenv()

logger = logging.getLogger("front-desk.voice-agent")


def create_server() -> AgentServer:
    settings = get_settings()
    server = AgentServer(log_level=settings.log_level.lower())

    @server.rtc_session(agent_name=settings.agent_name)
    async def entrypoint(ctx: JobContext) -> None:
        await start_session(ctx, get_settings())

    return server


def readiness_payload() -> dict[str, object]:
    report = assess_readiness(
        {
            "LIVEKIT_URL": get_settings().livekit_url,
            "LIVEKIT_API_KEY": get_settings().livekit_api_key,
            "LIVEKIT_API_SECRET": get_settings().livekit_api_secret,
            "GOOGLE_API_KEY": get_settings().google_api_key,
            "BACKEND_API_URL": get_settings().backend_api_url,
        }
    )
    return report.model_dump()


def main(argv: list[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    if arguments[:1] == ["readiness"]:
        payload = readiness_payload()
        print(json.dumps(payload))
        return 0 if payload["ready"] else 1

    payload = readiness_payload()
    if not payload["ready"]:
        missing = ", ".join(payload["missing"])  # type: ignore[arg-type]
        logger.error(
            "Worker not started. Missing required environment variables: %s. "
            "No LiveKit or Google connection was attempted.",
            missing,
        )
        print(
            f"Missing required environment variables: {missing}. "
            "Copy .env.example to .env and provide real credentials. "
            "No LiveKit or Google connection was attempted.",
            file=sys.stderr,
        )
        return 1

    if argv is not None:
        sys.argv = [sys.argv[0], *argv]
    cli.run_app(create_server())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
