import fnmatch
import os
from pathlib import Path

from core.splitters import is_file_supported

from .protocol import FileLister


class LocalFileLister(FileLister):

    async def list_metadata(
        self, root: Path, ignore_patterns: list[str] | frozenset[str] | None
    ) -> dict[str, tuple[int, float, int | None]]:
        root = root.resolve()
        result: dict[str, tuple[int, float, int | None]] = {}
        stack: list[Path] = [root]

        gitignore_map: dict[str, list[tuple[str, bool]]] = {}
        global_patterns: list[tuple[str, bool]] = [
            (p.replace(os.sep, "/").strip("/"), False) for p in (ignore_patterns or [])
        ]

        while stack:
            directory = stack.pop()
            _record_gitignore_patterns(directory, root, gitignore_map)
            _collect_entries(
                directory,
                root,
                stack,
                result,
                global_patterns,
                gitignore_map,
            )

        return result


def _record_gitignore_patterns(
    directory: Path,
    root: Path,
    gitignore_map: dict[str, list[tuple[str, bool]]],
) -> None:
    gitignore_file = directory / ".gitignore"
    if not gitignore_file.is_file():
        return
    key = (
        ""
        if directory.resolve() == root.resolve()
        else str(directory.relative_to(root)).replace(os.sep, "/").strip("/")
    )
    gitignore_map[key] = _parse_gitignore_file(gitignore_file, root)


def _collect_entries(
    directory: Path,
    root: Path,
    stack: list[Path],
    result: dict[str, tuple[int, float, int | None]],
    global_patterns: list[tuple[str, bool]],
    gitignore_map: dict[str, list[tuple[str, bool]]],
) -> None:
    try:
        with os.scandir(directory) as iterator:
            for entry in iterator:
                try:
                    rel = Path(entry.path).relative_to(root)
                except Exception:
                    rel = Path(str(entry.path).replace(str(root) + os.sep, "", 1))

                if _is_ignored(
                    rel,
                    entry.is_dir(follow_symlinks=False),
                    global_patterns,
                    gitignore_map,
                ):
                    continue

                if entry.is_dir(follow_symlinks=False):
                    stack.append(Path(entry.path))
                    continue

                if entry.is_file(follow_symlinks=False):
                    try:
                        stat_info = entry.stat(follow_symlinks=False)
                        inode = getattr(stat_info, "st_ino", None)
                        result[str(rel)] = (
                            stat_info.st_size,
                            stat_info.st_mtime,
                            int(inode) if inode is not None else None,
                        )
                    except Exception:
                        continue
    except Exception:
        return


def _parse_gitignore_file(gitignore_path: Path, root: Path) -> list[tuple[str, bool]]:
    try:
        raw = gitignore_path.read_text(encoding="utf-8")
    except Exception:
        return []

    if gitignore_path.parent.resolve() == root.resolve():
        dir_rel = ""
    else:
        dir_rel = (
            str(gitignore_path.parent.relative_to(root)).replace(os.sep, "/").strip("/")
        )

    parsed: list[tuple[str, bool]] = []
    for raw_line in raw.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        is_negated = line.startswith("!")
        if is_negated:
            line = line[1:].lstrip()

        trailing_slash = line.endswith("/")

        if line.startswith("./"):
            line = line[2:]

        if line.startswith("/"):
            anchored = line.lstrip("/")
            pattern = f"{dir_rel}/{anchored}" if dir_rel else anchored
        elif "/" in line:
            pattern = f"{dir_rel}/{line}" if dir_rel else line
        else:
            pattern = line

        if trailing_slash and not pattern.endswith("/"):
            pattern = f"{pattern}/"

        pattern = pattern.replace(os.sep, "/").strip("/")
        if pattern == "":
            continue
        parsed.append((pattern, is_negated))
    return parsed


def _is_ignored(
    rel_path: Path,
    is_directory: bool,
    global_patterns: list[tuple[str, bool]],
    gitignore_map: dict[str, list[tuple[str, bool]]],
) -> bool:
    if any(part.startswith(".") for part in rel_path.parts):
        return True

    if not is_directory and not is_file_supported(rel_path):
        return True

    normalized = str(rel_path).replace(os.sep, "/").strip("/")
    if not normalized:
        return False

    patterns: list[tuple[str, bool]] = []
    patterns.extend(global_patterns)
    for ancestor in _ancestors_for(rel_path):
        ancestor_patterns = gitignore_map.get(ancestor)
        if ancestor_patterns:
            patterns.extend(ancestor_patterns)

    ignored = False
    for pattern, is_negated in patterns:
        if _match(normalized, pattern, is_directory):
            ignored = not is_negated
    return ignored


def _ancestors_for(rel: Path) -> list[str]:
    parent = rel.parent
    if parent in (Path("."), Path("")):
        return [""]
    parts = list(parent.parts)
    ancestors: list[str] = [""]
    for index in range(len(parts)):
        ancestors.append("/".join(parts[: index + 1]).strip("/"))
    return ancestors


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
