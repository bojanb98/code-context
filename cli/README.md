# Code Context CLI

Command-line interface for semantic code search and indexing. Built with Python using cyclopts for CLI parsing.

## Installation

```bash
uv sync
```

## Configuration

Initialize configuration with interactive setup:
```bash
uv run ./src/main.py init
```

This creates a configuration file at `~/.code-context/settings.json` with settings for:
- Qdrant vector database connection
- Embedding service (Ollama or OpenAI-compatible)
- Optional code explanations
- Code chunking parameters

## Usage

### Initialize Configuration
```bash
./src/main.py init
```
Interactive setup for Qdrant, embedding services, and chunking parameters.

### Index Code
```bash
./src/main.py index [path] [--force]
```
Index a code directory for semantic search. Uses incremental updates by default.
- `path`: Directory to index (defaults to current directory)
- `--force`: Force complete reindexing

### Search Code
```bash
./src/main.py search <query> [path] [options]
```
Search indexed code using semantic similarity.
- `query`: Search query text (required)
- `path`: Directory to search in (defaults to current directory)
- `--limit <N>`: Maximum number of results (default: 5)
- `--output <format>`: Output format: simple, json, simple-json
- `--threshold <float>`: Similarity threshold (0.0-1.0)

### Remove from Index
```bash
./src/main.py drop [path]
```
Remove a code directory from the index.
- `path`: Directory to remove (defaults to current directory)

### MCP Server
```bash
./src/main.py mcp
```
Start MCP (Model Context Protocol) server for tool integration. Exposes search functionality as MCP tools.

## Examples

Index current directory:
```bash
./src/main.py index .
```

Search for authentication functions:
```bash
./src/main.py search "user authentication" --limit 3
```

Search with JSON output:
```bash
./src/main.py search "API endpoints" --output json
```

Remove project from index:
```bash
./src/main.py drop ./my-project
```

## Configuration

Configuration is managed through `~/.code-context/settings.json`. Key settings include:

- **Qdrant**: Vector database connection
- **Embedding**: Service URL, API key, model, and embedding size
- **Explainer**: Optional code explanation service
- **Chunking**: Code chunk size and overlap parameters
- **Storage**: Snapshot directory for incremental indexing

## Dependencies

- cyclopts: CLI framework
- rich: Terminal formatting
- pydantic: Configuration and validation
- mcp: Model Context Protocol support
