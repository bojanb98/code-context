# CLAUDE.md

---

## Goals
- Maintain **readability, determinism, and testability**.
- Prioritize **clarity and maintainability** over abstraction.
- Code should be **functional, explicit, and side-effect aware**.
- Every module should have a single clear purpose.

---

## Project Structure

### `/core`
Implements all logic for semantic indexing and search.

| Area | Description |
|-------|--------------|
| `core/services/` | Indexing, searching, embeddings, and explanation services |
| `core/splitters/` | Tree-sitter based chunkers and related types |
| `core/sync/` | Incremental file sync and hashing |
| `core/services/utils/` | Helper services (embeddings, explainer, collection naming) |

### `/cli`
Thin async command layer wrapping core services with `cyclopts`.
`ServiceFactory` handles construction and lifecycle of dependencies.

---

## Design Principles

### Code Style
- Python 3.13+, `async`/`await` by default. 
- Follow **PEP8 + Black + Ruff defaults**; 88-char lines.
- Use **type hints** everywhere.
- Prefer **dataclasses** for immutable records. 
- Log via **loguru**, retry via **tenacity**, never print from core modules.
- Avoid global state; configuration flows through `AppSettings`.

### Architecture
- **Core is framework-agnostic** and async-safe.
- **CLI and integrations** (MCP, REST, etc.) compose services — they never re-implement logic.
- **Tree-sitter** is the only parsing layer; do not add regex-based splitters.
- File synchronization uses **deterministic hashing** and `.gitignore` inheritance.
- All network operations (Qdrant, embedding APIs) must be **idempotent and retried** safely.
- Favor **composition over inheritance**

### Testing & Development

* CLI development uses:

  ```bash
  uv run src/main.py <command>
  ```
* Avoid mocking external APIs; use small test containers or fixtures.
* Unit tests should verify correctness of:

  * File scanning and `.gitignore` merging
  * Chunk extraction and doc inference
  * Embedding and search vector schema

---

## Tools

| Purpose           | Tool                |
| ----------------- | ------------------- |
| CLI framework     | Cyclopts            |
| Output formatting | Rich                |
| Async client      | Qdrant Python SDK   |
| Embeddings        | OpenAI API / Ollama |
| Code parsing      | tree-sitter         |
| Retry handling    | tenacity            |
| Logging           | loguru              |
| Build / Env       | uv                  |

---

## Extending the System

* Add new **splitters** or **embedders** by extending existing protocols.
* New features must integrate through service interfaces — never modify CLI directly.
* Keep API contracts stable across versions (`IndexingService`, `SearchService`).

---

## Summary

The repository values **predictable async systems**, **simple composition**, and **directness**.
When in doubt: *prefer fewer abstractions, smaller modules, and visible data flow.*
