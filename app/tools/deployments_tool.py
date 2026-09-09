import json

from langchain.tools import tool

from app.config import get_settings
from app.repositories import DeploymentsRepository

_repo = DeploymentsRepository(get_settings().data_dir)


@tool
def get_deployments(service: str = "", since: str = "", until: str = "") -> str:
    """Fetch deployment history (version, commit, timestamp, changelog).

    Known services: "payment-api", "notification-service".

    Args:
        service: Exact service name to filter by. Empty string returns all services.
        since: Inclusive lower bound on deploy time, ISO 8601 UTC. Empty string means no lower bound.
        until: Inclusive upper bound on deploy time, ISO 8601 UTC. Empty string means no upper bound.
    """
    results = _repo.get_deployments(service=service or None, since=since or None, until=until or None)
    if not results:
        return json.dumps({"count": 0, "deployments": [], "note": "No deployments matched these filters."})
    return json.dumps({"count": len(results), "deployments": results}, indent=2)
