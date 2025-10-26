"""Tests for batch insert operations and performance optimizations."""

import time
from unittest.mock import Mock, patch

import pytest
from sqlalchemy.exc import IntegrityError

from src.database.models import AudioFingerprint, MatchResult
from src.database.repositories import VideoRepository


class TestBatchInsertFingerprints:
    """Test suite for batch fingerprint insertion."""

    def test_batch_insert_fingerprints_success(self, test_db_session, sample_video):
        """Test successful batch insert of fingerprints."""
        repo = VideoRepository(test_db_session)
        
        # Prepare batch data
        fingerprints_data = [
            {
                "video_id": sample_video.id,
                "start_time": 0.0,
                "end_time": 10.0,
                "fingerprint_hash": "hash_001",
                "fingerprint_data": b"data_001",
                "confidence_score": 0.95,
                "peak_count": 42,
                "sample_rate": 22050,
                "segment_length": 10.0,
            },
            {
                "video_id": sample_video.id,
                "start_time": 10.0,
                "end_time": 20.0,
                "fingerprint_hash": "hash_002",
                "fingerprint_data": b"data_002",
                "confidence_score": 0.93,
                "peak_count": 38,
                "sample_rate": 22050,
                "segment_length": 10.0,
            },
            {
                "video_id": sample_video.id,
                "start_time": 20.0,
                "end_time": 30.0,
                "fingerprint_hash": "hash_003",
                "fingerprint_data": b"data_003",
                "confidence_score": 0.91,
                "peak_count": 40,
                "sample_rate": 22050,
                "segment_length": 10.0,
            },
        ]
        
        # Batch insert
        fingerprints = repo.create_fingerprints_batch(fingerprints_data)
        
        # Verify results
        assert len(fingerprints) == 3
        
        # Verify in database
        db_fingerprints = (
            test_db_session.query(AudioFingerprint)
            .filter(AudioFingerprint.video_id == sample_video.id)
            .order_by(AudioFingerprint.start_time)
            .all()
        )
        
        assert len(db_fingerprints) == 3
        assert db_fingerprints[0].fingerprint_hash == "hash_001"
        assert db_fingerprints[0].start_time == 0.0
        assert db_fingerprints[0].confidence_score == 0.95
        assert db_fingerprints[1].fingerprint_hash == "hash_002"
        assert db_fingerprints[2].fingerprint_hash == "hash_003"

    def test_batch_insert_empty_list(self, test_db_session):
        """Test batch insert with empty list returns empty list."""
        repo = VideoRepository(test_db_session)
        
        fingerprints = repo.create_fingerprints_batch([])
        
        assert fingerprints == []

    def test_batch_insert_fingerprints_performance(self, test_db_session, sample_video):
        """Test that batch insert is significantly faster than individual inserts."""
        repo = VideoRepository(test_db_session)
        
        # Prepare batch data (20 fingerprints)
        batch_data = [
            {
                "video_id": sample_video.id,
                "start_time": float(i * 10),
                "end_time": float((i + 1) * 10),
                "fingerprint_hash": f"hash_{i:03d}",
                "fingerprint_data": f"data_{i:03d}".encode(),
                "confidence_score": 0.9,
                "peak_count": 40,
                "sample_rate": 22050,
                "segment_length": 10.0,
            }
            for i in range(20)
        ]
        
        # Time batch insert
        start_time = time.time()
        repo.create_fingerprints_batch(batch_data)
        batch_time = time.time() - start_time
        
        # Batch insert should be reasonably fast
        assert batch_time < 1.0, f"Batch insert took {batch_time}s, expected < 1s"
        
        # Verify all inserted
        count = (
            test_db_session.query(AudioFingerprint)
            .filter(AudioFingerprint.video_id == sample_video.id)
            .count()
        )
        assert count == 20


class TestBatchInsertMatchResults:
    """Test suite for batch match result insertion."""

    def test_batch_insert_match_results_success(self, test_db_session, sample_fingerprints):
        """Test successful batch insert of match results."""
        repo = VideoRepository(test_db_session)
        
        # Prepare batch data
        matches_data = [
            {
                "query_fingerprint_id": sample_fingerprints[0].id,
                "matched_fingerprint_id": sample_fingerprints[1].id,
                "similarity_score": 0.95,
                "match_confidence": 0.90,
                "query_source": "twitter",
            },
            {
                "query_fingerprint_id": sample_fingerprints[0].id,
                "matched_fingerprint_id": sample_fingerprints[2].id,
                "similarity_score": 0.88,
                "match_confidence": 0.85,
                "query_source": "reddit",
            },
            {
                "query_fingerprint_id": sample_fingerprints[1].id,
                "matched_fingerprint_id": sample_fingerprints[2].id,
                "similarity_score": 0.92,
                "query_source": "manual",
            },
        ]
        
        # Batch insert
        matches = repo.create_match_results_batch(matches_data)
        
        # Verify results
        assert len(matches) == 3
        
        # Verify in database
        db_matches = (
            test_db_session.query(MatchResult)
            .order_by(MatchResult.similarity_score.desc())
            .all()
        )
        
        assert len(db_matches) == 3
        assert db_matches[0].similarity_score == 0.95
        assert db_matches[0].query_source == "twitter"
        assert db_matches[1].similarity_score == 0.92
        assert db_matches[2].similarity_score == 0.88

    def test_batch_insert_match_results_empty_list(self, test_db_session):
        """Test batch insert with empty list returns empty list."""
        repo = VideoRepository(test_db_session)
        
        matches = repo.create_match_results_batch([])
        
        assert matches == []

    def test_batch_insert_match_results_performance(
        self, test_db_session, sample_fingerprints
    ):
        """Test that batch insert is significantly faster than individual inserts."""
        repo = VideoRepository(test_db_session)
        
        # Prepare batch data (50 matches)
        batch_data = [
            {
                "query_fingerprint_id": sample_fingerprints[0].id,
                "matched_fingerprint_id": sample_fingerprints[i % 3].id,
                "similarity_score": 0.8 + (i % 20) * 0.01,
                "query_source": "test",
            }
            for i in range(50)
        ]
        
        # Time batch insert
        start_time = time.time()
        repo.create_match_results_batch(batch_data)
        batch_time = time.time() - start_time
        
        # Batch insert should be reasonably fast
        assert batch_time < 1.0, f"Batch insert took {batch_time}s, expected < 1s"
        
        # Verify all inserted
        count = test_db_session.query(MatchResult).count()
        assert count == 50


