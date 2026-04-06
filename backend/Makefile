IMAGE     := ulabel-backend
DEV_IMAGE := $(IMAGE)-dev
SRC       := src
TESTS     := tests

-include .env
export

DATASET_URL        := https://huggingface.co/datasets/IABD12/Perros_gatos/resolve/main/dogs-vs-cats.zip
DATASET_TMP        := /tmp/ulabel-dataset
STORAGE_ENDPOINT   ?= http://localhost:9000
STORAGE_ACCESS_KEY ?= minioadmin
STORAGE_SECRET_KEY ?= minioadmin
STORAGE_BUCKET     ?= ulabel
TEST_DATABASE_URL  ?= postgresql+asyncpg://ulabel:secret@localhost:5432/ulabel

.PHONY: help setup install pre-commit-install test test-integration format lint lint-fix typecheck check build run dev shell migrate migrate-create migrate-down seed-dataset docs docs-build

help:                ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*##"}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

# ── Environment ──────────────────────────────────────────────────────────────

setup:               ## Build the dev Docker image
	docker build --target dev -t $(DEV_IMAGE) .

install:             ## Sync all dependencies (including dev) into local .venv
	docker run --rm \
		-v $(PWD):/app \
		$(DEV_IMAGE) uv sync

pre-commit-install:  ## Install pre-commit hooks into .git/hooks
	docker run --rm \
		-v $(PWD):/app \
		-v $(PWD)/../.git:/app/../.git \
		$(DEV_IMAGE) uv run --group dev pre-commit install

dev:                 ## Start dev server with hot reload
	docker compose up app

shell:               ## Open an interactive shell inside the dev container
	docker run --rm -it \
		-v $(PWD)/$(SRC):/app/$(SRC) \
		-v $(PWD)/$(TESTS):/app/$(TESTS) \
		$(DEV_IMAGE) bash

# ── Quality ──────────────────────────────────────────────────────────────────

test-unit:                ## Run unit tests inside the dev container
	docker run --rm \
		-v $(PWD)/$(SRC):/app/$(SRC) \
		-v $(PWD)/$(TESTS):/app/$(TESTS) \
		$(DEV_IMAGE) uv run --group dev pytest tests/unit -v

test-cov:            ## Run all tests with coverage report (shows missing lines per file)
	docker run --rm \
		--network host \
		-e TEST_DATABASE_URL=$(TEST_DATABASE_URL) \
		-v $(PWD)/$(SRC):/app/$(SRC) \
		-v $(PWD)/$(TESTS):/app/$(TESTS) \
		$(DEV_IMAGE) uv run --group dev pytest tests/ --cov=ulabel --cov-report=term-missing -v

test-integration:    ## Run integration tests (requires TEST_DATABASE_URL)
	docker run --rm \
		--network host \
		-e TEST_DATABASE_URL=$(TEST_DATABASE_URL) \
		-v $(PWD)/$(SRC):/app/$(SRC) \
		-v $(PWD)/$(TESTS):/app/$(TESTS) \
		$(DEV_IMAGE) uv run --group dev pytest tests/integration -v

test-e2e:            ## Run end-to-end API tests (requires TEST_DATABASE_URL)
	docker run --rm \
		--network host \
		-e TEST_DATABASE_URL=$(TEST_DATABASE_URL) \
		-v $(PWD)/$(SRC):/app/$(SRC) \
		-v $(PWD)/$(TESTS):/app/$(TESTS) \
		$(DEV_IMAGE) uv run --group dev pytest tests/e2e -v

format:              ## Format code with ruff (edits files on host via volume mount)
	docker run --rm \
		-v $(PWD)/$(SRC):/app/$(SRC) \
		-v $(PWD)/$(TESTS):/app/$(TESTS) \
		$(DEV_IMAGE) uv run --group dev ruff format $(SRC)/ $(TESTS)/

lint:                ## Lint code with ruff
	docker run --rm \
		-v $(PWD)/$(SRC):/app/$(SRC) \
		-v $(PWD)/$(TESTS):/app/$(TESTS) \
		$(DEV_IMAGE) uv run --group dev ruff check $(SRC)/ $(TESTS)/

lint-fix:            ## Lint and auto-fix with ruff
	docker run --rm \
		-v $(PWD)/$(SRC):/app/$(SRC) \
		-v $(PWD)/$(TESTS):/app/$(TESTS) \
		$(DEV_IMAGE) uv run --group dev ruff check --fix $(SRC)/ $(TESTS)/

typecheck:           ## Type-check with mypy
	docker run --rm \
		-v $(PWD)/$(SRC):/app/$(SRC) \
		$(DEV_IMAGE) uv run --group dev mypy $(SRC)/

check: format lint typecheck test  ## Run all quality checks in order

# ── Documentation ────────────────────────────────────────────────────────────

docs:                ## Serve documentation locally with hot reload
	docker run --rm -p 8080:8080 \
		-v $(PWD)/docs:/app/docs:ro \
		-v $(PWD)/mkdocs.yml:/app/mkdocs.yml:ro \
		-v $(PWD)/$(SRC):/app/$(SRC):ro \
		$(DEV_IMAGE) uv run --group docs mkdocs serve -a 0.0.0.0:8080

docs-build:          ## Build documentation as static site
	docker run --rm \
		-v $(PWD)/docs:/app/docs:ro \
		-v $(PWD)/mkdocs.yml:/app/mkdocs.yml:ro \
		-v $(PWD)/$(SRC):/app/$(SRC):ro \
		-v $(PWD)/site:/app/site \
		$(DEV_IMAGE) uv run --group docs mkdocs build

# ── Docker ───────────────────────────────────────────────────────────────────

build:               ## Build the production runtime image
	docker build --target runtime -t $(IMAGE) .

run:                 ## Start the app with docker compose
	docker compose up app

# ── Migrations ────────────────────────────────────────────────────────────────

migrate:             ## Apply all pending migrations
	docker compose exec app alembic upgrade head

migrate-create:      ## Create a new migration (usage: make migrate-create msg="description")
	docker compose exec app alembic revision --autogenerate -m "$(msg)"

migrate-down:        ## Rollback the last migration
	docker compose exec app alembic downgrade -1

# ── Dataset ───────────────────────────────────────────────────────────────────

seed-dataset:        ## Download dogs-vs-cats dataset and upload to MinIO under datasets/
	@echo "→ Downloading and extracting dataset..."
	@docker run --rm --network host \
		-v $(DATASET_TMP):/data \
		alpine:3.20 sh -c "\
			apk add --no-cache wget unzip > /dev/null && \
			wget -q --show-progress -O /data/dogs-vs-cats.zip $(DATASET_URL) && \
			unzip -q -o /data/dogs-vs-cats.zip -d /data && \
			unzip -q -o /data/train.zip  -d /data && \
			unzip -q -o /data/test1.zip  -d /data"
	@echo "→ Uploading to $(STORAGE_ENDPOINT)/$(STORAGE_BUCKET)/datasets/ ..."
	@docker run --rm --network host \
		-v $(DATASET_TMP):/data:ro \
		rclone/rclone sync /data/ :s3:$(STORAGE_BUCKET)/datasets \
		  --s3-no-check-bucket \
		  --s3-provider Minio \
		  --s3-endpoint $(STORAGE_ENDPOINT) \
		  --s3-access-key-id $(STORAGE_ACCESS_KEY) \
		  --s3-secret-access-key $(STORAGE_SECRET_KEY) \
		  --s3-region us-east-1 \
		  --exclude "*.zip" \
		  --transfers 32 \
		  --progress
	@echo "✓ Dataset available at $(STORAGE_BUCKET)/datasets/"
