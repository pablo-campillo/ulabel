# Tooling & Technology Choices

This page documents the tools and libraries used in the uLabel backend, explaining why each was chosen and what trade-offs were considered.

## Language & Runtime

### Python 3.12

uLabel targets Python 3.12+ as its minimum version.

**Why 3.12:**

- `StrEnum` in the standard library — used for `ImageStatus`, `UserRole`, and `ImportJobStatus` without third-party dependencies.
- Improved error messages and performance optimizations (PEP 709 inlined comprehensions).
- Modern type hint syntax: `X | None` instead of `Optional[X]`, `list[T]` instead of `List[T]`.

**Trade-off:** Requiring 3.12+ excludes environments stuck on older Python versions. Since uLabel runs in Docker, this is not a practical concern.

### uvicorn + uvloop

The ASGI server uses `uvicorn` with `uvloop` as the event loop implementation.

**Why:** `uvloop` is a drop-in replacement for `asyncio`'s default event loop, written in Cython, that provides significantly higher throughput for I/O-bound workloads. Since every request touches the database and potentially object storage, this directly benefits latency under load.

## Package Management

### uv

[uv](https://docs.astral.sh/uv/) is used for dependency management and virtual environment handling.

**Why uv over pip/pip-tools:**

- 10-100x faster dependency resolution and installation (written in Rust).
- Deterministic lockfile (`uv.lock`) with cross-platform resolution.
- Built-in virtual environment management.
- Compatible with standard `pyproject.toml` — no proprietary configuration format.
- Active development by the same team behind `ruff`.

**Trade-off:** Relatively new tool. Mitigated by its standard `pyproject.toml` compatibility — falling back to pip is always possible.

## Code Quality

### ruff

[ruff](https://docs.astral.sh/ruff/) handles both linting and formatting.

**Why ruff over flake8 + isort + black:**

- Single tool replaces three (linter + import sorter + formatter).
- Written in Rust — runs in milliseconds, even on the full codebase.
- Compatible rule sets: supports flake8, isort, pyupgrade, and many more.
- Unified configuration in `pyproject.toml`.

**Configuration:**

```toml
[tool.ruff]
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I"]
```

Only `E` (pycodestyle errors), `F` (pyflakes), and `I` (isort) rules are enabled — enough to catch real issues without being noisy.

**Trade-off:** Less established than black/flake8 in enterprise environments. The output is effectively identical and the speed difference is substantial.

### mypy (strict mode)

Static type checking with `mypy` in strict mode ensures type correctness across the codebase.

```toml
[tool.mypy]
strict = true
python_version = "3.12"
```

**Why strict mode:** Catches missing type annotations, implicit `Any` types, and type errors that would otherwise surface at runtime. Combined with SQLAlchemy 2.0's `Mapped[T]` annotations, this provides end-to-end type safety from the database layer to the API response.

### pre-commit

[pre-commit](https://pre-commit.com/) runs quality checks automatically before each commit. The configuration file (`.pre-commit-config.yaml`) lives in the **repository root** (not in `backend/`) so that Git can find it. All hooks are scoped to `backend/` files via the `files: ^backend/` filter.

**Installation** (from the repo root):

```bash
pre-commit install
```

**Configured hooks:**

- `trailing-whitespace` — removes trailing whitespace.
- `end-of-file-fixer` — ensures files end with a newline.
- `check-yaml` / `check-toml` — validates YAML/TOML syntax.
- `check-merge-conflict` — prevents committing unresolved merge conflicts.
- `debug-statements` — catches leftover `breakpoint()` / `pdb` calls.
- `ruff check --fix` — linting with auto-fix.
- `ruff format` — formatting.
- `mypy` — type checking (runs via `make typecheck` inside Docker).

**Why:** Prevents poorly formatted or linted code from entering the repository. Fast enough (ruff runs in milliseconds) that it doesn't slow down the development workflow.

## Web Framework

### FastAPI

[FastAPI](https://fastapi.tiangolo.com/) is the web framework for the REST API.

**Why FastAPI:**

- Native async support — all route handlers are `async def`.
- Automatic OpenAPI documentation from type hints and Pydantic schemas.
- Dependency injection system via `Depends()`, which integrates naturally with `dependency-injector`.
- Pydantic v2 integration for request validation and response serialization.
- High performance (Starlette-based ASGI framework).

**Trade-off:** The ecosystem is younger than Django/Flask. For a focused API service (no admin panel, no template rendering), FastAPI's async-first approach is a better fit.

## Database

### SQLAlchemy 2.0 (async)

[SQLAlchemy 2.0](https://docs.sqlalchemy.org/) with the async API provides the ORM layer.

**Why SQLAlchemy 2.0:**

- `mapped_column` with `Mapped[T]` gives full type safety for model definitions.
- Native async session support via `AsyncSession` — no need for thread pool executors.
- `insert().on_conflict_do_update/nothing()` for PostgreSQL upsert semantics.
- Mature migration support via Alembic.
- Excellent integration with mypy for static analysis.

**Trade-off:** More complex than lighter alternatives (e.g., `databases`, `encode/orm`). The complexity pays off in type safety, migration support, and the ability to express advanced queries (subqueries, window functions, row-level locking).

### asyncpg

The PostgreSQL driver, chosen for:

- Native async protocol implementation (not a wrapper around a sync driver).
- Prepared statements and binary protocol for performance.
- Direct integration with SQLAlchemy's async engine.

### Alembic

Database migrations use Alembic with async support. The migration environment (`env.py`) runs migrations using the same `asyncpg` driver as the application, ensuring consistent behavior between migrations and runtime.

## Object Storage

### aioboto3

[aioboto3](https://github.com/terrycain/aioboto3) provides async S3 access.

**Why aioboto3:**

- Async wrapper around `boto3` — the standard AWS SDK for Python.
- Compatible with any S3-compatible service (MinIO in development, AWS S3 in production).
- Supports presigned URL generation, object listing, metadata, and uploads.

**Trade-off:** `aioboto3` is a community wrapper, not an official AWS library. The underlying `botocore` does the real work; `aioboto3` just makes it async-friendly.

## Serialization

### orjson

[orjson](https://github.com/ijl/orjson) is used for JSON serialization, specifically in the structured logging `JsonFormatter`.

**Why orjson:**

- Written in Rust — 2-10x faster than the standard `json` module.
- Native support for `datetime`, `UUID`, and `dataclass` serialization.
- Used in the hot path: every log line is serialized to JSON via orjson.

**Trade-off:** C extension dependency — requires a compatible build for the target platform. In practice, wheels are available for all common platforms.

## Dependency Injection

### dependency-injector

[dependency-injector](https://python-dependency-injector.ets-labs.org/) provides the DI framework.

**Why:**

- `DeclarativeContainer` pattern for centralized dependency wiring.
- Lifecycle management: `Singleton` for expensive resources (DB engine, storage), `Factory` for per-request resources (Unit of Work, use cases).
- YAML configuration loading with environment variable interpolation.
- Integration with FastAPI via `Provide[]` and `@inject`.

**Trade-off:** Adds a framework dependency for something that could be done manually. The benefit is eliminating boilerplate and getting lifecycle management (singleton vs factory) for free. The container is also the single place to swap implementations for testing.

## Testing

### pytest + pytest-anyio

Testing uses `pytest` with `pytest-anyio` for async test support.

**Why pytest-anyio over pytest-asyncio:**

- Supports multiple async backends (asyncio, trio).
- Consistent fixture handling for async fixtures.

**Testing strategy:**

- **Unit tests** (`tests/application/`, `tests/api/`): Use in-memory repositories and fake storage. Fast (milliseconds), no infrastructure needed.
- **Integration tests** (`tests/integration/`): Run against a real PostgreSQL database to verify SQL queries and migrations.
- **API tests** (`tests/api/`): Use `httpx.AsyncClient` with FastAPI's `TestClient` for full HTTP request/response testing.
- **E2E tests** (`tests/e2e/`): Exercise full API workflows against a real PostgreSQL database using `httpx.AsyncClient` with the FastAPI app. Storage is replaced by `FakeStorageService`.

## Documentation

### MkDocs + Material

[MkDocs](https://www.mkdocs.org/) with the [Material](https://squidfunk.github.io/mkdocs-material/) theme generates the documentation site.

**Why MkDocs:**

- Documentation as code — Markdown files versioned alongside the codebase.
- Material theme provides a modern, responsive UI with dark mode, search, and navigation tabs.
- [mkdocstrings](https://mkdocstrings.github.io/) auto-generates API reference from Python docstrings.
- Mermaid diagram support via `pymdownx.superfences`.

**Documentation structure** follows the [Diataxis framework](https://diataxis.fr/):

| Section | Purpose |
|---------|---------|
| Tutorials | Step-by-step learning guides |
| How-To Guides | Task-oriented recipes |
| Reference | Auto-generated API documentation |
| Explanation | Design decisions and architecture (this section) |
