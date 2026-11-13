"""LiveKit worker entry point.

`python worker.py` validates local configuration and then starts the LiveKit
Agents worker. It does not report a successful LiveKit or Google connection.
The framework health server reports connection status only after `cli.run_app`
is running with valid LiveKit credentials.
"""

import json
import logging
import sys

from livekit.agents import cli

from agent import server
from config.settings import assess_readiness, get_settings

logger = logging.getLogger("front-desk.voice-agent")


def readiness_payload() -> dict[str, object]:
    report = assess_readiness(
        {
            "LIVEKIT_URL": get_settings().livekit_url,
            "LIVEKIT_API_KEY": get_settings().livekit_api_key,
            "LIVEKIT_API_SECRET": get_settings().livekit_api_secret,
            "GOOGLE_API_KEY": get_settings().google_api_key,
            "BACKEND_API_URL": get_settings().backend_api_url,
            "BACKEND_API_TOKEN": get_settings().backend_api_token,
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
            "Copy .env.example to .env.local and provide real credentials. "
            "No LiveKit or Google connection was attempted.",
            file=sys.stderr,
        )
        return 1

    if argv is not None:
        sys.argv = [sys.argv[0], *argv]
    cli.run_app(server)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
