from dataclasses import dataclass
from pathlib import Path

from loguru import logger
from qdrant_client import AsyncQdrantClient, models

from .constants import (
    CODE_DENSE,
    CODE_SPARSE,
    DOC_DENSE,
    DOC_SPARSE,
    TEXT_EMBEDDING_MODEL,
)
from .utils import EmbeddingService, get_collection_name


@dataclass
class SearchResult:
    content: str
    doc: str | None
    relative_path: str
    start_line: int
    end_line: int
    language: str
    score: float


class SearchService:
    def __init__(
        self,
        client: AsyncQdrantClient,
        code_serivce: EmbeddingService,
        doc_serivce: EmbeddingService | None,
    ):
        self.client = client
        self.code_serivce = code_serivce
        self.doc_service = doc_serivce

    async def _perform_search(
        self,
        collection_name: str,
        query_text: str,
        limit: int = 10,
        threshold: float = 0.0,
    ) -> list[SearchResult]:
        prefetch = [
            models.Prefetch(
                query=await self.code_serivce.generate_embedding(query_text),
                using=CODE_DENSE,
                limit=limit,
            ),
            models.Prefetch(
                query=models.Document(text=query_text, model=TEXT_EMBEDDING_MODEL),
                using=CODE_SPARSE,
                limit=limit,
            ),
        ]

        if self.doc_service is not None:
            prefetch.append(
                models.Prefetch(
                    query=await self.doc_service.generate_embedding(query_text),
                    using=DOC_DENSE,
                    limit=limit,
                ),
            )
            prefetch.append(
                models.Prefetch(
                    query=models.Document(text=query_text, model=TEXT_EMBEDDING_MODEL),
                    using=DOC_SPARSE,
                    limit=limit,
                ),
            )

        search_result = await self.client.query_points(
            collection_name=collection_name,
            prefetch=prefetch,
            query=models.FusionQuery(fusion=models.Fusion.RRF),
            limit=limit,
            score_threshold=threshold,
        )

        results = []
        for point in search_result.points:
            payload = point.payload or {}
            results.append(
                SearchResult(
                    content=payload.get("content", ""),
                    doc=payload.get("doc", None),
                    relative_path=payload.get("relative_path", ""),
                    start_line=payload.get("start_line", 0),
                    end_line=payload.get("end_line", 0),
                    language=payload.get("language", "unknown"),
                    score=point.score,
                )
            )

        logger.debug("Found {} results for text query", len(results))
        return results

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
            has_explanations: Whether codebase was indexed with explanation vector
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

        codebase_path = codebase_path.expanduser().absolute().resolve()

        collection_name = get_collection_name(codebase_path)

        logger.debug("Searching in codebase: {}", codebase_path)

        if not await self.client.collection_exists(collection_name):
            logger.warning(
                "Collection '{}' does not exist for codebase '{}'",
                collection_name,
                codebase_path,
            )
            raise RuntimeError(
                f"Collection not indexed {collection_name}, path: {codebase_path}"
            )

        logger.debug("Searching with query: '{}'", query)
        results = await self._perform_search(collection_name, query, top_k, threshold)

        logger.debug("Found {} relevant results", len(results))
        return results
