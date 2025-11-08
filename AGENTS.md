# Repository Guidelines

## Project Structure & Architecture
- `core/` holds the semantic engine: `services/` (index/search orchestration over Qdrant and AsyncOpenAI embeddings), `splitters/` (Tree-Sitter chunker plus fallbacks), `graph/` (optional GraphRAG edge builder consuming splitter output), and `sync/` (file snapshots + diffing). Keep new modules feature-focused and under 500 LOC.
- `cli/` wraps the core via Cyclopts. `src/commands/` exposes `init/index/search/drop/mcp`, while `service_factory.py` wires Qdrant clients, embedding/explainer services, splitter, and synchronizer.
- `docker-compose.yaml` runs local Qdrant and Ollama; use it before invoking CLI commands that hit external services. Dist builds live under `cli/main.*` or `core/dist/`.

## Build, Test, and Development Commands
- `uv sync` (run inside `core/` or `cli/`) installs the locked environment from `uv.lock`.
- `uv run src/main.py <command>` (inside `cli/`) executes CLI flows, e.g. `uv run src/main.py index .` or `uv run src/main.py search "jwt middleware"`.
- `uv run python -m build` (inside the desired package) produces distributable artifacts when needed.
- `docker compose up -d` boots Qdrant and Ollama for local indexing/search loops.

## Coding Style & Naming Conventions
- Python 3.13+, type hints everywhere, functions target <50 lines. Prefer dataclasses for payloads (`SearchResult`, `Explanations`).
- Use modern python types - lowercase list, tuple, dict, T | None...
- Don't use Top file level docstrings
- Don't import annotations from future and there are no optional imports (no if condition: import)
- Prefer Literal["A", "B"] over Enums
- Format with `black` (line length 88) and keep modules import-order tidy; run `uv run black .` before sharing patches.
- Use descriptive snake_case for functions/variables, CapWords for classes, and module-level constants (e.g., `CODE_DENSE`) for shared config.
- Logging goes through `loguru`; CLI output uses `rich` for any user-facing text.

## Testing Guidelines
- No tests exist today and none should be added unless explicitly requested. When the need arises, default to `pytest` unit tests plus `testcontainers` for infrastructure touches (e.g., Qdrant). Place suites under `tests/`, naming files `test_<feature>.py`, and execute with `uv run pytest`.

## Commit & Pull Request Guidelines
- Follow the established conventional-style prefixes (`docs:`, `chore:`, etc.) seen in `git log`. Keep messages imperative and scoped to a single change.
- Contributors should not push commits or open PRs directly from an automated agent—always hand off patches/diffs for human review.
- PRs (when humans open them) must describe the problem, outline the solution, note config changes, and link any tracking issues. Screenshots or CLI transcripts help when touching user output.

## Configuration & Operational Notes
- User-facing settings live in `~/.code-context/settings.json`; each collection hash resides under `~/.code-context/configs/`. Respect these paths when documenting workflows.
- Never edit secrets in-source. Reference them via `AppSettings` environment overrides or `.env` per pydantic settings behavior.
