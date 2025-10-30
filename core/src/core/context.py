from pathlib import Path

from .indexing_service import IndexingConfig, IndexingService
from .qdrant import QdrantConfig, QdrantVectorDatabase, SearchResult
from .search_service import SearchService
from .utils import get_collection_name


class Context:
    def __init__(
        self,
        qdrant_config: QdrantConfig,
        indexing_config: IndexingConfig,
    ) -> None:
        self.vector_database = QdrantVectorDatabase(qdrant_config)
        self.indexing_service = IndexingService(self.vector_database, indexing_config)
        self.search_service = SearchService(self.vector_database)

    async def index(
        self,
        codebase_path: str | Path,
        force_reindex: bool = False,
    ):
        """Index a codebase for semantic search.

        This method intelligently determines whether to perform initial indexing
        or incremental reindexing based on the current state.

        Args:
            codebase_path: Path to the codebase
            force_reindex: Whether to force a complete reindexing

        Returns:
            Indexing statistics
        """
        return await self.indexing_service.index(Path(codebase_path), force_reindex)

    async def search(
        self,
        codebase_path: str | Path,
        query: str,
        top_k: int = 5,
        threshold: float = 0.0,
    ) -> list[SearchResult]:
        """Search indexed code semantically.

        Args:
            codebase_path: Path to the codebase
            query: Search query
            top_k: Number of results to return
            threshold: Similarity threshold

        Returns:
            List of search results

        Raises:
            CollectionNotIndexedError: If the codebase is not indexed
        """
        return await self.search_service.search(
            Path(codebase_path), query, top_k, threshold
        )

    async def has_index(self, codebase_path: Path) -> bool:
        """Check if codebase is indexed.

        Args:
            codebase_path: Path to the codebase

        Returns:
            True if indexed, False otherwise
        """
        collection_name = get_collection_name(codebase_path)
        return await self.vector_database.has_collection(collection_name)

    async def clear_index(self, codebase_path: str | Path) -> None:
        """Clear index for a codebase.

        Args:
            codebase_path: Path to the codebase
        """
        codebase_path = Path(codebase_path).resolve()
        await self.indexing_service.delete(codebase_path)
