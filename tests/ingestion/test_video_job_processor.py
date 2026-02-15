"""Tests for VideoJobProcessor."""

from unittest.mock import MagicMock, patch

import pytest

from src.ingestion.channel_ingester import VideoJobProcessor


class TestVideoJobProcessor:
    """Test the VideoJobProcessor class."""

    @pytest.fixture
    def processor(self):
        """Create a VideoJobProcessor instance."""
        return VideoJobProcessor()

    @pytest.mark.asyncio
    async def test_process_pending_videos_handles_early_exception(self, processor):
        """Test that process_pending_videos handles exceptions before repository initialization."""
        # Mock get_job_repository to raise an exception before returning
        with patch("src.ingestion.channel_ingester.get_job_repository") as mock_get_job_repo:
            mock_get_job_repo.side_effect = Exception("Database connection failed")

            # This should not raise a NameError when trying to close sessions
            with pytest.raises(Exception, match="Database connection failed"):
                await processor.process_pending_videos()

    @pytest.mark.asyncio
    async def test_process_pending_videos_handles_exception_in_try_block(self, processor):
        """Test that process_pending_videos properly closes sessions when exception in try block."""
        mock_job_repo = MagicMock()
        mock_video_repo = MagicMock()

        # Mock get_pending_jobs to raise an exception inside the try block
        mock_job_repo.get_pending_jobs.side_effect = Exception("Database query failed")

        with (
            patch(
                "src.ingestion.channel_ingester.get_job_repository", return_value=mock_job_repo
            ),
            patch(
                "src.ingestion.channel_ingester.get_video_repository", return_value=mock_video_repo
            ),
        ):
            # This should raise the original exception, not a NameError
            with pytest.raises(Exception, match="Database query failed"):
                await processor.process_pending_videos()

            # Verify both sessions were properly closed despite the exception
            mock_job_repo.session.close.assert_called_once()
            mock_video_repo.session.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_pending_videos_closes_sessions_on_success(self, processor):
        """Test that process_pending_videos properly closes sessions on successful execution."""
        mock_job_repo = MagicMock()
        mock_video_repo = MagicMock()

        # Mock get_pending_jobs to return empty list (no jobs to process)
        mock_job_repo.get_pending_jobs.return_value = []

        with (
            patch(
                "src.ingestion.channel_ingester.get_job_repository", return_value=mock_job_repo
            ),
            patch(
                "src.ingestion.channel_ingester.get_video_repository", return_value=mock_video_repo
            ),
        ):
            await processor.process_pending_videos()

            # Verify both sessions were closed
            mock_job_repo.session.close.assert_called_once()
            mock_video_repo.session.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_blocking_io_wrapped_with_asyncio_to_thread(self, processor):
        """Test that blocking I/O operations are wrapped with asyncio.to_thread."""
        import asyncio
        import json
        from unittest.mock import AsyncMock

        mock_job_repo = MagicMock()
        mock_video_repo = MagicMock()
        mock_job = MagicMock()
        mock_video = MagicMock()

        # Setup mock objects
        mock_job.id = 1
        mock_job.target_id = "video123"
        mock_job.parameters = json.dumps({"url": "https://youtube.com/watch?v=video123"})

        mock_video.id = 1
        mock_video.processing_started = None

        mock_job_repo.get_pending_jobs.return_value = [mock_job]
        mock_video_repo.get_video_by_id.return_value = mock_video
        mock_video_repo.check_fingerprints_exist.return_value = False

        # Mock the blocking operations and track if they run in threads
        mock_segments = [("seg1.wav", 0.0, 10.0)]
        mock_fingerprint = {
            "fingerprint_hash": "abc123",
            "confidence_score": 0.95,
            "peak_count": 100,
            "sample_rate": 22050,
        }

        with (
            patch("src.ingestion.channel_ingester.get_job_repository", return_value=mock_job_repo),
            patch("src.ingestion.channel_ingester.get_video_repository", return_value=mock_video_repo),
            patch("asyncio.to_thread", new_callable=AsyncMock) as mock_to_thread,
        ):
            # Configure mock_to_thread to call the function directly
            async def fake_to_thread(func, *args, **kwargs):
                return func(*args, **kwargs) if callable(func) else func

            mock_to_thread.side_effect = fake_to_thread

            # Mock the processor methods
            processor.video_processor.process_video_for_fingerprinting = MagicMock(
                return_value=mock_segments
            )
            processor.fingerprinter.extract_fingerprint = MagicMock(return_value=mock_fingerprint)
            processor.fingerprinter.serialize_fingerprint = MagicMock(return_value=b"serialized")
            processor.video_processor.cleanup_segments = MagicMock()

            # Enable cleanup to test all three blocking operations
            with patch("src.ingestion.channel_ingester.Config.CLEANUP_SEGMENTS_AFTER_PROCESSING", True):
                # Process one job
                await processor.process_video_job(mock_job, mock_video_repo, mock_job_repo)

            # Verify asyncio.to_thread was called for blocking operations
            # Should be called 3 times: process_video, extract_fingerprint, cleanup_segments
            assert mock_to_thread.call_count == 3, f"Expected 3 calls to asyncio.to_thread, got {mock_to_thread.call_count}"

