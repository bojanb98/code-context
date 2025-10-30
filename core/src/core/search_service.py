from pathlib import Path

from loguru import logger

from .qdrant.client import QdrantVectorDatabase
from .qdrant.types import SearchResult
from .utils import get_collection_name


class SearchService:
    def __init__(self, vector_database: QdrantVectorDatabase):
        self.vector_database = vector_database

    async def search(
        self,
        codebase_path: Path,
        query: str,
        top_k: int = 5,
        threshold: float = 0.5,
    ) -> list[SearchResult]:
        """Search indexed code semantically.

        Args:
            codebase_path: Path to the codebase to search in
            query: Search query (must not be empty)
            top_k: Number of results to return (1-50)
            threshold: Similarity threshold (0.0-1.0)

        Returns:
            List of search results

        Raises:
            CollectionNotIndexedError: If the codebase is not indexed
            ValueError: If query is empty or parameters are invalid
        """
        if not query or query.strip() == "":
            raise ValueError("Search query cannot be empty")

        if not (1 <= top_k <= 50):
            raise ValueError("top_k must be between 1 and 50")

        if not (0.0 <= threshold <= 1.0):
            raise ValueError("threshold must be between 0.0 and 1.0")

        codebase_path = codebase_path.resolve()
        collection_name = get_collection_name(codebase_path)

        logger.debug("Searching in codebase: {}", codebase_path)

        if not await self.vector_database.has_collection(collection_name):
            logger.warning(
                "Collection '{}' does not exist for codebase '{}'",
                collection_name,
                codebase_path,
            )
            raise RuntimeError(
                f"Collection not indexed {collection_name}, path: {codebase_path}"
            )

        logger.debug("Searching with query: '{}'", query)
        results = await self.vector_database.search(
            collection_name, query, top_k, threshold
        )

        logger.debug("Found {} relevant results", len(results))
        return results
