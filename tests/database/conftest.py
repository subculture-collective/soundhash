"""Shared fixtures for database tests."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.database.models import AudioFingerprint, Base, Channel, Video


@pytest.fixture
def test_db_session():
    """Create an in-memory SQLite database session for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    yield session

    session.close()


@pytest.fixture
def sample_channel(test_db_session):
    """Create a sample channel for testing."""
    channel = Channel(
        channel_id="UC_TEST_CHANNEL",
        channel_name="Test Channel",
        description="A test channel for batch operations",
        subscriber_count=1000,
        video_count=10,
        is_active=True,
    )
    test_db_session.add(channel)
    test_db_session.commit()
    return channel


@pytest.fixture
def sample_video(test_db_session, sample_channel):
    """Create a sample video for testing."""
    video = Video(
        video_id="TEST_VIDEO_001",
        channel_id=sample_channel.id,
        title="Test Video for Batch Operations",
        description="A test video",
        duration=180.0,
        processed=False,
    )
    test_db_session.add(video)
    test_db_session.commit()
    return video


@pytest.fixture
def sample_fingerprints(test_db_session, sample_video):
    """Create sample fingerprints for testing."""
    fingerprints = [
        AudioFingerprint(
            video_id=sample_video.id,
            start_time=0.0,
            end_time=10.0,
            fingerprint_hash="test_hash_001",
            fingerprint_data=b"test_data_001",
            confidence_score=0.95,
            peak_count=42,
            sample_rate=22050,
            segment_length=10.0,
        ),
        AudioFingerprint(
            video_id=sample_video.id,
            start_time=10.0,
            end_time=20.0,
            fingerprint_hash="test_hash_002",
            fingerprint_data=b"test_data_002",
            confidence_score=0.93,
            peak_count=38,
            sample_rate=22050,
            segment_length=10.0,
        ),
        AudioFingerprint(
            video_id=sample_video.id,
            start_time=20.0,
            end_time=30.0,
            fingerprint_hash="test_hash_003",
            fingerprint_data=b"test_data_003",
            confidence_score=0.91,
            peak_count=40,
            sample_rate=22050,
            segment_length=10.0,
        ),
    ]
    
    for fp in fingerprints:
        test_db_session.add(fp)
    
    test_db_session.commit()
    return fingerprints
