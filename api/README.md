# Code Context API

FastAPI service for semantic code search and indexing using Qdrant and FastEmbed.

## Installation

```bash
uv sync
```

## Usage

Start the development server:
```bash
uv run fastapi dev src/main.py
```

Or run the production server:
```bash
uv run fastapi run src/main.py
```

The API will be available at `http://localhost:19531` with Swagger documentation at `/swagger`.

## API Endpoints

### Indexing
- `POST /api/index` - Index a codebase directory
- `DELETE /api/index/{path}` - Remove index for a directory

### Search
- `GET /api/search` - Search indexed code with semantic query

## Configuration

The API uses the core library with configurable Qdrant and embedding settings. See `core/README.md` for detailed configuration options.

## Dependencies

- FastAPI for web framework
- Uvicorn for ASGI server
- Core library for indexing and search functionality
- Loguru for logging

## Architecture

Built on top of the custom Python core library that provides:
- Semantic embeddings using FastEmbed or any OpenAI compatible provider
- Vector storage with Qdrant
- Code splitting and indexing
- File synchronization and change detection
