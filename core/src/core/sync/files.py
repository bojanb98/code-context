import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path

from loguru import logger

from core.splitters import SUPPORTED_EXTENSIONS

from .merkle import MerkleDAG
from .util import DEFAULT_IGNORE_PATTERNS


@dataclass
class SynchronizerConfig:
    snapshot_dir: str
    ignore_patterns: list[str] = []


@dataclass
class DetectedChanges:
    added: list[str] = []
    modified: list[str] = []
    removed: list[str] = []


class FileSynchronizer:

    def __init__(self, root_dir: Path, config: SynchronizerConfig) -> None:
        self.root_dir = root_dir.resolve()
        self.snapshot_dir = Path(config.snapshot_dir).resolve()
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)
        self.snapshot_path = self._get_snapshot_path(self.root_dir, self.snapshot_dir)
        self.ignore_patterns = set(config.ignore_patterns + DEFAULT_IGNORE_PATTERNS)
        self.file_hashes: dict[str, str] = {}
        self.merkle_dag = MerkleDAG()

    def _get_snapshot_path(self, codebase_path: Path, snapshot_dir: Path) -> Path:
        path_hash = hashlib.md5(str(codebase_path).encode("utf-8")).hexdigest()
        return snapshot_dir / f"{path_hash}.json"

    async def _hash_file(self, file_path: Path) -> str:
        if not file_path.is_file():
            raise ValueError(f"Path is not a file: {file_path}")

        content = file_path.read_text(encoding="utf-8")
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    async def _generate_file_hashes(self, directory: Path) -> dict[str, str]:
        file_hashes: dict[str, str] = {}

        try:
            entries = list(directory.iterdir())
        except (OSError, PermissionError) as e:
            logger.warning("Cannot read directory {}: {}", directory, e)
            return file_hashes

        for entry in entries:
            relative_path = entry.relative_to(self.root_dir)

            if self._should_ignore(relative_path, entry.is_dir()):
                continue

            try:
                if entry.is_dir():
                    sub_hashes = await self._generate_file_hashes(entry)
                    file_hashes.update(sub_hashes)
                elif entry.is_file():
                    # Hash the file
                    file_hash = await self._hash_file(entry)
                    file_hashes[str(relative_path)] = file_hash

            except (OSError, PermissionError) as e:
                logger.warning("Cannot process {}: {}", entry, e)
                continue

        return file_hashes

    def _should_ignore(self, relative_path: Path, is_directory: bool = False) -> bool:
        if any(part.startswith(".") for part in relative_path.parts):
            return True

        if not is_directory and relative_path.suffix not in SUPPORTED_EXTENSIONS:
            return True

        if not self.ignore_patterns:
            return False

        normalized_path = str(relative_path).replace(os.sep, "/").strip("/")

        if not normalized_path:
            return False

        for pattern in self.ignore_patterns:
            if self._match_pattern(normalized_path, pattern, is_directory):
                return True

        return False

    def _match_pattern(
        self, file_path: str, pattern: str, is_directory: bool = False
    ) -> bool:
        clean_path = file_path.strip("/")
        clean_pattern = pattern.strip("/")

        if not clean_path or not clean_pattern:
            return False

        # Handle directory patterns (ending with /)
        if pattern.endswith("/"):
            if not is_directory:
                return False

            dir_pattern = clean_pattern[:-1]
            path_parts = clean_path.split("/")
            return any(
                self._simple_glob_match(part, dir_pattern) for part in path_parts
            )

        # Handle path patterns (containing /)
        if "/" in clean_pattern:
            return self._simple_glob_match(clean_path, clean_pattern)

        # Handle filename patterns (no /) - match against basename
        file_name = Path(clean_path).name
        return self._simple_glob_match(file_name, clean_pattern)

    def _simple_glob_match(self, text: str, pattern: str) -> bool:
        if not text or not pattern:
            return False

        # Convert glob pattern to regex
        import re

        regex_pattern = pattern.replace(".", r"\.").replace("*", ".*")
        regex = re.compile(f"^{regex_pattern}$")
        return bool(regex.match(text))

    def _build_merkle_dag(self, file_hashes: dict[str, str]) -> MerkleDAG:
        dag = MerkleDAG()

        # Sort paths for consistent ordering
        sorted_paths = sorted(file_hashes.keys())

        # Create a root node for the entire directory
        combined_hashes = "".join(file_hashes[path] for path in sorted_paths)
        root_node_data = f"root:{combined_hashes}"
        root_node_id = dag.add_node(root_node_data)

        # Add each file as a child of the root
        for path in sorted_paths:
            file_data = f"{path}:{file_hashes[path]}"
            dag.add_node(file_data, root_node_id)

        return dag

    async def initialize(self) -> None:
        """Initialize the synchronizer.

        Loads existing snapshot or creates a new one.
        """
        logger.info("Initializing file synchronizer for {}", self.root_dir)
        await self._load_snapshot()
        self.merkle_dag = self._build_merkle_dag(self.file_hashes)
        logger.info(
            f"File synchronizer initialized with {len(self.file_hashes)} file hashes"
        )

    async def check_for_changes(self) -> DetectedChanges:
        """Check for file changes since last synchronization.

        Returns:
            Dictionary with keys 'added', 'removed', 'modified' containing lists of file paths
        """
        logger.info("Checking for file changes...")

        # Generate current file hashes
        new_file_hashes = await self._generate_file_hashes(self.root_dir)
        new_merkle_dag = self._build_merkle_dag(new_file_hashes)

        # Compare the DAGs
        changes = MerkleDAG.compare(self.merkle_dag, new_merkle_dag)

        # If there are changes, do detailed file-level comparison
        if any(changes.values()):
            logger.info("Merkle DAG has changed. Comparing file states...")
            file_changes = self._compare_states(self.file_hashes, new_file_hashes)

            # Update stored state
            self.file_hashes = new_file_hashes
            self.merkle_dag = new_merkle_dag
            await self._save_snapshot()

            logger.info(
                f"Found changes: {len(file_changes['added'])} added, "
                f"{len(file_changes['removed'])} removed, "
                f"{len(file_changes['modified'])} modified"
            )
            return DetectedChanges(
                added=file_changes["added"],
                modified=file_changes["modified"],
                removed=file_changes["removed"],
            )

        logger.info("No changes detected based on Merkle DAG comparison")
        return DetectedChanges()

    def _compare_states(
        self,
        old_hashes: dict[str, str],
        new_hashes: dict[str, str],
    ) -> dict[str, list[str]]:
        added: list[str] = []
        removed: list[str] = []
        modified: list[str] = []

        # Find added and modified files
        for file_path, file_hash in new_hashes.items():
            if file_path not in old_hashes:
                added.append(file_path)
            elif old_hashes[file_path] != file_hash:
                modified.append(file_path)

        # Find removed files
        for file_path in old_hashes:
            if file_path not in new_hashes:
                removed.append(file_path)

        return {"added": added, "removed": removed, "modified": modified}

    def get_file_hash(self, file_path: str) -> str | None:
        """Get stored hash for a file.

        Args:
            file_path: Relative file path

        Returns:
            File hash or None if not found
        """
        return self.file_hashes.get(file_path)

    async def _save_snapshot(self) -> None:
        data = {
            "file_hashes": list(self.file_hashes.items()),
            "merkle_dag": self.merkle_dag.serialize(),
        }

        self.snapshot_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        logger.debug("Saved snapshot to {}", self.snapshot_path)

    async def _load_snapshot(self) -> None:
        if not self.snapshot_path.exists():
            self.file_hashes = await self._generate_file_hashes(self.root_dir)
            self.merkle_dag = self._build_merkle_dag(self.file_hashes)
            await self._save_snapshot()
            return

        try:
            data = json.loads(self.snapshot_path.read_text(encoding="utf-8"))

            # Reconstruct file hashes
            self.file_hashes = dict(data.get("file_hashes", []))

            # Reconstruct Merkle DAG
            merkle_data = data.get("merkle_dag")
            if merkle_data:
                self.merkle_dag = MerkleDAG.deserialize(merkle_data)

            logger.debug("Loaded snapshot from {}", self.snapshot_path)

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning("Failed to load snapshot: {}. Creating new one.", e)
            self.file_hashes = await self._generate_file_hashes(self.root_dir)
            self.merkle_dag = self._build_merkle_dag(self.file_hashes)
            await self._save_snapshot()

    async def delete_snapshot(self) -> None:
        """Delete snapshot file for a codebase.

        Args:
            codebase_path: Path to the codebase
        """
        try:
            if self.snapshot_path.exists():
                self.snapshot_path.unlink()
                logger.debug("Deleted snapshot file: {}", self.snapshot_path)
            else:
                logger.debug(
                    "Snapshot file not found (already deleted): {}", self.snapshot_path
                )

        except OSError as e:
            logger.error("Failed to delete snapshot file {}: {}", self.snapshot_path, e)
            raise
