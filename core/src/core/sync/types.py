from dataclasses import dataclass, field


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
