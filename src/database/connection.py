import importlib.util

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session as SQLASession
from sqlalchemy.orm import sessionmaker

from config.settings import Config

from .models import Base


class DatabaseManager:
    def __init__(self) -> None:
        self.engine: Engine | None = None
        self.Session: sessionmaker[SQLASession] | None = None

    def initialize(self) -> None:
        """Initialize database connection and create tables"""
        database_url = Config.get_database_url()

        # Auto-select driver if none specified and appropriate driver is available
        if database_url.startswith("postgresql://"):
            driver: str | None = None
            if importlib.util.find_spec("psycopg2") is not None:
                driver = "psycopg2"
            elif importlib.util.find_spec("psycopg") is not None:
                driver = "psycopg"
            if driver:
                database_url = database_url.replace("postgresql://", f"postgresql+{driver}://", 1)
        self.engine = create_engine(
            database_url,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            echo=False  # Set to True for SQL debugging
        )

        self.Session = sessionmaker(bind=self.engine)

        # Create all tables
        Base.metadata.create_all(self.engine)

    def get_session(self) -> SQLASession:
        """Get a new database session"""
        if not self.Session:
            self.initialize()
        assert self.Session is not None
        return self.Session()

    def close(self) -> None:
        """Close database connection"""
        if self.engine:
            self.engine.dispose()

# Global database manager instance
db_manager = DatabaseManager()
