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