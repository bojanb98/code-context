import itertools
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from loguru import logger
from qdrant_client import AsyncQdrantClient, models
from qdrant_client.models import FieldCondition, Filter, MatchValue

from core.graph import GraphEdgeBuilder
from core.splitters import CodeChunk, Splitter
from core.sync import FileSynchronizer

from .constants import (
    CODE_DENSE,
    CODE_SPARSE,
    DOC_DENSE,
    DOC_SPARSE,
    TEXT_EMBEDDING_MODEL,
)
from .utils import (
    Embedding,
    EmbeddingService,
    ExplainerService,
    GraphNode,
    GraphService,
    get_collection_name,
)

ITER_BATCH_SIZE = 128
SCROLL_BATCH_SIZE = 512


@dataclass
class Explanations:
    text: list[str]
    embeddings: list[Embedding]


class IndexingService:
    def __init__(
        self,
        client: AsyncQdrantClient,
        file_syncrhonizer: FileSynchronizer,
        splitter: Splitter,
        code_service: EmbeddingService,
        doc_service: EmbeddingService | None = None,
        explainer: ExplainerService | None = None,
        graph_service: GraphService | None = None,
    ):
        self.client = client
        self.synchronizer = file_syncrhonizer
        self.splitter = splitter
        self.code_service = code_service
        self.doc_service = doc_service
        self.explainer = explainer
        self.graph_service = graph_service
        self._graph_builder = GraphEdgeBuilder()

    async def delete(self, codebase_path: Path) -> None:
        codebase_path = codebase_path.expanduser().absolute().resolve()

        collection_name = get_collection_name(codebase_path)
        collection_exists = await self.client.collection_exists(collection_name)

        if collection_exists:
            await self.client.delete_collection(collection_name)

        if self.graph_service is not None:
            try:
                await self.graph_service.delete_graph(collection_name)
            except Exception as exc:
                logger.warning(
                    "Failed to delete graph for collection {}: {}",
                    collection_name,
                    exc,
                )

        await self.synchronizer.delete_snapshot(codebase_path)

    async def index(
        self,
        codebase_path: Path,
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

        collection_name = get_collection_name(codebase_path)

        await self._prepare_collection(
            codebase_path,
            self.code_service.size,
            self.doc_service.size if self.doc_service is not None else None,
            force_reindex,
        )

        results = await self.synchronizer.check_for_changes(codebase_path)

        if results.num_changes == 0:
            logger.debug("No changes found")
            return

        await self._delete_file_chunks(collection_name, results.to_remove)
        chunks = await self._get_chunks(codebase_path, results.to_add, self.splitter)
        for chunk_batch in itertools.batched(chunks, ITER_BATCH_SIZE):
            batch_list = list(chunk_batch)
            if not batch_list:
                continue

            contents = [c.content for c in batch_list]
            code_embeddings = await self.code_service.generate_embeddings(contents)

            doc_embeddings: list[Embedding] | None = None
            if self.doc_service is not None:
                batch_list = await self._augment_with_explanations(batch_list)
                doc_embeddings = await self.doc_service.generate_embeddings(
                    [c.doc or "unknown" for c in batch_list]
                )

            points = await self._get_points(batch_list, code_embeddings, doc_embeddings)

            await self.client.upsert(collection_name, points)

    async def _augment_with_explanations(
        self, chunks: list[CodeChunk]
    ) -> list[CodeChunk]:
        if self.explainer is None:
            return chunks

        indices = [
            (i, c.content)
            for i, c in enumerate(chunks)
            if c.doc is None or not c.doc.strip()
        ]
        explanations = await self.explainer.get_explanations([i[1] for i in indices])

        for (idx, _), exp in zip(indices, explanations):
            chunk = chunks[idx]
            chunks[idx] = CodeChunk(
                id=chunk.id,
                content=chunk.content,
                start_line=chunk.start_line,
                end_line=chunk.end_line,
                language=chunk.language,
                file_path=chunk.file_path,
                doc=exp,
                node=chunk.node,
                parent_chunk_id=chunk.parent_chunk_id,
            )

        return chunks

    async def _get_points(
        self,
        chunks: list[CodeChunk],
        code_embeddings: list[Embedding],
        doc_embeddings: list[Embedding] | None = None,
    ) -> list[models.PointStruct]:
        if doc_embeddings is None:
            return [
                models.PointStruct(
                    id=chunk.id,
                    vector={
                        CODE_DENSE: emb,
                        CODE_SPARSE: models.Document(
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
                for chunk, emb in zip(chunks, code_embeddings)
            ]
        return [
            models.PointStruct(
                id=chunk.id,
                vector={
                    CODE_DENSE: code_emb,
                    DOC_DENSE: exp_emb,
                    CODE_SPARSE: models.Document(
                        text=chunk.content, model=TEXT_EMBEDDING_MODEL
                    ),
                    DOC_SPARSE: models.Document(
                        text=chunk.doc or "unknown", model=TEXT_EMBEDDING_MODEL
                    ),
                },
                payload={
                    "content": chunk.content,
                    "doc": chunk.doc,
                    "relative_path": chunk.file_path,
                    "start_line": chunk.start_line,
                    "end_line": chunk.end_line,
                    "language": chunk.language,
                    "indexed_at": datetime.now(timezone.utc),
                },
            )
            for chunk, code_emb, exp_emb in zip(chunks, code_embeddings, doc_embeddings)
        ]

    async def _get_chunks(
        self, codebase_path: Path, files: list[str], splitter: Splitter
    ) -> list[CodeChunk]:
        all_chunks: list[CodeChunk] = []
        for file in files:
            file_path = codebase_path / file
            relative_path = file_path.relative_to(codebase_path)
            try:
                content = file_path.read_text(encoding="utf-8")
                chunks = await splitter.split(content, relative_path)
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
            CODE_DENSE: models.VectorParams(
                size=code_size,
                distance=models.Distance.COSINE,
            )
        }

        sparse_vectors: dict[str, models.SparseVectorParams] = {
            CODE_SPARSE: models.SparseVectorParams(modifier=models.Modifier.IDF)
        }

        if explanation_size is not None:
            dense_vectors[DOC_DENSE] = models.VectorParams(
                size=explanation_size,
                distance=models.Distance.COSINE,
            )
            sparse_vectors[DOC_SPARSE] = models.SparseVectorParams(
                modifier=models.Modifier.IDF
            )

        await self.client.create_collection(
            collection_name=collection_name,
            vectors_config=dense_vectors,
            sparse_vectors_config=sparse_vectors,
        )

    async def _delete_file_chunks(
        self, collection_name: str, file_paths: list[str]
    ) -> None:
        for path in file_paths:
            filter_condition = Filter(
                must=[FieldCondition(key="relative_path", match=MatchValue(value=path))]
            )

            await self.client.delete(collection_name, filter_condition)
