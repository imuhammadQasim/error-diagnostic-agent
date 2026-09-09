"""Agent tools. Each tool wraps one repository and exposes it to the LLM."""

from app.tools.database_tool import get_database_metrics
from app.tools.deployments_tool import get_deployments
from app.tools.external_tools import check_github_status, convert_time_to_utc
from app.tools.git_tool import get_git_commits
from app.tools.logs_tool import get_logs
from app.tools.metrics_tool import get_metrics
from app.tools.traces_tool import get_traces

ALL_TOOLS = [
    get_logs,
    get_metrics,
    get_database_metrics,
    get_deployments,
    get_traces,
    get_git_commits,
    check_github_status,
    convert_time_to_utc,
]

__all__ = [
    "ALL_TOOLS",
    "check_github_status",
    "convert_time_to_utc",
    "get_database_metrics",
    "get_deployments",
    "get_git_commits",
    "get_logs",
    "get_metrics",
    "get_traces",
]
