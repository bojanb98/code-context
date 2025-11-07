import itertools
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from loguru import logger
from qdrant_client import AsyncQdrantClient, models
from qdrant_client.models import FieldCondition, Filter, MatchValue

from core.splitters import CodeChunk, Splitter
from core.sync import FileSynchronizer

from .constants import CODE_INDEX, EXPLANATION_INDEX, TEXT_EMBEDDING_MODEL, TEXT_INDEX
from .utils import Embedding, EmbeddingService, ExplainerService, get_collection_name

ITER_BATCH_SIZE = 128


@dataclass
class EmbeddingConfig:
    service: EmbeddingService
    model: str
    size: int
    batch_size: int = 32


@dataclass
class ExplainerConfig:
    service: ExplainerService
    embedding: EmbeddingConfig


@dataclass
class Explanations:
    text: list[str]
    embeddings: list[Embedding]


class IndexingService:
    def __init__(
        self,
        client: AsyncQdrantClient,
        file_syncrhonizer: FileSynchronizer,
    ):
        self.client = client
        self.synchronizer = file_syncrhonizer

    async def delete(self, codebase_path: Path) -> None:
        codebase_path = codebase_path.expanduser().absolute().resolve()

        collection_name = get_collection_name(codebase_path)
        collection_exists = await self.client.collection_exists(collection_name)

        if collection_exists:
            await self.client.delete_collection(collection_name)

        await self.synchronizer.delete_snapshot(codebase_path)

    async def index(
        self,
        codebase_path: Path,
        splitter: Splitter,
        embedding: EmbeddingConfig,
        explainer: ExplainerConfig | None = None,
        force_reindex: bool = False,
    ) -> None:
        """Index a codebase, automatically handling initial indexing or incremental reindexing.

        Args:
            codebase_path: Path to the codebase to index
            force_reindex: Whether to force a complete reindexing

        Returns:
            IndexingStats with information about the indexing operation
        """
        codebase_path = codebase_path.expanduser().absolute().resolve()

        if not codebase_path.exists():
            raise RuntimeError("Invalid path")

        logger.debug("Starting indexing for codebase: {}", codebase_path)

        await self._prepare_collection(
            codebase_path,
            embedding.size,
            explainer.embedding.size if explainer is not None else None,
            force_reindex,
        )

        collection_name = get_collection_name(codebase_path)
        results = await self.synchronizer.check_for_changes(codebase_path)

        if results.num_changes == 0:
            logger.debug("No changes found")
            return

        await self._delete_file_chunks(collection_name, results.to_remove)
        chunks = await self._get_chunks(codebase_path, results.to_add, splitter)
        for chunk_batch in itertools.batched(chunks, ITER_BATCH_SIZE):
            contents = [c.content for c in chunk_batch]
            code_embeddings = await embedding.service.generate_embeddings(
                contents, embedding.model, embedding.batch_size
            )
            explanations: Explanations | None = None
            if explainer is not None:
                explanation_texts = await explainer.service.get_explanations(contents)
                explanation_embeddings = (
                    await explainer.embedding.service.generate_embeddings(
                        explanation_texts, explainer.embedding.model
                    )
                )
                explanations = Explanations(explanation_texts, explanation_embeddings)

            points = await self._get_points(
                list(chunk_batch), code_embeddings, explanations
            )
            await self.client.upsert(collection_name, points)

    async def _get_points(
        self,
        chunks: list[CodeChunk],
        embeddings: list[Embedding],
        explanations: Explanations | None = None,
    ) -> list[models.PointStruct]:
        if explanations is None:
            return [
                models.PointStruct(
                    id=uuid.uuid4().hex,
                    vector={
                        "code": emb,
                        "bm25": models.Document(
                            text=chunk.content, model=TEXT_EMBEDDING_MODEL
                        ),
                    },
                    payload={
                        "content": chunk.content,
                        "relative_path": chunk.file_path,
                        "start_line": chunk.start_line,
                        "end_line": chunk.end_line,
                        "language": chunk.language,
                        "indexed_at": datetime.now(timezone.utc),
                    },
                )
                for chunk, emb in zip(chunks, embeddings)
            ]
        return [
            models.PointStruct(
                id=uuid.uuid4().hex,
                vector={
                    "code": code_emb,
                    "explanation": exp_emb,
                    "bm25": models.Document(
                        text=chunk.content, model=TEXT_EMBEDDING_MODEL
                    ),
                },
                payload={
                    "content": chunk.content,
                    "relative_path": chunk.file_path,
                    "start_line": chunk.start_line,
                    "end_line": chunk.end_line,
                    "language": chunk.language,
                    "explanation": exp_text,
                    "indexed_at": datetime.now(timezone.utc),
                },
            )
            for chunk, code_emb, exp_text, exp_emb in zip(
                chunks, embeddings, explanations.text, explanations.embeddings
            )
        ]

    async def _get_chunks(
        self, codebase_path: Path, files: list[str], splitter: Splitter
    ) -> list[CodeChunk]:
        all_chunks: list[CodeChunk] = []
        for file in files:
            file_path = codebase_path / file
            try:
                content = file_path.read_text(encoding="utf-8")
                chunks = await splitter.split(content, file_path)
                all_chunks.extend(chunks)
            except Exception as e:
                logger.debug("Unable to read a file {} {}", file_path, e)

        return all_chunks

    async def _prepare_collection(
        self,
        codebase_path: Path,
        code_size: int,
        explanation_size: int | None = None,
        force_reindex: bool = False,
    ) -> None:
        collection_name = get_collection_name(codebase_path)

        collection_exists = await self.client.collection_exists(collection_name)

        if collection_exists and not force_reindex:
            logger.debug(
                "Collection {} already exists, skipping creation", collection_name
            )
            return

        if collection_exists and force_reindex:
            logger.debug(
                "Dropping existing collection {} for force reindex", collection_name
            )
            await self.delete(codebase_path)

        await self._create_collection(collection_name, code_size, explanation_size)
        logger.debug("Collection {} created successfully", collection_name)

    async def _create_collection(
        self, collection_name: str, code_size: int, explanation_size: int | None = None
    ) -> None:
        dense_vectors: dict[str, models.VectorParams] = {
            CODE_INDEX: models.VectorParams(
                size=code_size,
                distance=models.Distance.COSINE,
            )
        }

        if explanation_size is not None:
            dense_vectors[EXPLANATION_INDEX] = models.VectorParams(
                size=explanation_size,
                distance=models.Distance.COSINE,
            )

        await self.client.create_collection(
            collection_name=collection_name,
            vectors_config=dense_vectors,
            sparse_vectors_config={
                TEXT_INDEX: models.SparseVectorParams(modifier=models.Modifier.IDF)
            },
        )

    async def _get_embeddings(
        self, chunks: list[CodeChunk], config: EmbeddingConfig
    ) -> list[Embedding]:
        all_embeddings: list[Embedding] = []

        for chunk_batch in itertools.batched(chunks, config.batch_size):
            contents = [c.content for c in chunk_batch]
            embeddings = await config.service.generate_embeddings(
                contents, config.model
            )
            all_embeddings.extend(embeddings)

        return all_embeddings

    async def _delete_file_chunks(
        self, collection_name: str, file_paths: list[str]
    ) -> None:
        for path in file_paths:
            filter_condition = Filter(
                must=[FieldCondition(key="relative_path", match=MatchValue(value=path))]
            )

            await self.client.delete(collection_name, filter_condition)
