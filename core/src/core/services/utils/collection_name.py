from pathlib import Path

import xxhash

PREFIX = "code_chunks_"


def get_collection_name(path: Path) -> str:
    path_hash = xxhash.xxh3_64_hexdigest(str(path.absolute()).encode("utf-8"))
    return f"code_chunks_{path_hash[:8]}"
