from sqlalchemy.orm import Session
from typing import List, Optional, Any
from .models import Channel, Video, AudioFingerprint, MatchResult, ProcessingJob
from .connection import db_manager
from datetime import datetime

class VideoRepository:
    def __init__(self, session: Session) -> None:
        self.session = session
    
    def create_channel(self, channel_id: str, channel_name: Optional[str] = None, 
                      description: Optional[str] = None) -> Channel:
        """Create a new channel record"""
        channel = Channel(
            channel_id=channel_id,
            channel_name=channel_name,
            description=description
        )
        self.session.add(channel)
        self.session.commit()
        return channel
    
    def get_channel_by_id(self, channel_id: str) -> Optional[Channel]:
        """Get channel by YouTube channel ID"""
        return self.session.query(Channel).filter(
            Channel.channel_id == channel_id
        ).first()
    
    def create_video(self, video_id: str, channel_id: int, title: Optional[str] = None,
                    duration: Optional[float] = None, url: Optional[str] = None, **kwargs: Any) -> Video:
        """Create a new video record"""
        video = Video(
            video_id=video_id,
            channel_id=channel_id,
            title=title,
            duration=duration,  # type: ignore[arg-type]
            url=url,
            **kwargs
        )
        self.session.add(video)
        self.session.commit()
        return video
    
    def get_video_by_id(self, video_id: str) -> Optional[Video]:
        """Get video by YouTube video ID"""
        return self.session.query(Video).filter(
            Video.video_id == video_id
        ).first()
    
    def get_unprocessed_videos(self, limit: int = 100) -> List[Video]:
        """Get videos that haven't been processed yet"""
        return self.session.query(Video).filter(
            Video.processed == False
        ).limit(limit).all()
    
    def mark_video_processed(self, video_id: int, success: bool = True, 
                           error_message: Optional[str] = None) -> None:
        """Mark a video as processed"""
        video = self.session.get(Video, video_id)
        if video:
            video.processed = success
            video.processing_completed = datetime.utcnow()
            if error_message:
                video.processing_error = error_message
            self.session.commit()
    
    def create_fingerprint(self, video_id: int, start_time: float, end_time: float,
                          fingerprint_hash: str, fingerprint_data: bytes,
                          **kwargs: Any) -> AudioFingerprint:
        """Create a new audio fingerprint"""
        fingerprint = AudioFingerprint(
            video_id=video_id,
            start_time=start_time,  # type: ignore[arg-type]
            end_time=end_time,  # type: ignore[arg-type]
            fingerprint_hash=fingerprint_hash,
            fingerprint_data=fingerprint_data,
            **kwargs
        )
        self.session.add(fingerprint)
        self.session.commit()
        return fingerprint
    
    def find_matching_fingerprints(self, fingerprint_hash: str, 
                                  threshold: float = 0.8) -> List[AudioFingerprint]:
        """Find fingerprints with matching hash"""
        return self.session.query(AudioFingerprint).filter(
            AudioFingerprint.fingerprint_hash == fingerprint_hash
        ).all()
    
    def create_match_result(self, query_fp_id: int, matched_fp_id: int,
                           similarity_score: float, query_source: Optional[str] = None,
                           query_url: Optional[str] = None, query_user: Optional[str] = None) -> MatchResult:
        """Create a match result record"""
        match = MatchResult(
            query_fingerprint_id=query_fp_id,
            matched_fingerprint_id=matched_fp_id,
            similarity_score=similarity_score,  # type: ignore[arg-type]
            query_source=query_source,
            query_url=query_url,
            query_user=query_user
        )
        self.session.add(match)
        self.session.commit()
        return match
    
    def get_top_matches(self, query_fp_id: int, limit: int = 10) -> List[MatchResult]:
        """Get top matches for a query fingerprint"""
        return self.session.query(MatchResult).filter(
            MatchResult.query_fingerprint_id == query_fp_id
        ).order_by(
            MatchResult.similarity_score.desc()
        ).limit(limit).all()

class JobRepository:
    def __init__(self, session: Session) -> None:
        self.session = session
    
    def create_job(self, job_type: str, target_id: str, parameters: Optional[str] = None) -> ProcessingJob:
        """Create a new processing job"""
        job = ProcessingJob(
            job_type=job_type,
            target_id=target_id,
            parameters=parameters,
            status='pending'
        )
        self.session.add(job)
        self.session.commit()
        return job
    
    def get_pending_jobs(self, job_type: Optional[str] = None, limit: int = 10) -> List[ProcessingJob]:
        """Get pending jobs"""
        query = self.session.query(ProcessingJob).filter(
            ProcessingJob.status == 'pending'
        )
        if job_type:
            query = query.filter(ProcessingJob.job_type == job_type)
        
        return query.order_by(ProcessingJob.created_at).limit(limit).all()
    
    def get_jobs_by_target(self, job_type: str, target_id: str, statuses: Optional[List[str]] = None) -> List[ProcessingJob]:
        """Get jobs by target id and type, optionally filtered by status list"""
        query = self.session.query(ProcessingJob).filter(
            ProcessingJob.job_type == job_type,
            ProcessingJob.target_id == target_id,
        )
        if statuses:
            query = query.filter(ProcessingJob.status.in_(statuses))
        return query.order_by(ProcessingJob.created_at.desc()).all()
    
    def job_exists(self, job_type: str, target_id: str, statuses: Optional[List[str]] = None) -> bool:
        """Check if a job already exists for target_id and type (optionally in given statuses)"""
        query = self.session.query(ProcessingJob).filter(
            ProcessingJob.job_type == job_type,
            ProcessingJob.target_id == target_id,
        )
        if statuses:
            query = query.filter(ProcessingJob.status.in_(statuses))
        return self.session.query(query.exists()).scalar()
    
    def update_job_status(self, job_id: int, status: str, progress: Optional[float] = None,
                         current_step: Optional[str] = None, error_message: Optional[str] = None) -> None:
        """Update job status and progress"""
        job = self.session.get(ProcessingJob, job_id)
        if job:
            job.status = status
            if progress is not None:
                job.progress = progress  # type: ignore[assignment]
            if current_step:
                job.current_step = current_step
            if error_message:
                job.error_message = error_message
            
            if status == 'running' and not job.started_at:
                job.started_at = datetime.utcnow()
            elif status in ['completed', 'failed']:
                job.completed_at = datetime.utcnow()
            
            self.session.commit()

def get_video_repository() -> VideoRepository:
    """Get a video repository instance"""
    session = db_manager.get_session()
    return VideoRepository(session)

def get_job_repository() -> JobRepository:
    """Get a job repository instance"""
    session = db_manager.get_session()
    return JobRepository(session)