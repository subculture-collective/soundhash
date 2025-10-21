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
