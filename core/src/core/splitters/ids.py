from pathlib import Path

import xxhash

_COMPONENT_SEPARATOR = "\x1f"


def _normalize_file_path(file_path: Path) -> str:
    normalized = file_path.as_posix()

    drive_sep = normalized.find(":/")
    if drive_sep != -1:
        normalized = normalized[drive_sep + 2 :]

    normalized = normalized.lstrip("./")
    normalized = normalized.lstrip("/")
    return normalized or "."


def make_chunk_id_from_components(
    file_path: Path,
    node_type: str,
    parent_id: str | None,
    identifier: str,
) -> str:
    payload = _COMPONENT_SEPARATOR.join(
        (
            _normalize_file_path(file_path),
            node_type,
            parent_id or "",
            identifier,
        )
    )
    return xxhash.xxh3_128_hexdigest(payload.encode("utf-8"))
