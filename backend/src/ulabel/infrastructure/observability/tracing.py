"""OpenTelemetry distributed tracing configuration.

Sets up a TracerProvider with a configurable sampler that supports
both ratio-based sampling and forced sampling via HTTP header. Also
instruments FastAPI, SQLAlchemy, logging, and aiohttp.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Sequence

from opentelemetry import trace
from opentelemetry.context import Context
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.aiohttp_client import AioHttpClientInstrumentor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.sampling import (
    Decision,
    Sampler,
    SamplingResult,
    TraceIdRatioBased,
)
from opentelemetry.trace import Link, SpanKind
from opentelemetry.util.types import Attributes

if TYPE_CHECKING:
    from fastapi import FastAPI
    from sqlalchemy.ext.asyncio import AsyncEngine

logger = logging.getLogger(__name__)


class ForceTraceSampler(Sampler):
    """Sampler that delegates to a ratio-based sampler but forces sampling
    when the configured header is present in the span attributes."""

    def __init__(self, ratio: float, force_trace_header: str) -> None:
        """Initialize the sampler.

        Args:
            ratio: Base sampling ratio (0.0 to 1.0).
            force_trace_header: HTTP header name that forces sampling when set to "true".
        """
        self._delegate = TraceIdRatioBased(ratio)
        self._force_key = f"http.request.header.{force_trace_header.lower()}"

    def should_sample(
        self,
        parent_context: Context | None,
        trace_id: int,
        name: str,
        kind: SpanKind | None = None,
        attributes: Attributes | None = None,
        links: Sequence[Link] | None = None,
    ) -> SamplingResult:
        """Decide whether to sample a span.

        Forces sampling if the configured header is present and set to
        "true"; otherwise delegates to the ratio-based sampler.

        Args:
            parent_context: The parent span context, if any.
            trace_id: The trace identifier.
            name: The span name.
            kind: The span kind.
            attributes: Span attributes that may contain HTTP headers.
            links: Links to other spans.

        Returns:
            A SamplingResult indicating whether to record and sample.
        """
        if attributes:
            header_values = attributes.get(self._force_key)
            if header_values:
                values = (
                    header_values
                    if isinstance(header_values, (list, tuple))
                    else [header_values]
                )
                if any(str(v).lower() == "true" for v in values):
                    return SamplingResult(Decision.RECORD_AND_SAMPLE, attributes)

        return self._delegate.should_sample(
            parent_context, trace_id, name, kind, attributes, links
        )

    def get_description(self) -> str:
        """Return a human-readable description of this sampler.

        Returns:
            A string describing the sampler and its delegate.
        """
        return f"ForceTraceSampler(delegate={self._delegate.get_description()})"


def setup_tracing(
    service_name: str,
    endpoint: str,
    enabled: str,
    sample_ratio: str,
    force_trace_header: str,
) -> TracerProvider | None:
    """Initialize OpenTelemetry tracing with OTLP gRPC export.

    Args:
        service_name: The service name for the trace resource.
        endpoint: OTLP collector endpoint URL.
        enabled: Whether tracing is enabled ("true"/"false").
        sample_ratio: Ratio of traces to sample (e.g., "0.1" for 10%).
        force_trace_header: HTTP header name that forces sampling.

    Returns:
        The configured TracerProvider, or None if tracing is disabled.
    """
    if enabled.lower() != "true":
        logger.info("Tracing disabled")
        return None

    ratio = float(sample_ratio)
    resource = Resource.create({"service.name": service_name})

    sampler = ForceTraceSampler(ratio, force_trace_header)
    provider = TracerProvider(resource=resource, sampler=sampler)

    exporter = OTLPSpanExporter(endpoint=endpoint, insecure=True)
    provider.add_span_processor(BatchSpanProcessor(exporter))

    trace.set_tracer_provider(provider)
    logger.info("Tracing enabled: endpoint=%s, sample_ratio=%s", endpoint, ratio)
    return provider


def instrument_fastapi(app: FastAPI) -> None:
    """Add OpenTelemetry tracing middleware to the FastAPI app.

    Must be called at module level, before the ASGI lifespan builds
    the middleware stack. The middleware resolves the global TracerProvider
    at request time, so the provider can be set up later in the lifespan.

    Args:
        app: The FastAPI application to instrument.
    """
    FastAPIInstrumentor.instrument_app(app)


def instrument_libraries(engine: AsyncEngine) -> None:
    """Instrument libraries that do not depend on the middleware stack.

    Safe to call inside the ASGI lifespan.

    Args:
        engine: The async SQLAlchemy engine to instrument.
    """
    SQLAlchemyInstrumentor().instrument(engine=engine.sync_engine)
    LoggingInstrumentor().instrument(set_logging_format=True)
    AioHttpClientInstrumentor().instrument()
    logger.info("Instrumentation complete: SQLAlchemy, Logging, AioHTTP")


def shutdown_tracing(provider: TracerProvider | None) -> None:
    """Gracefully shut down the tracer provider and flush pending spans.

    Args:
        provider: The TracerProvider to shut down, or None if tracing is disabled.
    """
    if provider is not None:
        provider.shutdown()
        logger.info("Tracing shut down")
