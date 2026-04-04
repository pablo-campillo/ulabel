# Development Log

Chronological record of all features implemented and design decisions made during the development of uLabel, an image labeling platform. The project was built between March 27-31, 2026 across 20 Claude Code sessions and 28 commits.

---

## Day 1 - March 27, 2026: Full Backend

### Commit `a33272e` - First version of all backend features
- Complete hexagonal architecture: domain, application (use cases), API (FastAPI), infrastructure
- Entities: Project, Image, Labeler, Assignment, Label
- Ports and adapters for repositories and storage
- Dependency injection with `dependency-injector`
- PostgreSQL database with SQLAlchemy async + Alembic migrations
- MinIO as object storage (images)
- Basic token authentication

### Commit `bf462e0` - Labeler submit stats
- Statistics endpoint per labeler (submissions count)

### Commit `e8efd23` - Project listing with pagination

---

## Day 2 - March 28, 2026: Backend improvements + Frontend + Configuration

### Commit `4be4701` - Fix: Alembic in Docker
- Dockerfile fix to copy Alembic migrations into the container

### Commit `7f1d060` - Labeler autocomplete
- Labeler search by username with autocomplete

### Commit `8f64e01` - Add labelers to projects

### Commit `dde0456` - Filter by name in project listing

### Commit `4c51917` - Unique project name
- Uniqueness constraint on the name field

### Commit `1953371` - Initial frontend
- React + TypeScript + Vite application
- Admin dashboard: project CRUD, labeler assignment, statistics with charts (Recharts)
- Labeler dashboard: image labeling interface, image loading from presigned URLs
- Dockerized with nginx

### Commit `9d9cd7b` - YAML configuration with dependency-injector
- **Design decision**: Migrated from environment variables to `config.yml` file using the `Configuration` provider from dependency-injector

---

## Day 3 - March 29, 2026: API Refactoring + Observability + Frontend merge

### Commit `6830ed2` - Changed GET to POST for assignments
- **Design decision**: The "next image" endpoint changed from `GET /images/next?labeler_id=...` to `POST /assignments` with JSON body, because creating an assignment is an action with side-effects, not a query

### Commit `f2112db` - Global error handler and unified format
- Error response refactoring with centralized handler
- Unified response format across the entire API

### Commit `a077233` - Observability (3 pillars)
- **Metrics**: Prometheus with histograms and counters, `/metrics` endpoint with OpenMetrics + exemplars with TraceID
- **Traces**: OpenTelemetry with Tempo, FastAPI and SQLAlchemy instrumentation
- **Logs**: Structured JSON logging, trace_id correlation via LoggingInstrumentor
- **Grafana dashboards** (3):
    - uLabel Overview: req/s, error rate, P99 latency
    - uLabel Labeling Activity: labels/min, uploads/min, assignments/min
    - uLabel Traces & Logs: metrics-traces-logs correlation
- **Design decision**: Business logging in routers (API layer), NOT in use cases, because in hexagonal architecture the domain/application layers should remain pure
- **Design decision**: Logger via `logging.getLogger(__name__)` (stdlib), not injected via DI container, because OTel LoggingInstrumentor injects trace/span IDs globally
- Stack: Prometheus + Grafana + Tempo + Loki + Promtail

### Commits `4307962`, `487b007` - Merge feat/frontend into main

### Commit `5267307` - uvloop
- **Design decision**: uvloop as high-performance event loop (2-4x improvement), configured via `--loop uvloop` in uvicorn

### Session: Frontend update for new assignments API
- Renamed `getNextImage()` to `createAssignment()` to align with the new POST endpoint
- "Back" button in the labeling interface (disabled during active labeling)

---

## Day 4 - March 30, 2026: Observability fixes + Documentation + UX

### Commit `35679ea` - Fix observability
- **Critical bug**: Promtail crashing due to multiple configuration errors:
    - `docker: {}` stage incompatible with `docker_sd_configs`
    - Incorrect meta-label for compose service
    - `trace_id` as Loki label (high cardinality, 1 stream per request)
- **Bug**: `generate_latest()` called without `registry` argument causing `/metrics` to return 500
- **Bug**: `FastAPIInstrumentor.instrument_app()` inside the lifespan handler was too late (middleware stack already built), resulting in trace_id always being "0"
- **Fix**: Split instrumentation: `setup_tracing()` in lifespan, `instrument_app()` at module level
- **Bug**: `await` on synchronous container resources (`configure_logging`, tracer provider) causing crash
- **Design decision**: "Recent Traces" panel changed from Tempo query to Loki query, because Grafana 10.4.1 Tempo plugin only supports traceId lookups, not search queries

