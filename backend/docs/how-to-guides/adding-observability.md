# Adding Observability

How to add new logs, metrics, or traces to the uLabel backend.

!!! note "Architecture rule"
    Logging belongs in the **API layer** (routers and error handlers), never in use cases or domain entities. See [Observability Design](../explanation/observability.md#architectural-decision-where-to-log) for the rationale.

## Adding a Business Log

Business events are logged in router handlers after the use case completes successfully.

### Steps

1. Ensure the router file has a logger:

    ```python
    import logging

    logger = logging.getLogger(__name__)
    ```

2. Add a `logger.info()` call after the use case execution:

    ```python
    @router.post("/{project_id}/images/upload", ...)
    async def upload_image(project_id: UUID, file: UploadFile, ...):
        data = await file.read()
        image = await use_case.execute(
            project_id=project_id, data=data,
            content_type=file.content_type or "application/octet-stream",
        )
        logger.info(
            "Image uploaded: project=%s image=%s size_bytes=%d content_type=%s",
            project_id, image.id, len(data), file.content_type,
        )
        return ImageResponse(...)
    ```

### Conventions

- Use `logger.info()` for successful business events, `logger.warning()` for handled errors, `logger.error()` for failures.
- Format: `"Event description: key1=%s key2=%s"` with `%s`-style formatting (lazy evaluation, not f-strings).
- Log **identifiers and metadata**, not full payloads. For file uploads, log `size_bytes` instead of the file content.
- `trace_id` and `span_id` are injected automatically by `LoggingInstrumentor` — do not add them manually.

### Verification

Check the log appears in Loki:

```logql
{service="ulabel-backend"} |= "Image uploaded"
```

## Adding a Prometheus Metric

Metrics are defined in `src/ulabel/infrastructure/observability/metrics.py`.

### Steps

1. Define the metric at module level:

    ```python
    from prometheus_client import Counter

    IMAGES_UPLOADED_TOTAL = Counter(
        "images_uploaded_total",
        "Total images uploaded",
        ["project_id", "content_type"],
    )
    ```

2. Increment it in the router or middleware:

    ```python
    from ulabel.infrastructure.observability.metrics import IMAGES_UPLOADED_TOTAL

    IMAGES_UPLOADED_TOTAL.labels(
        project_id=str(project_id),
        content_type=file.content_type,
    ).inc()
    ```

3. To include an exemplar (links the metric to a trace):

    ```python
    from opentelemetry import trace

    span = trace.get_current_span()
    trace_id = trace.format_trace_id(span.get_span_context().trace_id)
    exemplar = {"TraceID": trace_id} if trace_id != "0" * 32 else None

    IMAGES_UPLOADED_TOTAL.labels(...).inc(exemplar=exemplar)
    ```

### Conventions

- Use **route templates** for path labels (e.g., `/v1/projects/{project_id}`), not actual UUIDs.
- Avoid high-cardinality labels (user IDs, image IDs) in metrics — use traces for per-request detail.
- The `/metrics` endpoint serves OpenMetrics format. Exemplars require this format.

### Verification

Check the metric appears at `http://localhost:8000/metrics`:

```bash
curl -s http://localhost:8000/metrics | grep images_uploaded_total
```

## Adding Tracing Instrumentation

Most tracing is automatic via instrumentors configured in `instrument_app()` (`tracing.py`). Manual spans are needed for operations not covered by auto-instrumentation.

### Adding a Manual Span

```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

async def some_operation():
    with tracer.start_as_current_span("operation-name") as span:
        span.set_attribute("custom.key", "value")
        result = await do_work()
        span.set_attribute("custom.result_count", len(result))
        return result
```

### Instrumenting a New Library

If you add a new external client (e.g., Redis, HTTP), check if an OpenTelemetry instrumentor exists:

1. Install: `uv add opentelemetry-instrumentation-<library>`
2. Add to `instrument_app()` in `tracing.py`:

    ```python
    from opentelemetry.instrumentation.redis import RedisInstrumentor

    def instrument_app(app: FastAPI, engine: AsyncEngine) -> None:
        # ... existing instrumentors ...
        RedisInstrumentor().instrument()
    ```

### Forcing a Trace

Send the `X-Force-Trace: true` header to guarantee a request is traced regardless of the sampling ratio:

```bash
curl -H "X-Force-Trace: true" http://localhost:8000/v1/projects
```

### Verification

Check the trace appears in Tempo via Grafana's Explore view, or in the Traces & Logs dashboard.

## Adding a Grafana Panel

Dashboard JSON files live in `etc/grafana/provisioning/dashboards/`.

### Steps

1. Edit the appropriate dashboard JSON file (or create a new one).
2. Add a panel object to the `panels` array:

    ```json
    {
      "title": "My New Panel",
      "type": "timeseries",
      "gridPos": { "h": 8, "w": 12, "x": 0, "y": 32 },
      "datasource": { "type": "prometheus", "uid": "${DS_PROMETHEUS}" },
      "targets": [
        {
          "expr": "sum(rate(my_metric_total[5m])) by (label)",
          "legendFormat": "{{ label }}",
          "exemplar": true
        }
      ],
      "fieldConfig": {
        "defaults": {
          "unit": "reqps",
          "custom": { "fillOpacity": 10 }
        }
      }
    }
    ```

3. For Loki log panels, use `"type": "logs"` and datasource `${DS_LOKI}`.
4. For Tempo trace panels, use `"type": "traces"` and datasource uid `tempo`. Example with TraceQL search:

    ```json
    {
      "title": "Trace Search",
      "type": "traces",
      "gridPos": { "h": 14, "w": 24, "x": 0, "y": 0 },
      "datasource": { "type": "tempo", "uid": "tempo" },
      "targets": [
        {
          "refId": "A",
          "queryType": "traceqlSearch",
          "filters": [
            {
              "id": "service-name",
              "tag": "resource.service.name",
              "operator": "=",
              "value": ["ulabel-backend"],
              "scope": "resource"
            },
            {
              "id": "min-duration",
              "tag": "duration",
              "operator": ">",
              "value": ["500ms"]
            }
          ],
          "limit": 50
        }
      ]
    }
    ```

    Tempo's `metrics_generator` enables TraceQL metrics queries, so span metrics (rate, duration, errors) are available in Prometheus and can be used in `timeseries` panels as well.

### Conventions

- Set `"exemplar": true` on Prometheus targets to enable trace linking.
- Use template variables (`${DS_PROMETHEUS}`, `${DS_LOKI}`) for datasource references.
- Use `gridPos` to position: `w` is width (max 24), `h` is height, `x`/`y` is position.

### Verification

Restart Grafana (or wait for auto-reload) and check the panel appears in the dashboard.

## Checklist

When adding any observability element, verify the full chain:

- [ ] **Log** — appears in Loki (`{service="ulabel-backend"} |= "your message"`)
- [ ] **Metric** — appears at `/metrics` endpoint
- [ ] **Trace** — appears in Tempo (use `X-Force-Trace: true` header)
- [ ] **Panel** — visible in the appropriate Grafana dashboard
- [ ] **Correlation** — log entry has clickable `trace_id`, metric exemplar links to trace
