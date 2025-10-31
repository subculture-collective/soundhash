"""
Structured logging for SoundHash with JSON output support.
Enables log aggregation and analysis with ELK stack or Loki.
"""

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any, Optional

from config.settings import Config


class StructuredFormatter(logging.Formatter):
    """
    JSON formatter for structured logging.
    Outputs logs in JSON format for easy parsing by log aggregation systems.
    """

    def __init__(self, include_trace_id: bool = True):
        """
        Initialize structured formatter.
        
        Args:
            include_trace_id: Whether to include OpenTelemetry trace IDs
        """
        super().__init__()
        self.include_trace_id = include_trace_id

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON.
        
        Args:
            record: Log record to format
            
        Returns:
            JSON-formatted log string
        """
        # Base log entry
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add trace ID if available and enabled
        if self.include_trace_id:
            try:
                from src.observability.tracing import tracing
                trace_id = tracing.get_current_trace_id()
                if trace_id:
                    log_entry["trace_id"] = trace_id
            except (ImportError, Exception) as e:
                # Tracing is optional; log at debug level if trace ID cannot be retrieved
                logging.getLogger(__name__).debug("Could not retrieve trace_id for structured log: %s", e)
        
        # Add extra fields from the log record
        if hasattr(record, "extra_fields"):
            log_entry.update(record.extra_fields)
        
        # Add custom attributes (anything added via extra={...})
        reserved_attrs = {
            "name", "msg", "args", "created", "filename", "funcName", "levelname",
            "levelno", "lineno", "module", "msecs", "message", "pathname", "process",
            "processName", "relativeCreated", "thread", "threadName", "exc_info",
            "exc_text", "stack_info", "extra_fields"
        }
        
        for key, value in record.__dict__.items():
            if key not in reserved_attrs and not key.startswith("_"):
                log_entry[key] = value
        
        return json.dumps(log_entry)


class StructuredLogger:
    """
    Enhanced logger with structured logging capabilities.
    Provides methods for logging with additional context and fields.
    """

    def __init__(self, name: str):
        """
        Initialize structured logger.
        
        Args:
            name: Logger name (typically __name__)
        """
        self.logger = logging.getLogger(name)
        self._configure_structured_logging()

    def _configure_structured_logging(self):
        """Configure structured logging output."""
        structured_enabled = getattr(Config, "STRUCTURED_LOGGING_ENABLED", False)
        
        if structured_enabled and not self.logger.handlers:
            # Create structured formatter
            formatter = StructuredFormatter(include_trace_id=True)
            
            # Create handler for stdout
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(formatter)
            
            # Add handler to logger
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    def log(
        self,
        level: int,
        message: str,
        extra_fields: Optional[dict[str, Any]] = None,
        **kwargs
    ):
        """
        Log a message with additional structured fields.
        
        Args:
            level: Log level (logging.INFO, logging.ERROR, etc.)
            message: Log message
            extra_fields: Additional fields to include in the log
            **kwargs: Additional keyword arguments for logger
        """
        record_extra = {"extra_fields": extra_fields or {}}
        self.logger.log(level, message, extra=record_extra, **kwargs)

    def info(self, message: str, **fields):
        """
        Log info message with structured fields.
        
        Args:
            message: Log message
            **fields: Additional fields to include
        """
        self.log(logging.INFO, message, extra_fields=fields)

    def warning(self, message: str, **fields):
        """
        Log warning message with structured fields.
        
        Args:
            message: Log message
            **fields: Additional fields to include
        """
        self.log(logging.WARNING, message, extra_fields=fields)

    def error(self, message: str, **fields):
        """
        Log error message with structured fields.
        
        Args:
            message: Log message
            **fields: Additional fields to include
        """
        self.log(logging.ERROR, message, extra_fields=fields)

    def debug(self, message: str, **fields):
        """
        Log debug message with structured fields.
        
        Args:
            message: Log message
            **fields: Additional fields to include
        """
        self.log(logging.DEBUG, message, extra_fields=fields)

    def critical(self, message: str, **fields):
        """
        Log critical message with structured fields.
        
        Args:
            message: Log message
            **fields: Additional fields to include
        """
        self.log(logging.CRITICAL, message, extra_fields=fields)

    def log_operation(
        self,
        operation: str,
        status: str,
        duration_ms: Optional[float] = None,
        **fields
    ):
        """
        Log an operation with standardized fields.
        
        Args:
            operation: Operation name
            status: Operation status (success, error, etc.)
            duration_ms: Operation duration in milliseconds
            **fields: Additional fields
        """
        log_fields = {
            "operation": operation,
            "status": status,
            **fields
        }
        
        if duration_ms is not None:
            log_fields["duration_ms"] = duration_ms
        
        level = logging.INFO if status == "success" else logging.ERROR
        self.log(level, f"Operation: {operation} - Status: {status}", extra_fields=log_fields)

    def log_metric(self, metric_name: str, value: float, unit: str = "", **fields):
        """
        Log a metric value.
        
        Args:
            metric_name: Metric name
            value: Metric value
            unit: Unit of measurement
            **fields: Additional fields
        """
        log_fields = {
            "metric_name": metric_name,
            "metric_value": value,
            "metric_unit": unit,
            **fields
        }
        
        self.log(
            logging.INFO,
            f"Metric: {metric_name}={value}{unit}",
            extra_fields=log_fields
        )


def get_structured_logger(name: str) -> StructuredLogger:
    """
    Get a structured logger instance.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        StructuredLogger instance
    """
    return StructuredLogger(name)
