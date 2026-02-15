#!/usr/bin/env python3
"""Test batch job checking functionality."""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from unittest.mock import MagicMock, patch
from src.database.repositories import JobRepository
from src.database.models import ProcessingJob


def test_jobs_exist_batch_empty_list():
    """Test batch checking with empty list returns empty set."""
    mock_session = MagicMock()
    repo = JobRepository(mock_session)
    
    result = repo.jobs_exist_batch("video_process", [], statuses=["pending", "running"])
    assert result == set()
    # Should not query database for empty list
    mock_session.query.assert_not_called()


def test_jobs_exist_batch_with_results():
    """Test batch checking returns correct set of IDs."""
    mock_session = MagicMock()
    
    # Mock query chain
    mock_query = MagicMock()
    mock_session.query.return_value = mock_query
    mock_query.filter.return_value = mock_query
    
    # Simulate 2 out of 3 videos having jobs
    mock_query.all.return_value = [("video1",), ("video3",)]
    
    repo = JobRepository(mock_session)
    result = repo.jobs_exist_batch(
        "video_process", 
        ["video1", "video2", "video3"], 
        statuses=["pending", "running"]
    )
    
    assert result == {"video1", "video3"}
    assert "video2" not in result
    
    # Verify query was constructed properly
    mock_session.query.assert_called_once()
    assert mock_query.filter.call_count == 2  # Two filter calls for job_type and target_id.in_


def test_jobs_exist_batch_no_status_filter():
    """Test batch checking without status filter."""
    mock_session = MagicMock()
    
    mock_query = MagicMock()
    mock_session.query.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.all.return_value = [("video1",)]
    
    repo = JobRepository(mock_session)
    result = repo.jobs_exist_batch("video_process", ["video1", "video2"])
    
    assert result == {"video1"}
    # Should only have one filter call when no statuses
    assert mock_query.filter.call_count == 1


if __name__ == "__main__":
    print("Testing batch job checking...")
    test_jobs_exist_batch_empty_list()
    print("✓ Empty list test passed")
    
    test_jobs_exist_batch_with_results()
    print("✓ Batch with results test passed")
    
    test_jobs_exist_batch_no_status_filter()
    print("✓ No status filter test passed")
    
    print("\n✅ All tests passed!")
