from dataclasses import dataclass
from pathlib import Path

from loguru import logger
from qdrant_client.models import FieldCondition, Filter, MatchValue

from .qdrant import QdrantVectorDatabase
from .qdrant.types import VectorDocument
from .splitters import TreeSitterSplitter
from .sync import FileSynchronizer, SynchronizerConfig
from .utils import get_collection_name


@dataclass
class IndexingConfig:
    batch_size: int
    chunk_size: int
    chunk_overlap: int
    synchronizer_config: SynchronizerConfig


class IndexingService:
    def __init__(self, vector_database: QdrantVectorDatabase, config: IndexingConfig):
        self.batch_size = config.batch_size
        self.vector_database = vector_database
        self.code_splitter = TreeSitterSplitter(
            chunk_size=config.chunk_size,
            chunk_overlap=config.chunk_overlap,
        )
        self.syncrhonizer_config = config.synchronizer_config
        self.synchronizers: dict[str, FileSynchronizer] = {}

    async def delete(self, codebase_path: Path) -> None:
        collection_name = get_collection_name(codebase_path)
        collection_exists = await self.vector_database.has_collection(collection_name)

        if collection_exists:
            await self.vector_database.drop_collection(collection_name)

        await FileSynchronizer(
            codebase_path, self.syncrhonizer_config
        ).delete_snapshot()

        if codebase_path is self.synchronizers:
            del self.synchronizers[collection_name]

    async def index(self, codebase_path: Path, force_reindex: bool = False):
        """Index a codebase, automatically handling initial indexing or incremental reindexing.

        Args:
            codebase_path: Path to the codebase to index
            force_reindex: Whether to force a complete reindexing

        Returns:
            IndexingStats with information about the indexing operation
        """
        codebase_path = codebase_path.resolve()

        logger.debug("Starting indexing for codebase: {}", codebase_path)

        collection_name = get_collection_name(codebase_path)
        collection_exists = await self.vector_database.has_collection(collection_name)

        if not collection_exists or force_reindex:
            logger.info(
                "Performing {} indexing for codebase: {}",
                "initial" if not collection_exists else "forced",
                codebase_path,
            )
            return await self._perform_initial_indexing(codebase_path, force_reindex)
        else:
            logger.info(
                "Performing incremental reindexing for codebase: {}", codebase_path
            )
            return await self._perform_incremental_reindexing(codebase_path)

    async def _perform_initial_indexing(
        self, codebase_path: Path, force_reindex: bool = False
    ):
        await self._prepare_collection(codebase_path, force_reindex)

        collecation_name = get_collection_name(codebase_path)

        changes = await self.synchronizers[collecation_name].check_for_changes()
        code_files = [Path(p).resolve() for p in changes.added]

        logger.debug("Found {} code files", len(code_files))

        if not code_files:
            return

        await self._process_file_list(code_files, codebase_path)

    async def _perform_incremental_reindexing(self, codebase_path: Path):
        collection_name = get_collection_name(codebase_path)

        synchronizer = self.synchronizers.get(collection_name)
        if not synchronizer:
            synchronizer = FileSynchronizer(codebase_path, self.syncrhonizer_config)
            await synchronizer.initialize()
            self.synchronizers[collection_name] = synchronizer

        current_synchronizer = self.synchronizers[collection_name]

        changes = await current_synchronizer.check_for_changes()

        total_changes = (
            len(changes.added) + len(changes.removed) + len(changes.modified)
        )

        if total_changes == 0:
            logger.debug("No file changes detected")
            return

        for file_path in changes.removed + changes.modified:
            await self._delete_file_chunks(collection_name, file_path)

        to_add = [
            Path(file_path).resolve() for file_path in changes.added + changes.modified
        ]

        await self._process_file_list(to_add, codebase_path)

        logger.debug(
            "Incremental reindexing complete. Added: {}, Removed: {}, Modified: {}",
            len(changes.added),
            len(changes.removed),
            len(changes.modified),
        )

    async def _prepare_collection(
        self, codebase_path: Path, force_reindex: bool = False
    ) -> None:
        collection_name = get_collection_name(codebase_path)

        collection_exists = await self.vector_database.has_collection(collection_name)

        if collection_name in self.synchronizers and force_reindex:
            await self.synchronizers[collection_name].delete_snapshot()
            del self.synchronizers[collection_name]

        self.synchronizers[collection_name] = FileSynchronizer(
            codebase_path, self.syncrhonizer_config
        )

        if collection_exists and not force_reindex:
            logger.debug(
                "Collection {} already exists, skipping creation", collection_name
            )
            return

        if collection_exists and force_reindex:
            logger.debug(
                "Dropping existing collection {} for force reindex", collection_name
            )
            await self.vector_database.drop_collection(collection_name)

        await self.vector_database.create_collection(collection_name)
        logger.debug("Collection {} created successfully", collection_name)

    def _matches_ignore_pattern(self, relative_path: Path) -> bool:
        if not self.syncrhonizer_config.ignore_patterns:
            return False

        import fnmatch
        import os

        normalized_path = str(relative_path).replace(os.sep, "/")

        for pattern in self.syncrhonizer_config.ignore_patterns:
            if fnmatch.fnmatch(normalized_path, pattern):
                return True

        return False

    async def _process_file_list(
        self, file_paths: list[Path], codebase_path: Path
    ) -> None:
        payloads = []

        for _, file_path in enumerate(file_paths):
            content = file_path.read_text(encoding="utf-8")
            chunks = await self.code_splitter.split(content, file_path)

            for chunk in chunks:
                relative_path = Path(chunk.file_path).relative_to(codebase_path)
                file_extension = Path(chunk.file_path).suffix

                payload = VectorDocument(
                    content=chunk.content,
                    relative_path=str(relative_path),
                    start_line=chunk.start_line,
                    end_line=chunk.end_line,
                    file_extension=file_extension,
                    metadata={
                        "language": chunk.language,
                        "codebasePath": str(codebase_path),
                    },
                )
                payloads.append(payload)

        collection_name = get_collection_name(codebase_path)
        await self.vector_database.upload_documents(collection_name, payloads)

    async def _delete_file_chunks(
        self, collection_name: str, relative_path: str
    ) -> None:
        filter_condition = Filter(
            must=[
                FieldCondition(
                    key="relative_path", match=MatchValue(value=relative_path)
                )
            ]
        )

        try:
            await self.vector_database.delete(collection_name, filter_condition)
            logger.info("Deleted chunks for file: {}", relative_path)
        except Exception as e:
            logger.error("Error deleting chunks for file {}: {}", relative_path, e)
            raise
