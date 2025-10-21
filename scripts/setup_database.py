#!/usr/bin/env python3
"""
Database setup script for SoundHash.
Creates the database schema using Alembic migrations.
"""

import argparse
import os
import subprocess
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.logging_config import create_section_logger, setup_logging
from config.settings import Config
from src.database.connection import db_manager


def setup_database():
    """Setup the PostgreSQL database using Alembic migrations"""
    # Parse CLI arguments
    parser = argparse.ArgumentParser(description="Setup SoundHash database")
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Set logging level",
    )
    parser.add_argument("--no-colors", action="store_true", help="Disable colored output")
    args = parser.parse_args()

    # Setup enhanced logging
    setup_logging(log_level=args.log_level, log_file=None, use_colors=not args.no_colors)
    logger = create_section_logger(__name__)

    try:
        logger.log_section_start("Database Setup", "Initializing SoundHash database schema")
        logger.info(f"Database URL: {Config.get_database_url_safe()}")

        # Run Alembic migrations
        logger.log_step(1, "Running database migrations", "Applying schema changes")
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            logger.log_error_box("Migration failed", result.stderr)
            sys.exit(1)

        logger.log_success("Migrations applied successfully!")

        # Test the connection
        logger.log_step(2, "Testing database connection", "Verifying connectivity")
        session = db_manager.get_session()
        from sqlalchemy import text

        session.execute(text("SELECT 1"))
        session.close()

        logger.log_success("Database connection test passed!")
        logger.log_section_end("Database Setup", success=True)

    except Exception as e:
        logger.log_error_box("Database setup failed", str(e))
        logger.error("Make sure PostgreSQL is running and credentials are correct in .env file")
        logger.log_section_end("Database Setup", success=False)
        sys.exit(1)


if __name__ == "__main__":
    setup_database()
