# Architecture

## Hexagonal Architecture (Ports & Adapters)

uLabel follows **Hexagonal Architecture** to maintain a clean separation of concerns and enable testability.

```
┌─────────────────────────────────────────────────┐
│                   API Layer                      │
│          (FastAPI Routers & Schemas)             │
├─────────────────────────────────────────────────┤
│               Application Layer                  │
│          (Use Cases / Business Logic)            │
├─────────────────────────────────────────────────┤
│                 Domain Layer                      │
│     (Entities, Ports, Business Rules)            │
├─────────────────────────────────────────────────┤
│             Infrastructure Layer                 │
│  (SQLAlchemy Repos, S3 Storage, Observability)   │
└─────────────────────────────────────────────────┘
```

### Domain Layer

The innermost layer contains:

- **Entities**: Core business objects (`Project`, `Image`, `Label`, `User`).
- **Ports**: Abstract interfaces (repositories, storage service) that define how the domain interacts with external systems.
- **Errors**: Domain-specific exception classes.

The domain has **zero external dependencies** — it defines contracts that other layers implement.

### Application Layer

Contains **use cases** that orchestrate business workflows:

- Each use case is a single class with an `execute()` method.
- Use cases depend on domain ports (injected via dependency injection).
- They enforce business rules and coordinate between multiple repositories.

### API Layer

The outermost entry point:

- **Routers**: FastAPI route handlers that translate HTTP requests into use case calls.
- **Schemas**: Pydantic models for request validation and response serialization.
- **Error Handlers**: Map domain errors to appropriate HTTP responses.

### Infrastructure Layer

Implements the domain ports:

- **SQLAlchemy Repositories**: Production database access using async SQLAlchemy.
- **In-Memory Repositories**: Test doubles for unit testing without a database.
- **S3 Storage Service**: Image storage via S3/MinIO.
- **Observability**: OpenTelemetry tracing, Prometheus metrics, structured logging.

## Dependency Injection

uLabel uses [dependency-injector](https://python-dependency-injector.ets-labs.org/) to wire everything together. The `Container` class in `container.py` defines all dependencies and their lifecycle.

## Key Design Decisions

| Decision | Rationale |
|---|---|
| Hexagonal Architecture | Testability and framework independence |
| Async throughout | High throughput for I/O-bound operations |
| SQLAlchemy 2.0 async | Modern async ORM with type safety |
| Domain ports as ABCs | Explicit contracts between layers |
| Use case per file | Clear responsibility and easy navigation |
| In-memory test doubles | Fast unit tests without infrastructure |
