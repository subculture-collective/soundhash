"""Integration test to verify batch operations work end-to-end."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.database.models import AudioFingerprint, Base
from src.database.repositories import VideoRepository


@pytest.mark.integration
def test_batch_fingerprint_integration():
    """Test complete workflow: create video -> batch insert fingerprints -> query."""
    # Setup in-memory database
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        repo = VideoRepository(session)

        # Create channel and video
        channel = repo.create_channel(
            channel_id="TEST_CHANNEL",
            channel_name="Integration Test Channel"
        )

        video = repo.create_video(
            video_id="TEST_VIDEO",
            channel_id=channel.id,
            title="Test Video"
        )

        # Prepare batch of fingerprints
        fingerprints_data = [
            {
                "video_id": video.id,
                "start_time": float(i * 10),
                "end_time": float((i + 1) * 10),
                "fingerprint_hash": f"hash_{i:03d}",
                "fingerprint_data": f"data_{i:03d}".encode(),
                "confidence_score": 0.9,
                "peak_count": 40,
                "sample_rate": 22050,
                "segment_length": 10.0,
            }
            for i in range(5)
        ]

        # Batch insert
        fingerprints = repo.create_fingerprints_batch(fingerprints_data)

        # Verify
        assert len(fingerprints) == 5

        # Query back from database
        db_fingerprints = (
            session.query(AudioFingerprint)
            .filter(AudioFingerprint.video_id == video.id)
            .order_by(AudioFingerprint.start_time)
            .all()
        )

        assert len(db_fingerprints) == 5
        assert db_fingerprints[0].fingerprint_hash == "hash_000"
        assert db_fingerprints[0].start_time == 0.0
        assert db_fingerprints[4].fingerprint_hash == "hash_004"
        assert db_fingerprints[4].start_time == 40.0

    finally:
        session.close()

