"""Video repository for database operations."""

import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import and_, func, or_, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from ..models import AudioFingerprint, Channel, MatchResult, Video
from .helpers import db_retry

logger = logging.getLogger(__name__)


class VideoRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    @db_retry()
    def create_channel(
        self, channel_id: str, channel_name: str | None = None, description: str | None = None
    ) -> Channel:
        """Create a new channel record with retry on transient errors"""
        try:
            channel = Channel(
                channel_id=channel_id, channel_name=channel_name, description=description
            )
            self.session.add(channel)
            self.session.commit()
            logger.debug(f"Created channel: {channel_id}")
            return channel
        except (IntegrityError, OperationalError, DBAPIError) as e:
            logger.error(f"Failed to create channel {channel_id}: {e}")
            raise

    @db_retry()
    def get_channel_by_id(self, channel_id: str) -> Channel | None:
        """Get channel by YouTube channel ID with retry on transient errors"""
        try:
            return self.session.query(Channel).filter(Channel.channel_id == channel_id).first()
        except (OperationalError, DBAPIError) as e:
            logger.error(f"Failed to get channel {channel_id}: {e}")
            raise

    @db_retry()
    def create_video(
        self,
        video_id: str,
        channel_id: int,
        title: str | None = None,
        duration: float | None = None,
        url: str | None = None,
        **kwargs: Any,
    ) -> Video:
        """Create a new video record with retry on transient errors"""
        try:
            video = Video(
                video_id=video_id,
                channel_id=channel_id,
                title=title,
                duration=duration,  # type: ignore[arg-type]
                url=url,
                **kwargs,
            )
            self.session.add(video)
            self.session.commit()
            logger.debug(f"Created video: {video_id}")
            return video
        except (IntegrityError, OperationalError, DBAPIError) as e:
            logger.error(f"Failed to create video {video_id}: {e}")
            raise

    @db_retry()
    def get_video_by_id(self, video_id: str) -> Video | None:
        """Get video by YouTube video ID with retry on transient errors"""
        try:
            return self.session.query(Video).filter(Video.video_id == video_id).first()
        except (OperationalError, DBAPIError) as e:
            logger.error(f"Failed to get video {video_id}: {e}")
            raise

    @db_retry()
    def get_unprocessed_videos(self, limit: int = 100) -> list[Video]:
        """Get videos that haven't been processed yet with retry on transient errors"""
        try:
            return self.session.query(Video).filter(~Video.processed).limit(limit).all()
        except (OperationalError, DBAPIError) as e:
            logger.error(f"Failed to get unprocessed videos: {e}")
            raise

    @db_retry()
    def mark_video_processed(
        self, video_id: int, success: bool = True, error_message: str | None = None
    ) -> None:
        """Mark a video as processed with retry on transient errors"""
        try:
            video = self.session.get(Video, video_id)
            if video:
                video.processed = success
                video.processing_completed = datetime.now(timezone.utc)
                if error_message:
                    video.processing_error = error_message
                self.session.commit()
                logger.debug(f"Marked video {video_id} as processed: {success}")
            else:
                logger.warning(f"Video {video_id} not found when marking as processed")
        except (OperationalError, DBAPIError) as e:
            logger.error(f"Failed to mark video {video_id} as processed: {e}")
            raise

    @db_retry()
    def create_fingerprint(
        self,
        video_id: int,
        start_time: float,
        end_time: float,
        fingerprint_hash: str,
        fingerprint_data: bytes,
        **kwargs: Any,
    ) -> AudioFingerprint:
        """Create a new audio fingerprint with retry on transient errors"""
        try:
            fingerprint = AudioFingerprint(
                video_id=video_id,
                start_time=start_time,  # type: ignore[arg-type]
                end_time=end_time,  # type: ignore[arg-type]
                fingerprint_hash=fingerprint_hash,
                fingerprint_data=fingerprint_data,
                **kwargs,
            )
            self.session.add(fingerprint)
            self.session.commit()
            logger.debug(f"Created fingerprint for video {video_id}: {fingerprint_hash}")
            return fingerprint
        except (IntegrityError, OperationalError, DBAPIError) as e:
            logger.error(f"Failed to create fingerprint for video {video_id}: {e}")
            raise

    @db_retry()
    def create_fingerprints_batch(
        self, fingerprints_data: list[dict[str, Any]]
    ) -> list[AudioFingerprint]:
        """
        Create multiple audio fingerprints in a single transaction.

        Args:
            fingerprints_data: List of dictionaries containing fingerprint data.
                Each dict should have keys: video_id, start_time, end_time,
                fingerprint_hash, fingerprint_data, and optional kwargs.

        Returns:
            List of created AudioFingerprint objects

        Example:
            fingerprints_data = [
                {
                    'video_id': 1,
                    'start_time': 0.0,
                    'end_time': 10.0,
                    'fingerprint_hash': 'abc123',
                    'fingerprint_data': b'...',
                    'confidence_score': 0.95,
                    'peak_count': 42
                },
                ...
            ]
        """
        try:
            if not fingerprints_data:
                return []

            fingerprints = []
            for fp_data in fingerprints_data:
                fingerprint = AudioFingerprint(
                    video_id=fp_data["video_id"],
                    start_time=fp_data["start_time"],  # type: ignore[arg-type]
                    end_time=fp_data["end_time"],  # type: ignore[arg-type]
                    fingerprint_hash=fp_data["fingerprint_hash"],
                    fingerprint_data=fp_data["fingerprint_data"],
                    confidence_score=fp_data.get("confidence_score"),
                    peak_count=fp_data.get("peak_count"),
                    sample_rate=fp_data.get("sample_rate"),
                    segment_length=fp_data.get("segment_length"),
                    n_fft=fp_data.get("n_fft", 2048),
                    hop_length=fp_data.get("hop_length", 512),
                )
                fingerprints.append(fingerprint)

            self.session.bulk_save_objects(fingerprints, return_defaults=True)
            self.session.commit()
            logger.debug(f"Batch created {len(fingerprints)} fingerprints")
            return fingerprints
        except (IntegrityError, OperationalError, DBAPIError) as e:
            logger.error(f"Failed to batch create fingerprints: {e}")
            raise

    @db_retry()
    def check_fingerprints_exist(
        self,
        video_id: int,
        sample_rate: int,
        n_fft: int,
        hop_length: int,
    ) -> bool:
        """
        Check if fingerprints already exist for a video with matching extraction parameters.
        
        This enables fingerprint reuse when parameters haven't changed, avoiding redundant work.
        
        Args:
            video_id: ID of the video to check
            sample_rate: Sample rate used for audio processing
            n_fft: FFT window size
            hop_length: Hop length for STFT
            
        Returns:
            True if fingerprints exist with matching parameters, False otherwise
        """
        try:
            count = (
                self.session.query(AudioFingerprint)
                .filter(
                    AudioFingerprint.video_id == video_id,
                    AudioFingerprint.sample_rate == sample_rate,
                    AudioFingerprint.n_fft == n_fft,
                    AudioFingerprint.hop_length == hop_length,
                )
                .count()
            )
            return count > 0
        except (OperationalError, DBAPIError) as e:
            logger.error(f"Failed to check fingerprint existence for video {video_id}: {e}")
            raise

    @db_retry()
    def find_matching_fingerprints(self, fingerprint_hash: str) -> list[AudioFingerprint]:
        """Find fingerprints with matching hash with retry on transient errors"""
        try:
            return (
                self.session.query(AudioFingerprint)
                .filter(AudioFingerprint.fingerprint_hash == fingerprint_hash)
                .all()
            )
        except (OperationalError, DBAPIError) as e:
            logger.error(f"Failed to find matching fingerprints for hash {fingerprint_hash}: {e}")
            raise

    @db_retry()
    def create_match_result(
        self,
        query_fp_id: int,
        matched_fp_id: int,
        similarity_score: float,
        query_source: str | None = None,
        query_url: str | None = None,
        query_user: str | None = None,
    ) -> MatchResult:
        """Create a match result record with retry on transient errors"""
        try:
            match = MatchResult(
                query_fingerprint_id=query_fp_id,
                matched_fingerprint_id=matched_fp_id,
                similarity_score=similarity_score,  # type: ignore[arg-type]
                query_source=query_source,
                query_url=query_url,
                query_user=query_user,
            )
            self.session.add(match)
            self.session.commit()
            logger.debug(f"Created match result: query={query_fp_id}, matched={matched_fp_id}")
            return match
        except (IntegrityError, OperationalError, DBAPIError) as e:
            logger.error(f"Failed to create match result: {e}")
            raise

    @db_retry()
    def create_match_results_batch(self, matches_data: list[dict[str, Any]]) -> list[MatchResult]:
        """
        Create multiple match results in a single transaction.

        Args:
            matches_data: List of dictionaries containing match data.
                Each dict should have keys: query_fingerprint_id, matched_fingerprint_id,
                similarity_score, and optional kwargs (query_source, query_url, query_user,
                match_confidence).

        Returns:
            List of created MatchResult objects

        Example:
            matches_data = [
                {
                    'query_fingerprint_id': 1,
                    'matched_fingerprint_id': 42,
                    'similarity_score': 0.95,
                    'match_confidence': 0.90,
                    'query_source': 'twitter'
                },
                ...
            ]
        """
        try:
            if not matches_data:
                return []

            matches = []
            for match_data in matches_data:
                match = MatchResult(
                    query_fingerprint_id=match_data["query_fingerprint_id"],
                    matched_fingerprint_id=match_data["matched_fingerprint_id"],
                    similarity_score=match_data["similarity_score"],  # type: ignore[arg-type]
                    match_confidence=match_data.get("match_confidence"),
                    query_source=match_data.get("query_source"),
                    query_url=match_data.get("query_url"),
                    query_user=match_data.get("query_user"),
                )
                matches.append(match)

            self.session.bulk_save_objects(matches, return_defaults=True)
            self.session.commit()
            logger.debug(f"Batch created {len(matches)} match results")
            return matches
        except (IntegrityError, OperationalError, DBAPIError) as e:
            logger.error(f"Failed to batch create match results: {e}")
            raise

    @db_retry()
    def get_top_matches(self, query_fp_id: int, limit: int = 10) -> list[MatchResult]:
        """Get top matches for a query fingerprint with retry on transient errors"""
        try:
            return (
                self.session.query(MatchResult)
                .filter(MatchResult.query_fingerprint_id == query_fp_id)
                .order_by(MatchResult.similarity_score.desc())
                .limit(limit)
                .all()
            )
        except (OperationalError, DBAPIError) as e:
            logger.error(f"Failed to get top matches for fingerprint {query_fp_id}: {e}")
            raise
