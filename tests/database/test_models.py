"""Tests for database models."""
from datetime import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.database.models import (
    AudioFingerprint,
    Base,
    Channel,
    MatchResult,
    ProcessingJob,
    Video,
)


@pytest.fixture
def in_memory_db():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    yield session
    
    session.close()


class TestDatabaseModels:
    """Test suite for database models."""

    def test_create_tables(self):
        """Test that all tables can be created."""
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        
        # Check that tables were created
        table_names = Base.metadata.tables.keys()
        assert 'channels' in table_names
        assert 'videos' in table_names
        assert 'audio_fingerprints' in table_names
        assert 'match_results' in table_names
        assert 'processing_jobs' in table_names

    def test_channel_model_creation(self, in_memory_db):
        """Test creating a Channel record."""
        channel = Channel(
            channel_id="UC123456789",
            channel_name="Test Channel",
            description="A test channel",
            subscriber_count=1000,
            video_count=50,
            is_active=True
        )
        
        in_memory_db.add(channel)
        in_memory_db.commit()
        
        # Query back
        retrieved = in_memory_db.query(Channel).filter_by(channel_id="UC123456789").first()
        
        assert retrieved is not None
        assert retrieved.channel_name == "Test Channel"
        assert retrieved.subscriber_count == 1000
        assert retrieved.is_active is True

    def test_video_model_creation(self, in_memory_db):
        """Test creating a Video record."""
        # First create a channel
        channel = Channel(
            channel_id="UC123456789",
            channel_name="Test Channel"
        )
        in_memory_db.add(channel)
        in_memory_db.commit()
        
        # Create video
        video = Video(
            video_id="dQw4w9WgXcQ",
            channel_id=channel.id,
            title="Test Video",
            description="A test video",
            duration=180.0,
            view_count=1000000,
            like_count=50000,
            url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            processed=False
        )
        
        in_memory_db.add(video)
        in_memory_db.commit()
        
        # Query back
        retrieved = in_memory_db.query(Video).filter_by(video_id="dQw4w9WgXcQ").first()
        
        assert retrieved is not None
        assert retrieved.title == "Test Video"
        assert retrieved.duration == 180.0
        assert retrieved.processed is False
        assert retrieved.channel_id == channel.id

    def test_audio_fingerprint_model_creation(self, in_memory_db):
        """Test creating an AudioFingerprint record."""
        # Create channel and video first
        channel = Channel(channel_id="UC123456789", channel_name="Test Channel")
        in_memory_db.add(channel)
        in_memory_db.commit()
        
        video = Video(
            video_id="dQw4w9WgXcQ",
            channel_id=channel.id,
            title="Test Video"
        )
        in_memory_db.add(video)
        in_memory_db.commit()
        
        # Create fingerprint
        fingerprint = AudioFingerprint(
            video_id=video.id,
            start_time=0.0,
            end_time=90.0,
            fingerprint_hash="abc123def456",
            fingerprint_data=b"binary_data_here",
            sample_rate=22050,
            segment_length=90.0,
            confidence_score=0.85,
            peak_count=100
        )
        
        in_memory_db.add(fingerprint)
        in_memory_db.commit()
        
        # Query back
        retrieved = in_memory_db.query(AudioFingerprint).filter_by(
            fingerprint_hash="abc123def456"
        ).first()
        
        assert retrieved is not None
        assert retrieved.start_time == 0.0
        assert retrieved.end_time == 90.0
        assert retrieved.confidence_score == 0.85
        assert retrieved.peak_count == 100

    def test_match_result_model_creation(self, in_memory_db):
        """Test creating a MatchResult record."""
        # Create necessary parent records
        channel = Channel(channel_id="UC123456789", channel_name="Test Channel")
        in_memory_db.add(channel)
        in_memory_db.commit()
        
        video = Video(video_id="dQw4w9WgXcQ", channel_id=channel.id, title="Test Video")
        in_memory_db.add(video)
        in_memory_db.commit()
        
        fp1 = AudioFingerprint(
            video_id=video.id,
            start_time=0.0,
            end_time=90.0,
            fingerprint_hash="hash1",
            fingerprint_data=b"data1"
        )
        fp2 = AudioFingerprint(
            video_id=video.id,
            start_time=90.0,
            end_time=180.0,
            fingerprint_hash="hash2",
            fingerprint_data=b"data2"
        )
        in_memory_db.add_all([fp1, fp2])
        in_memory_db.commit()
        
        # Create match result
        match = MatchResult(
            query_fingerprint_id=fp1.id,
            matched_fingerprint_id=fp2.id,
            similarity_score=0.92,
            match_confidence=0.88,
            query_source="twitter",
            query_url="https://twitter.com/user/status/123",
            query_user="testuser",
            responded=False
        )
        
        in_memory_db.add(match)
        in_memory_db.commit()
        
        # Query back
        retrieved = in_memory_db.query(MatchResult).filter_by(
            query_fingerprint_id=fp1.id
        ).first()
        
        assert retrieved is not None
        assert retrieved.similarity_score == 0.92
        assert retrieved.query_source == "twitter"
        assert retrieved.responded is False

    def test_processing_job_model_creation(self, in_memory_db):
        """Test creating a ProcessingJob record."""
        job = ProcessingJob(
            job_type="video_process",
            status="pending",
            target_id="dQw4w9WgXcQ",
            parameters='{"max_retries": 3}',
            progress=0.0,
            current_step="Initializing",
            retry_count=0,
            max_retries=3
        )
        
        in_memory_db.add(job)
        in_memory_db.commit()
        
        # Query back
        retrieved = in_memory_db.query(ProcessingJob).filter_by(
            job_type="video_process"
        ).first()
        
        assert retrieved is not None
        assert retrieved.status == "pending"
        assert retrieved.target_id == "dQw4w9WgXcQ"
        assert retrieved.progress == 0.0

    def test_channel_video_relationship(self, in_memory_db):
        """Test the relationship between Channel and Video."""
        channel = Channel(channel_id="UC123456789", channel_name="Test Channel")
        in_memory_db.add(channel)
        in_memory_db.commit()
        
        # Add multiple videos
        video1 = Video(video_id="video1", channel_id=channel.id, title="Video 1")
        video2 = Video(video_id="video2", channel_id=channel.id, title="Video 2")
        in_memory_db.add_all([video1, video2])
        in_memory_db.commit()
        
        # Query channel and access videos through relationship
        retrieved_channel = in_memory_db.query(Channel).filter_by(
            channel_id="UC123456789"
        ).first()
        
        assert len(retrieved_channel.videos) == 2
        assert retrieved_channel.videos[0].title in ["Video 1", "Video 2"]

    def test_video_fingerprints_relationship(self, in_memory_db):
        """Test the relationship between Video and AudioFingerprint."""
        channel = Channel(channel_id="UC123456789", channel_name="Test Channel")
        in_memory_db.add(channel)
        in_memory_db.commit()
        
        video = Video(video_id="dQw4w9WgXcQ", channel_id=channel.id, title="Test Video")
        in_memory_db.add(video)
        in_memory_db.commit()
        
        # Add multiple fingerprints
        fp1 = AudioFingerprint(
            video_id=video.id,
            start_time=0.0,
            end_time=90.0,
            fingerprint_hash="hash1",
            fingerprint_data=b"data1"
        )
        fp2 = AudioFingerprint(
            video_id=video.id,
            start_time=90.0,
            end_time=180.0,
            fingerprint_hash="hash2",
            fingerprint_data=b"data2"
        )
        in_memory_db.add_all([fp1, fp2])
        in_memory_db.commit()
        
        # Query video and access fingerprints through relationship
        retrieved_video = in_memory_db.query(Video).filter_by(
            video_id="dQw4w9WgXcQ"
        ).first()
        
        assert len(retrieved_video.fingerprints) == 2
        assert retrieved_video.fingerprints[0].start_time in [0.0, 90.0]

    def test_unique_constraint_channel_id(self, in_memory_db):
        """Test that channel_id must be unique."""
        channel1 = Channel(channel_id="UC123456789", channel_name="Channel 1")
        in_memory_db.add(channel1)
        in_memory_db.commit()
        
        # Try to add another channel with same channel_id
        channel2 = Channel(channel_id="UC123456789", channel_name="Channel 2")
        in_memory_db.add(channel2)
        
        with pytest.raises(Exception):  # SQLAlchemy will raise an IntegrityError
            in_memory_db.commit()

    def test_unique_constraint_video_id(self, in_memory_db):
        """Test that video_id must be unique."""
        channel = Channel(channel_id="UC123456789", channel_name="Test Channel")
        in_memory_db.add(channel)
        in_memory_db.commit()
        
        video1 = Video(video_id="dQw4w9WgXcQ", channel_id=channel.id, title="Video 1")
        in_memory_db.add(video1)
        in_memory_db.commit()
        
        # Try to add another video with same video_id
        video2 = Video(video_id="dQw4w9WgXcQ", channel_id=channel.id, title="Video 2")
        in_memory_db.add(video2)
        
        with pytest.raises(Exception):  # SQLAlchemy will raise an IntegrityError
            in_memory_db.commit()
