# Claude Context Extensions

Semantic code search and indexing system inspired by [@zilliz/claude-context-core](https://github.com/zilliztech/claude-context-core), built with a custom Python implementation using Qdrant. Supports FastEmbed and OpenAI compatible API for embeddings.

## Architecture

- `core/` - Python library for semantic code indexing and search using Qdrant
- `api/` - FastAPI REST service for HTTP interface to core functionality
- `cli/` - Rust command-line tool for API interaction

See individual README files for detailed documentation:
- [Core Documentation](core/README.md)
- [API Documentation](api/README.md)
- [CLI Documentation](cli/README.md)

## Quick Usage

Start API service:
```bash
cd api && uv sync && uv fastapi run src/main.py
```

Use CLI tool:
```bash
cd cli && go build -o code .
./code index [path]                    # Index current directory or specified path
./code search "query" [path]           # Search in current directory or specified path
./code drop [path]                     # Remove current directory or specified path from index
```

CLI binary can also be downloaded from [Releases](https://github.com/bojanb98/code-context/releases).
