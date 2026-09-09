from app.repositories import (
    DatabaseRepository,
    DeploymentsRepository,
    GitRepository,
    LogsRepository,
    MetricsRepository,
    TracesRepository,
)


def test_logs_repository_filters_by_service(data_dir):
    repo = LogsRepository(data_dir)
    results = repo.get_logs(service="payment-api")
    assert len(results) > 0
    assert all(r["service"] == "payment-api" for r in results)


def test_logs_repository_filters_by_level_and_time_window(data_dir):
    repo = LogsRepository(data_dir)
    errors = repo.get_logs(level="ERROR", since="2026-09-09T10:26:00Z", until="2026-09-09T10:28:00Z")
    assert len(errors) > 0
    assert all(e["level"] == "ERROR" for e in errors)
    assert all("2026-09-09T10:26:00Z" <= e["timestamp"] <= "2026-09-09T10:28:00Z" for e in errors)


def test_logs_repository_no_match_returns_empty_list(data_dir):
    repo = LogsRepository(data_dir)
    assert repo.get_logs(service="does-not-exist") == []


def test_metrics_repository_known_service(data_dir):
    repo = MetricsRepository(data_dir)
    result = repo.get_metrics(service="payment-api")
    assert result is not None
    assert "error_rate_percent" in result


def test_metrics_repository_unknown_service_returns_none(data_dir):
    repo = MetricsRepository(data_dir)
    assert repo.get_metrics(service="does-not-exist") is None


def test_metrics_repository_narrows_by_metric_name(data_dir):
    repo = MetricsRepository(data_dir)
    result = repo.get_metrics(service="payment-api", metric_names=["error_rate_percent"])
    assert list(result.keys()) == ["error_rate_percent"]


def test_database_repository_returns_pool_snapshots(data_dir):
    repo = DatabaseRepository(data_dir)
    result = repo.get_database_metrics(database="postgres-payments")
    snapshots = result["postgres-payments"]["snapshots"]
    assert len(snapshots) > 0
    # The pool should show exhaustion: active connections reach max_connections.
    max_conn = result["postgres-payments"]["max_connections"]
    assert any(s["active_connections"] == max_conn for s in snapshots)


def test_deployments_repository_finds_payment_api_deploy(data_dir):
    repo = DeploymentsRepository(data_dir)
    results = repo.get_deployments(service="payment-api")
    versions = {d["version"] for d in results}
    assert "v2.4.1" in versions


def test_traces_repository_finds_failed_trace(data_dir):
    repo = TracesRepository(data_dir)
    failed = repo.get_traces(service="payment-api", status_code=500)
    assert len(failed) > 0
    assert all(t["status_code"] == 500 for t in failed)


def test_git_repository_finds_relevant_commit(data_dir):
    repo = GitRepository(data_dir)
    commits = repo.get_commits(service="payment-api")
    shas = {c["sha"] for c in commits}
    assert "abc123f" in shas
