import json
from typing import Any

SUPPORTED_PROPERTIES = frozenset({"nolita", "nap_york"})


def property_from_job_metadata(metadata: str | None) -> str | None:
    if not metadata:
        return None
    try:
        payload: Any = json.loads(metadata)
    except (json.JSONDecodeError, TypeError):
        return None
    if not isinstance(payload, dict):
        return None
    property_id = payload.get("property")
    if not isinstance(property_id, str) or property_id not in SUPPORTED_PROPERTIES:
        return None
    return property_id
