.PHONY: help build up up-d down down-v logs migrate init

help:             ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*##"}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

# ── Docker ──────────────────────────────────────────────────────────────────

build:            ## Build all Docker images
	docker compose build

up:               ## Start the full platform (backend + frontend + db + storage)
	docker compose up --build

up-d:             ## Start the full platform in detached mode
	docker compose up --build -d

down:             ## Stop all services
	docker compose down

down-v:           ## Stop all services and remove volumes
	docker compose down -v

logs:             ## Follow logs from all services
	docker compose logs -f

# ── Database ────────────────────────────────────────────────────────────────

migrate:          ## Run pending database migrations
	docker compose exec app alembic upgrade head

# ── Bootstrap ──────────────────────────────────────────────────────────────

init:             ## Bootstrap the platform: migrate, seed users, seed dataset
	$(MAKE) migrate
	@echo "==> Seeding users..."
	docker compose exec db psql -U ulabel -d ulabel -c " \
	  INSERT INTO users (id, username, role) VALUES \
	    (gen_random_uuid(), 'admin',     'admin'), \
	    (gen_random_uuid(), 'labeler1',  'labeler'), \
	    (gen_random_uuid(), 'labeler2',  'labeler'), \
	    (gen_random_uuid(), 'labeler3',  'labeler'), \
	    (gen_random_uuid(), 'labeler4',  'labeler'), \
	    (gen_random_uuid(), 'labeler5',  'labeler'), \
	    (gen_random_uuid(), 'labeler6',  'labeler'), \
	    (gen_random_uuid(), 'labeler7',  'labeler'), \
	    (gen_random_uuid(), 'labeler8',  'labeler'), \
	    (gen_random_uuid(), 'labeler9',  'labeler'), \
	    (gen_random_uuid(), 'labeler10', 'labeler') \
	  ON CONFLICT (username) DO NOTHING;"
	@echo "==> Seeding dataset..."
	$(MAKE) -C backend seed-dataset
