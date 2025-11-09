from pathlib import Path
from typing import Iterable, Protocol


class FileContentReader(Protocol):

    def iter_bytes(self, path: Path, chunk_size: int = 65536) -> Iterable[bytes]: ...

    def read_text(self, path: Path, encoding: str = "utf-8") -> str: ...
