# Claude Code Extensions CLI

A command-line interface for indexing and searching codebases via a local HTTP API service.

## Overview

The `code` CLI provides commands to index, search, reindex, and unindex code directories. It communicates with a local API server running on `localhost:19531` to perform code indexing and semantic search operations.

## Installation

```bash
go build -o code .
```

## Usage

### Index a directory
```bash
code index <path>
```

### Search indexed code
```bash
code search <path> <query> [limit] [extensions]
```

- `path`: Directory path to search in
- `query`: Search query string
- `limit`: Maximum number of results (default: 5)
- `extensions`: File extensions to filter (e.g., ".go,.js")

### Search current working directory
```bash
code search-cwd <query> [limit] [extensions]
```

### Reindex a directory
```bash
code reindex <path>
```

### Remove index
```bash
code unindex <path>
```

## Configuration

The CLI expects the API service to be running on `http://localhost:19531`. Make sure the service is started before using any commands.

## Dependencies

- Go 1.24.8+
- [Cobra](https://github.com/spf13/cobra) for CLI framework

## License
