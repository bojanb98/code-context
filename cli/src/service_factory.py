from pathlib import Path
from typing import Literal

from core import (
    EmbeddingService,
    ExplainerService,
    FileSynchronizer,
    IndexingService,
    SearchService,
    TreeSitterSplitter,
)
from loguru import logger
from qdrant_client import AsyncQdrantClient

from config import AppSettings

EmbeddingType = Literal["code", "doc"]


class ServiceFactory:

    def __init__(self, settings: AppSettings) -> None:
        self.settings = settings
        self._client: AsyncQdrantClient | None = None
        self._code_embedding_service: EmbeddingService | None = None
        self._doc_embedding_service: EmbeddingService | None = None
        self._explainer_service: ExplainerService | None = None
        self._synchronizer: FileSynchronizer | None = None
        self._splitter: TreeSitterSplitter | None = None
        self._indexing_service: IndexingService | None = None
        self._search_service: SearchService | None = None
        self.initialize_logger()

    def initialize_logger(self) -> None:
        logger.remove()
        if self.settings.logging.enabled:
            log_file_path = Path(self.settings.logging.log_file_path).expanduser()
            log_file_path.parent.mkdir(parents=True, exist_ok=True)
            logger.add(
                str(log_file_path),
                level="DEBUG",
                rotation="10 MB",
                retention="7 days",
                format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
                enqueue=True,
            )
            logger.debug("Service factory initialized with debug logging")

    async def close(self) -> None:
        """Clean up all resources."""
        if self._client:
            await self._client.close()

        self._client = None
        self._code_embedding_service = None
        self._explainer_service = None
        self._synchronizer = None
        self._splitter = None
        self._indexing_service = None
        self._search_service = None
        self._initialized = False

    def get_client(self) -> AsyncQdrantClient:
        if not self._client:
            self._client = AsyncQdrantClient(
                url=str(self.settings.qdrant.url),
                api_key=self.settings.qdrant.api_key,
                timeout=120,
            )
        return self._client

    def get_code_embedding_service(self) -> EmbeddingService:
        if not self._code_embedding_service:
            self._code_embedding_service = EmbeddingService(
                str(self.settings.code_embedding.url),
                self.settings.code_embedding.api_key,
                self.settings.code_embedding.model,
                self.settings.code_embedding.size,
            )
        return self._code_embedding_service

    def get_doc_embedding_service(self) -> EmbeddingService | None:
        if not self.settings.features.explanation and self.settings.features.docs:
            return None

        if not self._doc_embedding_service:
            self._doc_embedding_service = EmbeddingService(
                str(self.settings.doc_embedding.url),
                self.settings.doc_embedding.api_key,
                self.settings.doc_embedding.model,
                self.settings.doc_embedding.size,
            )
        return self._doc_embedding_service

    def get_explainer_service(self) -> ExplainerService | None:
        if not self.settings.features.explanation:
            return None

        if not self._explainer_service:
            self._explainer_service = ExplainerService(
                str(self.settings.explainer.url),
                self.settings.explainer.api_key,
                self.settings.explainer.model,
                self.settings.explainer.parallelism,
            )
        return self._explainer_service

    def get_synchronizer(self) -> FileSynchronizer:
        if not self._synchronizer:
            self._synchronizer = FileSynchronizer(self.settings.storage.snapshots_dir)
        return self._synchronizer

    def get_splitter(self) -> TreeSitterSplitter:
        if not self._splitter:
            self._splitter = TreeSitterSplitter(
                self.settings.chunking.chunk_size,
                self.settings.chunking.chunk_overlap,
                self.settings.features.docs,
            )
        return self._splitter

    def get_indexing_service(self) -> IndexingService:
        if not self._indexing_service:
            self._indexing_service = IndexingService(
                self.get_client(),
                self.get_synchronizer(),
                self.get_splitter(),
                self.get_code_embedding_service(),
                self.get_doc_embedding_service(),
                self.get_explainer_service(),
            )
        return self._indexing_service

    def get_search_service(self) -> SearchService:
        if not self._search_service:
            self._search_service = SearchService(
                self.get_client(),
                self.get_code_embedding_service(),
                self.get_doc_embedding_service(),
            )
        return self._search_service
