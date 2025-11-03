from dataclasses import dataclass, field


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


@dataclass
class DetectedChanges:
    added: list[str] = field(default_factory=list)
    modified: list[str] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)

    @property
    def num_changes(self) -> int:
        return len(self.added) + len(self.modified) + len(self.removed)

    @property
    def to_add(self) -> list[str]:
        return self.added + self.modified

    @property
    def to_remove(self) -> list[str]:
        return self.modified + self.removed
