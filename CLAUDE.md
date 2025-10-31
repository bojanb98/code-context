# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Development Commands

### Core Library
```bash
cd core
uv sync                     # Install dependencies
```

### API Service
```bash
cd api
uv sync                     # Install dependencies
uv run fastapi dev src/main.py    # Development server (localhost:19531)
uv run fastapi run src/main.py    # Production server
```

### CLI Tool
```bash
cd cli
go build -o code .         # Build CLI binary
./code index <path>        # Index a codebase
./code search <path> <query> [limit] [extensions]  # Search indexed code
```

## Project Architecture

This is a semantic code search system with three main components:

### Core Library (`core/`)
Python library providing the main functionality:
- **Context**: Main entry point class that orchestrates indexing and search
- **IndexingService**: Handles code splitting, embedding generation, and vector storage with incremental reindexing support
- **SearchService**: Performs semantic search using vector similarity
- **QdrantVectorDatabase**: Manages vector storage using Qdrant with support for FastEmbed or OpenAI-compatible embeddings
- **FileSynchronizer**: Tracks file changes using Merkle trees for efficient incremental updates
- **TreeSitterSplitter**: Splits code files into chunks using tree-sitter for language-aware parsing

### API Service (`api/`)
FastAPI REST service exposing core functionality:
- Single dependency on local `core` library
- Two main endpoints: `/api/index` for indexing operations and `/api/search` for search
- Uses Pydantic for request/response models
- Configurable via environment variables and settings files
- Swagger documentation available at `/swagger`

### CLI Tool (`cli/`)
Go command-line interface for the API:
- Commands: `index`, `search`, `unindex`
- Communicates with API service on `localhost:19531`
- Expands relative paths to absolute paths before sending to API
- Formats search results for display

## Key Implementation Details

### Indexing Process
1. **File Discovery**: Scans directory for code files, respects ignore patterns
2. **Splitting**: Uses tree-sitter to split files into language-appropriate chunks
3. **Embedding**: Generates embeddings using FastEmbed or OpenAI-compatible providers
4. **Storage**: Stores vectors in Qdrant with metadata (file path, line numbers, language)
5. **Synchronization**: Tracks file state for incremental updates using Merkle trees

### Search Process
1. **Query Embedding**: Converts search query to vector embedding
2. **Similarity Search**: Finds similar vectors in Qdrant collection
3. **Filtering**: Applies similarity threshold and result limits
4. **Response**: Returns ranked results with file paths, line numbers, and content

### Configuration Management
- API settings stored in `~/.context/settings.json`
- Ignore patterns stored in `~/.context/ignored.json`
- Default embedding provider: OpenAI-compatible
- Default chunk size: 2500 characters with 300 overlap

## Development Notes

### Code Style
- Python: Black formatter with 88-character line length
- Go: Tab indentation, 120-character max line length
- Uses `loguru` for structured logging
- FastAPI with Pydantic for data validation

### Testing
- Core library has tests in `tests/` directory
- Run with `uv run python -m pytest` from `core/` directory

### Dependencies
- Core uses Qdrant client with FastEmbed, tree-sitter, loguru, and OpenAI
- API uses FastAPI with pydantic-settings
- CLI uses only Cobra CLI framework
- All components have minimal external dependencies
