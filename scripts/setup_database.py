#!/usr/bin/env python3
"""
Database setup script for SoundHash.
Creates the database schema using Alembic migrations.
"""

import logging
import os
import subprocess
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import Config
from src.database.connection import db_manager


def setup_database():
    """Setup the PostgreSQL database using Alembic migrations"""
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    try:
        logger.info("Setting up SoundHash database...")
        logger.info(f"Database URL: {Config.get_database_url()}")

        # Run Alembic migrations
        logger.info("Running database migrations...")
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            logger.error("Migration failed:")
            logger.error(result.stderr)
            sys.exit(1)

        logger.info("Migrations applied successfully!")

        # Test the connection
        logger.info("Testing database connection...")
        session = db_manager.get_session()
        from sqlalchemy import text

        session.execute(text("SELECT 1"))
        session.close()

        logger.info("Database connection test passed!")
        logger.info("Database setup completed successfully!")

    except Exception as e:
        logger.error(f"Database setup failed: {str(e)}")
        logger.error("Make sure PostgreSQL is running and credentials are correct in .env file")
        sys.exit(1)


if __name__ == "__main__":
    setup_database()
