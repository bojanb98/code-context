from dataclasses import dataclass
from pathlib import Path

from loguru import logger
from qdrant_client import AsyncQdrantClient, models

from .constants import CODE_INDEX, EXPLANATION_INDEX, TEXT_INDEX
from .utils import EmbeddingService, get_collection_name


@dataclass
class SearchResult:
    content: str
    explanation: str | None
    relative_path: str
    start_line: int
    end_line: int
    language: str
    score: float


class SearchService:
    def __init__(
        self,
        client: AsyncQdrantClient,
        embedding_service: EmbeddingService,
        code_model: str,
        explanation_model: str,
    ):
        self.client = client
        self.embedding_service = embedding_service
        self.code_model = code_model
        self.explanation_model = explanation_model

    async def _preform_search(
        self,
        collection_name: str,
        query_text: str,
        has_explanations: bool = False,
        limit: int = 10,
        threshold: float = 0.0,
    ) -> list[SearchResult]:
        prefetch = [
            models.Prefetch(
                query=await self.embedding_service.generate_embedding(
                    query_text, self.code_model
                ),
                using=CODE_INDEX,
                limit=limit * 2,
            ),
            models.Prefetch(
                query=models.Document(text=query_text, model=TEXT_INDEX),
                using=TEXT_INDEX,
                limit=limit * 2,
            ),
        ]

        if has_explanations:
            prefetch.append(
                models.Prefetch(
                    query=await self.embedding_service.generate_embedding(
                        query_text, self.explanation_model
                    ),
                    using=EXPLANATION_INDEX,
                    limit=limit * 2,
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
                    explanation=payload.get("explanation", None),
                    relative_path=payload.get("relative_path", ""),
                    start_line=payload.get("start_line", 0),
                    end_line=payload.get("end_line", 0),
                    language=payload.get("metadata", {}).get("language", "unknown"),
                    score=point.score,
                )
            )

        logger.debug("Found {} results for text query", len(results))
        return results

    async def search(
        self,
        codebase_path: Path,
        query: str,
        has_explanations: bool = False,
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

        codebase_path = codebase_path.resolve()
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
        results = await self._preform_search(
            collection_name, query, has_explanations, top_k, threshold
        )

        logger.debug("Found {} relevant results", len(results))
        return results
