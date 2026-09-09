from pathlib import Path

from app.repositories.base import JsonFileRepository


class GitRepository(JsonFileRepository):
    def __init__(self, data_dir: Path) -> None:
        super().__init__(data_dir, "git_commits.json")

    def get_commits(
        self,
        service: str | None = None,
        since: str | None = None,
        until: str | None = None,
    ) -> list[dict]:
        commits = self._load()
        if service:
            commits = [c for c in commits if c["service"] == service]
        if since:
            commits = [c for c in commits if c["timestamp"] >= since]
        if until:
            commits = [c for c in commits if c["timestamp"] <= until]
        return commits
