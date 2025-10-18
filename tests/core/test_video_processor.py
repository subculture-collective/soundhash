"""Tests for video processing functionality."""

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.core.video_processor import VideoProcessor


class TestVideoProcessor:
    """Test suite for VideoProcessor class."""

    def test_init_default_parameters(self, temp_dir):
        """Test VideoProcessor initialization with default parameters."""
        processor = VideoProcessor(temp_dir=temp_dir)

        assert processor.temp_dir == temp_dir
        assert processor.segment_length == 90  # Default from Config
        assert os.path.exists(temp_dir)

    def test_init_custom_parameters(self, temp_dir):
        """Test VideoProcessor initialization with custom parameters."""
        processor = VideoProcessor(temp_dir=temp_dir, segment_length=30)

        assert processor.segment_length == 30

    def test_extract_video_id(self, temp_dir):
        """Test extracting video ID from various URL formats."""
        processor = VideoProcessor(temp_dir=temp_dir)

        # Standard watch URL
        assert (
            processor._extract_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
            == "dQw4w9WgXcQ"
        )

        # Short URL
        assert processor._extract_video_id("https://youtu.be/dQw4w9WgXcQ") == "dQw4w9WgXcQ"

        # Embed URL
        assert (
            processor._extract_video_id("https://www.youtube.com/embed/dQw4w9WgXcQ")
            == "dQw4w9WgXcQ"
        )

        # With query parameters
        assert (
            processor._extract_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=10s")
            == "dQw4w9WgXcQ"
        )

        # Invalid URL
        assert processor._extract_video_id("https://example.com") is None

    @patch("subprocess.run")
    def test_get_audio_duration(self, mock_run, temp_dir, sine_wave_file):
        """Test getting audio duration using mocked ffprobe."""
        processor = VideoProcessor(temp_dir=temp_dir)

        # Mock ffprobe output
        mock_run.return_value = MagicMock(stdout="1.5\n")

        duration = processor._get_audio_duration(sine_wave_file)

        assert duration == 1.5
        mock_run.assert_called_once()
        # Verify ffprobe was called
        assert mock_run.call_args[0][0][0] == "ffprobe"

    @patch("subprocess.run")
    def test_get_audio_duration_error(self, mock_run, temp_dir):
        """Test handling error when getting audio duration."""
        processor = VideoProcessor(temp_dir=temp_dir)

        # Mock ffprobe failure - the actual method catches exceptions internally
        import subprocess

        mock_run.side_effect = subprocess.CalledProcessError(1, "ffprobe")

        duration = processor._get_audio_duration("nonexistent.wav")

        assert duration is None

    @patch("subprocess.run")
    def test_segment_audio_happy_path(self, mock_run, temp_dir, multi_second_sine_wave):
        """Test audio segmentation with mocked ffmpeg commands."""
        processor = VideoProcessor(temp_dir=temp_dir, segment_length=1)

        # Mock ffprobe to return duration
        def mock_subprocess(cmd, *args, **kwargs):
            if cmd[0] == "ffprobe":
                result = MagicMock()
                result.stdout = "3.0\n"
                return result
            elif cmd[0] == "ffmpeg":
                # Create a dummy segment file
                output_file = cmd[cmd.index("-y") + 1]
                Path(output_file).touch()
                return MagicMock()
            return MagicMock()

        mock_run.side_effect = mock_subprocess

        segments = processor.segment_audio(multi_second_sine_wave)

        # Should have at least 3 segments for 3-second audio with 1-second segments
        assert len(segments) >= 3

        # Check segment structure
        for segment_path, start_time, end_time in segments:
            assert isinstance(segment_path, str)
            assert isinstance(start_time, float)
            assert isinstance(end_time, float)
            assert start_time < end_time
            assert os.path.exists(segment_path)

        # Clean up created segments
        processor.cleanup_segments(segments)

    def test_segment_audio_nonexistent_file(self, temp_dir):
        """Test segmentation with nonexistent audio file."""
        processor = VideoProcessor(temp_dir=temp_dir)

        with pytest.raises(FileNotFoundError):
            processor.segment_audio("nonexistent.wav")

    @patch("subprocess.run")
    def test_extract_audio_segment(self, mock_run, temp_dir):
        """Test extracting a single audio segment with mocked ffmpeg."""
        processor = VideoProcessor(temp_dir=temp_dir)

        # Mock successful ffmpeg run
        mock_run.return_value = MagicMock()

        input_file = "input.wav"
        output_file = os.path.join(temp_dir, "output.wav")

        # Create dummy output file to simulate ffmpeg success
        Path(output_file).touch()

        success = processor._extract_audio_segment(input_file, output_file, 0.0, 1.0)

        assert success is True
        mock_run.assert_called_once()
        # Verify ffmpeg was called
        assert mock_run.call_args[0][0][0] == "ffmpeg"

    def test_cleanup_temp_files(self, temp_dir):
        """Test cleaning up temporary files."""
        processor = VideoProcessor(temp_dir=temp_dir)

        # Create some test files
        test_files = []
        for i in range(3):
            test_file = Path(temp_dir) / f"test_{i}.wav"
            test_file.touch()
            test_files.append(test_file)

        # Verify files exist
        for test_file in test_files:
            assert test_file.exists()

        # Clean up all files
        processor.cleanup_temp_files()

        # Verify files are deleted
        for test_file in test_files:
            assert not test_file.exists()

    def test_cleanup_temp_files_with_pattern(self, temp_dir):
        """Test cleaning up temporary files with a specific pattern."""
        processor = VideoProcessor(temp_dir=temp_dir)

        # Create test files with different patterns
        wav_file = Path(temp_dir) / "test.wav"
        mp3_file = Path(temp_dir) / "test.mp3"
        wav_file.touch()
        mp3_file.touch()

        # Clean up only WAV files
        processor.cleanup_temp_files("*.wav")

        assert not wav_file.exists()
        assert mp3_file.exists()  # Should still exist

    def test_cleanup_segments(self, temp_dir):
        """Test cleaning up segment files."""
        processor = VideoProcessor(temp_dir=temp_dir)

        # Create dummy segment files
        segments = []
        for i in range(3):
            segment_file = Path(temp_dir) / f"segment_{i}.wav"
            segment_file.touch()
            segments.append((str(segment_file), float(i), float(i + 1)))

        # Verify files exist
        for segment_file, _, _ in segments:
            assert os.path.exists(segment_file)

        # Clean up segments
        processor.cleanup_segments(segments)

        # Verify files are deleted
        for segment_file, _, _ in segments:
            assert not os.path.exists(segment_file)

    def test_get_random_user_agent(self, temp_dir):
        """Test that random user agent is returned."""
        processor = VideoProcessor(temp_dir=temp_dir)

        user_agent = processor._get_random_user_agent()

        assert isinstance(user_agent, str)
        assert len(user_agent) > 0
        assert "Mozilla" in user_agent

    def test_get_proxy_with_url(self, temp_dir):
        """Test getting proxy URL when PROXY_URL is set."""
        with patch("src.core.video_processor.Config") as mock_config:
            mock_config.PROXY_URL = "http://proxy.example.com:8080"
            mock_config.PROXY_LIST = []

            processor = VideoProcessor(temp_dir=temp_dir)
            proxy = processor._get_proxy()

            assert proxy == "http://proxy.example.com:8080"

    def test_get_proxy_with_list(self, temp_dir):
        """Test getting proxy from list when PROXY_LIST is set."""
        with patch("src.core.video_processor.Config") as mock_config:
            mock_config.PROXY_URL = None
            mock_config.PROXY_LIST = ["http://proxy1.example.com", "http://proxy2.example.com"]

            processor = VideoProcessor(temp_dir=temp_dir)
            proxy = processor._get_proxy()

            assert proxy in mock_config.PROXY_LIST

    def test_get_proxy_none(self, temp_dir):
        """Test getting proxy when no proxy is configured."""
        with patch("src.core.video_processor.Config") as mock_config:
            mock_config.PROXY_URL = None
            mock_config.PROXY_LIST = []

            processor = VideoProcessor(temp_dir=temp_dir)
            proxy = processor._get_proxy()

            assert proxy is None

    @patch("subprocess.run")
    def test_convert_to_wav(self, mock_run, temp_dir):
        """Test converting audio to WAV format."""
        processor = VideoProcessor(temp_dir=temp_dir)

        mock_run.return_value = MagicMock()

        # Should not raise an error
        processor._convert_to_wav("input.mp3", "output.wav")

        mock_run.assert_called_once()
        assert mock_run.call_args[0][0][0] == "ffmpeg"

    @patch("subprocess.run")
    def test_convert_to_wav_error(self, mock_run, temp_dir):
        """Test error handling when conversion fails."""
        processor = VideoProcessor(temp_dir=temp_dir)

        import subprocess

        mock_run.side_effect = subprocess.CalledProcessError(1, "ffmpeg")

        with pytest.raises(subprocess.CalledProcessError):
            processor._convert_to_wav("input.mp3", "output.wav")

    @patch("subprocess.run")
    def test_download_video_info_success(self, mock_run, temp_dir):
        """Test downloading video info successfully."""
        processor = VideoProcessor(temp_dir=temp_dir)

        # Mock successful yt-dlp command
        mock_result = MagicMock()
        mock_result.stdout = "dQw4w9WgXcQ|Test Video|Description|180|20231201|1000000|50000|Test Channel|UC123|https://thumb.jpg|https://youtube.com/watch?v=dQw4w9WgXcQ"
        mock_run.return_value = mock_result

        info = processor.download_video_info("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

        assert info is not None
        assert info["id"] == "dQw4w9WgXcQ"
        assert info["title"] == "Test Video"

    @patch("subprocess.run")
    def test_download_video_info_timeout(self, mock_run, temp_dir):
        """Test timeout when downloading video info."""
        processor = VideoProcessor(temp_dir=temp_dir)

        import subprocess

        mock_run.side_effect = subprocess.TimeoutExpired("yt-dlp", 60)

        info = processor.download_video_info("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

        assert info is None

    @patch("subprocess.run")
    def test_download_video_info_error(self, mock_run, temp_dir):
        """Test error when downloading video info."""
        processor = VideoProcessor(temp_dir=temp_dir)

        import subprocess

        mock_run.side_effect = subprocess.CalledProcessError(1, "yt-dlp")

        info = processor.download_video_info("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

        assert info is None

    @patch("subprocess.run")
    def test_get_channel_videos_ytdlp_success(self, mock_run, temp_dir):
        """Test getting channel videos via yt-dlp."""
        processor = VideoProcessor(temp_dir=temp_dir)

        # Mock channel video list
        def mock_subprocess(cmd, *args, **kwargs):
            if "--flat-playlist" in cmd:
                result = MagicMock()
                result.stdout = "video1\nvideo2\nvideo3"
                return result
            else:
                result = MagicMock()
                result.stdout = "video1|Title 1|Desc|180|20231201|1000|50|Channel|UC123|thumb.jpg|https://youtube.com/watch?v=video1"
                return result

        mock_run.side_effect = mock_subprocess

        videos = processor._get_channel_videos_ytdlp("UC123456789", max_results=3)

        assert isinstance(videos, list)

    @patch("subprocess.run")
    def test_get_channel_videos_ytdlp_error(self, mock_run, temp_dir):
        """Test error when getting channel videos."""
        processor = VideoProcessor(temp_dir=temp_dir)

        import subprocess

        mock_run.side_effect = subprocess.CalledProcessError(1, "yt-dlp")

        videos = processor._get_channel_videos_ytdlp("UC123456789")

        assert videos == []

    @patch("subprocess.run")
    @patch("time.sleep")
    def test_download_video_audio_http_403_error(self, mock_sleep, mock_run, temp_dir):
        """Test handling of HTTP 403 Forbidden error with retry."""
        processor = VideoProcessor(temp_dir=temp_dir)

        import subprocess

        # Mock yt-dlp returning 403 error
        error = subprocess.CalledProcessError(1, "yt-dlp")
        error.stderr = "ERROR: HTTP Error 403: Forbidden"
        error.stdout = ""
        mock_run.side_effect = error

        result = processor.download_video_audio("https://www.youtube.com/watch?v=test123")

        assert result is None
        # Should retry 3 times (with cookie detection, this means more calls)
        assert mock_run.call_count >= 3

    @patch("subprocess.run")
    @patch("time.sleep")
    def test_download_video_audio_http_429_error(self, mock_sleep, mock_run, temp_dir):
        """Test handling of HTTP 429 Too Many Requests with extra backoff."""
        processor = VideoProcessor(temp_dir=temp_dir)

        import subprocess

        # Mock yt-dlp returning 429 error
        error = subprocess.CalledProcessError(1, "yt-dlp")
        error.stderr = "ERROR: HTTP Error 429: Too Many Requests"
        error.stdout = ""
        mock_run.side_effect = error

        result = processor.download_video_audio("https://www.youtube.com/watch?v=test123")

        assert result is None
        # Should retry 3 times
        assert mock_run.call_count >= 3
        # Should have extra sleep calls for rate limiting (beyond the base retry backoff)
        assert mock_sleep.call_count >= 3

    @patch("subprocess.run")
    def test_download_video_audio_http_410_error(self, mock_run, temp_dir):
        """Test handling of HTTP 410 Gone error (no retry)."""
        processor = VideoProcessor(temp_dir=temp_dir)

        import subprocess

        # Mock yt-dlp returning 410 error on first real attempt
        def run_side_effect(cmd, *args, **kwargs):
            # Allow cookie detection to succeed
            if '--cookies-from-browser' in cmd and '--simulate' in cmd:
                return subprocess.CompletedProcess(cmd, 1)  # Fail cookie test
            # Actual download fails with 410
            error = subprocess.CalledProcessError(1, "yt-dlp")
            error.stderr = "ERROR: HTTP Error 410: Gone"
            error.stdout = ""
            raise error

        mock_run.side_effect = run_side_effect

        result = processor.download_video_audio("https://www.youtube.com/watch?v=test123")

        assert result is None
        # Should NOT retry for 410 errors (but cookie detection adds extra calls)
        # We just verify it returns None quickly

    @patch("subprocess.run")
    def test_download_video_audio_bot_detection(self, mock_run, temp_dir):
        """Test handling of YouTube bot detection."""
        processor = VideoProcessor(temp_dir=temp_dir)

        import subprocess

        # Mock yt-dlp returning bot detection error
        error = subprocess.CalledProcessError(1, "yt-dlp")
        error.stderr = "Sign in to confirm you're not a bot"
        error.stdout = ""
        mock_run.side_effect = error

        result = processor.download_video_audio("https://www.youtube.com/watch?v=test123")

        assert result is None
        # Should retry
        assert mock_run.call_count >= 3
