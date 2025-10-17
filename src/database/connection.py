import importlib

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config.settings import Config

from .models import Base


class DatabaseManager:
    def __init__(self):
        self.engine = None
        self.Session = None

    def initialize(self):
        """Initialize database connection and create tables"""
        database_url = Config.get_database_url()

        # Auto-select driver if none specified and appropriate driver is available
        if database_url.startswith("postgresql://"):
            driver = None
            if importlib.util.find_spec("psycopg2") is not None:
                driver = "psycopg2"
            elif importlib.util.find_spec("psycopg") is not None:
                driver = "psycopg"
            if driver:
                database_url = database_url.replace(
                    "postgresql://", f"postgresql+{driver}://", 1
                )
        self.engine = create_engine(
            database_url,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            echo=False,  # Set to True for SQL debugging
        )

        self.Session = sessionmaker(bind=self.engine)

        # Create all tables
        Base.metadata.create_all(self.engine)

    def get_session(self):
        """Get a new database session"""
        if not self.Session:
            self.initialize()
        return self.Session()

    def close(self):
        """Close database connection"""
        if self.engine:
            self.engine.dispose()


# Global database manager instance
db_manager = DatabaseManager()
