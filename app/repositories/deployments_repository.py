from pathlib import Path

from app.repositories.base import JsonFileRepository


class DeploymentsRepository(JsonFileRepository):
    def __init__(self, data_dir: Path) -> None:
        super().__init__(data_dir, "deployments.json")

    def get_deployments(
        self,
        service: str | None = None,
        since: str | None = None,
        until: str | None = None,
    ) -> list[dict]:
        deployments = self._load()
        if service:
            deployments = [d for d in deployments if d["service"] == service]
        if since:
            deployments = [d for d in deployments if d["deployed_at"] >= since]
        if until:
            deployments = [d for d in deployments if d["deployed_at"] <= until]
        return deployments
