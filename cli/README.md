# Code Context CLI

A command-line interface for indexing and searching codebases. The CLI provides semantic search capabilities by communicating with the Code Context API service.

## Installation

```bash
cargo build --release
```

## Usage

### Index a code directory
```bash
./code index <path> [--force]
```
Indexes a code directory for searching. Use `--force` to reindex even if already indexed.

### Search indexed code
```bash
./code search <path> <query> [limit] [extensions]
```
Searches indexed code using semantic similarity.
- `limit`: Maximum number of results (default: 5)
- `extensions`: File extensions to filter (e.g., ".go,.js")

### Remove a code directory
```bash
./code drop <path>
```
Removes a code directory from the index.

## Tech Stack

- **Rust** - Core CLI implementation
- **Clap** - Command-line argument parsing
- **Tokio** - Async runtime
- **Reqwest** - HTTP client for API communication
- **Serde** - JSON serialization/deserialization

## API Communication

The CLI communicates with the Code Context API service on `localhost:19531` for all operations.
