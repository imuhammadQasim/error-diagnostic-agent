from pathlib import Path

from app.repositories.base import JsonFileRepository


class MetricsRepository(JsonFileRepository):
    def __init__(self, data_dir: Path) -> None:
        super().__init__(data_dir, "metrics.json")

    def list_services(self) -> list[str]:
        return list(self._load().keys())

    def get_metrics(
        self,
        service: str,
        metric_names: list[str] | None = None,
        since: str | None = None,
        until: str | None = None,
    ) -> dict[str, list[dict]] | None:
        """Return one service's time series, optionally narrowed to specific
        metric names and/or a time window. Returns None if the service is
        unknown so the tool layer can report that clearly instead of
        silently returning an empty result.
        """
        all_metrics = self._load()
        if service not in all_metrics:
            return None

        series = all_metrics[service]
        if metric_names:
            series = {name: points for name, points in series.items() if name in metric_names}

        if since or until:
            filtered = {}
            for name, points in series.items():
                pts = points
                if since:
                    pts = [p for p in pts if p["timestamp"] >= since]
                if until:
                    pts = [p for p in pts if p["timestamp"] <= until]
                filtered[name] = pts
            series = filtered

        return series
