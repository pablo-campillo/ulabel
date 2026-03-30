.PHONY: help build up up-d down down-v logs migrate init bootstrap wait-healthy

TIMEOUT := 120

help:             ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*##"}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

# ── Docker ──────────────────────────────────────────────────────────────────

build:            ## Build all Docker images
	docker compose build

up:               ## Start the full platform (backend + frontend + db + storage + observability)
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

wait-healthy:
	@echo "==> Waiting for services to be ready (timeout: $(TIMEOUT)s)..."
	@db_ok=0; api_ok=0; elapsed=0; \
	while [ $$elapsed -lt $(TIMEOUT) ]; do \
		if [ $$db_ok -eq 0 ] && docker compose exec -T db pg_isready -U ulabel -q 2>/dev/null; then \
			echo "    - Database is ready"; \
			db_ok=1; \
		fi; \
		if [ $$api_ok -eq 0 ] && curl -sf http://localhost:8000/ >/dev/null 2>&1; then \
			echo "    - Backend API is ready"; \
			api_ok=1; \
		fi; \
		if [ $$db_ok -eq 1 ] && [ $$api_ok -eq 1 ]; then \
			echo "==> All services are ready."; \
			exit 0; \
		fi; \
		sleep 2; \
		elapsed=$$((elapsed + 2)); \
	done; \
	echo "ERROR: services did not become ready within $(TIMEOUT)s (db=$$db_ok, api=$$api_ok)"; \
	docker compose logs app --tail 20; \
	exit 1

init:             ## Bootstrap data: migrate, seed users, seed dataset
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

bootstrap:        ## Start everything, initialize data, and show access info
	$(MAKE) up-d
	$(MAKE) wait-healthy
	$(MAKE) init
	docker compose --profile docs up --build -d docs
	@echo ""
	@echo "══════════════════════════════════════════════════════════════"
	@echo "  uLabel platform is ready!"
	@echo "══════════════════════════════════════════════════════════════"
	@echo ""
	@echo "  Frontend        http://localhost:5173"
	@echo "  Backend API     http://localhost:8000"
	@echo "  API Docs        http://localhost:8000/redoc"
	@echo "  Documentation   http://localhost:8080"
	@echo "  Grafana         http://localhost:3000   (admin / admin)"
	@echo "  Prometheus      http://localhost:9090"
	@echo "  MinIO Console   http://localhost:9001   (minioadmin / minioadmin)"
	@echo "  PostgreSQL      localhost:5432          (ulabel / secret)"
	@echo ""
	@echo "  Seeded users:"
	@echo "    admin     -> role: admin"
	@echo "    labeler1  -> role: labeler  (..labeler10)"
	@echo ""
	@echo "  Next steps:"
	@echo "    1. Open http://localhost:5173 and log in as 'admin'"
	@echo "    2. Create a project and import images from the dataset"
	@echo "    3. Log in as 'labeler1' to start labeling"
	@echo ""
	@echo "  Useful commands:"
	@echo "    make logs       Follow all service logs"
	@echo "    make down       Stop all services"
	@echo "    make down-v     Stop and remove all data"
	@echo "══════════════════════════════════════════════════════════════"
