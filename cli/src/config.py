import os
from pathlib import Path

import xxhash
from pydantic import BaseModel, Field, HttpUrl, PositiveInt
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_DIR = (Path.home() / ".code-context").expanduser().absolute()
DEFAULT_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_CONFIG_PATH = DEFAULT_DIR / "settings.json"

CONFIGS_DIR = DEFAULT_DIR / "configs"
CONFIGS_DIR.mkdir(parents=True, exist_ok=True)


class QdrantConfig(BaseModel):

    url: HttpUrl = Field(
        default=HttpUrl("http://localhost:6333"),
        description="Qdrant server URL",
    )
    api_key: str | None = Field(
        default=None,
        description="Qdrant API key",
    )


class EmbeddingConfig(BaseModel):

    url: HttpUrl = Field(
        default=HttpUrl("http://localhost:11434/v1"),
        description="Embedding service URL",
    )
    api_key: str = Field(
        default="ollama",
        description="API key for embedding service",
    )
    model: str = Field(
        default="vuongnguyen2212/CodeRankEmbed", description="Embedding model name"
    )
    size: PositiveInt = Field(
        default=768, description="Embedding size", multiple_of=2, le=2048
    )


class ExplainerConfig(BaseModel):
    url: HttpUrl = Field(
        default=HttpUrl("http://localhost:11434/v1"),
        description="Explainer service URL",
    )
    api_key: str = Field(
        default="ollama",
        description="API key for explainer service",
    )
    model: str = Field(default="gemma3:1b-it-q8_0", description="Explainer model name")
    parallelism: int = Field(
        default=2, description="Number of parallel explanation requests"
    )


class ChunkingConfig(BaseModel):
    chunk_size: PositiveInt = Field(
        default=2500,
        description="Size of each chunk in characters",
        multiple_of=10,
        le=1e5,
    )
    chunk_overlap: PositiveInt = Field(
        default=300,
        description="Overlap between chunks in characters",
        multiple_of=10,
        le=3000,
    )


class StorageConfig(BaseModel):

    snapshots_dir: Path = Field(
        default=DEFAULT_DIR / "snapshots",
        description="Directory for snapshots",
    )


class LoggingConfig(BaseModel):

    log_file_path: Path = Field(
        default=Path("/tmp/code-context-cli-debug.log"),
        description="Path to debug log file",
    )
    enabled: bool = Field(default=True, description="Whether debug logging is enabled")


class FeaturesConfig(BaseModel):

    docs: bool = Field(default=True, description="Whether doc parsing is enabled")
    explanation: bool = Field(
        default=True, description="Whether explanation generation is enabled"
    )
    graph: bool = Field(
        default=False,
        description="Whether graph search is enabled (requires FalkorDB)",
    )


class GraphConfig(BaseModel):

    host: str = Field(default="localhost", description="FalkorDB host")
    port: PositiveInt = Field(
        default=6379,
        description="FalkorDB port",
        le=65535,
    )
    username: str | None = Field(
        default="falkordb",
        description="FalkorDB username",
    )
    password: str | None = Field(
        default=None,
        description="FalkorDB password",
    )


class AppSettings(BaseSettings):

    model_config = SettingsConfigDict(
        env_file="~/.code-context/.env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        env_prefix="CODE_CONTEXT",
        case_sensitive=True,
        extra="ignore",
    )

    qdrant: QdrantConfig = Field(default_factory=QdrantConfig)
    code_embedding: EmbeddingConfig = Field(default_factory=EmbeddingConfig)
    doc_embedding: EmbeddingConfig = Field(
        default=EmbeddingConfig(
            url=HttpUrl("http://localhost:11434/v1"),
            model="hf.co/nomic-ai/nomic-embed-text-v1.5-GGUF:F16",
            size=768,
        )
    )
    features: FeaturesConfig = Field(default_factory=FeaturesConfig)
    explainer: ExplainerConfig = Field(default_factory=ExplainerConfig)
    chunking: ChunkingConfig = Field(default_factory=ChunkingConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    graph: GraphConfig = Field(default_factory=GraphConfig)


def load_config(collection_name: str | None = None) -> tuple[AppSettings, bool]:
    config_path = DEFAULT_CONFIG_PATH
    hash_path = DEFAULT_DIR / ".settings.hash"
    if collection_name is not None:
        config_path = CONFIGS_DIR / f"{collection_name}.json"
        if not config_path.exists():
            config_path = DEFAULT_CONFIG_PATH
        else:
            hash_path = CONFIGS_DIR / f".{collection_name}.hash"
    contents = config_path.read_text()
    has_changed = config_path != DEFAULT_CONFIG_PATH
    if hash_path.exists():
        hash = hash_path.read_text()
        has_changed = hash != xxhash.xxh3_64_hexdigest(contents)
    return AppSettings.model_validate_json(contents), has_changed


def save_config(settings: AppSettings, collection_name: str | None = None) -> None:
    config_path = DEFAULT_CONFIG_PATH
    hash_path = DEFAULT_DIR / ".settings.hash"
    if collection_name is not None:
        config_path = CONFIGS_DIR / f"{collection_name}.json"
        hash_path = CONFIGS_DIR / f".{collection_name}.hash"
    output = settings.model_dump_json(indent=2)
    config_path.write_text(output)
    hash_path.write_text(xxhash.xxh3_64_hexdigest(output))


def delete_config(collection_name: str) -> None:
    config_path = CONFIGS_DIR / f"{collection_name}.json"
    hash_path = CONFIGS_DIR / f".{collection_name}.hash"
    if config_path.exists():
        os.remove(config_path)
    if hash_path.exists():
        os.remove(hash_path)
