"""Claude Context Core - Python implementation with Qdrant and FastEmbed."""

from .context import Context
from .settings import Settings
from .types import IndexingStats, ChangeStats, CollectionNotIndexedError

__version__ = "0.1.0"
__all__ = [
    "Context",
    "Settings",
    "IndexingStats",
    "ChangeStats",
    "CollectionNotIndexedError",
]

