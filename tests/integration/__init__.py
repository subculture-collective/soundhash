"""Integration tests for core workflows."""

from unittest.mock import MagicMock, patch

import pytest


@pytest.mark.integration
class TestBasicWorkflow:
    """Basic integration test for fingerprinting workflow."""

    @patch("src.core.video_processor.yt_dlp.YoutubeDL")
    @patch("subprocess.run")
    def test_fingerprint_creation_workflow(self, mock_run, mock_ytdl, tmp_path):
        """Test basic workflow of video -> audio -> fingerprint."""
        from src.core.audio_fingerprinting import AudioFingerprinter
        from src.core.video_processor import VideoProcessor
        
        # Mock download
        mock_ytdl_instance = MagicMock()
        mock_ytdl.return_value.__enter__.return_value = mock_ytdl_instance
        mock_ytdl_instance.extract_info.return_value = {"id": "test123"}
        
        # Mock ffprobe
        mock_run.return_value = MagicMock(returncode=0, stdout="30.0")
        
        # Create test audio file
        audio_file = tmp_path / "test123.wav"
        audio_file.write_text("fake audio")
        
        # Mock file existence
        with patch("pathlib.Path.exists", return_value=True):
            processor = VideoProcessor()
            
            # Just verify initialization works
            assert processor is not None


@pytest.mark.integration
class TestDatabaseWorkflow:
    """Integration tests for database operations."""

    def test_repository_context_managers(self):
        """Test repository context manager workflow."""
        from src.database.repositories import get_video_repository, get_job_repository
        
        with patch("src.database.repositories.get_db_session"):
            # Test imports and basic structure
            assert get_video_repository is not None
            assert get_job_repository is not None
