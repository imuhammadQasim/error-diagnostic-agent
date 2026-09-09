import json

from langchain.tools import tool

from app.config import get_settings
from app.repositories import DatabaseRepository

_repo = DatabaseRepository(get_settings().data_dir)


@tool
def get_database_metrics(database: str = "", since: str = "", until: str = "") -> str:
    """Fetch database connection-pool snapshots and slow queries.

    Known databases: "postgres-payments" (used by payment-api),
    "postgres-notifications" (used by notification-service).

    Args:
        database: Exact database name. Empty string returns all databases.
        since: Inclusive lower bound on snapshot timestamps, ISO 8601 UTC. Empty string means no lower bound.
        until: Inclusive upper bound on snapshot timestamps, ISO 8601 UTC. Empty string means no upper bound.
    """
    result = _repo.get_database_metrics(database=database or None, since=since or None, until=until or None)
    if not result:
        return json.dumps({
            "error": f"Unknown database '{database}'." if database else "No database data available.",
            "known_databases": _repo.list_databases(),
        })
    return json.dumps(result, indent=2)
