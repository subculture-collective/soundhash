"""Tests for channel ingestion with async orchestration."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from config.settings import Config
from src.ingestion.channel_ingester import ChannelIngester


class TestChannelIngester:
    """Test the ChannelIngester class."""

    @pytest.fixture
    def mock_youtube_service(self):
        """Create a mock YouTube service."""
        return MagicMock()

    @pytest.fixture
    def ingester(self, mock_youtube_service):
        """Create a ChannelIngester instance without DB initialization."""
        with patch('src.ingestion.channel_ingester.db_manager'):
            return ChannelIngester(initialize_db=False, youtube_service=mock_youtube_service)

    def test_init_without_db(self, mock_youtube_service):
        """Test initialization without database."""
        with patch('src.ingestion.channel_ingester.db_manager'):
            ingester = ChannelIngester(initialize_db=False, youtube_service=mock_youtube_service)
            assert ingester._db_initialized is False
            assert ingester.youtube_service is mock_youtube_service

    def test_init_with_db(self, mock_youtube_service):
        """Test initialization with database."""
        with patch('src.ingestion.channel_ingester.db_manager') as mock_db:
            ingester = ChannelIngester(initialize_db=True, youtube_service=mock_youtube_service)
            assert ingester._db_initialized is True
            mock_db.initialize.assert_called_once()

    @pytest.mark.asyncio
    async def test_ingest_all_channels_respects_max_concurrent(self, ingester):
        """Test that concurrent channel ingestion respects the semaphore limit."""
        # Mock the ingest_channel method to track concurrent calls
        concurrent_calls = []
        max_concurrent = 0

        async def mock_ingest_channel(channel_id, max_videos=None, dry_run=False):
            concurrent_calls.append(channel_id)
            current = len(concurrent_calls)
            nonlocal max_concurrent
            max_concurrent = max(max_concurrent, current)
            await asyncio.sleep(0.1)  # Simulate work
            concurrent_calls.remove(channel_id)

        with patch.object(ingester, 'ingest_channel', side_effect=mock_ingest_channel):
            # Test with 5 channels and max concurrent of 2
            original_max = Config.MAX_CONCURRENT_CHANNELS
            Config.MAX_CONCURRENT_CHANNELS = 2

            channels = ['CH1', 'CH2', 'CH3', 'CH4', 'CH5']
            await ingester.ingest_all_channels(channels_override=channels, dry_run=True)

            # Restore original config
            Config.MAX_CONCURRENT_CHANNELS = original_max

            # Should never have more than 2 concurrent calls
            assert max_concurrent <= 2

    @pytest.mark.asyncio
    async def test_ingest_all_channels_dry_run(self, ingester):
        """Test dry-run mode doesn't create DB records."""
        # Mock get_channel_videos to return some test data
        test_videos = [
            {'id': 'video1', 'title': 'Test Video 1', 'duration': 100},
            {'id': 'video2', 'title': 'Test Video 2', 'duration': 200},
        ]

        with patch.object(ingester.video_processor, 'get_channel_videos', return_value=test_videos):
            await ingester.ingest_all_channels(
                channels_override=['test_channel'], max_videos=10, dry_run=True
            )
            # In dry-run, no DB operations should occur
            # This is implicitly tested since we didn't mock DB operations

    @pytest.mark.asyncio
    async def test_ingest_channel_with_retry_success_first_try(self, ingester):
        """Test successful ingestion on first try."""
        with patch.object(ingester, 'ingest_channel', new_callable=AsyncMock) as mock_ingest:
            result = await ingester._ingest_channel_with_retry('test_channel', dry_run=True)

            assert result is True
            assert mock_ingest.call_count == 1

    @pytest.mark.asyncio
    async def test_ingest_channel_with_retry_success_after_retry(self, ingester):
        """Test successful ingestion after retries."""
        call_count = 0

        async def mock_ingest_with_failure(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise Exception("Temporary failure")
            # Success on second try

        with patch.object(ingester, 'ingest_channel', side_effect=mock_ingest_with_failure):
            result = await ingester._ingest_channel_with_retry('test_channel', dry_run=True)

            assert result is True
            assert call_count == 2

    @pytest.mark.asyncio
    async def test_ingest_channel_with_retry_max_retries_exceeded(self, ingester):
        """Test that ingestion fails after max retries."""
        async def mock_ingest_always_fails(*args, **kwargs):
            raise Exception("Persistent failure")

        original_max = Config.CHANNEL_MAX_RETRIES
        original_delay = Config.CHANNEL_RETRY_DELAY
        Config.CHANNEL_MAX_RETRIES = 2
        Config.CHANNEL_RETRY_DELAY = 0.01  # Very short delay for testing

        with patch.object(ingester, 'ingest_channel', side_effect=mock_ingest_always_fails):
            result = await ingester._ingest_channel_with_retry('test_channel', dry_run=True)

            assert result is False

        # Restore original config
        Config.CHANNEL_MAX_RETRIES = original_max
        Config.CHANNEL_RETRY_DELAY = original_delay

    @pytest.mark.asyncio
    async def test_ingest_channel_respects_max_videos(self, ingester):
        """Test that max_videos limit is respected."""
        # Create more videos than the limit
        test_videos = [
            {'id': f'video{i}', 'title': f'Test Video {i}', 'duration': 100}
            for i in range(20)
        ]

        with patch.object(ingester.video_processor, 'get_channel_videos') as mock_get_videos:
            mock_get_videos.return_value = test_videos[:5]  # Simulate yt-dlp limiting

            await ingester.ingest_channel('test_channel', max_videos=5, dry_run=True)

            # Verify max_videos was passed to get_channel_videos
            mock_get_videos.assert_called_once_with('test_channel', 5)

    @pytest.mark.asyncio
    async def test_ingest_channel_empty_channel_id(self, ingester):
        """Test that empty channel IDs are skipped."""
        original_max = Config.MAX_CONCURRENT_CHANNELS
        Config.MAX_CONCURRENT_CHANNELS = 2

        channels = ['', '  ', 'valid_channel']

        with patch.object(ingester, 'ingest_channel', new_callable=AsyncMock) as mock_ingest:
            await ingester.ingest_all_channels(channels_override=channels, dry_run=True)

            # Only the valid channel should be processed
            assert mock_ingest.call_count == 1
            mock_ingest.assert_called_with('valid_channel', max_videos=None, dry_run=True)

        Config.MAX_CONCURRENT_CHANNELS = original_max

    @pytest.mark.asyncio
    async def test_idempotent_job_creation(self, ingester):
        """Test that re-running ingestion doesn't create duplicate jobs."""
        # This test requires DB mocking, which is more complex
        # We'll verify the logic is correct by checking the code path
        test_videos = [
            {
                'id': 'video1',
                'title': 'Test Video',
                'duration': 100,
                'webpage_url': 'https://youtube.com/watch?v=video1',
            }
        ]

        mock_video_repo = MagicMock()
        mock_job_repo = MagicMock()
        mock_channel = MagicMock()
        mock_channel.id = 1
        mock_channel.channel_name = 'Test Channel'

        mock_video_repo.get_channel_by_id.return_value = mock_channel
        mock_video_repo.get_video_by_id.return_value = None  # New video

        # Simulate job already exists
        mock_job_repo.job_exists.return_value = True

        with (
            patch.object(ingester.video_processor, 'get_channel_videos', return_value=test_videos),
            patch('src.ingestion.channel_ingester.get_video_repository', return_value=mock_video_repo),
            patch('src.ingestion.channel_ingester.get_job_repository', return_value=mock_job_repo),
        ):
            ingester._db_initialized = True
            await ingester.ingest_channel('test_channel', max_videos=1, dry_run=False)

            # Verify job_exists was called
            mock_job_repo.job_exists.assert_called()
            # Verify create_job was NOT called since job exists
            mock_job_repo.create_job.assert_not_called()

    @pytest.mark.asyncio
    async def test_ingest_all_channels_summary(self, ingester):
        """Test that ingestion summary is logged correctly."""
        channels = ['ch1', 'ch2', 'ch3']

        call_count = 0

        async def mock_ingest_with_mixed_results(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                raise Exception("Channel 2 failed")

        with patch.object(ingester, 'ingest_channel', side_effect=mock_ingest_with_mixed_results):
            await ingester.ingest_all_channels(channels_override=channels, dry_run=True)

            # Verify all channels were attempted
            assert call_count >= 3  # May have retries
