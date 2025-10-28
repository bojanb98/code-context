# Claude Context API

A REST API service that exposes the [@zilliz/claude-context-core](https://github.com/zilliztech/claude-context-core) library for semantic code search and indexing. Built with Bun and Elysia.js.

## Overview

This API provides powerful semantic search capabilities for codebases using vector embeddings and Milvus vector database. It allows you to:

- Index local codebases for semantic search
- Search code using natural language queries
- Manage ignore patterns for indexing
- Configure embedding providers (OpenAI, Ollama)

## Features

- **Semantic Code Search**: Find relevant code using natural language queries
- **Multiple Embedding Providers**: Support for OpenAI and Ollama embeddings
- **Vector Database Storage**: Uses Milvus for efficient vector similarity search
- **Ignore Pattern Management**: Configure which files to exclude from indexing
- **RESTful API**: Clean HTTP endpoints with validation
- **OpenAPI Documentation**: Auto-generated API documentation
- **Project-Specific Configuration**: Per-project settings and ignore patterns

## Requirements

- Bun 1.3.0+
- Node.js 18+
- Milvus vector database
- OpenAI API key (for OpenAI embeddings) or Ollama instance

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd claude-context-api

# Install dependencies
bun install

# Copy environment variables
cp .env.example .env
```

## Configuration

Configuration is managed through:
- Environment variables
- `~/.context-cli/settings.json` file
- API endpoints

### Environment Variables

```bash
# Milvus Configuration
MILVUS_ADDRESS=localhost:19530
MILVUS_TOKEN=your-milvus-token

# OpenAI Embeddings (if using OpenAI)
EMBEDDING_CLASS=openai
EMBEDDING_URL=https://api.openai.com/v1
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_TOKEN=your-openai-api-key

# Ollama Embeddings (if using Ollama)
EMBEDDING_CLASS=ollama
EMBEDDING_URL=http://localhost:11434
EMBEDDING_MODEL=vuongnguyen2212/CodeRankEmbed

# Server Configuration
PORT=3000
HOST=localhost
```

## Usage

### Starting the Server

```bash
# Development mode with hot reload
bun run dev

# Production mode
bun run src/index.ts
```

The API will be available at `http://localhost:3000`

### API Endpoints

#### Indexing Operations

**Index a Codebase**
```http
POST /api/index
Content-Type: application/json

{
  "path": "/path/to/your/codebase",
  "force": false
}
```

**Clear Index**
```http
DELETE /api/index
Content-Type: application/json

{
  "path": "/path/to/your/codebase"
}
```

**Reindex Modified Files**
```http
POST /api/index/reindex
Content-Type: application/json

{
  "path": "/path/to/your/codebase"
}
```

#### Search Operations

**Semantic Search**
```http
GET /api/search?path=/path/to/codebase&query=function that handles authentication&limit=5
```

Response:
```json
{
  "results": [
    {
      "file": "src/auth/login.ts",
      "startLine": 15,
      "endLine": 45,
      "score": 0.92,
      "language": "typescript",
      "content": "function authenticateUser(credentials) { ... }"
    }
  ],
  "query": "function that handles authentication",
  "path": "/path/to/codebase",
  "limit": 5,
  "totalResults": 1
}
```

#### Configuration

**Get Current Configuration**
```http
GET /api/config
```

Response:
```json
{
  "embeddingClass": "ollama",
  "embeddingUrl": "http://localhost:11434",
  "embeddingModel": "vuongnguyen2212/CodeRankEmbed",
  "embeddingToken": "not set",
  "milvusAddress": "localhost:19530",
  "milvusToken": "not set"
}
```

#### Ignore Pattern Management

**Add Ignore Pattern**
```http
POST /api/ignored
Content-Type: application/json

{
  "path": "/path/to/project",
  "pattern": "*.test.js"
}
```

**List Ignore Patterns**
```http
GET /api/ignored?path=/path/to/project
```

**Remove Ignore Pattern**
```http
DELETE /api/ignored
Content-Type: application/json

{
  "path": "/path/to/project",
  "pattern": "*.test.js"
}
```

#### Health Check

```http
GET /api/status
```

### API Documentation

OpenAPI documentation is automatically generated and available at:
- Swagger UI: `http://localhost:3000/swagger`
- OpenAPI JSON: `http://localhost:3000/openapi`

## Architecture

The API follows a vertical slice architecture:

```
src/
├── routes/           # API route handlers
│   ├── config/      # Configuration endpoints
│   ├── ignored/     # Ignore pattern management
│   ├── index/       # Indexing operations
│   └── search/      # Search operations
├── services/        # Business logic
│   ├── config.service.ts      # Configuration management
│   └── ignored-files.service.ts # Ignore patterns
├── context.ts       # Context initialization and core logic
├── logger.ts        # Winston logging configuration
└── index.ts         # Application entry point
```

## Development

### Code Style

- TypeScript with strict type checking
- Vertical slice architecture
- Functions under 50 lines
- Files under 500 lines
- Elysia built-in validation
- Winston for structured logging

### Running Tests

```bash
bun test
```

### Adding New Routes

1. Create route file in `src/routes/`
2. Follow existing patterns with validation
3. Add to main application in `src/index.ts`

## Examples

### Basic Usage

```bash
# Index a project
curl -X POST http://localhost:3000/api/index \
  -H "Content-Type: application/json" \
  -d '{"path": "/path/to/my-project"}'

# Search for code
curl "http://localhost:3000/api/search?path=/path/to/my-project&query=authentication function&limit=3"

# Add ignore patterns
curl -X POST http://localhost:3000/api/ignored \
  -H "Content-Type: application/json" \
  -d '{"path": "/path/to/my-project", "pattern": "node_modules/**"}'
```

### JavaScript/TypeScript Client

```javascript
// Index a codebase
const indexResponse = await fetch('http://localhost:3000/api/index', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    path: './my-project',
    force: false
  })
});

// Search semantically
const searchResponse = await fetch(
  'http://localhost:3000/api/search?path=./my-project&query=user authentication&limit=5'
);
const results = await searchResponse.json();

console.log('Found results:', results.results);
```

## Environment Variables Reference

| Variable | Description | Default |
|----------|-------------|---------|
| `PORT` | Server port | `3000` |
| `HOST` | Server hostname | `localhost` |
| `MILVUS_ADDRESS` | Milvus database address | `localhost:19530` |
| `MILVUS_TOKEN` | Milvus authentication token | (empty) |
| `EMBEDDING_CLASS` | Embedding provider (`openai`/`ollama`) | `ollama` |
| `EMBEDDING_URL` | Embedding service URL | `http://localhost:11434` |
| `EMBEDDING_MODEL` | Embedding model name | `vuongnguyen2212/CodeRankEmbed` |
| `EMBEDDING_TOKEN` | API token for embeddings | (empty) |

## Troubleshooting

### Common Issues

1. **Milvus Connection Failed**
   - Ensure Milvus is running on the configured address
   - Check network connectivity and firewall settings

2. **Embedding Service Unavailable**
   - For Ollama: Ensure Ollama is running and the model is pulled
   - For OpenAI: Verify API key and network access

3. **Indexing Fails**
   - Check file permissions on the target directory
   - Verify ignore patterns don't exclude all files
   - Ensure sufficient disk space for vector storage

### Logging

The application uses Winston for structured logging. Logs include:
- Request/response details
- Error messages with stack traces
- Progress updates for indexing operations
- Configuration changes

## License

Private project - all rights reserved.