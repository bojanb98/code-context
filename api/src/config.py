import json
from pathlib import Path
from typing import ClassVar, Literal

from core import Context
from core.context import IndexingConfig
from core.qdrant import QdrantConfig
from core.qdrant.client import EmbeddingConfig
from core.sync import SynchronizerConfig
from loguru import logger
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

    batch_size: int = Field(default=32, description="Batch size for processing")
    chunk_size: int = Field(default=2500, description="Chunk size for text splitting")
    chunk_overlap: int = Field(
        default=300, description="Chunk overlap for text splitting"
    )

    config_dir: str = Field(
        default=".context", description="Configuration directory name"
    )
    snapshot_dir: str = Field(
        default="~/.code-context/snapshots", description="Snapshot directory path"
    )


class ConfigManager:

    CONFIG_FILE: ClassVar[str] = "settings.json"
    IGNORED_FILE: ClassVar[str] = "ignored.json"

    def __init__(self, settings: AppSettings):
        self.settings = settings
        self.config_dir = Path.home() / settings.config_dir
        self.config_file = self.config_dir / self.CONFIG_FILE
        self.ignored_file = self.config_dir / self.IGNORED_FILE

    def ensure_config_dir(self) -> None:
        """Ensure configuration directory exists."""
        self.config_dir.mkdir(exist_ok=True)

    async def load_settings(self) -> dict:
        """Load settings from configuration file."""
        try:
            if self.config_file.exists():
                with open(self.config_file, "r", encoding="utf-8") as f:
                    config_data = json.load(f)
                logger.debug(f"Loaded configuration from {self.config_file}")
                return config_data
            else:
                logger.info("No configuration file found, using defaults")
                return {}
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            return {}

    async def save_settings(self, config_data: dict) -> None:
        """Save settings to configuration file."""
        try:
            self.ensure_config_dir()
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            logger.info(f"Configuration saved to {self.config_file}")
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            raise

    async def load_ignored_patterns(self) -> dict[str, list[str]]:
        """Load ignored patterns from configuration file."""
        try:
            if self.ignored_file.exists():
                with open(self.ignored_file, "r", encoding="utf-8") as f:
                    patterns = json.load(f)
                logger.debug(f"Loaded ignored patterns from {self.ignored_file}")
                return patterns
            else:
                logger.info("No ignored patterns file found, using empty patterns")
                return {}
        except Exception as e:
            logger.error(f"Failed to load ignored patterns: {e}")
            return {}

    async def save_ignored_patterns(self, patterns: dict[str, list[str]]) -> None:
        """Save ignored patterns to configuration file."""
        try:
            self.ensure_config_dir()
            with open(self.ignored_file, "w", encoding="utf-8") as f:
                json.dump(patterns, f, indent=2, ensure_ascii=False)
            logger.info(f"Ignored patterns saved to {self.ignored_file}")
        except Exception as e:
            logger.error(f"Failed to save ignored patterns: {e}")
            raise

    def get_current_project_path(self) -> str:
        """Get current working directory as project path."""
        return str(Path.cwd())


_settings: AppSettings | None = None
_config_manager: ConfigManager | None = None
_context: Context | None = None


def get_settings() -> AppSettings:
    global _settings
    if _settings is None:
        _settings = AppSettings()
    return _settings


def get_config_manager() -> ConfigManager:
    global _config_manager
    if _config_manager is None:
        settings = get_settings()
        _config_manager = ConfigManager(settings)
    return _config_manager


def get_context() -> Context:
    global _context
    if _context is None:
        settings = get_settings()
        _context = Context(
            QdrantConfig(
                EmbeddingConfig(
                    settings.embedding_model,
                    settings.embedding_provider,
                    settings.embedding_url,
                    settings.embedding_api_key,
                ),
                "server",
                settings.qdrant_url,
                settings.qdrant_api_key,
            ),
            IndexingConfig(
                settings.batch_size,
                settings.chunk_size,
                settings.chunk_overlap,
                SynchronizerConfig(settings.snapshot_dir),
            ),
        )

    return _context
