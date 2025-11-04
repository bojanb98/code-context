# CLAUDE.md

Semantic code search system with two components: Python core library, Python cyclopts CLI.

## Development Commands

### Core Library
```bash
cd core && uv sync
```


### CLI Tool
```bash
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


### CLI (`cli/`)
Rust command-line tool:
- Commands: `index`, `search`, `drop`
- Uses `core` module as base
- Path expansion and result formatting

## Key Features

- **Hybrid Search**: Combines semantic similarity and keyword matching
- **Incremental Updates**: Hash based change detection
- **Multi-language Support**: Tree-sitter parsing for 15+ languages
- **Flexible Embeddings**: OpenAI-compatible providers
- **Configurable**: Chunk size, overlap, batch processing, ignore patterns

## Code Style

- **Python**: Black formatter, 88-char line length, modern 3.13 typing
- **Logging**: loguru for structured output
- **Testing**: Core library tests in `tests/` directory
