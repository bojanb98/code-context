from dataclasses import dataclass
from typing import Any


@dataclass
class SearchResult:
    content: str
    relative_path: str
    start_line: int
    end_line: int
    language: str
    score: float


@dataclass
class VectorDocument:
    content: str
    relative_path: str
    start_line: int
    end_line: int
    file_extension: str
    metadata: dict[str, Any]


@dataclass
class SearchOptions:
    top_k: int = 10
    threshold: float = 0.5
