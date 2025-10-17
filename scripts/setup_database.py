#!/usr/bin/env python3
"""
Database setup script for SoundHash.
Creates the database schema and initializes the system.
"""

import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging


def setup_database():
    """Setup the PostgreSQL database and create all tables"""
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    try:
        logger.info("Setting up SoundHash database...")

        # Initialize database connection
        db_manager.initialize()

        logger.info("Database setup completed successfully!")
        logger.info(f"Connected to: {Config.get_database_url()}")

        # Test the connection
        session = db_manager.get_session()
        from sqlalchemy import text

        session.execute(text("SELECT 1"))
        session.close()

        logger.info("Database connection test passed!")

    except Exception as e:
        logger.error(f"Database setup failed: {str(e)}")
        logger.error(
            "Make sure PostgreSQL is running and credentials are correct in .env file"
        )
        sys.exit(1)


if __name__ == "__main__":
    setup_database()
