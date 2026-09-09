import json
from pathlib import Path
from typing import Any


class JsonFileRepository:
    """Loads a JSON file from disk once and keeps it in memory.

    Every static-data repository subclasses this. Swapping a data source
    later (e.g. logs -> Datadog) means writing a new repository with the
    same public method signatures and pointing the matching tool at it -
    nothing above the repository layer has to change.
    """

    def __init__(self, data_dir: Path, filename: str) -> None:
        self._path = data_dir / filename
        self._data: Any | None = None

    def _load(self) -> Any:
        if self._data is None:
            with self._path.open(encoding="utf-8") as f:
                self._data = json.load(f)
        return self._data
