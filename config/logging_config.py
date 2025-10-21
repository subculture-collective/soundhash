"""
Enhanced logging configuration for SoundHash with colors and better formatting.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path

import colorlog


class PrettyFormatter(logging.Formatter):
    """Custom formatter with enhanced visual appeal and emojis."""

    EMOJI_MAP = {"DEBUG": "🔍", "INFO": "ℹ️", "WARNING": "⚠️", "ERROR": "❌", "CRITICAL": "💥"}

    def format(self, record):
        # Add emoji to the level name
        emoji = self.EMOJI_MAP.get(record.levelname, "📝")
        record.emoji = emoji

        # Add some nice formatting for different types of messages
        if hasattr(record, "module"):
            # Make module names more readable
            record.clean_module = record.module.replace("_", " ").title()

        return super().format(record)


class ProgressLogger:
    """Helper class for showing progress with visual indicators."""

    def __init__(self, logger, total_items, description="Processing"):
        self.logger = logger
        self.total_items = total_items
        self.description = description
        self.current_item = 0
        self.start_time = datetime.now()

    def update(self, increment=1, item_name=None):
        self.current_item += increment
        percentage = (self.current_item / self.total_items) * 100

        # Create progress bar
        bar_length = 30
        filled_length = int(bar_length * self.current_item // self.total_items)
        bar = "█" * filled_length + "░" * (bar_length - filled_length)

        # Calculate elapsed time and ETA
        elapsed = datetime.now() - self.start_time
        if self.current_item > 0:
            eta_seconds = (elapsed.total_seconds() / self.current_item) * (
                self.total_items - self.current_item
            )
            eta = f"ETA: {int(eta_seconds//60)}m {int(eta_seconds%60)}s"
        else:
            eta = "ETA: calculating..."

        item_info = f" | {item_name}" if item_name else ""

        self.logger.info(
            f"📊 {self.description}: [{bar}] {percentage:.1f}% ({self.current_item}/{self.total_items}){item_info} | {eta}"
        )

    def complete(self):
        elapsed = datetime.now() - self.start_time
        self.logger.info(f"✅ {self.description} completed! Total time: {elapsed}")


def setup_logging(log_level="INFO", log_file=None, use_colors=True):
    """
    Setup enhanced logging configuration with colors and better formatting.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
        use_colors: Whether to use colored output (auto-detected for terminals)
    """
    # Auto-detect if we should use colors
    if use_colors is None:
        use_colors = sys.stdout.isatty()

    # Clear any existing handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Set log level
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    root_logger.setLevel(numeric_level)

    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)

    if use_colors:
        # Colored formatter for console
        console_format = (
            "%(log_color)s%(emoji)s %(asctime)s%(reset)s "
            "%(bold_blue)s[%(name)s]%(reset)s "
            "%(log_color)s%(levelname)-8s%(reset)s "
            "%(white)s%(message)s%(reset)s"
        )

        console_formatter = colorlog.ColoredFormatter(
            console_format,
            datefmt="%H:%M:%S",
            reset=True,
            log_colors={
                "DEBUG": "cyan",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "red,bg_white",
            },
            secondary_log_colors={},
            style="%",
        )

        # Apply custom formatting
        class ColoredPrettyFormatter(PrettyFormatter, colorlog.ColoredFormatter):
            def __init__(self, *args, **kwargs):
                colorlog.ColoredFormatter.__init__(self, *args, **kwargs)

        console_formatter = ColoredPrettyFormatter(
            console_format,
            datefmt="%H:%M:%S",
            reset=True,
            log_colors={
                "DEBUG": "cyan",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "red,bg_white",
            },
        )
    else:
        # Simple formatter for non-color environments
        console_format = "%(emoji)s %(asctime)s [%(name)s] %(levelname)-8s %(message)s"
        console_formatter = PrettyFormatter(console_format, datefmt="%H:%M:%S")

    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file)
        file_format = "%(asctime)s [%(name)s] %(levelname)-8s %(message)s"
        file_formatter = logging.Formatter(file_format, datefmt="%Y-%m-%d %H:%M:%S")
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

    return root_logger


def create_section_logger(name, description=""):
    """Create a logger for a specific section with nice headers."""
    logger = logging.getLogger(name)

    def log_section_start(self, title, description=""):
        self.info("=" * 60)
        self.info(f"🚀 {title}")
        if description:
            self.info(f"   {description}")
        self.info("=" * 60)

    def log_section_end(self, title, success=True):
        status = "✅ COMPLETED" if success else "❌ FAILED"
        self.info("-" * 60)
        self.info(f"{status}: {title}")
        self.info("-" * 60)

    def log_step(self, step_num, description, details=""):
        self.info(f"📋 Step {step_num}: {description}")
        if details:
            self.info(f"   └─ {details}")

    def log_success(self, message):
        self.info(f"✅ {message}")

    def log_warning_box(self, message):
        self.warning("⚠️  " + "─" * 50)
        self.warning(f"⚠️  {message}")
        self.warning("⚠️  " + "─" * 50)

    def log_error_box(self, message, details=""):
        self.error("❌ " + "━" * 50)
        self.error(f"❌ ERROR: {message}")
        if details:
            self.error(f"❌ Details: {details}")
        self.error("❌ " + "━" * 50)

    # Add methods to logger instance
    logger.log_section_start = lambda title, description="": log_section_start(
        logger, title, description
    )
    logger.log_section_end = lambda title, success=True: log_section_end(
        logger, title, success
    )
    logger.log_step = lambda step_num, description, details="": log_step(
        logger, step_num, description, details
    )
    logger.log_success = lambda message: log_success(logger, message)
    logger.log_warning_box = lambda message: log_warning_box(logger, message)
    logger.log_error_box = lambda message, details="": log_error_box(
        logger, message, details
    )

    return logger


# Convenience function to get a progress tracker
def get_progress_logger(logger, total_items, description="Processing"):
    """Get a progress logger for showing visual progress bars."""
    return ProgressLogger(logger, total_items, description)
