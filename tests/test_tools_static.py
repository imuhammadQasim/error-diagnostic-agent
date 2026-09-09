import json

from app.tools import (
    get_database_metrics,
    get_deployments,
    get_git_commits,
    get_logs,
    get_metrics,
    get_traces,
)


def test_get_logs_tool_returns_valid_json():
    raw = get_logs.invoke({"service": "payment-api"})
    data = json.loads(raw)
    assert data["count"] > 0
    assert all(entry["service"] == "payment-api" for entry in data["logs"])


def test_get_metrics_tool_unknown_service_reports_error_not_crash():
    raw = get_metrics.invoke({"service": "does-not-exist"})
    data = json.loads(raw)
    assert "error" in data
    assert "known_services" in data


def test_get_database_metrics_tool_defaults_to_all_databases():
    raw = get_database_metrics.invoke({})
    data = json.loads(raw)
    assert "postgres-payments" in data
    assert "postgres-notifications" in data


def test_get_deployments_tool_finds_relevant_deploy():
    raw = get_deployments.invoke({"service": "payment-api"})
    data = json.loads(raw)
    commit_shas = {d["commit_sha"] for d in data["deployments"]}
    assert "abc123f" in commit_shas


def test_get_traces_tool_filters_by_status_code():
    raw = get_traces.invoke({"status_code": 500})
    data = json.loads(raw)
    assert data["count"] > 0
    assert all(t["status_code"] == 500 for t in data["traces"])


def test_get_git_commits_tool_returns_commit_messages():
    raw = get_git_commits.invoke({"service": "payment-api"})
    data = json.loads(raw)
    messages = [c["message"] for c in data["commits"]]
    assert any("retry logic" in m for m in messages)
