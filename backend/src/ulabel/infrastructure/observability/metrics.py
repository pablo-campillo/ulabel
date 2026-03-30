"""Prometheus metrics collection and HTTP middleware.

Defines counters, histograms, and gauges for HTTP request tracking,
and provides a Starlette middleware that records metrics per request.
"""

from __future__ import annotations

import time

from prometheus_client import Counter, Gauge, Histogram, generate_latest
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Match

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


def _get_path_template(request: Request) -> str:
    """Extract the route path template to avoid high-cardinality labels from UUIDs."""
    app = request.app
    for route in app.routes:
        match, _ = route.matches(request.scope)
        if match == Match.FULL:
            return getattr(route, "path", request.url.path)
    return request.url.path


class PrometheusMiddleware(BaseHTTPMiddleware):
    """Starlette middleware that records Prometheus metrics for each HTTP request."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Record request count, duration, and in-progress gauge metrics.

        Args:
            request: The incoming HTTP request.
            call_next: The next middleware or route handler.

        Returns:
            The HTTP response from the downstream handler.
        """
        path = _get_path_template(request)

        if path == "/metrics":
            return await call_next(request)

        method = request.method
        REQUESTS_IN_PROGRESS.labels(method=method, path=path).inc()
        start = time.perf_counter()

        try:
            response = await call_next(request)
        except Exception as exc:
            EXCEPTIONS_TOTAL.labels(
                method=method, path=path, exception_type=type(exc).__name__
            ).inc()
            raise
        finally:
            duration = time.perf_counter() - start
            REQUESTS_IN_PROGRESS.labels(method=method, path=path).dec()

        REQUEST_DURATION_SECONDS.labels(method=method, path=path).observe(duration)
        REQUESTS_TOTAL.labels(method=method, path=path, status=response.status_code).inc()
        return response


async def metrics_route(request: Request) -> Response:
    """Serve Prometheus metrics in text exposition format.

    Args:
        request: The incoming HTTP request.

    Returns:
        A plain-text response with all collected Prometheus metrics.
    """
    return Response(
        content=generate_latest(),
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )
