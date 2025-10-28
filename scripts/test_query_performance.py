#!/usr/bin/env python3
"""Test and benchmark critical database queries.

This script measures the performance of common database queries to ensure
they meet performance targets (< 100ms for most operations).
"""

import argparse
import logging
import statistics
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.logging_config import setup_logging
from config.settings import Config
from src.database.connection import db_manager
from src.database.monitoring import get_query_metrics, reset_query_metrics
from src.database.repositories import get_job_repository, get_video_repository

logger = logging.getLogger(__name__)


def benchmark_query(
    name: str, func: Callable[..., Any], iterations: int = 5, *args: Any, **kwargs: Any
) -> dict[str, Any]:
    """Benchmark a query function.
    
    Args:
        name: Query name for reporting
        func: Function to benchmark
        iterations: Number of times to run the query
        *args: Positional arguments for func
        **kwargs: Keyword arguments for func
        
    Returns:
        Dictionary with benchmark results
    """
    durations = []
    
    for i in range(iterations):
        start = time.time()
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start
            durations.append(duration)
            
            if i == 0:  # Log result type on first iteration
                logger.debug(f"{name}: returned {type(result).__name__}")
        except Exception as e:
            logger.error(f"{name} failed: {e}")
            return {
                "name": name,
                "error": str(e),
                "success": False,
            }
    
    return {
        "name": name,
        "success": True,
        "iterations": iterations,
        "min_ms": min(durations) * 1000,
        "max_ms": max(durations) * 1000,
        "avg_ms": statistics.mean(durations) * 1000,
        "median_ms": statistics.median(durations) * 1000,
        "p95_ms": (
            statistics.quantiles(durations, n=20)[18] * 1000 if len(durations) >= 20 else max(durations) * 1000
        ),
    }


def print_results(results: list[dict[str, Any]]) -> None:
    """Print benchmark results in a formatted table.
    
    Args:
        results: List of benchmark result dictionaries
    """
    print("\n" + "=" * 80)
    print("Database Query Performance Benchmark Results")
    print("=" * 80)
    print(f"Target: < 100ms for p95")
    print("-" * 80)
    print(f"{'Query Name':<40} {'Avg (ms)':<12} {'P95 (ms)':<12} {'Status':<10}")
    print("-" * 80)
    
    passed = 0
    failed = 0
    
    for result in results:
        if not result.get("success", False):
            print(f"{result['name']:<40} {'ERROR':<12} {'ERROR':<12} {'FAILED':<10}")
            failed += 1
            continue
        
        avg_ms = result["avg_ms"]
        p95_ms = result["p95_ms"]
        
        # Determine status
        if p95_ms < 100:
            status = "✓ PASS"
            passed += 1
        elif p95_ms < 200:
            status = "⚠ WARN"
            passed += 1
        else:
            status = "✗ FAIL"
            failed += 1
        
        print(f"{result['name']:<40} {avg_ms:<12.2f} {p95_ms:<12.2f} {status:<10}")
    
    print("-" * 80)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 80 + "\n")


def run_benchmarks() -> list[dict[str, Any]]:
    """Run all benchmark queries.
    
    Returns:
        List of benchmark results
    """
    logger.info("Starting database query benchmarks...")
    
    # Initialize database
    db_manager.initialize()
    
    results = []
    
    # Get repository instances
    video_repo = get_video_repository()
    job_repo = get_job_repository()
    
    try:
        # Test 1: Get channel by ID (should be fast with index)
        results.append(
            benchmark_query(
                "Get channel by ID",
                video_repo.get_channel_by_id,
                iterations=10,
                channel_id="test_channel_123",
            )
        )
        
        # Test 2: Get video by ID (should be fast with index)
        results.append(
            benchmark_query(
                "Get video by ID",
                video_repo.get_video_by_id,
                iterations=10,
                video_id="test_video_123",
            )
        )
        
        # Test 3: Get unprocessed videos (partial index should help)
        results.append(
            benchmark_query(
                "Get unprocessed videos (limit 100)",
                video_repo.get_unprocessed_videos,
                iterations=10,
                limit=100,
            )
        )
        
        # Test 4: Get pending jobs (should use composite index)
        results.append(
            benchmark_query(
                "Get pending jobs (limit 10)",
                job_repo.get_pending_jobs,
                iterations=10,
                limit=10,
            )
        )
        
        # Test 5: Check job exists (should use composite index)
        results.append(
            benchmark_query(
                "Check job exists",
                job_repo.job_exists,
                iterations=10,
                job_type="video_process",
                target_id="test_target_123",
                statuses=["pending", "running"],
            )
        )
        
        # Test 6: Count jobs by status
        results.append(
            benchmark_query(
                "Count jobs by status",
                job_repo.count_jobs_by_status,
                iterations=10,
                status="pending",
            )
        )
        
        # Test 7: Find matching fingerprints (should use hash index)
        results.append(
            benchmark_query(
                "Find matching fingerprints",
                video_repo.find_matching_fingerprints,
                iterations=10,
                fingerprint_hash="test_hash_123",
            )
        )
        
    finally:
        # Clean up
        video_repo.session.close()
        job_repo.session.close()
    
    return results


def print_query_metrics() -> None:
    """Print query performance metrics from monitoring."""
    metrics = get_query_metrics()
    
    print("\n" + "=" * 80)
    print("Query Performance Metrics (from monitoring)")
    print("=" * 80)
    print(f"Total queries executed: {metrics['total_queries']}")
    print(f"Slow queries (>100ms): {metrics['slow_queries']}")
    print(f"Slow query percentage: {metrics['slow_query_percentage']:.2f}%")
    print(f"Average query duration: {metrics['average_duration']*1000:.2f}ms")
    print(f"Total duration: {metrics['total_duration']:.2f}s")
    print("=" * 80 + "\n")


def main() -> int:
    """Main entry point.
    
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    parser = argparse.ArgumentParser(description="Benchmark database query performance")
    parser.add_argument(
        "--iterations",
        type=int,
        default=10,
        help="Number of iterations per query (default: 10)",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO)",
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(level=args.log_level)
    
    # Reset metrics before starting
    reset_query_metrics()
    
    # Run benchmarks
    results = run_benchmarks()
    
    # Print results
    print_results(results)
    
    # Print query metrics
    print_query_metrics()
    
    # Check if any queries failed
    failed = sum(1 for r in results if not r.get("success", False))
    if failed > 0:
        logger.error(f"{failed} queries failed")
        return 1
    
    # Check if any queries exceeded p95 target
    slow = sum(1 for r in results if r.get("success", False) and r.get("p95_ms", 0) > 100)
    if slow > 0:
        logger.warning(f"{slow} queries exceeded p95 target of 100ms")
    
    logger.info("Benchmark complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())
