"""Structured logging configuration for the uLabel service.

Supports both JSON (using orjson) and plain-text log formats, with
OpenTelemetry trace/span ID injection.
"""

import logging
import sys
from datetime import datetime, timezone

import orjson


class JsonFormatter(logging.Formatter):
    """High-performance JSON log formatter using orjson."""

    def __init__(self, service_name: str) -> None:
        """Initialize with the service name to include in each log entry.

        Args:
            service_name: Name of the service for log identification.
        """
        super().__init__()
        self.service_name = service_name

    def format(self, record: logging.LogRecord) -> str:
        """Format a log record as a JSON string.

        Args:
            record: The log record to format.

        Returns:
            A JSON-encoded string with timestamp, level, message, and trace IDs.
        """
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "service": self.service_name,
            "trace_id": getattr(record, "otelTraceID", ""),
            "span_id": getattr(record, "otelSpanID", ""),
        }
        if record.exc_info and record.exc_info[1] is not None:
            log_entry["exception"] = self.formatException(record.exc_info)
        return orjson.dumps(log_entry).decode()


def configure_logging(log_level: str, log_format: str, service_name: str) -> None:
    """Configure the root logger with the specified level and format.

    Args:
        log_level: Logging level (e.g., "INFO", "DEBUG").
        log_format: Output format, either "json" or "text".
        service_name: Service name for JSON log entries.
    """
    root = logging.getLogger()
    root.setLevel(log_level.upper())

    # Remove existing handlers to avoid duplicates
    root.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)

    if log_format == "json":
        handler.setFormatter(JsonFormatter(service_name))
    else:
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s %(levelname)-8s %(name)s [%(otelTraceID)s] %(message)s",
                defaults={"otelTraceID": ""},
            )
        )

    root.addHandler(handler)

    # Suppress noisy loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
