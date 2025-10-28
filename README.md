# Claude Context Extensions

This project extends [@zilliz/claude-context-core](https://github.com/zilliztech/claude-context-core) for easier local use and integration. It provides a REST API service and command-line interface for indexing and searching codebases using semantic embeddings.

## Purpose

Intended to make claude-context-core more accessible for local development and integration into other tools. Provides HTTP API and CLI interfaces to the core functionality.

## Organization

- `api/` - REST API service built with Bun and Elysia.js
- `cli/` - Go command-line interface for API interaction

See individual README files for detailed documentation:
- [API Documentation](api/README.md)
- [CLI Documentation](cli/README.md)

## Quick Usage

Start API service:
```bash
cd api && bun install && bun run dev
```

Use CLI tool:
```bash
cd cli && go build -o code .
./code index /path/to/project
./code search /path/to/project "function handling auth"
```
