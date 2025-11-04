# Code Context Core

Python library for semantic code search and indexing. Provides vector-based code search with hybrid capabilities and incremental indexing.

## Installation

```bash
uv sync
```

## Quick Start

```python
import asyncio
from pathlib import Path
from qdrant_client import AsyncQdrantClient
from core import (
    EmbeddingService,
    SearchService,
    IndexingService,
    TreeSitterSplitter,
    FileSynchronizer
)

async def main():
    # Initialize services
    client = AsyncQdrantClient(url="http://localhost:6333")
    embedding_service = EmbeddingService("http://localhost:11434/v1", "ollama")
    synchronizer = FileSynchronizer("./snapshots")
    splitter = TreeSitterSplitter(chunk_size=2500, chunk_overlap=300)

    indexing_service = IndexingService(client, synchronizer)
    search_service = SearchService(
        client,
        embedding_service,
        embedding_model="vuongnguyen2212/CodeRankEmbed",
        explainer_embedding_model="hf.co/nomic-ai/nomic-embed-text-v1.5-GGUF:F16"
    )

    # Index a codebase
    await indexing_service.index(
        Path("./my-project"),
        splitter,
        embedding_config
    )

    # Search the codebase
    results = await search_service.search(
        Path("./my-project"),
        "function that handles user authentication",
        top_k=5
    )

    for result in results:
        print(f"{result.relative_path}:{result.start_line}-{result.end_line}")
        print(f"Language: {result.language}")
        print(f"Score: {result.score:.3f}")
        print(f"Content: {result.content[:200]}...")

asyncio.run(main())
```

## Core Components

### Services

- **IndexingService**: Orchestrates file processing and vector storage
- **SearchService**: Handles semantic search queries with hybrid capabilities
- **EmbeddingService**: Manages embedding generation via OpenAI-compatible APIs
- **ExplainerService**: Provides code explanations using LLMs
- **FileSynchronizer**: Handles incremental updates with change detection

### Splitters

- **TreeSitterSplitter**: Language-aware code splitting using tree-sitter parsers
- **BaseSplitter**: Abstract base for custom splitters

### Utilities

- **CollectionName**: Generates unique collection names per project
- **Embedding**: Type definitions for embedding vectors

## API

### Main Classes

#### IndexingService
```python
async def index(
    self,
    path: Path,
    splitter: TreeSitterSplitter,
    embedding_config: EmbeddingConfig,
    force_reindex: bool = False
) -> None
```

#### SearchService
```python
async def search(
    self,
    path: Path,
    query: str,
    top_k: int = 5,
    threshold: float = 0.0
) -> list[SearchResult]
```

#### EmbeddingService
```python
async def generate_embedding(self, query: str, model: str) -> Embedding
async def generate_embeddings(
    self,
    queries: list[str],
    model: str,
    batch_size: int = 32
) -> list[Embedding]
```

### Data Models

```python
@dataclass
class SearchResult:
    content: str           # Code chunk content
    relative_path: str     # Relative file path
    start_line: int        # Start line number
    end_line: int          # End line number
    language: str          # Programming language
    score: float           # Similarity score (0-1)
    explanation: str | None = None  # Code explanation if enabled

@dataclass
class EmbeddingConfig:
    service: EmbeddingService
    model: str
    size: int | None = None
```

## Supported Languages

JavaScript, TypeScript, Python, Java, C/C++, C#, Go, Rust, Scala, PHP, Ruby, Swift, Kotlin

Language detection is automatic based on file extensions using tree-sitter parsers.

## Features

- **Hybrid Search**: Combines semantic similarity and keyword matching
- **Incremental Updates**: Merkle tree-based change detection
- **Language-Aware Splitting**: Context-preserving code chunking
- **Async Operations**: Full async/await support
