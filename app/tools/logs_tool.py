import json

from langchain.tools import tool

from app.config import get_settings
from app.repositories import LogsRepository

_repo = LogsRepository(get_settings().data_dir)


@tool
def get_logs(service: str = "", level: str = "", since: str = "", until: str = "") -> str:
    """Fetch application log entries, optionally filtered.

    Known services: "payment-api", "notification-service", "checkout-api".
    Log levels: "INFO", "WARN", "ERROR".

    Args:
        service: Exact service name to filter by. Empty string returns all services.
        level: Exact log level to filter by. Empty string returns all levels.
        since: Inclusive lower bound, ISO 8601 UTC, e.g. "2026-09-09T10:00:00Z". Empty string means no lower bound.
        until: Inclusive upper bound, ISO 8601 UTC. Empty string means no upper bound.
    """
    results = _repo.get_logs(
        service=service or None,
        level=level or None,
        since=since or None,
        until=until or None,
    )
    if not results:
        return json.dumps({"count": 0, "logs": [], "note": "No log entries matched these filters."})
    return json.dumps({"count": len(results), "logs": results}, indent=2)
