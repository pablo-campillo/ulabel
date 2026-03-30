# ── base ─────────────────────────────────────────────────────────────────────
FROM python:3.12-slim AS base

WORKDIR /app

# Install uv from official image — faster and avoids pip overhead
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH"

# ── builder ───────────────────────────────────────────────────────────────────
# Installs only production dependencies.
# Separating dependency installation from source copy maximises layer cache:
# deps are only reinstalled when pyproject.toml / uv.lock change.
FROM base AS builder

COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev --no-install-project

COPY src/ ./src/
RUN uv sync --frozen --no-dev

# ── runtime ───────────────────────────────────────────────────────────────────
# Minimal image: no uv, no build tools, no dev/test dependencies.
FROM python:3.12-slim AS runtime

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/src   /app/src
COPY config.yml  ./
COPY alembic.ini ./
COPY alembic/    ./alembic/

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["uvicorn", "ulabel.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--loop", "uvloop"]

# ── dev ───────────────────────────────────────────────────────────────────────
# Extends builder with dev dependencies (pytest, ruff, mypy, …) and test files.
# Use this stage for local development and CI.
FROM builder AS dev

RUN uv sync --frozen --group docs

COPY config.yml ./
COPY tests/ ./tests/

CMD ["uv", "run", "--group", "dev", "pytest", "tests/", "-v"]
