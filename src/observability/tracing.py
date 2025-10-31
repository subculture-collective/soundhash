"""
OpenTelemetry distributed tracing integration for SoundHash.
Provides trace context propagation, span creation, and Jaeger export.
"""

import logging
from contextlib import contextmanager
from typing import Any, Optional

from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter as JaegerThriftExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.trace import SpanKind, Status, StatusCode

from config.settings import Config

logger = logging.getLogger(__name__)


class TracingManager:
    """Manages OpenTelemetry distributed tracing configuration."""

    def __init__(self):
        """Initialize tracing manager."""
        self.enabled = getattr(Config, "TRACING_ENABLED", False)
        self.service_name = getattr(Config, "TRACING_SERVICE_NAME", "soundhash")
        self.environment = getattr(Config, "TRACING_ENVIRONMENT", "development")
        self._noop_tracer = None  # Cache for no-op tracer when disabled
        self.jaeger_enabled = getattr(Config, "JAEGER_ENABLED", False)
        self.otlp_enabled = getattr(Config, "OTLP_ENABLED", False)
        self.console_export = getattr(Config, "TRACING_CONSOLE_EXPORT", False)
        
        self.tracer_provider: Optional[TracerProvider] = None
        self.tracer: Optional[trace.Tracer] = None
        
        if self.enabled:
            self._initialize_tracing()

    def _initialize_tracing(self):
        """Initialize OpenTelemetry tracing with configured exporters."""
        try:
            # Create resource with service information
            resource = Resource.create({
                "service.name": self.service_name,
                "service.version": getattr(Config, "API_VERSION", "1.0.0"),
                "deployment.environment": self.environment,
            })
            
            # Create tracer provider
            self.tracer_provider = TracerProvider(resource=resource)
            
            # Add Jaeger exporter if enabled
            if self.jaeger_enabled:
                jaeger_host = getattr(Config, "JAEGER_AGENT_HOST", "localhost")
                jaeger_port = int(getattr(Config, "JAEGER_AGENT_PORT", 6831))
                
                jaeger_exporter = JaegerThriftExporter(
                    agent_host_name=jaeger_host,
                    agent_port=jaeger_port,
                )
                self.tracer_provider.add_span_processor(
                    BatchSpanProcessor(jaeger_exporter)
                )
                logger.info(f"Jaeger tracing enabled: {jaeger_host}:{jaeger_port}")
            
            # Add OTLP exporter if enabled (for modern observability backends)
            if self.otlp_enabled:
                otlp_endpoint = getattr(Config, "OTLP_ENDPOINT", "http://localhost:4317")
                
                otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
                self.tracer_provider.add_span_processor(
                    BatchSpanProcessor(otlp_exporter)
                )
                logger.info(f"OTLP tracing enabled: {otlp_endpoint}")
            
            # Add console exporter for debugging
            if self.console_export:
                console_exporter = ConsoleSpanExporter()
                self.tracer_provider.add_span_processor(
                    BatchSpanProcessor(console_exporter)
                )
                logger.info("Console span export enabled")
            
            # Set global tracer provider
            trace.set_tracer_provider(self.tracer_provider)
            
            # Get tracer instance
            self.tracer = trace.get_tracer(__name__)
            
            logger.info(f"Distributed tracing initialized for service: {self.service_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize tracing: {e}")
            self.enabled = False

    def start_span(
        self,
        name: str,
        kind: SpanKind = SpanKind.INTERNAL,
        attributes: Optional[dict[str, Any]] = None,
    ):
        """
        Start a new span with the given name and attributes.
        
        Args:
            name: Name of the span
            kind: Type of span (INTERNAL, SERVER, CLIENT, PRODUCER, CONSUMER)
            attributes: Optional attributes to attach to the span
            
        Returns:
            Span object or NoOp span if tracing is disabled
        """
        if not self.enabled or not self.tracer:
            # Cache no-op tracer to avoid repeated creation
            if self._noop_tracer is None:
                self._noop_tracer = trace.get_tracer(__name__)
            return self._noop_tracer.start_span(name)
        
        return self.tracer.start_span(
            name=name,
            kind=kind,
            attributes=attributes or {},
        )

    @contextmanager
    def trace_operation(
        self,
        operation_name: str,
        kind: SpanKind = SpanKind.INTERNAL,
        attributes: Optional[dict[str, Any]] = None,
    ):
        """
        Context manager for tracing an operation.
        
        Args:
            operation_name: Name of the operation being traced
            kind: Type of span
            attributes: Optional attributes to attach to the span
            
        Yields:
            Active span object
            
        Example:
            with tracing.trace_operation("process_video", attributes={"video_id": "123"}):
                # Your code here
                pass
        """
        span = self.start_span(operation_name, kind=kind, attributes=attributes)
        
        try:
            with trace.use_span(span, end_on_exit=True):
                yield span
        except Exception as e:
            if span:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
            raise

    def add_span_attributes(self, span, attributes: dict[str, Any]):
        """
        Add attributes to the current span.
        
        Args:
            span: Span object to add attributes to
            attributes: Dictionary of attributes to add
        """
        if span and self.enabled:
            for key, value in attributes.items():
                span.set_attribute(key, value)

    def add_span_event(self, span, name: str, attributes: Optional[dict[str, Any]] = None):
        """
        Add an event to the current span.
        
        Args:
            span: Span object to add event to
            name: Name of the event
            attributes: Optional attributes for the event
        """
        if span and self.enabled:
            span.add_event(name, attributes=attributes or {})

    def set_span_error(self, span, error: Exception):
        """
        Mark span as error and record exception details.
        
        Args:
            span: Span object to mark as error
            error: Exception that occurred
        """
        if span and self.enabled:
            span.set_status(Status(StatusCode.ERROR, str(error)))
            span.record_exception(error)

    def get_current_trace_id(self) -> Optional[str]:
        """
        Get the current trace ID if tracing is enabled.
        
        Returns:
            Trace ID as hex string or None
        """
        if not self.enabled:
            return None
        
        current_span = trace.get_current_span()
        if current_span:
            trace_id = current_span.get_span_context().trace_id
            return format(trace_id, "032x") if trace_id else None
        
        return None

    def shutdown(self):
        """Shutdown tracing and flush any pending spans."""
        if self.tracer_provider:
            self.tracer_provider.shutdown()
            logger.info("Tracing shutdown complete")


# Global tracing manager instance
tracing = TracingManager()
