import json

from langchain.tools import tool

from app.config import get_settings
from app.repositories import GitRepository

_repo = GitRepository(get_settings().data_dir)


@tool
def get_git_commits(service: str = "", since: str = "", until: str = "") -> str:
    """Fetch recent git commits (author, message, files changed, PR number).

    Known services: "payment-api", "notification-service", "checkout-api".

    Args:
        service: Exact service name to filter by. Empty string returns all services.
        since: Inclusive lower bound on commit time, ISO 8601 UTC. Empty string means no lower bound.
        until: Inclusive upper bound on commit time, ISO 8601 UTC. Empty string means no upper bound.
    """
    results = _repo.get_commits(service=service or None, since=since or None, until=until or None)
    if not results:
        return json.dumps({"count": 0, "commits": [], "note": "No commits matched these filters."})
    return json.dumps({"count": len(results), "commits": results}, indent=2)
