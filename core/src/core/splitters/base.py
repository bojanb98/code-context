from abc import ABC, abstractmethod
from pathlib import Path
from typing import Protocol

from .types import CodeChunk


class Splitter(Protocol):
    """Protocol for code splitters."""

    async def split(self, code: str, file_path: Path) -> list[CodeChunk]:
        """Split code into chunks.

        Args:
            code: Code content to split
            language: Programming language
            file_path: Path to the file

        Returns:
            List of code chunks
        """
        ...

    def set_chunk_size(self, chunk_size: int) -> None:
        """Set chunk size.

        Args:
            chunk_size: Maximum chunk size in characters
        """
        ...

    def set_chunk_overlap(self, chunk_overlap: int) -> None:
        """Set chunk overlap.

        Args:
            chunk_overlap: Overlap size in characters
        """
        ...


class BaseSplitter(ABC):
    """Abstract base class for splitters."""

    def __init__(self, chunk_size: int = 2500, chunk_overlap: int = 300) -> None:
        """Initialize splitter.

        Args:
            chunk_size: Maximum chunk size in characters
            chunk_overlap: Overlap size in characters
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    @abstractmethod
    async def split(self, code: str, file_path: Path) -> list[CodeChunk]:
        """Split code into chunks.

        Args:
            code: Code content to split
            language: Programming language
            file_path: Path to the file

        Returns:
            List of code chunks
        """
        ...

    def set_chunk_size(self, chunk_size: int) -> None:
        """Set chunk size.

        Args:
            chunk_size: Maximum chunk size in characters
        """
        self.chunk_size = chunk_size

    def set_chunk_overlap(self, chunk_overlap: int) -> None:
        """Set chunk overlap.

        Args:
            chunk_overlap: Overlap size in characters
        """
        self.chunk_overlap = chunk_overlap
