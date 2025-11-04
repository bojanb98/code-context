# CLAUDE.md

Semantic code search system with Python core library and cyclopts CLI.

## Development Commands

### Core Library
```bash
cd core && uv sync
```

### CLI Tool
```bash
cd cli && uv sync
./src/main.py init                          # Interactive configuration
./src/main.py index [path] [--force]        # Index directory
./src/main.py search <query> [path]         # Search
./src/main.py drop [path]                   # Remove from index
./src/main.py mcp                           # Start MCP server
```

## Architecture

### Core (`core/`)
Python library with modular structure:
- **IndexingService**: Orchestrates file processing and vector storage
- **SearchService**: Handles semantic search queries with hybrid capabilities
- **EmbeddingService**: Manages embedding generation via OpenAI-compatible APIs
- **ExplainerService**: Provides code explanations using LLMs
- **FileSynchronizer**: Merkle tree-based incremental updates
- **TreeSitterSplitter**: Language-aware code splitting
- **CollectionName**: Generates unique collection names per project

### CLI (`cli/`)
Python command-line tool:
- Commands: `init`, `index`, `search`, `drop`, `mcp`
- Configuration management via pydantic-settings
- Rich terminal output formatting
- MCP server integration for tool usage

## Key Features

- **Hybrid Search**: Combines semantic similarity and keyword matching
- **Incremental Updates**: Merkle tree-based change detection
- **Multi-language Support**: Tree-sitter parsing for 15+ languages
- **Flexible Embeddings**: OpenAI-compatible providers including Ollama
- **Code Explanations**: Optional LLM-powered code explanations
- **MCP Integration**: Model Context Protocol server for tool integration

## Code Style

### Python
- **Formatter**: Black with 88-character line length
- **Type Hints**: Modern Python 3.13 typing syntax
- **Async/Await**: Full async pattern for I/O operations
- **Dependencies**: Managed with uv package manager

### Libraries and Tools
- **cyclopts**: Modern CLI argument parsing
- **pydantic**: Data validation and configuration management
- **rich**: Terminal formatting and progress display
- **loguru**: Structured logging with rotation
- **qdrant-client**: Vector database client
- **tree-sitter**: Language parsing for code splitting
- **mcp**: Model Context Protocol server implementation
- **tenacity**: Retry logic with exponential backoff

### Project Structure
- **Modular Design**: Clear separation between services, utilities, and CLI
- **Configuration**: Centralized settings with environment variable support
- **Error Handling**: Comprehensive error handling and logging
- **Testing**: Tests organized in `tests/` directory

### Development Practices
- **Async-First**: All I/O operations use async/await patterns
- **Type Safety**: Comprehensive type annotations throughout
- **Configuration Management**: Environment-based configuration with defaults
- **Service Factory**: Dependency injection pattern for service management
