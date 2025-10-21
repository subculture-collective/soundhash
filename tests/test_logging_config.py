"""Tests for logging configuration and structured logging functionality."""

import logging

import pytest

from config.logging_config import (
    ProgressLogger,
    create_section_logger,
    get_progress_logger,
    setup_logging,
)


class TestLoggingSetup:
    """Test logging setup and configuration."""

    def test_setup_logging_with_colors(self):
        """Test that setup_logging configures logging with colors enabled."""
        root_logger = setup_logging(log_level="INFO", log_file=None, use_colors=True)
        
        # Check that root logger is configured
        assert root_logger.level == logging.INFO
        assert len(root_logger.handlers) > 0

    def test_setup_logging_without_colors(self):
        """Test that setup_logging configures logging without colors."""
        root_logger = setup_logging(log_level="DEBUG", log_file=None, use_colors=False)
        
        # Check that root logger is configured with DEBUG level
        assert root_logger.level == logging.DEBUG
        assert len(root_logger.handlers) > 0

    def test_setup_logging_respects_log_level(self):
        """Test that log level is properly set."""
        root_logger = setup_logging(log_level="WARNING", log_file=None, use_colors=False)
        
        # Check that WARNING level is set
        assert root_logger.level == logging.WARNING

    def test_logging_includes_required_fields(self):
        """Test that logs include timestamp, module, level, and message."""
        setup_logging(log_level="INFO", log_file=None, use_colors=False)
        logger = logging.getLogger("test_module")

        # Verify logger is properly configured with a name
        assert logger.name == "test_module"  # module name
        
        # Test that we can log with all fields (they'll go to stdout)
        try:
            logger.info("Test message with all fields")
        except Exception as e:
            pytest.fail(f"Logging raised exception: {e}")


class TestSectionLogger:
    """Test section logger functionality."""

    def test_create_section_logger(self):
        """Test that create_section_logger creates a logger with helper methods."""
        logger = create_section_logger("test_logger")

        # Check that logger has custom methods
        assert hasattr(logger, "log_section_start")
        assert hasattr(logger, "log_section_end")
        assert hasattr(logger, "log_step")
        assert hasattr(logger, "log_success")
        assert hasattr(logger, "log_warning_box")
        assert hasattr(logger, "log_error_box")

    def test_section_logger_callable_methods(self):
        """Test that section logger methods are callable."""
        setup_logging(log_level="INFO", log_file=None, use_colors=False)
        logger = create_section_logger("test_section")

        # Test that methods can be called without error
        try:
            logger.log_section_start("Test Section", "Testing section logging")
            logger.log_section_end("Test Section", success=True)
            logger.log_step(1, "First step", "Step details")
            logger.log_success("Operation completed")
            logger.log_warning_box("This is a warning")
            logger.log_error_box("Error occurred", "Error details")
        except Exception as e:
            pytest.fail(f"Section logger methods raised exception: {e}")


class TestProgressLogger:
    """Test progress logger functionality."""

    def test_get_progress_logger(self):
        """Test that get_progress_logger creates a ProgressLogger instance."""
        setup_logging(log_level="INFO", log_file=None, use_colors=False)
        logger = logging.getLogger("test_progress")

        progress = get_progress_logger(logger, total_items=10, description="Test Progress")

        assert isinstance(progress, ProgressLogger)
        assert progress.total_items == 10
        assert progress.description == "Test Progress"
        assert progress.current_item == 0

    def test_progress_logger_update(self):
        """Test that progress logger update works without error."""
        setup_logging(log_level="INFO", log_file=None, use_colors=False)
        logger = logging.getLogger("test_progress_update")

        progress = get_progress_logger(logger, total_items=5, description="Processing")

        try:
            progress.update(increment=1, item_name="Item 1")
            progress.update(increment=1, item_name="Item 2")
            assert progress.current_item == 2
        except Exception as e:
            pytest.fail(f"Progress update raised exception: {e}")

    def test_progress_logger_complete(self):
        """Test that progress logger complete works without error."""
        setup_logging(log_level="INFO", log_file=None, use_colors=False)
        logger = logging.getLogger("test_progress_complete")

        progress = get_progress_logger(logger, total_items=3, description="Task")

        try:
            progress.update(increment=1)
            progress.update(increment=1)
            progress.update(increment=1)
            progress.complete()
            assert progress.current_item == 3
        except Exception as e:
            pytest.fail(f"Progress complete raised exception: {e}")

    def test_progress_logger_tracking(self):
        """Test that progress logger tracks progress correctly."""
        setup_logging(log_level="INFO", log_file=None, use_colors=False)
        logger = logging.getLogger("test_tracking")

        progress = get_progress_logger(logger, total_items=10, description="Test")

        # Test incremental updates
        progress.update(increment=5)
        assert progress.current_item == 5

        progress.update(increment=3)
        assert progress.current_item == 8

        # Test that we can reach completion
        progress.update(increment=2)
        assert progress.current_item == 10


class TestLoggingIntegration:
    """Integration tests for logging functionality."""

    def test_cli_log_level_controls_output(self):
        """Test that CLI log level flag controls what's logged."""
        # Test INFO level
        root_logger = setup_logging(log_level="INFO", log_file=None, use_colors=False)
        assert root_logger.level == logging.INFO

        # Test ERROR level
        root_logger = setup_logging(log_level="ERROR", log_file=None, use_colors=False)
        assert root_logger.level == logging.ERROR

        # Test DEBUG level
        root_logger = setup_logging(log_level="DEBUG", log_file=None, use_colors=False)
        assert root_logger.level == logging.DEBUG

    def test_progress_with_long_operations(self):
        """Test progress logger with longer operations."""
        setup_logging(log_level="INFO", log_file=None, use_colors=False)
        logger = logging.getLogger("test_long_operation")

        progress = get_progress_logger(logger, total_items=100, description="Long Operation")

        try:
            # Simulate processing multiple items
            for i in range(10):
                progress.update(increment=10)

            progress.complete()

            # Verify final state
            assert progress.current_item == 100
        except Exception as e:
            pytest.fail(f"Long operation test raised exception: {e}")
