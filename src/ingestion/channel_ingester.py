import asyncio
import json
import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any

from config.logging_config import create_section_logger, get_progress_logger
from config.settings import Config
from src.core.audio_fingerprinting import AudioFingerprinter
from src.core.video_processor import VideoProcessor as CoreVideoProcessor
from src.database.connection import db_manager
from src.database.repositories import (
    JobRepository,
    VideoRepository,
    get_job_repository,
    get_video_repository,
)

if TYPE_CHECKING:
    from src.api.youtube_service import YouTubeAPIService

try:
    from src.api.youtube_service import YouTubeAPIService as _YouTubeAPIService

    YOUTUBE_API_AVAILABLE = True
    YouTubeAPIService = _YouTubeAPIService  # type: ignore[misc,assignment]
except ImportError:
    YOUTUBE_API_AVAILABLE = False


class ChannelIngester:
    """
    Handles ingestion of videos from YouTube channels and processing for fingerprinting.
    """

    def __init__(self, initialize_db: bool = True, youtube_service: Any | None = None) -> None:
        # Initialize YouTube API service if available
        self.youtube_service = youtube_service
        if not self.youtube_service and YOUTUBE_API_AVAILABLE:
            try:
                self.youtube_service = YouTubeAPIService()  # type: ignore[misc]
                self.logger = create_section_logger(__name__)
                self.logger.log_success("YouTube Data API service initialized")
            except Exception as e:
                self.logger = create_section_logger(__name__)
                self.logger.log_warning_box(f"Failed to initialize YouTube API service: {e}")
        else:
            self.logger = create_section_logger(__name__)

        # Use the core video processor for download/segmentation
        self.video_processor = CoreVideoProcessor(youtube_service=self.youtube_service)
        self.fingerprinter = AudioFingerprinter()
        self.target_channels = Config.TARGET_CHANNELS
        self._db_initialized = False

        # Initialize database (can be skipped for dry-run)
        if initialize_db:
            db_manager.initialize()
            self._db_initialized = True

    async def ingest_all_channels(
        self,
        channels_override: list[str] | None = None,
        max_videos: int | None = None,
        dry_run: bool = False,
    ) -> None:
        """Ingest videos from all configured channels or provided override list"""
        channels = channels_override or self.target_channels
        self.logger.info(f"🎯 Starting ingestion for {len(channels)} channels")

        # Create progress tracker
        progress = get_progress_logger(self.logger, len(channels), "Channel Ingestion")

        for _i, channel_id in enumerate(channels):
            if channel_id.strip():  # Skip empty channel IDs
                progress.update(increment=0, item_name=f"Channel {channel_id}")
                await self.ingest_channel(
                    channel_id.strip(), max_videos=max_videos, dry_run=dry_run
                )
                progress.update(increment=1)

        progress.complete()

    async def ingest_channel(
        self, channel_id: str, max_videos: int | None = None, dry_run: bool = False
    ) -> None:
        """
        Ingest videos from a specific channel.
        Creates channel and video records, then queues processing jobs.
        """
        self.logger.info(f"📺 Starting ingestion for channel: {channel_id}")

        try:
            # Warn about unlimited processing
            if max_videos is None:
                self.logger.log_warning_box(
                    f"Processing ALL videos for channel {channel_id}. This may take a very long time!"
                )

            # Get videos from channel via yt-dlp
            videos_info = self.video_processor.get_channel_videos(channel_id, max_videos)

            if not videos_info:
                self.logger.log_warning_box(f"No videos found for channel {channel_id}")
                return

            # Dry-run: just log summary and return without DB access
            if dry_run or not self._db_initialized:
                self.logger.info(
                    f"🔍 [DRY-RUN] Channel {channel_id}: found {len(videos_info)} videos"
                )
                for i, vi in enumerate(videos_info[:5], 1):
                    self.logger.info(f"   {i}. {vi.get('id')} | {vi.get('title')}")
                if len(videos_info) > 5:
                    self.logger.info(f"   ... and {len(videos_info) - 5} more videos")
                return

            # Proceed with DB operations
            video_repo = get_video_repository()
            job_repo = get_job_repository()

            # Get or create channel record
            channel = video_repo.get_channel_by_id(channel_id)
            if not channel:
                self.logger.info(f"Creating new channel record for {channel_id}")
                channel = video_repo.create_channel(
                    channel_id=channel_id,
                    channel_name=f"Channel {channel_id}",  # Will be updated with real name
                )

            # Update channel info with first video's channel data
            if (
                videos_info
                and channel.channel_name
                and not channel.channel_name.startswith("Channel ")
            ):
                first_video = videos_info[0]
                if first_video.get("channel"):
                    channel.channel_name = first_video["channel"]
                    video_repo.session.commit()

            new_videos = 0
            updated_videos = 0

            for video_info in videos_info:
                try:
                    # Check if video already exists
                    existing_video = video_repo.get_video_by_id(video_info["id"])

                    if existing_video:
                        # Update existing video if needed
                        if self._should_update_video(existing_video, video_info):
                            self._update_video_record(existing_video, video_info, video_repo)
                            updated_videos += 1
                    else:
                        # Create new video record
                        if dry_run:
                            self.logger.info(
                                f"[DRY-RUN] Would create video and job for {video_info['id']}"
                            )
                            continue

                        video_repo.create_video(
                            video_id=video_info["id"],
                            channel_id=int(channel.id),  # type: ignore[arg-type]
                            title=video_info.get("title"),
                            description=video_info.get("description"),
                            duration=(
                                float(video_info["duration"])
                                if video_info.get("duration")
                                else None
                            ),
                            view_count=video_info.get("view_count"),
                            like_count=video_info.get("like_count"),
                            upload_date=self._parse_upload_date(video_info.get("upload_date")),
                            url=video_info.get("webpage_url"),
                            thumbnail_url=video_info.get("thumbnail"),
                        )

                        # Create processing job for this video (idempotent)
                        if not job_repo.job_exists(
                            "video_process", video_info["id"], statuses=["pending", "running"]
                        ):
                            job_repo.create_job(
                                job_type="video_process",
                                target_id=video_info["id"],
                                parameters=json.dumps(
                                    {"url": video_info.get("webpage_url"), "channel_id": channel_id}
                                ),
                            )
                        else:
                            self.logger.debug(
                                f"Job already exists for video {video_info['id']}, skipping job creation"
                            )

                        new_videos += 1

                except Exception as e:
                    self.logger.error(
                        f"Error processing video {video_info.get('id', 'unknown')}: {str(e)}"
                    )
                    continue

            # Update channel last processed time
            channel.last_processed = datetime.utcnow()
            video_repo.session.commit()

            self.logger.info(
                f"Channel {channel_id} ingestion complete: {new_videos} new videos, {updated_videos} updated"
            )

        except Exception as e:
            self.logger.error(f"Error ingesting channel {channel_id}: {str(e)}")
            raise

    def _should_update_video(self, existing_video: Any, video_info: dict[str, Any]) -> bool:
        """Check if video record should be updated with new info"""
        # Update if view count or like count has changed significantly
        current_views = existing_video.view_count or 0
        new_views = video_info.get("view_count", 0) or 0

        if abs(new_views - current_views) > current_views * 0.1:  # 10% change
            return True

        # Update if not processed and now we have duration
        if (
            not existing_video.processed
            and video_info.get("duration")
            and not existing_video.duration
        ):
            return True

        return False

    def _update_video_record(
        self, video: Any, video_info: dict[str, Any], repo: VideoRepository
    ) -> None:
        """Update existing video record with new information"""
        video.view_count = video_info.get("view_count")
        video.like_count = video_info.get("like_count")
        if video_info.get("duration") and not video.duration:
            video.duration = video_info.get("duration")
        video.updated_at = datetime.utcnow()
        repo.session.commit()

    def _parse_upload_date(self, upload_date_str: str | None) -> datetime | None:
        """Parse upload date string from yt-dlp"""
        if not upload_date_str:
            return None
        try:
            # yt-dlp returns dates in YYYYMMDD format
            return datetime.strptime(upload_date_str, "%Y%m%d")
        except (ValueError, TypeError):
            return None


