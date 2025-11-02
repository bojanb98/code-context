from pathlib import Path
from typing import Annotated, Literal

from core import Context
from core.context import IndexingConfig
from core.qdrant import QdrantConfig
from core.qdrant.client import EmbeddingConfig
from core.qdrant.explainer_service import ExplainerConfig
from core.sync import SynchronizerConfig
from fastapi import Depends
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="allow"
    )

    qdrant_url: str = Field(default="localhost:6333", description="Qdrant server URL")
    qdrant_api_key: str = Field(default="", description="Qdrant API key")

    embedding_provider: Literal["fastembed", "openai"] = Field(
        default="openai", description="Embedding provider type"
    )
    embedding_model: str = Field(
        default="vuongnguyen2212/CodeRankEmbed",
        description="Model name for embeddings",
    )
    embedding_url: str | None = Field(
        default="http://localhost:11434/v1", description="URL for openai provider"
    )
    embedding_api_key: str = Field(
        default="api_key", description="API key in case of openai provider"
    )
    embedding_size: int | None = Field(default=768, description="Embedding vector size")

    explainer_model: str | None = Field(
        default="gemma3:1b-it-q8_0",
        description="Model name for explanations",
    )
    explainer_url: str = Field(
        default="http://localhost:11434/v1", description="URL for openai provider"
    )
    explainer_api_key: str = Field(
        default="api_key", description="API key in case of openai provider"
    )
    explainer_parallelism: int = Field(
        default=8, description="Parallelism for LLM explanations"
    )

    batch_size: int = Field(default=32, description="Batch size for processing")
    chunk_size: int = Field(default=2500, description="Chunk size for text splitting")
    chunk_overlap: int = Field(
        default=300, description="Chunk overlap for text splitting"
    )

    snapshot_dir: str = Field(
        default=str(Path.home() / ".code-context/snapshots"),
        description="Snapshot directory path",
    )


_settings: AppSettings | None = None
_context: Context | None = None


def get_settings() -> AppSettings:
    global _settings
    if _settings is None:
        _settings = AppSettings()
    return _settings


def get_context() -> Context:
    global _context
    if _context is None:
        settings = get_settings()
        explainer_config: ExplainerConfig | None = None
        if settings.explainer_model is not None:
            explainer_config = ExplainerConfig(
                settings.explainer_url,
                settings.explainer_model,
                settings.explainer_api_key,
                settings.explainer_parallelism,
            )
        _context = Context(
            QdrantConfig(
                EmbeddingConfig(
                    settings.embedding_model,
                    settings.embedding_provider,
                    settings.embedding_url,
                    settings.embedding_api_key,
                    settings.embedding_size,
                ),
                "server",
                settings.qdrant_url,
                settings.qdrant_api_key,
                settings.batch_size,
            ),
            IndexingConfig(
                settings.batch_size,
                settings.chunk_size,
                settings.chunk_overlap,
                SynchronizerConfig(settings.snapshot_dir),
            ),
            explainer_config,
        )

    return _context


ContextDep = Annotated[Context, Depends(get_context)]
