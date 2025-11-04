# Code Context

Semantic code search and indexing system built with Python. Provides AI-powered code search through vector embeddings and hybrid search capabilities.

## Architecture

- `core/` - Python library for semantic code indexing and search
- `cli/` - Command-line interface for indexing and searching

See individual README files for detailed documentation:
- [Core Documentation](core/README.md)
- [CLI Documentation](cli/README.md)

## Quick Usage

Install and configure CLI:
```bash
cd cli && uv sync
./src/main.py init                    # Configure embedding service and Qdrant
```

Index and search code:
```bash
./src/main.py index [path]            # Index current directory or specified path
./src/main.py search "query" [path]   # Search in current directory or specified path
./src/main.py drop [path]             # Remove current directory or specified path from index
```

MCP server support:
```bash
./src/main.py mcp                     # Start MCP server for tool integration
```
