from pathlib import Path

from app.repositories.base import JsonFileRepository


class TracesRepository(JsonFileRepository):
    def __init__(self, data_dir: Path) -> None:
        super().__init__(data_dir, "traces.json")

    def get_traces(
        self,
        service: str | None = None,
        endpoint: str | None = None,
        status_code: int | None = None,
        since: str | None = None,
        until: str | None = None,
    ) -> list[dict]:
        traces = self._load()
        if service:
            traces = [t for t in traces if t["service"] == service]
        if endpoint:
            traces = [t for t in traces if t["endpoint"] == endpoint]
        if status_code is not None:
            traces = [t for t in traces if t["status_code"] == status_code]
        if since:
            traces = [t for t in traces if t["timestamp"] >= since]
        if until:
            traces = [t for t in traces if t["timestamp"] <= until]
        return traces
