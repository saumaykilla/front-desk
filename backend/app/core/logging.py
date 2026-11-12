"""Application logging configuration."""

import logging


def configure_logging(level: str) -> None:
    """Configure process logging. Invalid levels fall back to INFO and are logged once."""

    resolved = level.upper()
    if resolved not in logging.getLevelNamesMapping():
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        )
        logging.getLogger(__name__).warning("Unknown LOG_LEVEL '%s'; using INFO.", level)
        return

    logging.basicConfig(
        level=resolved,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
