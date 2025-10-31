"""Tests for distributed tracing functionality."""

from unittest.mock import MagicMock, patch
from opentelemetry.trace import SpanKind

from src.observability.tracing import TracingManager


class TestTracingManager:
    """Test tracing manager functionality."""

    @patch('src.observability.tracing.Config')
    def test_tracing_disabled_by_default(self, mock_config):
        """Test that tracing is disabled by default."""
        mock_config.TRACING_ENABLED = False
        
        manager = TracingManager()
        
        assert manager.enabled is False
        assert manager.tracer_provider is None
        assert manager.tracer is None

    @patch('src.observability.tracing.Config')
    @patch('src.observability.tracing.TracerProvider')
    @patch('src.observability.tracing.trace.set_tracer_provider')
    @patch('src.observability.tracing.trace.get_tracer')
    def test_tracing_initialization(
        self, mock_get_tracer, mock_set_provider, mock_tracer_provider, mock_config
    ):
        """Test that tracing initializes correctly when enabled."""
        mock_config.TRACING_ENABLED = True
        mock_config.TRACING_SERVICE_NAME = "test-service"
        mock_config.TRACING_ENVIRONMENT = "test"
        mock_config.JAEGER_ENABLED = False
        mock_config.OTLP_ENABLED = False
        mock_config.TRACING_CONSOLE_EXPORT = False
        mock_config.API_VERSION = "1.0.0"
        
        manager = TracingManager()
        
        assert manager.enabled is True
        assert manager.service_name == "test-service"
        assert manager.environment == "test"
        mock_tracer_provider.assert_called_once()

    @patch('src.observability.tracing.Config')
    def test_start_span_when_disabled(self, mock_config):
        """Test that starting a span when disabled returns a no-op span."""
        mock_config.TRACING_ENABLED = False
        
        manager = TracingManager()
        span = manager.start_span("test_operation")
        
        assert span is not None

    @patch('src.observability.tracing.Config')
    @patch('src.observability.tracing.TracerProvider')
    @patch('src.observability.tracing.trace.set_tracer_provider')
    @patch('src.observability.tracing.trace.get_tracer')
    def test_start_span_when_enabled(
        self, mock_get_tracer, mock_set_provider, mock_tracer_provider, mock_config
    ):
        """Test starting a span when tracing is enabled."""
        mock_config.TRACING_ENABLED = True
        mock_config.TRACING_SERVICE_NAME = "test-service"
        mock_config.TRACING_ENVIRONMENT = "test"
        mock_config.JAEGER_ENABLED = False
        mock_config.OTLP_ENABLED = False
        mock_config.TRACING_CONSOLE_EXPORT = False
        mock_config.API_VERSION = "1.0.0"
        
        mock_tracer = MagicMock()
        mock_get_tracer.return_value = mock_tracer
        
        manager = TracingManager()
        manager.start_span("test_operation", kind=SpanKind.CLIENT, attributes={"key": "value"})
        
        mock_tracer.start_span.assert_called_once_with(
            name="test_operation",
            kind=SpanKind.CLIENT,
            attributes={"key": "value"}
        )

    @patch('src.observability.tracing.Config')
    @patch('src.observability.tracing.TracerProvider')
    @patch('src.observability.tracing.trace.set_tracer_provider')
    @patch('src.observability.tracing.trace.get_tracer')
    @patch('src.observability.tracing.trace.use_span')
    def test_trace_operation_context_manager(
        self, mock_use_span, mock_get_tracer, mock_set_provider, mock_tracer_provider, mock_config
    ):
        """Test the trace_operation context manager."""
        mock_config.TRACING_ENABLED = True
        mock_config.TRACING_SERVICE_NAME = "test-service"
        mock_config.TRACING_ENVIRONMENT = "test"
        mock_config.JAEGER_ENABLED = False
        mock_config.OTLP_ENABLED = False
        mock_config.TRACING_CONSOLE_EXPORT = False
        mock_config.API_VERSION = "1.0.0"
        
        mock_tracer = MagicMock()
        mock_span = MagicMock()
        mock_tracer.start_span.return_value = mock_span
        mock_get_tracer.return_value = mock_tracer
        
        manager = TracingManager()
        
        with manager.trace_operation("test_op", attributes={"test": "value"}):
            pass
        
        mock_tracer.start_span.assert_called_once()
        mock_use_span.assert_called_once()

    @patch('src.observability.tracing.Config')
    @patch('src.observability.tracing.TracerProvider')
    @patch('src.observability.tracing.trace.set_tracer_provider')
    @patch('src.observability.tracing.trace.get_tracer')
    def test_add_span_attributes(
        self, mock_get_tracer, mock_set_provider, mock_tracer_provider, mock_config
    ):
        """Test adding attributes to a span."""
        mock_config.TRACING_ENABLED = True
        mock_config.TRACING_SERVICE_NAME = "test-service"
        mock_config.TRACING_ENVIRONMENT = "test"
        mock_config.JAEGER_ENABLED = False
        mock_config.OTLP_ENABLED = False
        mock_config.TRACING_CONSOLE_EXPORT = False
        mock_config.API_VERSION = "1.0.0"
        
        mock_span = MagicMock()
        manager = TracingManager()
        
        manager.add_span_attributes(mock_span, {"key1": "value1", "key2": "value2"})
        
        assert mock_span.set_attribute.call_count == 2

    @patch('src.observability.tracing.Config')
    @patch('src.observability.tracing.TracerProvider')
    @patch('src.observability.tracing.trace.set_tracer_provider')
    @patch('src.observability.tracing.trace.get_tracer')
    def test_set_span_error(
        self, mock_get_tracer, mock_set_provider, mock_tracer_provider, mock_config
    ):
        """Test marking a span as error."""
        mock_config.TRACING_ENABLED = True
        mock_config.TRACING_SERVICE_NAME = "test-service"
        mock_config.TRACING_ENVIRONMENT = "test"
        mock_config.JAEGER_ENABLED = False
        mock_config.OTLP_ENABLED = False
        mock_config.TRACING_CONSOLE_EXPORT = False
        mock_config.API_VERSION = "1.0.0"
        
        mock_span = MagicMock()
        manager = TracingManager()
        
        error = Exception("Test error")
        manager.set_span_error(mock_span, error)
        
        mock_span.set_status.assert_called_once()
        mock_span.record_exception.assert_called_once_with(error)

    @patch('src.observability.tracing.Config')
    @patch('src.observability.tracing.TracerProvider')
    @patch('src.observability.tracing.trace.set_tracer_provider')
    @patch('src.observability.tracing.trace.get_tracer')
    @patch('src.observability.tracing.trace.get_current_span')
    def test_get_current_trace_id(
        self, mock_get_current_span, mock_get_tracer, mock_set_provider, mock_tracer_provider, mock_config
    ):
        """Test getting the current trace ID."""
        mock_config.TRACING_ENABLED = True
        mock_config.TRACING_SERVICE_NAME = "test-service"
        mock_config.TRACING_ENVIRONMENT = "test"
        mock_config.JAEGER_ENABLED = False
        mock_config.OTLP_ENABLED = False
        mock_config.TRACING_CONSOLE_EXPORT = False
        mock_config.API_VERSION = "1.0.0"
        
        mock_span = MagicMock()
        mock_span_context = MagicMock()
        mock_span_context.trace_id = 12345
        mock_span.get_span_context.return_value = mock_span_context
        mock_get_current_span.return_value = mock_span
        
        manager = TracingManager()
        trace_id = manager.get_current_trace_id()
        
        assert trace_id is not None
        assert isinstance(trace_id, str)
