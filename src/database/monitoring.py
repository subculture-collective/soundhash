"""Database query performance monitoring.

This module provides query performance tracking and logging for slow queries.
"""

import logging
import time
from typing import Any

from sqlalchemy import event
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)

# Track query metrics
query_metrics = {
    "total_queries": 0,
    "slow_queries": 0,
    "total_duration": 0.0,
}


@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(
    conn: Any, cursor: Any, statement: str, parameters: Any, context: Any, executemany: bool
) -> None:
    """Record query start time before execution."""
    conn.info.setdefault("query_start_time", []).append(time.time())


@event.listens_for(Engine, "after_cursor_execute")
def after_cursor_execute(
    conn: Any, cursor: Any, statement: str, parameters: Any, context: Any, executemany: bool
) -> None:
    """Log slow queries and record metrics after execution."""
    total = time.time() - conn.info["query_start_time"].pop(-1)

    # Update metrics
    query_metrics["total_queries"] += 1
    query_metrics["total_duration"] += total

    # Log slow queries (> 100ms)
    if total > 0.1:
        query_metrics["slow_queries"] += 1
        logger.warning(
            f"Slow query ({total:.3f}s): {statement[:200]}...",
            extra={"duration": total, "query": statement},
        )


def get_query_metrics() -> dict[str, Any]:
    """Get current query performance metrics.
    
    Returns:
        Dictionary containing query performance statistics
    """
    if query_metrics["total_queries"] > 0:
        avg_duration = query_metrics["total_duration"] / query_metrics["total_queries"]
    else:
        avg_duration = 0.0

    return {
        "total_queries": query_metrics["total_queries"],
        "slow_queries": query_metrics["slow_queries"],
        "total_duration": query_metrics["total_duration"],
        "average_duration": avg_duration,
        "slow_query_percentage": (
            (query_metrics["slow_queries"] / query_metrics["total_queries"] * 100)
            if query_metrics["total_queries"] > 0
            else 0.0
        ),
    }


def reset_query_metrics() -> None:
    """Reset query performance metrics."""
    query_metrics["total_queries"] = 0
    query_metrics["slow_queries"] = 0
    query_metrics["total_duration"] = 0.0


def enable_monitoring() -> None:
    """Enable query performance monitoring.
    
    This is called automatically when the module is imported,
    but can be called explicitly if needed.
    """
    logger.info("Query performance monitoring enabled")


# Auto-enable monitoring when module is imported
enable_monitoring()