### Promtail migration to docker_sd_configs
- From `static_configs` (path-based scraping) to `docker_sd_configs` (automatic container discovery via Docker socket)
- **Design decision**: Do NOT use Loki Docker driver plugin (it's an alternative to Promtail, not a complement)

### Commit `4203401` - MkDocs documentation
- **Design decision**: Diataxis framework (Tutorials, How-To Guides, Reference, Explanation)
- MkDocs with Material theme + mkdocstrings (auto-generation from Google-style docstrings)
- Google-style docstrings added to ~67 Python files
- 14 documentation pages
- **Design decision**: All Makefile targets containerized (only Docker required on host)
- `make docs` on port 8080 (avoids conflict with backend on 8000)

### Commits `ce38556` - `c5bb5eb` - Documentation CI/CD
- GitHub Actions workflow for automatic docs deployment to GitHub Pages
- Repository made public for free GitHub Pages hosting
- **Bug**: `uv sync --extra docs` incorrect; fix: `uv sync --group docs` (dependency-groups vs optional-dependencies)

### Commit `bc1edb6` - Extended documentation
- 5 explanation pages:
    - `architecture.md`: Mermaid diagrams (platform, hexagonal, DI)
    - `database.md`: ER diagram, decisions (async, upsert, skip_locked, eager loading)
    - `api-design.md`: endpoint map, schemas, error handling, middleware stack
    - `image-ingestion.md`: image lifecycle (statechart), bulk ingestion, implicit shuffle via UUID v4
    - `tooling.md`: Python toolchain
- **Documented design decision**: UUID v4s are random by nature, so ordering by `id` acts as an implicit shuffle -- no need for explicit randomization

### Commit `23207b6` - Interactive chart zoom
- Click-drag to select area + automatic zoom + "Reset Zoom" button on Daily Labeling Progress
- Optional `isZoomed`/`onResetZoom` props on `ChartContainer.tsx` for reusability

---

## Day 5 - March 31, 2026: Final documentation + Fixes

### Commit `e7e3f41` - README.md and Quick Start
- Complete README: description, prerequisites, `make bootstrap`, service URL/credentials table, user guide with screenshots
- Quick-start tutorial in MkDocs with 6 screenshots
- Content duplicated (README for GitHub, docs for MkDocs site) and adapted to each format

### Commit `0e4463b` - Documentation site reference
- Link to `https://pablo-campillo.github.io/ulabel/` in README

### Commit `23b6a22` - Fix missing mkdocs.yml

### Commit `b6856f3` - Fix observability and Grafana
- Final adjustments to datasources and Grafana dashboards

### Commit `09405b0` - Fix frontend
- TypeScript error in Recharts: `activeLabel` type `string | number` not accepted by handlers expecting `string`

---

## Day 6 - April 4, 2026: Project listing redesign

### Fix: Race condition in CreateAssignmentUseCase

**Bug identified**: `CreateAssignmentUseCase` called `get_next_pending()` and `save()` in **separate database sessions**. The `FOR UPDATE SKIP LOCKED` lock acquired during `get_next_pending` was released when its session closed, before `save` opened a new session. In the gap between the two transactions, a concurrent request could select and assign the same image to a different labeler.

**Design decision**: Atomic `assign_next_pending` repository method instead of full Unit of Work pattern
- New `ImageRepository.assign_next_pending(project_id, labeler_id, assigned_at)` method that performs SELECT FOR UPDATE SKIP LOCKED + domain mutation + UPDATE within a single transaction
- The use case now calls one method instead of three (`get_next_pending` + `image.assign()` + `save`)
- **Rationale**: Only one confirmed race condition. A full Unit of Work would touch 20+ files across all repositories and use cases. The atomic method is surgically targeted (5 files), does not block a future UoW migration, and `assign_next_pending` is a legitimate domain operation ("atomically claim the next available image")

### Removed hardcoded ASSIGNMENT_TIMEOUT in favor of config

**Problem**: `ASSIGNMENT_TIMEOUT = timedelta(minutes=30)` was hardcoded in the `create_assignment` router, while `config.yml` already had `tasks.image_assignment_timeout_seconds: 60`. The two values diverged (30 min vs 60 s) and the presigned URL expiry was not configurable.

**Solution**: Removed the `ASSIGNMENT_TIMEOUT` constant and injected `config.tasks.image_assignment_timeout_seconds` via dependency-injector's `Provide[Container.config.tasks.image_assignment_timeout_seconds.as_int()]` directly into the endpoint function. Updated all documentation references from "30 minutes" / "1800" to reference the config file value (60 seconds).

**Design decision**: Used `Provide[Container.config...]` injection (option B) instead of creating a new provider in the container — follows the existing pattern and requires fewer changes.

### Planned refactor: Separate ProjectSummary vs ProjectDetail

**Problem identified**: The `GET /projects` list endpoint resolves labeler usernames by making N individual queries to `UserRepository` from the API layer (`_resolve_labelers`). However:

- The admin list frontend only uses `labelers.length` (count) — never the usernames
- The labeler list frontend doesn't show labelers at all
- Only the admin detail view needs resolved labeler usernames
- No `GET /projects/{id}` endpoint exists — the detail page fetches ALL projects (`getProjects(100, 0)`) and filters client-side
- Labeler resolution happens in the API layer (router) instead of the use case, violating the hexagonal architecture

**Design decisions**:

- **Two response schemas**: `ProjectSummary` (with `labeler_count: int`) for listings and `ProjectDetail` (with `labelers: list[LabelerInfo]`) for detail/mutation responses
- **New `GET /projects/{id}` endpoint**: Returns `ProjectDetail` with resolved labelers, eliminates the client-side fetch-all-and-filter antipattern
- **Batch user resolution**: New `UserRepository.get_by_ids(ids: set[UUID]) -> list[User]` method with a single `WHERE id IN (...)` query instead of N individual lookups
- **New `GetProjectUseCase`**: Centralizes labeler resolution in the application layer (not the API router), receiving both `ProjectRepository` and `UserRepository`
- **Application DTOs**: `ProjectWithLabelers` dataclass in the application layer to carry the resolved data without polluting the domain model

**Rationale**: The list endpoint was doing unnecessary work (resolving usernames nobody displays) and the resolution was architecturally misplaced (API layer calling repositories directly). The summary/detail split follows the principle of not fetching data you don't need, and moving business logic to the application layer respects the hexagonal architecture boundaries.

### Streaming export to MinIO

**Problem**: `ExportLabelsUseCase` loaded all label rows into memory (`list[LabelExportRow]`), built the entire CSV/JSON file as `bytes`, and uploaded it with a single `put_object`. For large projects this consumed excessive memory proportional to the number of labels.

**Solution**: End-to-end streaming pipeline across three layers:
1. **Database**: `get_export_data` changed from `list` return to `AsyncIterator` using SQLAlchemy's `session.stream()` for server-side cursoring
2. **Formatters**: `_generate_csv` and `_generate_json` converted to async generators yielding byte chunks (CSV: one chunk per row; JSON: manual array framing with `[`, `,`, `]`)
3. **Storage**: New `upload_file_streaming` method using S3 multipart upload with a 5MB `bytearray` buffer per part

**Design decisions**:
- **New `upload_file_streaming` method instead of modifying `upload_file`**: The existing `upload_file(data: bytes)` is still used by image upload and other callers that have the full data in memory. Adding a separate streaming method avoids breaking existing contracts
- **5MB buffer for multipart parts**: S3 requires a minimum of 5MB per part (except the last). The implementation accumulates chunks in a `bytearray` and flushes when the threshold is reached
- **`try/except` with `abort_multipart_upload`**: On any error during streaming, orphaned multipart parts are cleaned up to avoid storage leaks
- **Metadata preserved**: `label_count` metadata is passed via `create_multipart_upload`, so the caching mechanism (head_object + label_count comparison) works unchanged

---

## Cross-cutting sessions

### Unified make bootstrap and Docker Compose
- **Design decision**: Root `docker-compose.yaml` uses `include:` to compose backend and frontend (Docker Compose v2.20+)
- Each sub-compose is independently usable
- `make bootstrap`: single command to bring up everything, initialize data, and display a banner with URLs
- Hot reload on backend via volume mounts `./src:/app/src`

### Assignment expiration investigation
- Identified timing gap: `image_assignment_timeout_seconds: 60` but the expiration job runs every 5 min (`image_expiry_interval_seconds: 300`), so expiration is not instantaneous
- ~~Tests use `TIMEOUT = 30 min` vs production `60s` (discrepancy noted)~~ — resolved: both now use `config.tasks.image_assignment_timeout_seconds`

---

## Summary of key design decisions

| Decision | Rationale |
|----------|-----------|
| Hexagonal architecture | Separation of concerns, testability, framework independence |
| `config.yml` with dependency-injector | Centralized and typed configuration, better than scattered env vars |
| POST for creating assignments (not GET) | Side-effects require POST method |
| Logging in routers, not in use cases | Domain/application layers should remain pure (hexagonal) |
| uvloop | 2-4x performance improvement with no code changes |
| Promtail + docker_sd_configs | Automatic container discovery, better than static paths |
| Diataxis for documentation | Proven framework for technical documentation |
| Containerized Makefile targets | Only Docker required on host, reproducible environment |
| Docker Compose `include:` | Each service with its own independent compose, clean composition |
| UUID v4 as implicit shuffle | No need for explicit randomization for image ordering |
| ProjectSummary vs ProjectDetail schemas | Don't fetch data you don't need; list vs detail have different requirements |
| Batch `get_by_ids` in UserRepository | Single `WHERE IN` query instead of N individual lookups |
| Labeler resolution in use case, not API | Hexagonal: business logic belongs in application layer, not routers |