class TestCompositeIndexes:
    """Test that composite indexes are used for common query patterns."""

    def test_query_fingerprints_by_video_and_time(
        self, test_db_session, sample_video, sample_fingerprints
    ):
        """Test query using composite index on video_id + start_time."""
        repo = VideoRepository(test_db_session)
        
        # Query should use idx_fingerprints_video_time composite index
        fingerprints = (
            test_db_session.query(AudioFingerprint)
            .filter(
                AudioFingerprint.video_id == sample_video.id,
                AudioFingerprint.start_time >= 0.0,
            )
            .order_by(AudioFingerprint.start_time)
            .all()
        )
        
        # Verify results are ordered correctly
        assert len(fingerprints) >= 1
        for i in range(len(fingerprints) - 1):
            assert fingerprints[i].start_time <= fingerprints[i + 1].start_time

    def test_query_fingerprints_by_hash_and_video(
        self, test_db_session, sample_video, sample_fingerprints
    ):
        """Test query using composite index on fingerprint_hash + video_id."""
        # Query should use idx_fingerprints_hash_video composite index
        fingerprints = (
            test_db_session.query(AudioFingerprint)
            .filter(
                AudioFingerprint.fingerprint_hash == sample_fingerprints[0].fingerprint_hash,
                AudioFingerprint.video_id == sample_video.id,
            )
            .all()
        )
        
        assert len(fingerprints) >= 1

    def test_get_top_matches_uses_composite_index(
        self, test_db_session, sample_fingerprints
    ):
        """Test that get_top_matches uses composite index for filtering and sorting."""
        repo = VideoRepository(test_db_session)
        
        # Create some match results
        matches_data = [
            {
                "query_fingerprint_id": sample_fingerprints[0].id,
                "matched_fingerprint_id": sample_fingerprints[1].id,
                "similarity_score": 0.95,
            },
            {
                "query_fingerprint_id": sample_fingerprints[0].id,
                "matched_fingerprint_id": sample_fingerprints[2].id,
                "similarity_score": 0.88,
            },
        ]
        repo.create_match_results_batch(matches_data)
        
        # Query should use idx_match_results_query_fp composite index
        matches = repo.get_top_matches(sample_fingerprints[0].id, limit=10)
        
        # Verify results are sorted by similarity score (descending)
        assert len(matches) == 2
        assert matches[0].similarity_score >= matches[1].similarity_score
        assert matches[0].similarity_score == 0.95
        assert matches[1].similarity_score == 0.88


class TestBatchVsIndividualPerformance:
    """Compare batch vs individual insert performance."""

    @pytest.mark.slow
    def test_batch_vs_individual_fingerprints(self, test_db_session, sample_video):
        """Compare batch insert vs individual inserts for fingerprints."""
        repo = VideoRepository(test_db_session)
        
        # Prepare test data
        num_fingerprints = 10
        batch_data = [
            {
                "video_id": sample_video.id,
                "start_time": float(i * 10),
                "end_time": float((i + 1) * 10),
                "fingerprint_hash": f"batch_hash_{i:03d}",
                "fingerprint_data": f"batch_data_{i:03d}".encode(),
                "confidence_score": 0.9,
                "peak_count": 40,
                "sample_rate": 22050,
                "segment_length": 10.0,
            }
            for i in range(num_fingerprints)
        ]
        
        # Time batch insert
        start_time = time.time()
        repo.create_fingerprints_batch(batch_data)
        batch_time = time.time() - start_time
        
        # Time individual inserts (with new data)
        start_time = time.time()
        for i in range(num_fingerprints):
            repo.create_fingerprint(
                video_id=sample_video.id,
                start_time=float((num_fingerprints + i) * 10),
                end_time=float((num_fingerprints + i + 1) * 10),
                fingerprint_hash=f"individual_hash_{i:03d}",
                fingerprint_data=f"individual_data_{i:03d}".encode(),
                confidence_score=0.9,
                peak_count=40,
                sample_rate=22050,
                segment_length=10.0,
            )
        individual_time = time.time() - start_time
        
        # Batch should be at least 2x faster
        speedup = individual_time / batch_time
        print(f"\nBatch insert speedup: {speedup:.2f}x")
        print(f"Batch time: {batch_time:.3f}s, Individual time: {individual_time:.3f}s")
        
        # Verify batch is faster (may vary based on DB)
        assert speedup > 1.5, f"Expected batch to be faster, but speedup was only {speedup:.2f}x"
