# Claude Context Core - Python Implementation

Python implementation of Claude Context Core using Qdrant and FastEmbed for semantic code search and indexing.

## Installation

```bash
uv sync
```

## Quick Start

```python
import asyncio
from core import Context
from core.qdrant import QdrantConfig
from core.indexing_service import IndexingConfig
from core.sync import SynchronizerConfig

async def main():
    qdrant_config = QdrantConfig(
        embedding_model="sentence-transformers/all-MiniLM-L6-v2",
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
        print(f"Score: {result.score}")

asyncio.run(main())
```

## Configuration

Configure using separate config objects:

```python
from core.qdrant import QdrantConfig
from core.indexing_service import IndexingConfig
from core.sync import SynchronizerConfig

qdrant_config = QdrantConfig(
    embedding_model="sentence-transformers/all-MiniLM-L6-v2",
    location="memory",  # "memory" or "server"
    url="https://your-cluster.cloud.qdrant.io:6333",  # For server
    api_key="your-api-key",  # For server
    batch_size=32
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
```

## API

### Context Class

- `index(path, force_reindex=False)`: Index codebase for search
- `search(path, query, top_k=5, threshold=0.5)`: Search indexed code
- `has_index(path)`: Check if codebase is indexed
- `clear_index(path)`: Remove index data

### Data Models

```python
@dataclass
class SearchResult:
    content: str
    relative_path: str
    start_line: int
    end_line: int
    language: str
    score: float

@dataclass
class IndexingStats:
    indexed_files: int
    total_chunks: int
    status: str

@dataclass
class ChangeStats:
    added: int
    removed: int
    modified: int
```

## Supported Languages

JavaScript, TypeScript, Python, Java, C/C++, C#, Go, Rust, Scala, PHP, Ruby, Swift, Kotlin, Objective-C


## Architecture

- **Embeddings**: FastEmbed wrapper for text embeddings
- **Vector Database**: Qdrant client wrapper
- **Code Splitters**: Tree-sitter based code splitting
- **Synchronization**: Merkle tree file change detection
- **Context**: Main orchestrator class
