# Claude Context Core - Python Implementation

Python implementation of Claude Context Core using Qdrant for vector storage with support for both FastEmbed and OpenAI-compatible embedding providers for semantic code search and indexing.

## Installation

```bash
uv sync
```

## Quick Start

```python
import asyncio
from core import Context
from core.qdrant import QdrantConfig, EmbeddingConfig
from core.indexing_service import IndexingConfig
from core.sync import SynchronizerConfig

async def main():
    # Configure embedding provider (FastEmbed)
    embedding_config = EmbeddingConfig(
        model="sentence-transformers/all-MiniLM-L6-v2",
        provider="fastembed"
    )

    # Or use OpenAI-compatible provider
    # embedding_config = EmbeddingConfig(
    #     model="text-embedding-3-small",
    #     provider="openai",
    #     url="https://api.openai.com/v1",
    #     api_key="your-openai-api-key",
    #     size=1536
    # )

    qdrant_config = QdrantConfig(
        embedding=embedding_config,
        location="memory"
    )

    sync_config = SynchronizerConfig(
        snapshot_dir="./snapshots",
        ignore_patterns=["node_modules/**", "*.test.py"]
    )

    indexing_config = IndexingConfig(
        batch_size=32,
        chunk_size=2500,
        chunk_overlap=300,
        synchronizer_config=sync_config
    )

    context = Context(qdrant_config, indexing_config)

    # Index a codebase
    await context.index("./my-project")

    # Search the codebase
    results = await context.search(
        "./my-project",
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

## Configuration

### Embedding Configuration

Choose between FastEmbed (local) or OpenAI-compatible providers:

```python
from core.qdrant import QdrantConfig, EmbeddingConfig

# FastEmbed (local, free)
fastembed_config = EmbeddingConfig(
    model="sentence-transformers/all-MiniLM-L6-v2",
    provider="fastembed"
)

# OpenAI-compatible (requires API key and URL)
openai_config = EmbeddingConfig(
    model="text-embedding-3-small",
    provider="openai",
    url="https://api.openai.com/v1",
    api_key="your-api-key",
    size=1536  # Embedding dimension
)
```

### Vector Database Configuration

```python
from core.qdrant import QdrantConfig

qdrant_config = QdrantConfig(
    embedding=embedding_config,  # EmbeddingConfig from above
    location="memory",  # "memory" or "server"
    url="https://your-cluster.cloud.qdrant.io:6333",  # For server
    api_key="your-qdrant-api-key",  # For server
    batch_size=32
)
```

### Indexing Configuration

```python
from core.indexing_service import IndexingConfig
from core.sync import SynchronizerConfig

sync_config = SynchronizerConfig(
    snapshot_dir="./snapshots",
    ignore_patterns=[
        "node_modules/**",
        "*.test.py",
        "*.spec.js",
        "dist/**",
        "build/**"
    ]
)

indexing_config = IndexingConfig(
    batch_size=32,
    chunk_size=2500,
    chunk_overlap=300,
    synchronizer_config=sync_config
)
```

## API

### Context Class

The main entry point for all operations:

- `index(path, force_reindex=False)`: Index codebase for search with intelligent incremental updates
- `search(path, query, top_k=5, threshold=0.0)`: Search indexed code semantically
- `has_index(path)`: Check if codebase is indexed
- `clear_index(path)`: Remove index data completely

### Data Models

```python
@dataclass
class SearchResult:
    """Single search result with metadata"""
    content: str           # Code chunk content
    relative_path: str     # Relative file path
    start_line: int        # Start line number
    end_line: int          # End line number
    language: str          # Programming language
    score: float           # Similarity score (0-1)

@dataclass
class EmbeddingConfig:
    """Configuration for embedding providers"""
    model: str
    provider: Literal["fastembed", "openai"] = "fastembed"
    url: str | None = None          # Required for openai provider
    api_key: str = ""              # Required for openai provider
    size: int | None = None        # Required for openai provider

@dataclass
class QdrantConfig:
    """Configuration for Qdrant vector database"""
    embedding: EmbeddingConfig
    location: Literal["memory", "server"] = "memory"
    url: str | None = None
    api_key: str | None = None
    batch_size: int = 32
```

## Search Capabilities

The system supports hybrid search combining:

- **Semantic Search**: Vector similarity using embeddings
- **Keyword Search**: BM25 sparse vector search
- **Hybrid Fusion**: Uses Reciprocal Rank Fusion (RRF)

```python
# Basic semantic search
results = await context.search("./codebase", "user authentication")

# With similarity threshold (only return high-quality matches)
results = await context.search("./codebase", "API endpoints", threshold=0.7)

# Limit number of results
results = await context.search("./codebase", "error handling", top_k=3)
```

## Supported Languages

JavaScript, TypeScript, Python, Java, C/C++, C#, Go, Rust, Scala, PHP, Ruby, Swift, Kotlin

**Language Detection**: Automatically detected from file extensions using tree-sitter parsers.

## Architecture

The system is built with modular components:

- **Embedding Providers**: Pluggable embedding generation (FastEmbed, OpenAI-compatible)
- **Vector Database**: Qdrant client with hybrid search capabilities
- **Code Splitters**: Tree-sitter based language-aware code splitting with fallback
- **File Synchronization**: Merkle tree-based change detection for incremental updates
- **Indexing Service**: Orchestrates file processing and vector storage
- **Search Service**: Handles query processing and result ranking
- **Context**: Main public API coordinating all services
