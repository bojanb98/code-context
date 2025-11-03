import fnmatch
import hashlib
import os
from pathlib import Path

from core.splitters import SUPPORTED_EXTENSIONS

from .types import FileRecord


def _sha256_of_file(path: Path, chunk_size: int = 65536) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()


def _should_ignore(
    relative_path: Path,
    is_directory: bool = False,
    ignore_patterns: frozenset[str] = frozenset(),
) -> bool:

    if any(part.startswith(".") for part in relative_path.parts):
        return True

    if not is_directory and relative_path.suffix not in SUPPORTED_EXTENSIONS:
        return True

    if not ignore_patterns:
        return False

    normalized = str(relative_path).replace(os.sep, "/").strip("/")
    if not normalized:
        return False

    def _match(file_path: str, pattern: str, is_dir: bool) -> bool:
        clean = pattern.strip("/")
        if not clean:
            return False
        if pattern.endswith("/"):
            if not is_dir:
                return False
            for part in file_path.split("/"):
                if fnmatch.fnmatchcase(part, clean):
                    return True
            return False
        if "/" in clean:
            return fnmatch.fnmatchcase(file_path, clean)
        basename = Path(file_path).name
        return fnmatch.fnmatchcase(basename, clean)

    for pat in ignore_patterns:
        if _match(normalized, pat, is_directory):
            return True
    return False


async def scan_metadata(
    root: Path, ignore_patterns: frozenset[str] = frozenset()
) -> dict[str, tuple[int, float, int | None]]:
    """
    Fast metadata-only scan: returns mapping relative_path -> (size, mtime, inode)
    """
    root = root.resolve()
    result: dict[str, tuple[int, float, int | None]] = {}
    stack: list[Path] = [root]

    while stack:
        directory = stack.pop()
        try:
            with os.scandir(directory) as it:
                for entry in it:
                    try:
                        rel = Path(entry.path).relative_to(root)
                    except Exception:
                        rel = Path(str(entry.path).replace(str(root) + os.sep, "", 1))

                    if _should_ignore(rel, entry.is_dir(), ignore_patterns):
                        continue

                    if entry.is_dir(follow_symlinks=False):
                        stack.append(Path(entry.path))
                    elif entry.is_file(follow_symlinks=False):
                        try:
                            st = entry.stat(follow_symlinks=False)
                            inode = getattr(st, "st_ino", None)
                            result[str(rel)] = (
                                st.st_size,
                                st.st_mtime,
                                int(inode) if inode is not None else None,
                            )
                        except Exception:
                            continue
        except Exception:
            continue

    return result


async def scan_and_hash_all(root: Path, should_ignore) -> dict[str, FileRecord]:
    meta = await scan_metadata(root, should_ignore)
    records: dict[str, FileRecord] = {}
    for rel, (size, mtime, inode) in meta.items():
        p = root / rel
        try:
            h = _sha256_of_file(p)
        except Exception:
            continue
        records[rel] = FileRecord(size=size, mtime=mtime, inode=inode, hash=h)
    return records


async def build_snapshot_records(
    root: Path,
    meta_map: dict[str, tuple[int, float, int | None]],
    prev_snapshot: dict[str, FileRecord],
) -> dict[str, FileRecord]:

    res: dict[str, FileRecord] = {}
    for rel, (size, mtime, inode) in meta_map.items():
        prev = prev_snapshot.get(rel)
        if prev and prev.size == size and prev.mtime == mtime and prev.inode == inode:
            res[rel] = prev
            continue
        p = root / rel
        try:
            h = _sha256_of_file(p)
        except Exception:
            continue
        res[rel] = FileRecord(size=size, mtime=mtime, inode=inode, hash=h)
    return res
