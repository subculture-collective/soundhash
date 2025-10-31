"""Tests for structured logging functionality."""

import json
import logging
from unittest.mock import MagicMock, patch

from src.observability.structured_logging import StructuredFormatter, StructuredLogger, get_structured_logger


class TestStructuredFormatter:
    """Test structured formatter functionality."""

    def test_format_basic_log_record(self):
        """Test formatting a basic log record."""
        formatter = StructuredFormatter(include_trace_id=False)
        
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        formatted = formatter.format(record)
        log_entry = json.loads(formatted)
        
        assert log_entry["level"] == "INFO"
        assert log_entry["logger"] == "test"
        assert log_entry["message"] == "Test message"
        assert log_entry["module"] == "test"
        assert log_entry["line"] == 10
        assert "timestamp" in log_entry

    def test_format_log_record_with_exception(self):
        """Test formatting a log record with exception."""
        formatter = StructuredFormatter(include_trace_id=False)
        
        try:
            raise ValueError("Test error")
        except ValueError:
            import sys
            exc_info = sys.exc_info()
        
        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=10,
            msg="Error occurred",
            args=(),
            exc_info=exc_info
        )
        
        formatted = formatter.format(record)
        log_entry = json.loads(formatted)
        
        assert log_entry["level"] == "ERROR"
        assert "exception" in log_entry
        assert "ValueError" in log_entry["exception"]

    def test_format_log_record_with_extra_fields(self):
        """Test formatting a log record with extra fields."""
        formatter = StructuredFormatter(include_trace_id=False)
        
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None
        )
        record.extra_fields = {"user_id": "123", "request_id": "abc"}
        
        formatted = formatter.format(record)
        log_entry = json.loads(formatted)
        
        assert log_entry["user_id"] == "123"
        assert log_entry["request_id"] == "abc"

    @patch('src.observability.structured_logging.tracing')
    def test_format_log_record_with_trace_id(self, mock_tracing):
        """Test formatting a log record with trace ID."""
        formatter = StructuredFormatter(include_trace_id=True)
        mock_tracing.get_current_trace_id.return_value = "test-trace-id"
        
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        formatted = formatter.format(record)
        log_entry = json.loads(formatted)
        
        assert log_entry["trace_id"] == "test-trace-id"


class TestStructuredLogger:
    """Test structured logger functionality."""

    @patch('src.observability.structured_logging.Config')
    def test_logger_initialization(self, mock_config):
        """Test logger initialization."""
        mock_config.STRUCTURED_LOGGING_ENABLED = False
        
        logger = StructuredLogger("test")
        
        assert logger.logger is not None
        assert logger.logger.name == "test"

    @patch('src.observability.structured_logging.Config')
    def test_info_logging(self, mock_config):
        """Test info level logging."""
        mock_config.STRUCTURED_LOGGING_ENABLED = False
        
        logger = StructuredLogger("test")
        logger.logger = MagicMock()
        
        logger.info("Test message", user_id="123", action="test")
        
        logger.logger.log.assert_called_once()
        call_args = logger.logger.log.call_args
        assert call_args[0][0] == logging.INFO
        assert call_args[0][1] == "Test message"
        assert "extra_fields" in call_args[1]["extra"]
        assert call_args[1]["extra"]["extra_fields"]["user_id"] == "123"

    @patch('src.observability.structured_logging.Config')
    def test_error_logging(self, mock_config):
        """Test error level logging."""
        mock_config.STRUCTURED_LOGGING_ENABLED = False
        
        logger = StructuredLogger("test")
        logger.logger = MagicMock()
        
        logger.error("Error occurred", error_code="500")
        
        logger.logger.log.assert_called_once()
        call_args = logger.logger.log.call_args
        assert call_args[0][0] == logging.ERROR
        assert call_args[0][1] == "Error occurred"

    @patch('src.observability.structured_logging.Config')
    def test_warning_logging(self, mock_config):
        """Test warning level logging."""
        mock_config.STRUCTURED_LOGGING_ENABLED = False
        
        logger = StructuredLogger("test")
        logger.logger = MagicMock()
        
        logger.warning("Warning message", threshold="80%")
        
        logger.logger.log.assert_called_once()
        call_args = logger.logger.log.call_args
        assert call_args[0][0] == logging.WARNING

    @patch('src.observability.structured_logging.Config')
    def test_log_operation(self, mock_config):
        """Test logging an operation."""
        mock_config.STRUCTURED_LOGGING_ENABLED = False
        
        logger = StructuredLogger("test")
        logger.logger = MagicMock()
        
        logger.log_operation(
            "process_video",
            status="success",
            duration_ms=1500.5,
            video_id="123"
        )
        
        logger.logger.log.assert_called_once()
        call_args = logger.logger.log.call_args
        assert call_args[0][0] == logging.INFO
        assert "process_video" in call_args[0][1]
        
        extra_fields = call_args[1]["extra"]["extra_fields"]
        assert extra_fields["operation"] == "process_video"
        assert extra_fields["status"] == "success"
        assert extra_fields["duration_ms"] == 1500.5
        assert extra_fields["video_id"] == "123"

    @patch('src.observability.structured_logging.Config')
    def test_log_metric(self, mock_config):
        """Test logging a metric."""
        mock_config.STRUCTURED_LOGGING_ENABLED = False
        
        logger = StructuredLogger("test")
        logger.logger = MagicMock()
        
        logger.log_metric("cpu_usage", 75.5, unit="%", server="prod-1")
        
        logger.logger.log.assert_called_once()
        call_args = logger.logger.log.call_args
        
        extra_fields = call_args[1]["extra"]["extra_fields"]
        assert extra_fields["metric_name"] == "cpu_usage"
        assert extra_fields["metric_value"] == 75.5
        assert extra_fields["metric_unit"] == "%"
        assert extra_fields["server"] == "prod-1"


class TestGetStructuredLogger:
    """Test get_structured_logger helper function."""

    @patch('src.observability.structured_logging.Config')
    def test_get_structured_logger(self, mock_config):
        """Test getting a structured logger instance."""
        mock_config.STRUCTURED_LOGGING_ENABLED = False
        
        logger = get_structured_logger("test")
        
        assert isinstance(logger, StructuredLogger)
        assert logger.logger.name == "test"
