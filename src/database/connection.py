import importlib.util

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session as SQLASession
from sqlalchemy.orm import sessionmaker

from config.settings import Config


class DatabaseManager:
    def __init__(self) -> None:
        self.engine: Engine | None = None
        self.Session: sessionmaker[SQLASession] | None = None

    def initialize(self) -> None:
        """Initialize database connection.

        Note: Tables are created via Alembic migrations, not here.
        Use `alembic upgrade head` to create or update the schema.
        """
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
        from sqlalchemy.pool import QueuePool
        
        # Build connect_args with statement timeout
        connect_args = {
            "options": f"-c statement_timeout={Config.DATABASE_STATEMENT_TIMEOUT}"
        }
        
        self.engine = create_engine(
            database_url,
            poolclass=QueuePool,
            pool_size=Config.DATABASE_POOL_SIZE,
            max_overflow=Config.DATABASE_MAX_OVERFLOW,
            pool_timeout=Config.DATABASE_POOL_TIMEOUT,
            pool_recycle=Config.DATABASE_POOL_RECYCLE,
            pool_pre_ping=True,  # Verify connections before using
            echo=Config.DATABASE_ECHO,
            connect_args=connect_args,
        )

        self.Session = sessionmaker(bind=self.engine)

        # Note: Schema is managed by Alembic migrations
        # Use `alembic upgrade head` to create/update tables

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
