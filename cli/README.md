# Code Context CLI

CLI wrapper around the core library: index, search, drop, configure, and run an MCP server.

## Stack
Python 3.13+, cyclopts (CLI), rich (output), pydantic settings and core module. Commands are registered in `src/main.py`. :contentReference[oaicite:4]{index=4}

## Commands
- `init` - interactive configuration
- `index` - index or reindex a directory
- `search` - semantic search
- `drop` - remove a codebase index
- `mcp` - start MCP server

Command registration (in `src/main.py`): `init`, `index`, `search`, `drop`, `mcp`. :contentReference[oaicite:5]{index=5}

## Installation
```bash
cd cli
uv sync
````

## Running (local development)

Use `uv run` to execute the CLI directly from sources:

```bash
uv run src/main.py init
uv run src/main.py index .
uv run src/main.py search "database connection setup"
uv run src/main.py drop .
uv run src/main.py mcp
```

These map to the commands exposed by `src/main.py`. 

## Typical Workflow

```bash
uv run src/main.py init
uv run src/main.py index ~/projects/myapp
uv run src/main.py search "function that validates JWT" --limit 5 # Uses ./ as project directory
```

## Notes

- The CLI constructs services via `ServiceFactory` (Qdrant client, embedding/explainer services, splitter, synchronizer, indexing/search). 
- `search` supports plain, `json`, and `simple-json` outputs; threshold and limit are supported flags. 
