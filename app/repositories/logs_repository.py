from pathlib import Path

from app.repositories.base import JsonFileRepository


class LogsRepository(JsonFileRepository):
    def __init__(self, data_dir: Path) -> None:
        super().__init__(data_dir, "logs.json")

    def get_logs(
        self,
        service: str | None = None,
        level: str | None = None,
        since: str | None = None,
        until: str | None = None,
    ) -> list[dict]:
        """Return log entries matching all given filters.

        Timestamps are fixed-width ISO 8601 UTC strings (e.g.
        "2026-09-09T10:27:10Z"), so plain string comparison sorts and
        bounds them correctly without a parsing step.
        """
        entries = self._load()
        if service:
            entries = [e for e in entries if e["service"] == service]
        if level:
            entries = [e for e in entries if e["level"] == level.upper()]
        if since:
            entries = [e for e in entries if e["timestamp"] >= since]
        if until:
            entries = [e for e in entries if e["timestamp"] <= until]
        return entries
