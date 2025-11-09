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
from .utils import EmbeddingService, GraphService, get_collection_name


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

    _DEFAULT_GRAPH_LIMIT = 30

    def __init__(
        self,
        client: AsyncQdrantClient,
        code_serivce: EmbeddingService,
        doc_serivce: EmbeddingService | None,
        graph_service: GraphService | None = None,
    ):
        self.client = client
        self.code_serivce = code_serivce
        self.doc_service = doc_serivce
        self.graph_service = graph_service

    async def _perform_search(
        self,
        collection_name: str,
        query_text: str,
        limit: int = 10,
        threshold: float = 0.0,
    ) -> tuple[list[SearchResult], list[str]]:
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
        point_ids: list[str] = []
        for point in search_result.points:
            payload = point.payload or {}
            point_ids.append(str(point.id))
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
        return results, point_ids

    async def search(
        self,
        codebase_path: Path,
        query: str,
        top_k: int = 5,
        threshold: float = 0.5,
        max_graph_hops: int | None = None,
        graph_limit: int | None = None,
    ) -> list[SearchResult]:
        """Search indexed code semantically.

        Args:
            codebase_path: Path to the codebase to search in
            query: Search query (must not be empty)
            has_explanations: Whether codebase was indexed with explanation vector
            top_k: Number of results to return (1-50)
            threshold: Similarity threshold (0.0-1.0)
            max_graph_hops: Optional graph expansion depth (>=1) to augment results
            graph_limit: Optional limit for number of graph nodes (defaults to 30)

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

        if max_graph_hops is not None and max_graph_hops < 1:
            raise ValueError("max_graph_hops must be >= 1 when provided")

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
        results, point_ids = await self._perform_search(
            collection_name, query, top_k, threshold
        )

        final_results = await self._expand_with_graph(
            collection_name,
            results,
            point_ids,
            graph_limit or self._DEFAULT_GRAPH_LIMIT,
            max_graph_hops,
        )

        logger.debug("Found {} relevant results", len(final_results))
        return final_results

    async def _expand_with_graph(
        self,
        collection_name: str,
        seeds: list[SearchResult],
        seed_ids: list[str],
        limit: int,
        max_graph_hops: int | None,
    ) -> list[SearchResult]:
        if (
            self.graph_service is None
            or max_graph_hops is None
            or not seeds
            or not seed_ids
        ):
            return seeds

        try:
            graph_nodes, _ = await self.graph_service.neighbors(
                collection_name=collection_name,
                node_ids=seed_ids,
                max_hops=max_graph_hops,
            )
        except Exception as exc:
            logger.warning("Graph expansion failed: {}", exc)
            return seeds

        logger.debug(
            "Graph expansion requested (hops=%d) produced %d nodes",
            max_graph_hops,
            len(graph_nodes),
        )

        result_by_id: dict[str, SearchResult] = {}
        ordered_results: list[SearchResult] = []

        for idx, seed in enumerate(seeds):
            if idx >= len(seed_ids):
                break
            seed_id = seed_ids[idx]
            result_by_id[seed_id] = seed
            ordered_results.append(seed)

        for node in graph_nodes:
            node_id = node.id
            if not node_id or node_id in result_by_id:
                continue
            result = SearchResult(
                content=node.content or "",
                doc=node.doc,
                relative_path=node.relative_path or "",
                start_line=node.start_line or 0,
                end_line=node.end_line or 0,
                language=node.language or "unknown",
                score=0.0,
            )
            result_by_id[node_id] = result
            ordered_results.append(result)

            if len(ordered_results) >= limit:
                break

        return ordered_results[:limit]
