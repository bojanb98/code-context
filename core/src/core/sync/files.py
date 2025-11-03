from pathlib import Path

from loguru import logger

from .comparator import compare_snapshot_to_current
from .io import load_snapshot, snapshot_path_for, write_snapshot
from .scanner import build_snapshot_records, scan_and_hash_all, scan_metadata
from .types import DetectedChanges
from .util import DEFAULT_IGNORE_PATTERNS


class FileSynchronizer:

    def __init__(
        self,
        snapshots_dir: Path | None = None,
        ignore_patterns: list[str] | None = None,
    ) -> None:
        self.snapshots_dir = (
            (snapshots_dir or (Path.home() / ".code-context" / "snapshots"))
            .expanduser()
            .resolve()
        )
        self.snapshots_dir.mkdir(parents=True, exist_ok=True)

        self.ignore_patterns = frozenset(
            (ignore_patterns or []) + DEFAULT_IGNORE_PATTERNS
        )

    async def check_for_changes(self, codebase_path: Path) -> DetectedChanges:
        codebase_path = codebase_path.expanduser().resolve()
        snapshot_path = snapshot_path_for(codebase_path, self.snapshots_dir)

        # If no snapshot exists, create initial snapshot (hash every file) and
        # report every file as added.
        if not snapshot_path.exists():
            initial = await scan_and_hash_all(codebase_path, self.ignore_patterns)
            write_snapshot(snapshot_path, initial)
            return DetectedChanges(added=sorted(initial.keys()))

        # Load previous snapshot from disk (synchronizer is ephemeral; always load)
        old_files = load_snapshot(snapshot_path)

        # Fast metadata scan
        current_meta = await scan_metadata(codebase_path, self.ignore_patterns)

        # Compare
        changes = await compare_snapshot_to_current(
            codebase_path, old_files, current_meta
        )

        # If changes occurred, rebuild snapshot records (reusing hashes where unchanged)
        if changes.added or changes.modified or changes.removed:
            new_records = await build_snapshot_records(
                codebase_path, current_meta, old_files
            )
            write_snapshot(snapshot_path, new_records)

        return changes

    async def delete_snapshot(self, codebase_path: Path) -> None:
        """
        Delete the snapshot file for the given codebase path (if present).

        Raises:
            OSError: if filesystem unlink fails for reasons other than file not existing.
        """
        snapshot_path = snapshot_path_for(codebase_path, self.snapshots_dir)

        try:
            if snapshot_path.exists():
                snapshot_path.unlink()
                logger.debug("Deleted snapshot file: {}", snapshot_path)
            else:
                logger.debug(
                    "Snapshot file not found (already deleted): {}", snapshot_path
                )
        except OSError as exc:
            logger.error("Failed to delete snapshot file {}: {}", snapshot_path, exc)
            raise
