# Claude Context Extensions

Semantic code search and indexing system inspired by [@zilliz/claude-context-core](https://github.com/zilliztech/claude-context-core), built with a custom Python implementation using Qdrant and FastEmbed.

## Architecture

- `core/` - Python library for semantic code indexing and search using Qdrant
- `api/` - FastAPI REST service for HTTP interface to core functionality
- `cli/` - Go command-line tool for API interaction

See individual README files for detailed documentation:
- [Core Documentation](core/README.md)
- [API Documentation](api/README.md)
- [CLI Documentation](cli/README.md)

## Quick Usage

Start API service:
```bash
cd api && uv sync && uv run uvicorn src.app:app --reload --host 0.0.0.0 --port 19531
```

Use CLI tool:
```bash
cd cli && go build -o code .
./code index /path/to/project
./code search /path/to/project "function handling auth"
```
