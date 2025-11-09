import json
from pathlib import Path

import xxhash

from .repository import FileRecord, FileStateRepository

SNAPSHOT_VERSION = 1


class SnapshotFileStateRepository(FileStateRepository):
    def __init__(self, snapshots_dir: Path | None = None) -> None:
        self.snapshots_dir = (
            (snapshots_dir or (Path.home() / ".code-context" / "snapshots"))
            .expanduser()
            .resolve()
        )
        self.snapshots_dir.mkdir(parents=True, exist_ok=True)

    def has_state(self, codebase_path: Path) -> bool:
        return self._snapshot_path_for(codebase_path).exists()

    def load(self, codebase_path: Path) -> dict[str, FileRecord]:
        path = self._snapshot_path_for(codebase_path)
        if not path.exists():
            return {}
        try:
            raw = path.read_text(encoding="utf-8")
            data = json.loads(raw)
        except Exception:
            return {}
        if int(data.get("version", 0)) != SNAPSHOT_VERSION:
            return {}
        files = data.get("files", {})
        return {p: FileRecord.from_dict(rec) for p, rec in files.items()}

    def save(self, codebase_path: Path, files: dict[str, FileRecord]) -> None:
        payload = {
            "version": SNAPSHOT_VERSION,
            "files": {path: record.to_dict() for path, record in files.items()},
        }
        snapshot_path = self._snapshot_path_for(codebase_path)
        snapshot_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def delete(self, codebase_path: Path) -> None:
        path = self._snapshot_path_for(codebase_path)
        if path.exists():
            path.unlink()

    def _snapshot_path_for(self, codebase_path: Path) -> Path:
        resolved = str(codebase_path.expanduser().resolve())
        name = xxhash.xxh3_64_hexdigest(resolved.encode("utf-8"))
        return self.snapshots_dir / f"{name}.json"
