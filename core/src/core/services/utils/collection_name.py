import hashlib
from pathlib import Path

PREFIX = "code_chunks_"


def get_collection_name(path: Path) -> str:
    path_hash = hashlib.md5(str(path.absolute()).encode("utf-8")).hexdigest()
    return f"code_chunks_{path_hash[:8]}"
