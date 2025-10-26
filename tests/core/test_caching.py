"""Tests for caching functionality."""

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from config.settings import Config
from src.core.video_processor import VideoProcessor


class TestYtDlpCaching:
    """Test suite for yt-dlp caching functionality."""

    def test_cache_directory_created(self, temp_dir):
        """Test that cache directory is created on VideoProcessor initialization."""
        cache_dir = os.path.join(temp_dir, "yt-dlp-cache")
        
        with patch.object(Config, "ENABLE_YT_DLP_CACHE", True):
            with patch.object(Config, "YT_DLP_CACHE_DIR", cache_dir):
                processor = VideoProcessor(temp_dir=temp_dir)
                
                assert os.path.exists(cache_dir), "Cache directory should be created"

    def test_cache_directory_not_created_when_disabled(self, temp_dir):
        """Test that cache directory is not created when caching is disabled."""
        cache_dir = os.path.join(temp_dir, "yt-dlp-cache")
        
        with patch.object(Config, "ENABLE_YT_DLP_CACHE", False):
            with patch.object(Config, "YT_DLP_CACHE_DIR", cache_dir):
                processor = VideoProcessor(temp_dir=temp_dir)
                
                # Cache dir should not be created when caching is disabled
                assert not os.path.exists(cache_dir), "Cache directory should not be created when disabled"

    @patch("subprocess.run")
    def test_cache_dir_passed_to_ytdlp_when_enabled(self, mock_run, temp_dir):
        """Test that --cache-dir is passed to yt-dlp when caching is enabled."""
        cache_dir = os.path.join(temp_dir, "yt-dlp-cache")
        
        with patch.object(Config, "ENABLE_YT_DLP_CACHE", True):
            with patch.object(Config, "YT_DLP_CACHE_DIR", cache_dir):
                processor = VideoProcessor(temp_dir=temp_dir)
                
                # Mock successful yt-dlp execution
                mock_run.return_value = MagicMock(
                    returncode=0,
                    stdout="test_id|Test Title|Description|100|20231026|1000|50|Test Channel|UC123|thumb.jpg|https://youtube.com/watch?v=test_id",
                    stderr=""
                )
                
                # Call download_video_info which should include --cache-dir
                result = processor.download_video_info("https://www.youtube.com/watch?v=test_id")
                
                # Check that subprocess.run was called
                assert mock_run.called
                
                # Get the command that was passed to subprocess.run
                call_args = mock_run.call_args
                cmd = call_args[0][0]  # First positional argument
                
                # Verify --cache-dir is in the command
                assert "--cache-dir" in cmd, "Should include --cache-dir flag"
                assert cache_dir in cmd, f"Should include cache directory: {cache_dir}"

    @patch("subprocess.run")
    def test_cache_dir_not_passed_when_disabled(self, mock_run, temp_dir):
        """Test that --cache-dir is not passed to yt-dlp when caching is disabled."""
        cache_dir = os.path.join(temp_dir, "yt-dlp-cache")
        
        with patch.object(Config, "ENABLE_YT_DLP_CACHE", False):
            with patch.object(Config, "YT_DLP_CACHE_DIR", cache_dir):
                processor = VideoProcessor(temp_dir=temp_dir)
                
                # Mock successful yt-dlp execution
                mock_run.return_value = MagicMock(
                    returncode=0,
                    stdout="test_id|Test Title|Description|100|20231026|1000|50|Test Channel|UC123|thumb.jpg|https://youtube.com/watch?v=test_id",
                    stderr=""
                )
                
                # Call download_video_info
                result = processor.download_video_info("https://www.youtube.com/watch?v=test_id")
                
                # Check that subprocess.run was called
                assert mock_run.called
                
                # Get the command that was passed to subprocess.run
                call_args = mock_run.call_args
                cmd = call_args[0][0]  # First positional argument
                
                # Verify --cache-dir is NOT in the command
                assert "--cache-dir" not in cmd, "Should not include --cache-dir flag when disabled"


class TestFingerprintCaching:
    """Test suite for fingerprint caching functionality."""

    def test_check_fingerprints_exist_returns_false_for_new_video(self):
        """Test that check_fingerprints_exist returns False for videos without fingerprints."""
        from unittest.mock import MagicMock
        from src.database.repositories import VideoRepository
        
        # Create a mock session
        mock_session = MagicMock()
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 0  # No existing fingerprints
        
        repo = VideoRepository(mock_session)
        
        # Check for fingerprints - should return False
        result = repo.check_fingerprints_exist(
            video_id=1,
            sample_rate=22050,
            n_fft=2048,
            hop_length=512
        )
        
        assert result is False, "Should return False when no fingerprints exist"

    def test_check_fingerprints_exist_returns_true_for_existing(self):
        """Test that check_fingerprints_exist returns True when fingerprints exist with matching params."""
        from unittest.mock import MagicMock
        from src.database.repositories import VideoRepository
        
        # Create a mock session
        mock_session = MagicMock()
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 5  # 5 existing fingerprints
        
        repo = VideoRepository(mock_session)
        
        # Check for fingerprints - should return True
        result = repo.check_fingerprints_exist(
            video_id=1,
            sample_rate=22050,
            n_fft=2048,
            hop_length=512
        )
        
        assert result is True, "Should return True when fingerprints exist"

    def test_check_fingerprints_exist_returns_false_for_different_params(self):
        """Test that check_fingerprints_exist returns False when params don't match."""
        from unittest.mock import MagicMock
        from src.database.repositories import VideoRepository
        
        # Create a mock session
        mock_session = MagicMock()
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 0  # Different params, no match
        
        repo = VideoRepository(mock_session)
        
        # Check with different sample_rate - should return False
        result = repo.check_fingerprints_exist(
            video_id=1,
            sample_rate=44100,  # Different from existing 22050
            n_fft=2048,
            hop_length=512
        )
        
        assert result is False, "Should return False when parameters don't match"

    def test_fingerprint_data_includes_extraction_params(self):
        """Test that fingerprint data includes n_fft and hop_length parameters."""
        from src.core.audio_fingerprinting import AudioFingerprinter
        
        fingerprinter = AudioFingerprinter(sample_rate=22050, n_fft=2048, hop_length=512)
        
        # Verify the parameters are stored
        assert fingerprinter.n_fft == 2048
        assert fingerprinter.hop_length == 512
        assert fingerprinter.sample_rate == 22050
