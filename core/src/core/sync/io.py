import hashlib
import json
from pathlib import Path

from .types import FileRecord

SNAPSHOT_VERSION = 1


def snapshot_path_for(codebase_path: Path, snapshots_dir: Path) -> Path:
    resolved = str(codebase_path.resolve())
    name = hashlib.md5(resolved.encode("utf-8")).hexdigest()
    return snapshots_dir / f"{name}.json"


def write_snapshot(path: Path, files: dict[str, FileRecord]) -> None:
    payload = {
        "version": SNAPSHOT_VERSION,
        "files": {p: r.to_dict() for p, r in files.items()},
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def load_snapshot(path: Path) -> dict[str, FileRecord]:
    try:
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
        if int(data.get("version", 0)) != SNAPSHOT_VERSION:
            return {}
        return {p: FileRecord.from_dict(d) for p, d in data.get("files", {}).items()}
    except Exception:
        return {}
