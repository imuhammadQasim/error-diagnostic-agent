import json

from langchain.tools import tool

from app.config import get_settings
from app.repositories import TracesRepository

_repo = TracesRepository(get_settings().data_dir)


@tool
def get_traces(service: str = "", endpoint: str = "", status_code: int = 0, since: str = "", until: str = "") -> str:
    """Fetch distributed traces (per-span timing breakdown) for requests.

    Known services: "payment-api", "notification-service".
    Known endpoints: "/api/payments/charge", "/api/payments/refund", "/api/notifications/send".

    Args:
        service: Exact service name to filter by. Empty string returns all services.
        endpoint: Exact endpoint path to filter by. Empty string returns all endpoints.
        status_code: HTTP status code to filter by, e.g. 500. Pass 0 to skip this filter.
        since: Inclusive lower bound, ISO 8601 UTC. Empty string means no lower bound.
        until: Inclusive upper bound, ISO 8601 UTC. Empty string means no upper bound.
    """
    results = _repo.get_traces(
        service=service or None,
        endpoint=endpoint or None,
        status_code=status_code or None,
        since=since or None,
        until=until or None,
    )
    if not results:
        return json.dumps({"count": 0, "traces": [], "note": "No traces matched these filters."})
    return json.dumps({"count": len(results), "traces": results}, indent=2)
