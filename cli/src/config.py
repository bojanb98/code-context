import json
from pathlib import Path

from pydantic import BaseModel, Field, HttpUrl, PositiveInt
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_DIR = (Path.home() / ".code-context").expanduser().absolute()

DEFAULT_CONFIG_PATH = DEFAULT_DIR / "settings.json"


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

    enabled: bool = Field(default=False, description="Whether explanations are enabled")
    url: HttpUrl = Field(
        default=HttpUrl("http://localhost:11434/v1"),
        description="Explainer service URL",
    )
    api_key: str = Field(
        default="ollama",
        description="API key for explainer service",
    )
    model: str = Field(default="gemma3:1b-it-q8_0 ", description="Explainer model name")
    embedding: EmbeddingConfig = EmbeddingConfig(
        url=HttpUrl("http://localhost:11434/v1"),
        model="hf.co/nomic-ai/nomic-embed-text-v1.5-GGUF:F16",
        size=512,
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
    embedding: EmbeddingConfig = Field(default_factory=EmbeddingConfig)
    explainer: ExplainerConfig = Field(default_factory=ExplainerConfig)
    chunking: ChunkingConfig = Field(default_factory=ChunkingConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)


def load_config(file_path: str | None = None) -> AppSettings:
    config_path = Path(file_path or DEFAULT_CONFIG_PATH)
    contents = json.loads(config_path.read_text())
    return AppSettings.model_validate(contents)


def save_config(settings: AppSettings, file_path: str | None = None) -> None:
    config_path = Path(file_path or DEFAULT_CONFIG_PATH)
    config_path.write_text(settings.model_dump_json(indent=2))
