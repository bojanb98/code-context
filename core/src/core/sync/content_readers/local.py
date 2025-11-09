from pathlib import Path
from typing import Iterable

from .protocol import FileContentReader


class LocalFileContentReader(FileContentReader):

    def iter_bytes(self, path: Path, chunk_size: int = 65536) -> Iterable[bytes]:
        with path.open("rb") as handle:
            while True:
                chunk = handle.read(chunk_size)
                if not chunk:
                    break
                yield chunk

    def read_text(self, path: Path, encoding: str = "utf-8") -> str:
        return path.read_text(encoding=encoding)
