"""Callable voice-agent tools.

No tools are registered. Reservation, check-in, check-out, knowledge, and
escalation tools will be added only after an approved implementation plan.
"""

from collections.abc import Sequence
from typing import Any


def load_tools() -> Sequence[Any]:
    return ()
