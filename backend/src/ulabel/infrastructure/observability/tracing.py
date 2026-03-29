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
        return f"ForceTraceSampler(delegate={self._delegate.get_description()})"


def setup_tracing(
    service_name: str,
    endpoint: str,
    enabled: str,
    sample_ratio: str,
    force_trace_header: str,
) -> TracerProvider | None:
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


def instrument_app(app: FastAPI, engine: AsyncEngine) -> None:
    FastAPIInstrumentor.instrument_app(app)
    SQLAlchemyInstrumentor().instrument(engine=engine.sync_engine)
    LoggingInstrumentor().instrument(set_logging_format=False)
    AioHttpClientInstrumentor().instrument()
    logger.info("Instrumentation complete: FastAPI, SQLAlchemy, Logging, AioHTTP")


def shutdown_tracing(provider: TracerProvider | None) -> None:
    if provider is not None:
        provider.shutdown()
        logger.info("Tracing shut down")
