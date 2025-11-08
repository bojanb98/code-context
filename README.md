# Code Context

Semantic code search and indexing system built with Python. Provides Semantic code search through vector embeddings and hybrid search capabilities.

## Quick Usage

To use you can download correct binay from [Releases](https://github.com/bojanb98/code-context/releases). Before usage you need to run init command to configure the Qdrant instance and embeddings provider:

```bash
code-context init
```

Supports any OpenAI API compatible provider, including Ollama. If you want to quickly setup local Qdrant and Ollama just copy provider [Docker Compose file](./docker-compose.yaml), or run:
```
docker compose up -d
```
from the repo root. Default CLI configuration values are already setup to work with local stack. FalkorDB usage is optional.

Index and search code:
```bash
code-context index [path]            # Index current directory or specified path
code-context search "query" [path]   # Search in current directory or specified path
code-context drop [path]             # Remove current directory or specified path from index
```

MCP server support:
```bash
code-context mcp                     # Start MCP server for tool integration
```

## Functionalities

1. **Semantic chunking** - using Tree-Sitter
2. **Hybrid search** - using bm25 + any dense embedding model 
3. **Incremental reindexing** - based on xxhash hashing
4. **Docstring extraction** (Optional) - creates additional bm25 + dense index for search
5. **Explanation generation** (Optional) - augments chunks with no docstring using small LLM
6. **Graph RAG** (Optional) - additional graph traversal + reranking step based on initial chunks, backed by FalkorDB

## Architecture

- `core/` - Python library for semantic code indexing and search
- `cli/` - Command-line interface for indexing and searching

See individual README files for detailed documentation:
- [Core Documentation](core/README.md)
- [CLI Documentation](cli/README.md)
