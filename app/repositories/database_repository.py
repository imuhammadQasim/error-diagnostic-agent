from pathlib import Path

from app.repositories.base import JsonFileRepository


class DatabaseRepository(JsonFileRepository):
    def __init__(self, data_dir: Path) -> None:
        super().__init__(data_dir, "database_metrics.json")

    def list_databases(self) -> list[str]:
        return list(self._load().keys())

    def get_database_metrics(
        self,
        database: str | None = None,
        since: str | None = None,
        until: str | None = None,
    ) -> dict:
        """Return connection-pool snapshots and slow queries for one
        database, or for all databases if none is named. Returns {} if a
        named database is unknown.
        """
        all_dbs = self._load()

        if database:
            if database not in all_dbs:
                return {}
            all_dbs = {database: all_dbs[database]}

        if not (since or until):
            return all_dbs

        result = {}
        for name, db in all_dbs.items():
            snapshots = db["snapshots"]
            if since:
                snapshots = [s for s in snapshots if s["timestamp"] >= since]
            if until:
                snapshots = [s for s in snapshots if s["timestamp"] <= until]
            result[name] = {**db, "snapshots": snapshots}
        return result
