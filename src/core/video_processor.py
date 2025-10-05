import yt_dlp
import subprocess
import os
import tempfile
from typing import List, Tuple, Optional, Dict
from pathlib import Path
import logging
from config.settings import Config

class VideoProcessor:
    """
    Handles video download, audio extraction, and segmentation for audio fingerprinting.
    """
    
    def __init__(self, temp_dir: str = None):
        self.temp_dir = temp_dir or Config.TEMP_DIR
        self.segment_length = Config.SEGMENT_LENGTH_SECONDS
        
        # Ensure temp directory exists
        Path(self.temp_dir).mkdir(parents=True, exist_ok=True)
        
        # Configure yt-dlp options
        self.ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f'{self.temp_dir}/%(id)s.%(ext)s',
            'writeinfojson': True,
            'writethumbnail': False,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
                'preferredquality': '192',
            }],
            'quiet': True,
            'no_warnings': True,
        }
        
        self.logger = logging.getLogger(__name__)
    
    def download_video_info(self, url: str) -> Optional[Dict]:
        """
        Extract video metadata without downloading.
        Returns video information dictionary.
        """
        try:
            with yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True}) as ydl:
                info = ydl.extract_info(url, download=False)
                return {
                    'id': info.get('id'),
                    'title': info.get('title'),
                    'description': info.get('description'),
                    'duration': info.get('duration'),
                    'upload_date': info.get('upload_date'),
                    'view_count': info.get('view_count'),
                    'like_count': info.get('like_count'),
                    'channel': info.get('channel'),
                    'channel_id': info.get('channel_id'),
                    'thumbnail': info.get('thumbnail'),
                    'webpage_url': info.get('webpage_url'),
                }
        except Exception as e:
            self.logger.error(f"Error extracting video info from {url}: {str(e)}")
            return None
    
    def download_video_audio(self, url: str) -> Optional[str]:
        """
        Download video and extract audio.
        Returns path to the extracted audio file.
        """
        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                video_id = info['id']
                
                # Find the audio file
                audio_file = f"{self.temp_dir}/{video_id}.wav"
                if os.path.exists(audio_file):
                    return audio_file
                
                # Try alternative extensions
                for ext in ['.m4a', '.mp3', '.webm']:
                    alt_file = f"{self.temp_dir}/{video_id}{ext}"
                    if os.path.exists(alt_file):
                        # Convert to wav
                        wav_file = f"{self.temp_dir}/{video_id}.wav"
                        self._convert_to_wav(alt_file, wav_file)
                        return wav_file
                
                self.logger.error(f"Audio file not found after download: {video_id}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error downloading video {url}: {str(e)}")
            return None
    
    def _convert_to_wav(self, input_file: str, output_file: str):
        """Convert audio file to WAV format using ffmpeg"""
        try:
            subprocess.run([
                'ffmpeg', '-i', input_file,
                '-acodec', 'pcm_s16le',
                '-ar', str(Config.FINGERPRINT_SAMPLE_RATE),
                '-ac', '1',  # Mono
                '-y',  # Overwrite output file
                output_file
            ], check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Error converting {input_file} to WAV: {e}")
            raise
    
    def segment_audio(self, audio_file: str, segment_length: int = None) -> List[Tuple[str, float, float]]:
        """
        Split audio file into segments for processing.
        Returns list of (segment_file_path, start_time, end_time) tuples.
        """
        if not os.path.exists(audio_file):
            raise FileNotFoundError(f"Audio file not found: {audio_file}")
        
        segment_length = segment_length or self.segment_length
        segments = []
        
        try:
            # Get audio duration using ffprobe
            duration = self._get_audio_duration(audio_file)
            if duration is None:
                self.logger.error(f"Could not determine duration of {audio_file}")
                return []
            
            # Create segments
            start_time = 0
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
                    self.logger.warning(f"Failed to extract segment {start_time}-{end_time} from {audio_file}")
                
                start_time = end_time
            
            self.logger.info(f"Created {len(segments)} segments from {audio_file}")
            return segments
            
        except Exception as e:
            self.logger.error(f"Error segmenting audio file {audio_file}: {str(e)}")
            return []
    
    def _get_audio_duration(self, audio_file: str) -> Optional[float]:
        """Get audio duration in seconds using ffprobe"""
        try:
            result = subprocess.run([
                'ffprobe', '-v', 'quiet',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                audio_file
            ], capture_output=True, text=True, check=True)
            
            return float(result.stdout.strip())
        except (subprocess.CalledProcessError, ValueError) as e:
            self.logger.error(f"Error getting duration of {audio_file}: {e}")
            return None
    
    def _extract_audio_segment(self, input_file: str, output_file: str, 
                              start_time: float, duration: float) -> bool:
        """Extract a segment from audio file using ffmpeg"""
        try:
            subprocess.run([
                'ffmpeg', '-i', input_file,
                '-ss', str(start_time),
                '-t', str(duration),
                '-acodec', 'pcm_s16le',
                '-ar', str(Config.FINGERPRINT_SAMPLE_RATE),
                '-ac', '1',  # Mono
                '-y',  # Overwrite output file
                output_file
            ], check=True, capture_output=True)
            
            return os.path.exists(output_file)
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Error extracting segment: {e}")
            return False
    
    def cleanup_temp_files(self, file_pattern: str = None):
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
    
    def get_channel_videos(self, channel_id: str, max_results: int = 50) -> List[Dict]:
        """
        Get list of videos from a YouTube channel.
        Returns list of video information dictionaries.
        """
        try:
            channel_url = f"https://www.youtube.com/channel/{channel_id}/videos"
            
            opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': True,
                'playlistend': max_results,
            }
            
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(channel_url, download=False)
                
                if 'entries' not in info:
                    self.logger.warning(f"No videos found for channel {channel_id}")
                    return []
                
                videos = []
                for entry in info['entries']:
                    if entry:
                        video_url = f"https://www.youtube.com/watch?v={entry['id']}"
                        video_info = self.download_video_info(video_url)
                        if video_info:
                            videos.append(video_info)
                
                self.logger.info(f"Found {len(videos)} videos for channel {channel_id}")
                return videos
                
        except Exception as e:
            self.logger.error(f"Error getting videos for channel {channel_id}: {str(e)}")
            return []
    
    def process_video_for_fingerprinting(self, video_url: str) -> Optional[List[Tuple[str, float, float]]]:
        """
        Complete pipeline: download video, extract audio, and create segments.
        Returns list of (segment_file, start_time, end_time) or None if failed.
        """
        try:
            # Download audio
            audio_file = self.download_video_audio(video_url)
            if not audio_file:
                return None
            
            # Segment audio
            segments = self.segment_audio(audio_file)
            
            # Clean up the original audio file but keep segments
            os.remove(audio_file)
            
            return segments
            
        except Exception as e:
            self.logger.error(f"Error processing video {video_url}: {str(e)}")
            return None