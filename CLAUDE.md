# CLAUDE.md

Semantic code search system with three components: Python core library, FastAPI service, and Rust CLI.

## Development Commands

### Core Library
```bash
cd core && uv sync
```

### API Service
```bash
cd api && uv sync
uv run fastapi dev src/main.py    # Dev server
uv run fastapi run src/main.py    # Production server
```

### CLI Tool
```bash
cd cli && cargo build --release
./code index [path] [--force]    # Index directory
./code search <query> [path] [--limit N] [--extensions .go,.js]  # Search
./code drop [path]               # Remove from index
```

## Architecture

### Core (`core/`)
Python library with modular structure:
- **Context**: Main API entry point
- **IndexingService**: Orchestrates file processing and vector storage
- **SearchService**: Handles semantic search queries
- **QdrantVectorDatabase**: Vector storage with hybrid search (semantic + keyword)
- **TreeSitterSplitter**: Language-aware code splitting
- **FileSynchronizer**: Merkle tree-based incremental updates

### API (`api/`)
FastAPI service exposing core functionality:
- `/api/index` - Index and clear operations
- `/api/search` - Semantic search with query parameters
- Configuration via environment variables
- Swagger docs at `/swagger`

### CLI (`cli/`)
Rust command-line tool:
- Commands: `index`, `search`, `drop`
- HTTP client communicating with API service
- Path expansion and result formatting

## Key Features

- **Hybrid Search**: Combines semantic similarity and keyword matching
- **Incremental Updates**: Merkle tree-based change detection
- **Multi-language Support**: Tree-sitter parsing for 15+ languages
- **Flexible Embeddings**: FastEmbed (local) or OpenAI-compatible providers
- **Configurable**: Chunk size, overlap, batch processing, ignore patterns

## Configuration

Default settings can be overridden via environment variables:
- Embedding provider/model (FastEmbed or OpenAI-compatible)
- Qdrant server configuration
- Chunk size (2500) and overlap (300)
- Batch processing (32)
- Snapshot directory (`~/.code-context/snapshots`)

## Code Style

- **Python**: Black formatter, 88-char line length
- **Rust**: Standard rustfmt patterns
- **Logging**: loguru for structured output
- **Testing**: Core library tests in `tests/` directory
