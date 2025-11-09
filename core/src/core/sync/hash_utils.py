from pathlib import Path

import xxhash

from .content_readers import FileContentReader


def hash_file(path: Path, reader: FileContentReader, chunk_size: int = 65536) -> str:
    hasher = xxhash.xxh3_128()
    for chunk in reader.iter_bytes(path, chunk_size):
        hasher.update(chunk)
    return hasher.hexdigest()
