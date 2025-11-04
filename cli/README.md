# Code Context CLI

A command-line interface for indexing and searching codebases. The CLI provides semantic search capabilities by using Code Context core module. Built using cyclopts library.

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
