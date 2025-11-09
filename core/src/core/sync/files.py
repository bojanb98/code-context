from pathlib import Path

from loguru import logger

from .comparator import compare_snapshot_to_current
from .content_readers import FileContentReader, LocalFileContentReader
from .file_listing import FileLister, LocalFileLister
from .hash_utils import hash_file
from .state import FileRecord, FileStateRepository, SnapshotFileStateRepository
from .types import DetectedChanges
from .util import DEFAULT_IGNORE_PATTERNS


class FileSynchronizer:

    def __init__(
        self,
        ignore_patterns: list[str] | None = None,
        file_state_repository: FileStateRepository = SnapshotFileStateRepository(),
        file_content_reader: FileContentReader = LocalFileContentReader(),
        file_lister: FileLister = LocalFileLister(),
    ) -> None:
        self.state_repository = file_state_repository
        self.content_reader = file_content_reader
        self.file_lister = file_lister

        self.ignore_patterns = frozenset(
            (ignore_patterns or []) + DEFAULT_IGNORE_PATTERNS
        )

    async def check_for_changes(self, codebase_path: Path) -> DetectedChanges:
        codebase_path = codebase_path.expanduser().resolve()
        current_meta = await self.file_lister.list_metadata(
            codebase_path, self.ignore_patterns
        )

        if not self.state_repository.has_state(codebase_path):
            initial_records = self._build_snapshot_records(
                codebase_path, current_meta, {}
            )
            self.state_repository.save(codebase_path, initial_records)
            return DetectedChanges(added=sorted(initial_records.keys()))

        old_files = self.state_repository.load(codebase_path)

        changes = await compare_snapshot_to_current(
            codebase_path, old_files, current_meta, self.content_reader
        )

        if changes.added or changes.modified or changes.removed:
            new_records = self._build_snapshot_records(
                codebase_path, current_meta, old_files
            )
            self.state_repository.save(codebase_path, new_records)

        return changes

    async def delete_snapshot(self, codebase_path: Path) -> None:
        """
        Delete the snapshot file for the given codebase path (if present).

        Raises:
            OSError: if filesystem unlink fails for reasons other than file not existing.
        """
        codebase_path = codebase_path.expanduser().resolve()

        try:
            if self.state_repository.has_state(codebase_path):
                self.state_repository.delete(codebase_path)
                logger.debug("Deleted snapshot for {}", codebase_path)
            else:
                logger.debug("Snapshot not found (already deleted): {}", codebase_path)
        except OSError as exc:
            logger.error("Failed to delete snapshot for {}: {}", codebase_path, exc)
            raise

    def _build_snapshot_records(
        self,
        codebase_path: Path,
        meta_map: dict[str, tuple[int, float, int | None]],
        prev_snapshot: dict[str, FileRecord],
    ) -> dict[str, FileRecord]:
        records: dict[str, FileRecord] = {}
        for rel_path, (size, mtime, inode) in meta_map.items():
            previous = prev_snapshot.get(rel_path)
            if (
                previous
                and previous.size == size
                and previous.mtime == mtime
                and previous.inode == inode
            ):
                records[rel_path] = previous
                continue

            file_path = codebase_path / rel_path
            try:
                digest = hash_file(file_path, self.content_reader)
            except Exception:
                continue
            records[rel_path] = FileRecord(
                size=size,
                mtime=mtime,
                inode=inode,
                hash=digest,
            )
        return records
