import fnmatch
import os
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import xxhash

from core.splitters import is_file_supported

from .types import FileRecord


def _file_hash(path: Path, chunk_size: int = 65536) -> str:
    h = xxhash.xxh3_128()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()


def _match(file_path: str, pattern: str, is_dir: bool) -> bool:
    """
    Match a normalized file path (forward-slash, no leading slash) against a pattern.

    The matching rules are adapted from the previous implementation:
    - pattern ending with "/" => only matches directories; match against any path segment
    - pattern contains "/" (not ending) => treat as a path pattern and fnmatch the whole relative path
    - pattern without "/" => fnmatch against basename
    """
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
        # pattern contains directory components: match against the full (relative) path
        return fnmatch.fnmatchcase(file_path, clean)
    # pattern without slash matches the basename
    basename = Path(file_path).name
    return fnmatch.fnmatchcase(basename, clean)


def _parse_gitignore_file(gitignore_path: Path, root: Path) -> List[Tuple[str, bool]]:
    """
    Parse a .gitignore file and return a list of (pattern, is_negation).
    The returned patterns are expressed *relative to the repository root* when appropriate
    so they can be compared against normalized relative paths produced by the scanner.

    Supported subset:
      - blank lines and comments (#) ignored
      - negation with leading '!'
      - leading slash '/' anchors pattern to .gitignore directory
      - patterns with slashes are treated as path patterns relative to .gitignore directory
      - patterns without slash match basenames (and will be applied only to descendants of the .gitignore dir)
      - trailing slash retains directory-only semantics
    """
    try:
        raw = gitignore_path.read_text(encoding="utf-8")
    except Exception:
        return []

    dir_rel = (
        ""  # empty string means repository root
        if gitignore_path.parent.resolve() == root.resolve()
        else str(gitignore_path.parent.relative_to(root))
        .replace(os.sep, "/")
        .strip("/")
    )

    parsed: List[Tuple[str, bool]] = []
    for raw_line in raw.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        is_neg = line.startswith("!")
        if is_neg:
            line = line[1:].lstrip()

        # Keep trailing slash if present (directory-only pattern)
        trailing_slash = line.endswith("/")

        # Strip leading ./ (common in some .gitignore) and normalize
        if line.startswith("./"):
            line = line[2:]

        if line.startswith("/"):
            # anchored to the .gitignore directory
            anchored = line.lstrip("/")
            pat = f"{dir_rel}/{anchored}" if dir_rel else anchored
        elif "/" in line:
            # contains a slash: relative to the .gitignore directory
            pat = f"{dir_rel}/{line}" if dir_rel else line
        else:
            # no slash: basename match; keep as-is (will match only descendants because we only
            # apply these patterns for paths under this .gitignore's directory)
            pat = line

        if trailing_slash and not pat.endswith("/"):
            pat = pat + "/"

        pat = pat.replace(os.sep, "/").strip("/")
        # keep empty string for root-based patterns if that makes sense, but prevent blank
        if pat == "":
            # a pattern that normalizes to empty is meaningless; skip
            continue
        parsed.append((pat, is_neg))
    return parsed


def _ancestors_for(rel: Path) -> List[str]:
    """
    Return a list of ancestor directory keys (strings normalized with forward slashes),
    ordered from repository root ('') down to the immediate parent of rel.

    Examples:
      rel = Path("a/b/c.txt") => ["", "a", "a/b"]
      rel = Path("x.txt") => [""]
    """
    parent = rel.parent
    if parent == Path(".") or parent == Path(""):
        return [""]
    parts = list(parent.parts)
    ancestors: List[str] = [""]
    for i in range(len(parts)):
        anc = "/".join(parts[: i + 1]).strip("/")
        ancestors.append(anc)
    return ancestors


async def scan_metadata(
    root: Path, ignore_patterns: Iterable[str] | frozenset[str] = frozenset()
) -> dict[str, tuple[int, float, int | None]]:
    """
    Fast metadata-only scan: returns mapping relative_path -> (size, mtime, inode).

    This function now:
      - accepts the usual global ignore patterns (the patterns you pass from FileSynchronizer)
      - discovers .gitignore files and parses them
      - applies combined ignore rules (global first, then ancestor .gitignore patterns from root->leaf).
    """
    root = root.resolve()
    result: dict[str, tuple[int, float, int | None]] = {}
    stack: list[Path] = [root]

    # Map directory-relative-string -> list[(pattern, is_neg)]
    gitignore_map: Dict[str, List[Tuple[str, bool]]] = {}

    # Normalize global ignore patterns into list[(pattern, False)]
    global_patterns: List[Tuple[str, bool]] = [
        (p.replace(os.sep, "/").strip("/"), False) for p in (ignore_patterns or [])
    ]

    while stack:
        directory = stack.pop()
        try:
            # detect .gitignore in this directory before iterating entries so entries
            # under this directory are evaluated with these patterns applied
            gitignore_file = directory / ".gitignore"
            if gitignore_file.is_file():
                key = (
                    ""
                    if directory.resolve() == root.resolve()
                    else str(directory.relative_to(root))
                    .replace(os.sep, "/")
                    .strip("/")
                )
                gitignore_map[key] = _parse_gitignore_file(gitignore_file, root)

            with os.scandir(directory) as it:
                for entry in it:
                    try:
                        rel = Path(entry.path).relative_to(root)
                    except Exception:
                        # fallback (robustness on strange mounts)
                        rel = Path(str(entry.path).replace(str(root) + os.sep, "", 1))

                    # Build an ignore checker closure for this rel
                    def _is_ignored(relative_path: Path, is_directory: bool) -> bool:
                        # KEEP previous behavior: ignore dotfile entries unconditionally
                        if any(part.startswith(".") for part in relative_path.parts):
                            return True

                        if not is_directory and not is_file_supported(relative_path):
                            return True

                        normalized = str(relative_path).replace(os.sep, "/").strip("/")
                        if not normalized:
                            return False

                        # Collect patterns, in order:
                        # 1) global patterns
                        # 2) ancestor .gitignore patterns from root -> closest parent
                        patterns: List[Tuple[str, bool]] = []
                        patterns.extend(global_patterns)
                        for anc in _ancestors_for(relative_path):
                            anc_patterns = gitignore_map.get(anc)
                            if anc_patterns:
                                patterns.extend(anc_patterns)

                        # Evaluate patterns sequentially: last match wins. Track current ignored state.
                        ignored = False
                        for pat, is_neg in patterns:
                            if _match(normalized, pat, is_directory):
                                ignored = not is_neg
                                # keep scanning to let later patterns override
                        return ignored

                    if _is_ignored(rel, entry.is_dir()):
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
                            # skip unreadable file
                            continue
        except Exception:
            # on any directory error, skip it
            continue

    return result


async def scan_and_hash_all(root: Path, ignore_patterns) -> dict[str, FileRecord]:
    """
    NOTE: kept the original signature so callers (FileSynchronizer) don't need to change.
    This function uses scan_metadata (which now supports .gitignore).
    """
    meta = await scan_metadata(root, ignore_patterns)
    records: dict[str, FileRecord] = {}
    for rel, (size, mtime, inode) in meta.items():
        p = root / rel
        try:
            h = _file_hash(p)
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
            h = _file_hash(p)
        except Exception:
            continue
        res[rel] = FileRecord(size=size, mtime=mtime, inode=inode, hash=h)
    return res
