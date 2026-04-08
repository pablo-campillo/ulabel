"""Prometheus metrics collection and HTTP middleware.

Defines counters, histograms, and gauges for HTTP request tracking,
and provides a pure ASGI middleware that records metrics per request.
Uses OpenMetrics exposition format with exemplars linking metrics to traces.
"""

from __future__ import annotations

import time
from typing import Any

from opentelemetry import trace
from prometheus_client import REGISTRY, Counter, Gauge, Histogram
from prometheus_client.openmetrics.exposition import CONTENT_TYPE_LATEST, generate_latest
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Match
from starlette.types import ASGIApp, Message, Receive, Scope, Send

REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"],
)

REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "path"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

REQUESTS_IN_PROGRESS = Gauge(
    "http_requests_in_progress",
    "HTTP requests currently being processed",
    ["method", "path"],
)

EXCEPTIONS_TOTAL = Counter(
    "http_exceptions_total",
    "Total unhandled exceptions",
    ["method", "path", "exception_type"],
)

DOMAIN_ERRORS_TOTAL = Counter(
    "domain_errors_total",
    "Total domain errors by error code",
    ["code", "status"],
)


def _get_path_template(scope: Scope, app: Any) -> str:
    """Extract the route path template to avoid high-cardinality labels from UUIDs."""
    raw_path: str = scope.get("path", "/")
    if app is None:
        return raw_path
    for route in app.routes:
        match, _ = route.matches(scope)
        if match == Match.FULL:
            path: str = getattr(route, "path", raw_path)
            return path
    return raw_path


class PrometheusMiddleware:
    """Pure ASGI middleware that records Prometheus metrics for each HTTP request."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = _get_path_template(scope, scope.get("app"))

        if path == "/metrics":
            await self.app(scope, receive, send)
            return

        method: str = scope.get("method", "GET")
        REQUESTS_IN_PROGRESS.labels(method=method, path=path).inc()
        start = time.perf_counter()
        status_code = 500

        async def send_wrapper(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception as exc:
            EXCEPTIONS_TOTAL.labels(
                method=method, path=path, exception_type=type(exc).__name__
            ).inc()
            raise
        finally:
            duration = time.perf_counter() - start
            REQUESTS_IN_PROGRESS.labels(method=method, path=path).dec()

            span = trace.get_current_span()
            trace_id = trace.format_trace_id(span.get_span_context().trace_id)
            exemplar = {"TraceID": trace_id} if trace_id != "0" * 32 else None

            REQUEST_DURATION_SECONDS.labels(method=method, path=path).observe(
                duration, exemplar=exemplar
            )
            REQUESTS_TOTAL.labels(method=method, path=path, status=status_code).inc(
                exemplar=exemplar
            )


async def metrics_route(request: Request) -> Response:
    """Serve Prometheus metrics in OpenMetrics exposition format.

    Uses OpenMetrics format to support exemplars linking metrics to traces.

    Args:
        request: The incoming HTTP request.

    Returns:
        A response with all collected Prometheus metrics in OpenMetrics format.
    """
    return Response(
        content=generate_latest(REGISTRY),  # type: ignore[no-untyped-call]
        media_type=CONTENT_TYPE_LATEST,
    )
