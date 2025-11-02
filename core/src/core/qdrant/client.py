import itertools
import ssl
import uuid
from dataclasses import dataclass
from typing import Any, Literal

from loguru import logger
from openai import AsyncOpenAI as OpenAI
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    Document,
    Filter,
    FilterSelector,
    Fusion,
    FusionQuery,
    Modifier,
    PointStruct,
    PointVectors,
    Prefetch,
    SparseVectorParams,
    VectorParams,
)

from .explainer_service import ExplainerConfig, ExplainerService
from .types import SearchResult, VectorDocument

TEXT_EMBEDDING_MODEL = "Qdrant/bm25"

Embedding = list[float] | Document


@dataclass
class EmbeddingConfig:
    model: str
    provider: Literal["fastembed", "openai"] = "fastembed"
    url: str | None = None
    api_key: str = ""
    size: int | None = None

    def __post_init__(self):
        if self.provider == "openai":
            if self.url is None:
                raise ValueError("URL must be set for openai provider")
            if self.size is None:
                raise ValueError("Size must be set for openai provider")


@dataclass
class QdrantConfig:
    embedding: EmbeddingConfig
    location: Literal["memory", "server"] = "memory"
    url: str | None = None
    api_key: str | None = None
    batch_size: int = 32


class QdrantVectorDatabase:
    def __init__(
        self,
        config: QdrantConfig,
        explainer_config: ExplainerConfig | None = None,
    ) -> None:
        self.embedding = config.embedding
        self._client: QdrantClient = self._create_client(
            config.location, config.url, config.api_key
        )
        self.size = (
            self.client.get_embedding_size(self.embedding.model)
            if self.embedding.provider == "fastembed"
            else self.embedding.size or 768
        )
        self.batch_size = config.batch_size
        self.openai: OpenAI | None = None
        self.explainer: ExplainerService | None = None
        self.error_vector = [0.0 for _ in range(self.size)]
        if explainer_config is not None:
            self.explainer = ExplainerService(explainer_config)

    @property
    def client(self) -> QdrantClient:
        return self._client

    def _get_openai(self) -> OpenAI:
        if self.embedding.provider != "openai":
            raise ValueError("Invalid embedding provider")
        if self.openai is None:
            self.openai = OpenAI(
                base_url=self.embedding.url,
                api_key=self.embedding.api_key,
            )

        return self.openai

    def _create_client(
        self,
        location: Literal["memory", "server"] = "memory",
        url: str | None = None,
        api_key: str | None = None,
    ) -> QdrantClient:
        if location == "memory":
            logger.info("Using in-memory Qdrant client")
            return QdrantClient(":memory:")

        if url is None:
            raise ValueError("Qdrant URL is required for server deployment")

        return QdrantClient(
            url=url, api_key=api_key, verify=ssl.create_default_context()
        )

    async def create_collection(self, collection_name: str) -> None:
        if await self.has_collection(collection_name):
            logger.debug("Collection '{}' already exists", collection_name)
            return

        dense_vectors: dict[str, VectorParams] = {
            "code": VectorParams(
                size=self.size,
                distance=Distance.COSINE,
            )
        }

        if self.explainer is not None:
            dense_vectors["explanation"] = VectorParams(
                size=self.size,
                distance=Distance.COSINE,
            )

        self.client.create_collection(
            collection_name=collection_name,
            vectors_config=dense_vectors,
            sparse_vectors_config={"bm25": SparseVectorParams(modifier=Modifier.IDF)},
        )

        logger.debug("Collection '{}' created successfully", collection_name)

    async def has_collection(self, collection_name: str) -> bool:
        try:
            return self.client.collection_exists(collection_name=collection_name)
        except Exception as e:
            logger.error("Error checking collection existence: {}", e)
            return False

    async def list_collections(self) -> list[str]:
        try:
            collections = self.client.get_collections()
            return [collection.name for collection in collections.collections]
        except Exception as e:
            logger.error("Error listing collections: {}", e)
            return []

    async def drop_collection(self, collection_name: str) -> None:
        logger.info("Dropping collection '{}'", collection_name)

        try:
            self.client.delete_collection(collection_name=collection_name)
            logger.info("Collection '{}' dropped successfully", collection_name)
        except Exception as e:
            logger.error("Error dropping collection '{}': {}", collection_name, e)
            raise

    async def _create_embeddings(self, queries: list[str]) -> list[Embedding]:
        if self.embedding.provider == "fastembed":
            return [
                Document(text=query, model=self.embedding.model) for query in queries
            ]

        openai = self._get_openai()

        batches = itertools.batched(queries, self.batch_size)

        embeddings: list[Embedding] = []

        for batch in batches:

            response = await openai.embeddings.create(
                input=batch, model=self.embedding.model
            )

            for emb in response.data:
                embeddings.append(emb.embedding)

        return embeddings

    async def _create_embedding(self, query: str) -> Embedding:
        if self.embedding.provider == "fastembed":
            return Document(text=query, model=self.embedding.model)

        openai = self._get_openai()

        response = await openai.embeddings.create(
            input=query, model=self.embedding.model
        )

        return response.data[0].embedding

    async def _get_explanations(self, code_chunks: list[str]) -> None | list[Embedding]:
        if self.explainer is None:
            return None

        explanations = await self.explainer.get_explanations(code_chunks)

        embeddings = await self._create_embeddings(explanations)

        return embeddings

    def _get_points(
        self,
        documents: list[VectorDocument],
        code_embeddings: list[Embedding],
        explanation_embeddings: list[Embedding] | None,
    ) -> list[PointStruct]:
        if explanation_embeddings is None:
            return [
                PointStruct(
                    id=uuid.uuid4().hex,
                    vector={
                        "code": emb,
                        "bm25": Document(text=doc.content, model=TEXT_EMBEDDING_MODEL),
                    },
                    payload={
                        "content": doc.content,
                        "relative_path": doc.relative_path,
                        "start_line": doc.start_line,
                        "end_line": doc.end_line,
                        "file_extension": doc.file_extension,
                        "metadata": doc.metadata,
                    },
                )
                for doc, emb in zip(documents, code_embeddings)
            ]
        return [
            PointStruct(
                id=uuid.uuid4().hex,
                vector={
                    "code": emb1,
                    "explanation": emb2,
                    "bm25": Document(text=doc.content, model=TEXT_EMBEDDING_MODEL),
                },
                payload={
                    "content": doc.content,
                    "relative_path": doc.relative_path,
                    "start_line": doc.start_line,
                    "end_line": doc.end_line,
                    "file_extension": doc.file_extension,
                    "metadata": doc.metadata,
                },
            )
            for doc, emb1, emb2 in zip(
                documents, code_embeddings, explanation_embeddings
            )
        ]

    async def upload_documents(
        self, collection_name: str, documents: list[VectorDocument]
    ) -> None:
        """Upload documents into collection.

        Args:
            collection_name: Name of the collection
            documents: List of documents to upload
        """
        if not documents:
            return

        logger.info("Inserting {} documents into '{}'", len(documents), collection_name)

        code_chunks = [doc.content for doc in documents]

        code_embeddings = await self._create_embeddings(code_chunks)
        explanation_embeddings = await self._get_explanations(code_chunks)

        points = self._get_points(documents, code_embeddings, explanation_embeddings)

        try:
            self.client.upload_points(
                collection_name=collection_name,
                points=points,
                batch_size=self.batch_size,
            )
            logger.info("Successfully inserted {} documents", len(documents))
        except Exception as e:
            logger.error("Error inserting documents: {}", e)
            raise

    async def search(
        self,
        collection_name: str,
        query_text: str,
        limit: int = 10,
        score_threshold: float = 0.0,
    ) -> list[SearchResult]:
        """Search for similar documents using text query with automatic embedding.

        Args:
            collection_name: Name of the collection
            query_text: Query text to search for
            limit: Maximum number of results to return
            score_threshold: Minimum similarity score threshold

        Returns:
            List of search results
        """
        logger.debug(
            "Text searching in '{}' with query: '{}...'",
            collection_name,
            query_text[:50],
        )

        try:
            prefetch = [
                Prefetch(
                    query=await self._create_embedding(query_text),
                    using="code",
                    limit=limit * 2,
                ),
                Prefetch(
                    query=Document(text=query_text, model=TEXT_EMBEDDING_MODEL),
                    using="bm25",
                    limit=limit * 2,
                ),
            ]
            search_result = self.client.query_points(
                collection_name=collection_name,
                prefetch=prefetch,
                query=FusionQuery(fusion=Fusion.RRF),
                limit=limit,
                score_threshold=score_threshold,
            )

            results = []
            for point in search_result.points:
                payload = point.payload or {}
                results.append(
                    SearchResult(
                        content=payload.get("content", ""),
                        relative_path=payload.get("relative_path", ""),
                        start_line=payload.get("start_line", 0),
                        end_line=payload.get("end_line", 0),
                        language=payload.get("metadata", {}).get("language", "unknown"),
                        score=point.score,
                    )
                )

            logger.debug("Found {} results for text query", len(results))
            return results

        except Exception as e:
            logger.error("Error searching collection with text: {}", e)
            raise

    async def delete(self, collection_name: str, filter: Filter) -> None:
        """Delete documents using a filter condition.

        Args:
            collection_name: Name of the collection
            filter: Filter condition to select points for deletion
        """
        logger.debug("Deleting documents from '{}' using filter", collection_name)

        try:
            self.client.delete(
                collection_name=collection_name,
                points_selector=FilterSelector(filter=filter),
            )
            logger.debug("Successfully deleted documents using filter")
        except Exception as e:
            logger.error("Error deleting documents with filter: {}", e)
            raise

    async def update_vectors(
        self, collection_name: str, updates: list[dict[str, Any]]
    ) -> None:
        """Update vectors for existing points efficiently.

        Args:
            collection_name: Name of the collection
            updates: List of updates with id, vector, and optional payload
        """
        if not updates:
            return

        logger.debug("Updating {} vectors in '{}'", len(updates), collection_name)

        try:
            point_vectors = []
            for update in updates:
                point_vectors.append(
                    PointVectors(
                        id=update["id"],
                        vector=update["vector"],
                    )
                )

            self.client.update_vectors(
                collection_name=collection_name,
                points=point_vectors,
            )

            logger.debug("Successfully updated {} vectors", len(updates))
        except Exception as e:
            logger.error("Error updating vectors: {}", e)
            raise
