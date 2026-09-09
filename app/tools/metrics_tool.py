import json

from langchain.tools import tool

from app.config import get_settings
from app.repositories import MetricsRepository

_repo = MetricsRepository(get_settings().data_dir)


@tool
def get_metrics(service: str, metric_names: str = "", since: str = "", until: str = "") -> str:
    """Fetch time-series metrics (error rate, latency, request count, CPU, memory) for one service.

    Known services: "payment-api", "notification-service", "checkout-api".
    Known metric names: "error_rate_percent", "latency_p95_ms",
    "request_count_per_minute", "cpu_percent", "memory_percent" (CPU/memory
    only available for payment-api).

    Args:
        service: Exact service name. Required.
        metric_names: Comma-separated metric names to narrow the result, e.g. "error_rate_percent,latency_p95_ms". Empty string returns all available metrics for the service.
        since: Inclusive lower bound, ISO 8601 UTC. Empty string means no lower bound.
        until: Inclusive upper bound, ISO 8601 UTC. Empty string means no upper bound.
    """
    names = [n.strip() for n in metric_names.split(",") if n.strip()] or None
    result = _repo.get_metrics(service=service, metric_names=names, since=since or None, until=until or None)
    if result is None:
        return json.dumps({
            "error": f"Unknown service '{service}'.",
            "known_services": _repo.list_services(),
        })
    return json.dumps({"service": service, "metrics": result}, indent=2)
