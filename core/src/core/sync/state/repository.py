from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(slots=True)
class FileRecord:
    size: int
    mtime: float
    inode: int | None
    hash: str

    def to_dict(self) -> dict:
        return {
            "size": self.size,
            "mtime": self.mtime,
            "inode": self.inode,
            "hash": self.hash,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "FileRecord":
        return cls(
            size=int(d["size"]),
            mtime=float(d["mtime"]),
            inode=d.get("inode"),
            hash=str(d["hash"]),
        )


class FileStateRepository(Protocol):
    def has_state(self, codebase_path: Path) -> bool: ...

    def load(self, codebase_path: Path) -> dict[str, FileRecord]: ...

    def save(self, codebase_path: Path, files: dict[str, FileRecord]) -> None: ...

    def delete(self, codebase_path: Path) -> None: ...
