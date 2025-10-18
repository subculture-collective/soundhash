import os
import random
import subprocess
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any

from config.logging_config import create_section_logger
from config.settings import Config

if TYPE_CHECKING:
    from src.api.youtube_service import YouTubeAPIService

try:
    from src.api.youtube_service import YouTubeAPIService as _YouTubeAPIService

    YOUTUBE_API_AVAILABLE = True
    YouTubeAPIService = _YouTubeAPIService  # type: ignore[misc,assignment]
except ImportError:
    YOUTUBE_API_AVAILABLE = False


class VideoProcessor:
    """
    Handles video download, audio extraction, and segmentation for audio fingerprinting.
    Uses YouTube Data API for metadata when available, falls back to yt-dlp for audio download.
    """

    def __init__(
        self,
        temp_dir: str = "./temp",
        segment_length: int | None = None,
        youtube_service: Any | None = None,
    ) -> None:
        """
        Initialize VideoProcessor.

        Args:
            temp_dir: Directory for temporary files
            segment_length: Length of audio segments in seconds (uses Config.SEGMENT_LENGTH_SECONDS if None)
            youtube_service: Optional YouTube API service instance
        """
        self.temp_dir = temp_dir
        self.segment_length = segment_length or Config.SEGMENT_LENGTH_SECONDS
        self.youtube_service = youtube_service

        # Create temp directory if it doesn't exist
        os.makedirs(self.temp_dir, exist_ok=True)

        # Setup yt-dlp configuration for audio download fallback
        self.ydl_opts: dict[str, Any] = {
            "format": "bestaudio/best",
            "outtmpl": f"{self.temp_dir}/%(id)s.%(ext)s",
            "extractaudio": True,
            "audioformat": "wav",
            "audioquality": 0,
        }
        self.logger = create_section_logger(__name__)

        # Try to initialize YouTube API service if not provided
        if not self.youtube_service and YOUTUBE_API_AVAILABLE:
            try:
                self.youtube_service = YouTubeAPIService()  # type: ignore[misc]
                self.logger.info("YouTube Data API service initialized")
            except Exception as e:
                self.logger.warning(f"Failed to initialize YouTube API service: {e}")
                self.logger.info("Will fall back to yt-dlp for all operations")

    def download_video_info(self, url: str) -> dict[str, Any] | None:
        """
        Extract video metadata without downloading using enhanced subprocess approach.
        Returns video information dictionary.
        """
        try:
            # Enhanced command with anti-detection measures
            cmd = [
                "yt-dlp",
                "--print",
                "%(id)s|%(title)s|%(description)s|%(duration)s|%(upload_date)s|%(view_count)s|%(like_count)s|%(channel)s|%(channel_id)s|%(thumbnail)s|%(webpage_url)s",
                "--no-playlist",
                "--user-agent",
                self._get_random_user_agent(),
                "--sleep-interval",
                "1",
                "--extractor-retries",
                "2",
            ]

            # Add proxy if configured
            if Config.USE_PROXY and (Config.PROXY_URL or Config.PROXY_LIST):
                proxy = self._get_proxy()
                if proxy:
                    cmd.extend(["--proxy", proxy])

            # Try to use cookies from browser if available
            try:
                # Test Chrome cookies first (only if file exists)
                chrome_paths = [
                    "/home/onnwee/.config/google-chrome",
                    "/home/onnwee/.config/chromium",
                ]
                for chrome_path in chrome_paths:
                    if os.path.exists(chrome_path):
                        test_cmd = [
                            "yt-dlp",
                            "--cookies-from-browser",
                            "chrome",
                            "--simulate",
                            "--quiet",
                            url,
                        ]
                        test_result = subprocess.run(test_cmd, capture_output=True, timeout=5)
                        if test_result.returncode == 0:
                            cmd.extend(["--cookies-from-browser", "chrome"])
                            break
                else:
                    # Try Firefox if Chrome not available or failed
                    firefox_paths = [
                        "/home/onnwee/.mozilla/firefox",
                        "/home/onnwee/snap/firefox/common/.mozilla/firefox",
                        "/home/onnwee/.var/app/org.mozilla.firefox/.mozilla/firefox",
                    ]
                    for firefox_path in firefox_paths:
                        if os.path.exists(firefox_path):
                            test_cmd = [
                                "yt-dlp",
                                "--cookies-from-browser",
                                "firefox",
                                "--simulate",
                                "--quiet",
                                url,
                            ]
                            test_result = subprocess.run(test_cmd, capture_output=True, timeout=5)
                            if test_result.returncode == 0:
                                cmd.extend(["--cookies-from-browser", "firefox"])
                                break
            except:
                # Continue without browser cookies if they're not available
                self.logger.debug("No browser cookies available or accessible")

            cmd.append(url)

            result = subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=60)

            # Parse the output
            if result.stdout.strip():
                parts = result.stdout.strip().split("|")
                if len(parts) >= 11:
                    return {
                        "id": parts[0] if parts[0] != "NA" else None,
                        "title": parts[1] if parts[1] != "NA" else None,
                        "description": parts[2] if parts[2] != "NA" else None,
                        "duration": (
                            int(parts[3]) if parts[3] != "NA" and parts[3].isdigit() else None
                        ),
                        "upload_date": parts[4] if parts[4] != "NA" else None,
                        "view_count": (
                            int(parts[5]) if parts[5] != "NA" and parts[5].isdigit() else None
                        ),
                        "like_count": (
                            int(parts[6]) if parts[6] != "NA" and parts[6].isdigit() else None
                        ),
                        "channel": parts[7] if parts[7] != "NA" else None,
                        "channel_id": parts[8] if parts[8] != "NA" else None,
                        "thumbnail": parts[9] if parts[9] != "NA" else None,
                        "webpage_url": parts[10] if parts[10] != "NA" else None,
                    }
            return None
        except subprocess.CalledProcessError as e:
            self.logger.error(f"yt-dlp command failed for {url}: {e}")
            if e.stderr:
                self.logger.error(f"yt-dlp stderr: {e.stderr}")
            return None
        except subprocess.TimeoutExpired:
            self.logger.error(f"yt-dlp command timed out for {url}")
            return None
        except Exception as e:
            self.logger.error(f"Error extracting video info from {url}: {str(e)}")
            return None

    def download_video_audio(self, url: str, max_retries: int = 3) -> str | None:
        """
        Download video and extract audio with enhanced anti-detection measures.
        Downloads audio in best available format, then converts to WAV separately.
        Returns path to the extracted audio file.
        """
        # Extract video ID from URL
        video_id = url.split("v=")[-1].split("&")[0] if "v=" in url else url.split("/")[-1]
        wav_file = Path(self.temp_dir) / f"{video_id}.wav"

        for attempt in range(max_retries):
            try:
                self.logger.info(
                    f"Downloading audio from: {url} (attempt {attempt + 1}/{max_retries})"
                )

                # Add random delay between attempts to avoid rate limiting
                if attempt > 0:
                    delay = random.uniform(5, 15) + (attempt * 2)  # Exponential backoff with jitter
                    self.logger.info(f"Waiting {delay:.1f} seconds before retry...")
                    time.sleep(delay)

                downloaded_file = Path(self.temp_dir) / f"{video_id}.%(ext)s"

                # Enhanced yt-dlp command with anti-detection measures
                cmd = [
                    "yt-dlp",
                    "-f",
                    "bestaudio",  # best audio format available
                    "-o",
                    str(downloaded_file),  # output template
                    "--user-agent",
                    self._get_random_user_agent(),  # Random user agent
                    "--sleep-interval",
                    "1",  # Sleep between downloads
                    "--max-sleep-interval",
                    "3",  # Maximum sleep interval
                    "--extractor-retries",
                    "3",  # Retry extraction on failure
                    "--fragment-retries",
                    "3",  # Retry fragments on failure
                    "--retry-sleep",
                    "exp=1:5",  # Exponential backoff for retries
                ]

                # Add proxy if configured
                if Config.USE_PROXY and (Config.PROXY_URL or Config.PROXY_LIST):
                    proxy = self._get_proxy()
                    if proxy:
                        cmd.extend(["--proxy", proxy])
                        self.logger.debug(f"Using proxy: {proxy}")

                # Configure extractor args and cookies (settings-driven > cookies file > auto-detect)
                if Config.YT_PLAYER_CLIENT:
                    cmd.extend(
                        ["--extractor-args", f"youtube:player_client={Config.YT_PLAYER_CLIENT}"]
                    )

                cookies_configured = False

                # Use explicit cookies file if provided
                if getattr(Config, "YT_COOKIES_FILE", None) and os.path.exists(
                    str(Config.YT_COOKIES_FILE)
                ):
                    cmd.extend(["--cookies", str(Config.YT_COOKIES_FILE)])
                    cookies_configured = True
                    self.logger.debug(f"Using cookies file: {Config.YT_COOKIES_FILE}")

                # Use explicit cookies-from-browser if provided
                elif getattr(Config, "YT_COOKIES_FROM_BROWSER", None):
                    browser_arg = str(Config.YT_COOKIES_FROM_BROWSER)
                    if getattr(Config, "YT_BROWSER_PROFILE", None):
                        browser_arg = (
                            f"{Config.YT_COOKIES_FROM_BROWSER}:{Config.YT_BROWSER_PROFILE}"
                        )
                    cmd.extend(["--cookies-from-browser", browser_arg])
                    cookies_configured = True
                    self.logger.debug(f"Using cookies from browser: {browser_arg}")

                # Fallback auto-detection of available browsers
                if not cookies_configured:
                    try:
                        for browser in ["chrome", "chromium", "brave", "edge", "firefox"]:
                            test_cmd = [
                                "yt-dlp",
                                "--cookies-from-browser",
                                browser,
                                "--simulate",
                                "--quiet",
                                url,
                            ]
                            test_result = subprocess.run(test_cmd, capture_output=True, timeout=5)
                            if test_result.returncode == 0:
                                cmd.extend(["--cookies-from-browser", browser])
                                self.logger.debug(f"Using {browser} cookies (auto)")
                                cookies_configured = True
                                break
                    except Exception:
                        self.logger.debug("Auto-detect cookies-from-browser failed")

                # Append URL last
                cmd.append(url)

                self.logger.debug(
                    f"Running yt-dlp command: {' '.join(cmd[:8])}..."
                )  # Don't log full command with user agent
                subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=600)

                # Find the actual downloaded file
                actual_file = None
                for file_path in Path(self.temp_dir).glob(f"{video_id}.*"):
                    if file_path.suffix.lower() in [
                        ".webm",
                        ".m4a",
                        ".mp3",
                        ".opus",
                        ".aac",
                        ".mp4",
                    ]:
                        actual_file = file_path
                        break

                if not actual_file or not actual_file.exists():
                    self.logger.error(f"Downloaded audio file not found in: {self.temp_dir}")
                    if attempt < max_retries - 1:
                        continue
                    return None

                self.logger.info(f"Downloaded audio file: {actual_file}")

                # Convert to WAV using ffmpeg
                self.logger.info(f"Converting to WAV: {wav_file}")
                self._convert_to_wav(str(actual_file), str(wav_file))

                # Clean up original downloaded file
                actual_file.unlink()

                if wav_file.exists():
                    self.logger.info(f"Successfully processed audio: {wav_file}")
                    return str(wav_file)
                else:
                    self.logger.error(f"WAV conversion failed: {wav_file}")
                    if attempt < max_retries - 1:
                        continue
                    return None

            except subprocess.CalledProcessError as e:
                self.logger.error(f"yt-dlp command failed (attempt {attempt + 1}): {e}")
                if e.stderr:
                    self.logger.error(f"yt-dlp stderr: {e.stderr}")
                    err_text = (
                        e.stderr
                        if isinstance(e.stderr, str)
                        else e.stderr.decode("utf-8", errors="ignore")
                    )
                    if "Sign in to confirm you’re not a bot" in err_text or "not a bot" in err_text:
                        self.logger.error(
                            "YouTube requested sign-in to confirm you're not a bot. Remediation options: "
                            "1) Set YT_COOKIES_FILE in .env to a Netscape cookies.txt exported from your browser; "
                            "2) Set YT_COOKIES_FROM_BROWSER (e.g., chrome|chromium|firefox) and optionally YT_BROWSER_PROFILE; "
                            "3) Configure a proxy via USE_PROXY/PROXY_URL; 4) Retry later."
                        )
                if e.stdout:
                    self.logger.error(f"yt-dlp stdout: {e.stdout}")

                # Check if it's a 403 error or similar that might benefit from retry
                if "403" in str(e.stderr) or "Forbidden" in str(e.stderr):
                    if attempt < max_retries - 1:
                        self.logger.info("Got 403 error, will retry with different parameters...")
                        continue

                if attempt == max_retries - 1:
                    return None

            except subprocess.TimeoutExpired:
                self.logger.error(f"yt-dlp command timed out (attempt {attempt + 1})")
                if attempt < max_retries - 1:
                    continue
                return None

            except Exception as e:
                self.logger.error(
                    f"Error downloading video {url} (attempt {attempt + 1}): {str(e)}"
                )
                if attempt < max_retries - 1:
                    continue
                return None

        return None

    def _get_random_user_agent(self) -> str:
        """Get a random user agent to avoid detection"""
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:120.0) Gecko/20100101 Firefox/120.0",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ]
        return random.choice(user_agents)

    def _get_proxy(self) -> str | None:
        """Get a proxy URL if configured"""
        if Config.PROXY_URL:
            return Config.PROXY_URL
        elif Config.PROXY_LIST:
            # Filter out empty strings
            valid_proxies = [p.strip() for p in Config.PROXY_LIST if p.strip()]
            if valid_proxies:
                return random.choice(valid_proxies)
        return None

    def _convert_to_wav(self, input_file: str, output_file: str) -> None:
        """Convert audio file to WAV format using ffmpeg"""
        try:
            subprocess.run(
                [
                    "ffmpeg",
                    "-i",
                    input_file,
                    "-acodec",
                    "pcm_s16le",
                    "-ar",
                    str(Config.FINGERPRINT_SAMPLE_RATE),
                    "-ac",
                    "1",  # Mono
                    "-y",  # Overwrite output file
                    output_file,
                ],
                check=True,
                capture_output=True,
            )
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Error converting {input_file} to WAV: {e}")
            raise

    def segment_audio(
        self, audio_file: str, segment_length: int | None = None
    ) -> list[tuple[str, float, float]]:
        """
        Split audio file into segments for processing.
        Returns list of (segment_file_path, start_time, end_time) tuples.
        """
        if not os.path.exists(audio_file):
            raise FileNotFoundError(f"Audio file not found: {audio_file}")

        segment_length = segment_length or self.segment_length
        segments: list[tuple[str, float, float]] = []

        try:
            # Get audio duration using ffprobe
            duration = self._get_audio_duration(audio_file)
            if duration is None:
                self.logger.error(f"Could not determine duration of {audio_file}")
                return []

            # Create segments
            start_time: float = 0.0
            segment_id = 0

            while start_time < duration:
                end_time = min(start_time + segment_length, duration)

                # Create segment file path
                base_name = Path(audio_file).stem
                segment_file = f"{self.temp_dir}/{base_name}_segment_{segment_id:04d}.wav"

                # Extract segment using ffmpeg
                success = self._extract_audio_segment(
                    audio_file, segment_file, start_time, end_time - start_time
                )

                if success:
                    segments.append((segment_file, start_time, end_time))
                    segment_id += 1
                else:
                    self.logger.warning(
                        f"Failed to extract segment {start_time}-{end_time} from {audio_file}"
                    )

                start_time = end_time

            self.logger.info(f"Created {len(segments)} segments from {audio_file}")
            return segments

        except Exception as e:
            self.logger.error(f"Error segmenting audio file {audio_file}: {str(e)}")
            return []

    def _get_audio_duration(self, audio_file: str) -> float | None:
        """Get audio duration in seconds using ffprobe"""
        try:
            result = subprocess.run(
                [
                    "ffprobe",
                    "-v",
                    "quiet",
                    "-show_entries",
                    "format=duration",
                    "-of",
                    "default=noprint_wrappers=1:nokey=1",
                    audio_file,
                ],
                capture_output=True,
                text=True,
                check=True,
            )

            return float(result.stdout.strip())
        except (subprocess.CalledProcessError, ValueError) as e:
            self.logger.error(f"Error getting duration of {audio_file}: {e}")
            return None

    def _extract_audio_segment(
        self, input_file: str, output_file: str, start_time: float, duration: float
    ) -> bool:
        """Extract a segment from audio file using ffmpeg"""
        try:
            subprocess.run(
                [
                    "ffmpeg",
                    "-i",
                    input_file,
                    "-ss",
                    str(start_time),
                    "-t",
                    str(duration),
                    "-acodec",
                    "pcm_s16le",
                    "-ar",
                    str(Config.FINGERPRINT_SAMPLE_RATE),
                    "-ac",
                    "1",  # Mono
                    "-y",  # Overwrite output file
                    output_file,
                ],
                check=True,
                capture_output=True,
            )

            return os.path.exists(output_file)

        except subprocess.CalledProcessError as e:
            self.logger.error(f"Error extracting segment: {e}")
            return False

    def cleanup_temp_files(self, file_pattern: str | None = None) -> None:
        """Clean up temporary files"""
        try:
            if file_pattern:
                # Clean specific pattern
                for file_path in Path(self.temp_dir).glob(file_pattern):
                    file_path.unlink()
            else:
                # Clean all files in temp directory
                for file_path in Path(self.temp_dir).iterdir():
                    if file_path.is_file():
                        file_path.unlink()

            self.logger.info(f"Cleaned up temporary files: {file_pattern or 'all'}")

        except Exception as e:
            self.logger.error(f"Error cleaning up temp files: {str(e)}")

    def get_channel_videos(
        self, channel_id: str, max_results: int | None = None
    ) -> list[dict[str, Any]]:
        """
        Get list of videos from a YouTube channel using Data API when available,
        fallback to yt-dlp subprocess approach.
        Returns list of video information dictionaries.
        """
        # Try YouTube Data API first
        if self.youtube_service:
            try:
                videos = self.youtube_service.get_channel_videos(channel_id, max_results)
                if videos:
                    self.logger.info(
                        f"Retrieved {len(videos)} videos via YouTube Data API for channel {channel_id}"
                    )
                    return videos
            except Exception as e:
                self.logger.warning(f"YouTube Data API failed for channel {channel_id}: {e}")

        # Fallback to yt-dlp subprocess
        return self._get_channel_videos_ytdlp(channel_id, max_results)

    def process_video_for_fingerprinting(
        self, video_url: str, cleanup_segments: bool | None = None
    ) -> list[tuple[str, float, float]] | None:
        """
        Complete pipeline: download video, extract audio, and create segments.
        Returns list of (segment_file, start_time, end_time) or None if failed.

        Args:
            video_url: URL of the video to process
            cleanup_segments: Whether to clean up segment files after processing.
                             If None, uses Config.CLEANUP_SEGMENTS_AFTER_PROCESSING
        """
        audio_file = None
        segments = []

        try:
            # Download audio
            audio_file = self.download_video_audio(video_url)
            if not audio_file:
                return None

            # Segment audio
            segments = self.segment_audio(audio_file)

            if not segments:
                return None

            # Determine cleanup behavior

            # This is where fingerprinting would happen - for now just return the segments
            # In a real implementation, you'd process each segment for fingerprinting here
            self.logger.info(f"Created {len(segments)} segments for fingerprinting")

            # Clean up based on configuration
            if not Config.KEEP_ORIGINAL_AUDIO and audio_file and os.path.exists(audio_file):
                os.remove(audio_file)
                self.logger.info(f"Removed original audio file: {audio_file}")

            return segments

        except Exception as e:
            self.logger.error(f"Error processing video {video_url}: {str(e)}")

            # Clean up on error
            if audio_file and os.path.exists(audio_file):
                os.remove(audio_file)
            for segment_file, _, _ in segments:
                if os.path.exists(segment_file):
                    os.remove(segment_file)

            return None

    def cleanup_segments(self, segments: list[tuple[str, float, float]]) -> None:
        """
        Clean up segment files after processing.

        Args:
            segments: List of (segment_file, start_time, end_time) tuples
        """
        try:
            for segment_file, _, _ in segments:
                if os.path.exists(segment_file):
                    os.remove(segment_file)
                    self.logger.debug(f"Removed segment file: {segment_file}")

            self.logger.info(f"Cleaned up {len(segments)} segment files")

        except Exception as e:
            self.logger.error(f"Error cleaning up segment files: {str(e)}")

    def _extract_video_id(self, url: str) -> str | None:
        """Extract YouTube video ID from URL"""
        try:
            if "v=" in url:
                return url.split("v=")[1].split("&")[0]
            elif "youtu.be/" in url:
                return url.split("youtu.be/")[1].split("?")[0]
            elif "/embed/" in url:
                return url.split("/embed/")[1].split("?")[0]
            return None
        except:
            return None

    def _download_video_info_ytdlp(self, url: str) -> dict[str, Any] | None:
        """Fallback method using yt-dlp subprocess for video info"""
        try:
            # Use subprocess to get video info with cookies from browser to avoid bot detection
            cmd = [
                "yt-dlp",
                "--print",
                "%(id)s|%(title)s|%(description)s|%(duration)s|%(upload_date)s|%(view_count)s|%(like_count)s|%(channel)s|%(channel_id)s|%(thumbnail)s|%(webpage_url)s",
                "--no-playlist",
            ]

            # Try to use cookies from browser if available
            try:
                subprocess.run(
                    [
                        "yt-dlp",
                        "--cookies-from-browser",
                        "chrome",
                        "--simulate",
                        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                    ],
                    check=True,
                    capture_output=True,
                    timeout=10,
                )
                cmd.extend(["--cookies-from-browser", "chrome"])
            except:
                pass

            cmd.append(url)

            result = subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=30)

            # Parse the output
            if result.stdout.strip():
                parts = result.stdout.strip().split("|")
                if len(parts) >= 11:
                    return {
                        "id": parts[0] if parts[0] != "NA" else None,
                        "title": parts[1] if parts[1] != "NA" else None,
                        "description": parts[2] if parts[2] != "NA" else None,
                        "duration": (
                            int(parts[3]) if parts[3] != "NA" and parts[3].isdigit() else None
                        ),
                        "upload_date": parts[4] if parts[4] != "NA" else None,
                        "view_count": (
                            int(parts[5]) if parts[5] != "NA" and parts[5].isdigit() else None
                        ),
                        "like_count": (
                            int(parts[6]) if parts[6] != "NA" and parts[6].isdigit() else None
                        ),
                        "channel": parts[7] if parts[7] != "NA" else None,
                        "channel_id": parts[8] if parts[8] != "NA" else None,
                        "thumbnail": parts[9] if parts[9] != "NA" else None,
                        "webpage_url": parts[10] if parts[10] != "NA" else None,
                    }
            return None
        except subprocess.CalledProcessError as e:
            self.logger.error(f"yt-dlp command failed for {url}: {e}")
            if e.stderr:
                self.logger.error(f"yt-dlp stderr: {e.stderr}")
            return None
        except subprocess.TimeoutExpired:
            self.logger.error(f"yt-dlp command timed out for {url}")
            return None
        except Exception as e:
            self.logger.error(f"Error extracting video info from {url}: {str(e)}")
            return None

    def _get_channel_videos_ytdlp(
        self, channel_id: str, max_results: int | None = None
    ) -> list[dict[str, Any]]:
        """Fallback method using yt-dlp subprocess for channel videos"""
        try:
            channel_url = f"https://www.youtube.com/channel/{channel_id}/videos"

            # Use simple subprocess approach with browser cookies to avoid bot detection
            self.logger.info(f"Getting videos from channel: {channel_url}")

            cmd = ["yt-dlp", "--flat-playlist", "--print", "%(id)s"]

            # Only add playlist-end if we have a limit
            if max_results is not None and max_results != float("inf"):
                cmd.extend(["--playlist-end", str(max_results)])

            # Try to use cookies from browser if available
            try:
                subprocess.run(
                    [
                        "yt-dlp",
                        "--cookies-from-browser",
                        "chrome",
                        "--simulate",
                        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                    ],
                    check=True,
                    capture_output=True,
                    timeout=10,
                )
                cmd.extend(["--cookies-from-browser", "chrome"])
            except:
                pass

            cmd.append(channel_url)
            result = subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=60)

            video_ids = result.stdout.strip().split("\n") if result.stdout.strip() else []
            self.logger.info(f"Found {len(video_ids)} video IDs for channel {channel_id}")

            # Get video info for each ID
            videos = []
            for video_id in video_ids:
                if video_id:
                    video_url = f"https://www.youtube.com/watch?v={video_id}"
                    video_info = self.download_video_info(video_url)
                    if video_info:
                        videos.append(video_info)

            self.logger.info(
                f"Successfully processed {len(videos)} videos for channel {channel_id}"
            )
            return videos

        except subprocess.CalledProcessError as e:
            self.logger.error(f"yt-dlp command failed for channel {channel_id}: {e}")
            if e.stderr:
                self.logger.error(f"yt-dlp stderr: {e.stderr}")
            return []
        except Exception as e:
            self.logger.error(f"Error getting videos for channel {channel_id}: {str(e)}")
            return []