class VideoJobProcessor:
    """
    Processes individual videos for fingerprinting.
    Handles the complete pipeline from video to stored fingerprints.
    """

    def __init__(self) -> None:
        # Use the core video processor implementation
        self.video_processor = CoreVideoProcessor()
        self.fingerprinter = AudioFingerprinter()
        self.logger = logging.getLogger(__name__)

    async def process_pending_videos(self, batch_size: int = 5) -> None:
        """Process videos that are queued for processing"""
        job_repo = get_job_repository()
        video_repo = get_video_repository()

        while True:
            # Get pending jobs
            jobs = job_repo.get_pending_jobs("video_process", limit=batch_size)

            if not jobs:
                self.logger.info("No pending video processing jobs")
                break

            self.logger.info(f"Processing {len(jobs)} video jobs")

            for job in jobs:
                try:
                    await self.process_video_job(job, video_repo, job_repo)
                except Exception as e:
                    self.logger.error(f"Error processing job {job.id}: {str(e)}")
                    if job.id:
                        job_repo.update_job_status(job.id, "failed", error_message=str(e))

    async def process_video_job(
        self, job: Any, video_repo: VideoRepository, job_repo: JobRepository
    ) -> None:
        """Process a single video processing job"""
        job_repo.update_job_status(job.id, "running", 0.0, "Starting video processing")

        try:
            # Parse job parameters
            params = json.loads(job.parameters or "{}")
            video_url = params.get("url")
            video_id = job.target_id

            if not video_url:
                raise ValueError("No video URL in job parameters")

            # Get video record
            video = video_repo.get_video_by_id(video_id)
            if not video:
                raise ValueError(f"Video record not found: {video_id}")

            # Mark video as processing started
            video.processing_started = datetime.utcnow()
            video_repo.session.commit()

            job_repo.update_job_status(job.id, "running", 0.2, "Downloading and segmenting audio")

            # Process video and get segments
            segments = self.video_processor.process_video_for_fingerprinting(video_url)

            if not segments:
                raise ValueError("Failed to process video or no segments created")

            job_repo.update_job_status(
                job.id, "running", 0.5, f"Extracting fingerprints from {len(segments)} segments"
            )

            # Process each segment
            fingerprints_created = 0

            for i, (segment_file, start_time, end_time) in enumerate(segments):
                try:
                    # Extract fingerprint
                    fingerprint_data = self.fingerprinter.extract_fingerprint(segment_file)

                    # Store fingerprint in database
                    serialized_data = self.fingerprinter.serialize_fingerprint(fingerprint_data)

                    video_repo.create_fingerprint(
                        video_id=int(video.id),  # type: ignore[arg-type]
                        start_time=start_time,
                        end_time=end_time,
                        fingerprint_hash=fingerprint_data["fingerprint_hash"],
                        fingerprint_data=serialized_data,
                        confidence_score=fingerprint_data["confidence_score"],
                        peak_count=fingerprint_data["peak_count"],
                        segment_length=end_time - start_time,
                        sample_rate=fingerprint_data["sample_rate"],
                    )

                    fingerprints_created += 1

                    # Clean up segment file
                    import os

                    if os.path.exists(segment_file):
                        os.remove(segment_file)

                    # Update progress
                    progress_value = 0.5 + (0.4 * (i + 1) / len(segments))
                    job_repo.update_job_status(
                        job.id,
                        "running",
                        progress_value,
                        f"Processed segment {i+1}/{len(segments)}",
                    )

                except Exception as e:
                    self.logger.error(f"Error processing segment {start_time}-{end_time}: {str(e)}")
                    continue

            # Mark video as processed
            if video.id:
                video_repo.mark_video_processed(video.id, success=True)

            if job.id:
                job_repo.update_job_status(
                    job.id, "completed", 1.0, f"Created {fingerprints_created} fingerprints"
                )

            self.logger.info(
                f"Successfully processed video {video_id}: {fingerprints_created} fingerprints"
            )

        except Exception as e:
            # Mark video as failed
            video = video_repo.get_video_by_id(job.target_id)
            if video and video.id:
                video_repo.mark_video_processed(video.id, success=False, error_message=str(e))

            raise


async def main() -> None:
    """Main ingestion process"""
    logging.basicConfig(level=logging.INFO)

    ingester = ChannelIngester()
    processor = VideoJobProcessor()

    # First, ingest channel data
    await ingester.ingest_all_channels()

    # Then process videos
    await processor.process_pending_videos()


if __name__ == "__main__":
    asyncio.run(main())
