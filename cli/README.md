# Code Context CLI

A command-line interface for indexing and searching codebases. The CLI provides semantic search capabilities by communicating with the Code Context API service.

## Installation

```bash
cargo build --release
```

## Usage

### Index a code directory
```bash
./code index [path] [--force]
```
Indexes a code directory for searching. Defaults to current directory when no path is provided.

### Search indexed code
```bash
./code search <query> [path] [options]
```
Searches indexed code using semantic similarity. Query is the first argument. Defaults to current directory when no path is provided.

**Options:**
- `--limit <N>`: Maximum number of results (default: 5)
- `--extensions <list>`: File extensions to filter (e.g., ".go,.js")

### Remove a code directory
```bash
./code drop [path]
```
Removes a code directory from the index. Defaults to current directory when no path is provided.

## Tech Stack

- **Rust** - Core CLI implementation
- **Clap** - Command-line argument parsing
- **Tokio** - Async runtime
- **Reqwest** - HTTP client for API communication
- **Serde** - JSON serialization/deserialization

## API Communication

The CLI communicates with the Code Context API service on `localhost:19531` for all operations.
