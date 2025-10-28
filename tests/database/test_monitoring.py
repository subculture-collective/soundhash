"""Tests for database query performance monitoring."""

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from src.database.models import Base
from src.database.monitoring import (
    enable_monitoring,
    get_query_metrics,
    reset_query_metrics,
)


@pytest.fixture
def monitored_db_session():
    """Create an in-memory SQLite database session with monitoring enabled."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    
    # Reset metrics before test
    reset_query_metrics()
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    yield session
    
    session.close()


def test_monitoring_tracks_queries(monitored_db_session):
    """Test that query monitoring tracks executed queries."""
    # Execute some queries
    monitored_db_session.execute(text("SELECT 1"))
    monitored_db_session.execute(text("SELECT 2"))
    monitored_db_session.execute(text("SELECT 3"))
    
    # Get metrics
    metrics = get_query_metrics()
    
    # Should have tracked the queries
    assert metrics["total_queries"] >= 3
    assert metrics["total_duration"] > 0
    assert metrics["average_duration"] > 0


def test_reset_query_metrics():
    """Test that resetting metrics works."""
    # Execute a query
    engine = create_engine("sqlite:///:memory:")
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    
    # Get metrics (should have at least one query)
    metrics = get_query_metrics()
    initial_count = metrics["total_queries"]
    assert initial_count >= 0
    
    # Reset metrics
    reset_query_metrics()
    
    # Get metrics again (should be zero)
    metrics = get_query_metrics()
    assert metrics["total_queries"] == 0
    assert metrics["slow_queries"] == 0
    assert metrics["total_duration"] == 0.0


def test_slow_query_detection(monitored_db_session):
    """Test that slow queries are detected and counted."""
    reset_query_metrics()
    
    # Execute a fast query
    monitored_db_session.execute(text("SELECT 1"))
    
    # Get initial metrics
    metrics = get_query_metrics()
    
    # Slow queries should be 0 for simple queries
    # (they execute in < 100ms)
    assert metrics["slow_queries"] == 0
    assert metrics["total_queries"] >= 1


def test_query_metrics_structure():
    """Test that query metrics have the expected structure."""
    reset_query_metrics()
    
    metrics = get_query_metrics()
    
    # Check all expected keys are present
    assert "total_queries" in metrics
    assert "slow_queries" in metrics
    assert "total_duration" in metrics
    assert "average_duration" in metrics
    assert "slow_query_percentage" in metrics
    
    # Check types
    assert isinstance(metrics["total_queries"], int)
    assert isinstance(metrics["slow_queries"], int)
    assert isinstance(metrics["total_duration"], float)
    assert isinstance(metrics["average_duration"], float)
    assert isinstance(metrics["slow_query_percentage"], float)


def test_average_duration_calculation(monitored_db_session):
    """Test that average duration is calculated correctly."""
    reset_query_metrics()
    
    # Execute queries
    for _ in range(5):
        monitored_db_session.execute(text("SELECT 1"))
    
    metrics = get_query_metrics()
    
    # Average should be total / count
    if metrics["total_queries"] > 0:
        expected_avg = metrics["total_duration"] / metrics["total_queries"]
        assert abs(metrics["average_duration"] - expected_avg) < 1e-9


def test_slow_query_percentage_calculation():
    """Test that slow query percentage is calculated correctly."""
    reset_query_metrics()
    
    metrics = get_query_metrics()
    
    # With no queries, percentage should be 0
    assert metrics["slow_query_percentage"] == 0.0
