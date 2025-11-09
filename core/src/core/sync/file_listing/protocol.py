from pathlib import Path
from typing import Protocol


class FileLister(Protocol):
    async def list_metadata(
        self, root: Path, ignore_patterns: list[str] | frozenset[str] | None
    ) -> dict[str, tuple[int, float, int | None]]: ...
