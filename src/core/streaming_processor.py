"""Streaming audio processor for real-time fingerprint matching."""

import logging
import time
from collections import deque

import numpy as np

from src.core.audio_fingerprinting import AudioFingerprinter

logger = logging.getLogger(__name__)


class StreamingAudioProcessor:
    """
    Process streaming audio in real-time for fingerprint matching.

    Maintains a sliding buffer of audio data and periodically extracts
    fingerprints to find matches in the database.
    """

    def __init__(
        self,
        sample_rate: int = 22050,
        buffer_duration: float = 3.0,  # 3 second buffer
        hop_duration: float = 0.5,     # Check every 0.5 seconds
    ):
        """
        Initialize streaming audio processor.

        Args:
            sample_rate: Audio sample rate in Hz
            buffer_duration: Duration of audio buffer in seconds
            hop_duration: How often to process the buffer in seconds
        """
        self.sample_rate = sample_rate
        self.buffer_size = int(sample_rate * buffer_duration)
        self.hop_size = int(sample_rate * hop_duration)
        self.audio_buffer: deque = deque(maxlen=self.buffer_size)
        self.fingerprinter = AudioFingerprinter(sample_rate=sample_rate)
        self.total_matches = 0
        self.samples_processed = 0
        self.last_process_time = time.time()

    def add_audio(self, audio_chunk: bytes) -> None:
        """
        Add audio chunk to buffer.

        Args:
            audio_chunk: Raw audio data as bytes (expected to be float32)
        """
        try:
            # Convert bytes to numpy array (assumes float32 format)
            audio_array = np.frombuffer(audio_chunk, dtype=np.float32)
            self.audio_buffer.extend(audio_array)
            self.samples_processed += len(audio_array)
        except Exception as e:
            logger.error(f"Error adding audio to buffer: {e}")
            raise

    def should_process(self) -> bool:
        """Check if buffer has enough data to process."""
        return len(self.audio_buffer) >= self.hop_size

    def get_buffer_array(self) -> np.ndarray:
        """Convert buffer to numpy array."""
        return np.array(self.audio_buffer, dtype=np.float32)

    async def process_buffer(self) -> list[dict]:
        """
        Extract fingerprint from current buffer and find matches.

        Returns:
            List of matching videos with similarity scores
        """
        if not self.should_process():
            return []

        try:
            # Convert buffer to numpy array
            audio = self.get_buffer_array()

            # Extract fingerprint
            fingerprint_result = self.fingerprinter.extract_fingerprint_from_audio(
                audio, self.sample_rate
            )

            # Find matches using the fingerprint
            matches = await self.find_matches(fingerprint_result)

            if matches:
                self.total_matches += len(matches)
                logger.info(f"Found {len(matches)} matches in buffer")

            self.last_process_time = time.time()
            return matches

        except Exception as e:
            logger.error(f"Error processing buffer: {e}")
            return []

    async def find_matches(self, fingerprint: dict) -> list[dict]:
        """
        Find matches for the fingerprint in database.

        Args:
            fingerprint: Fingerprint data dictionary

        Returns:
            List of matching videos with metadata
        """
        try:
            from src.database.connection import db_manager
            from src.database.models import AudioFingerprint, Video

            session = db_manager.get_session()

            try:
                # Get fingerprint hash for initial filtering
                fp_hash = fingerprint.get('fingerprint_hash')
                compact_fp = fingerprint.get('compact_fingerprint')

                if fp_hash is None or compact_fp is None:
                    return []

                # Query similar fingerprints (exact hash match for now)
                # In production, this would use more sophisticated similarity search
                similar_fps = (
                    session.query(AudioFingerprint, Video)
                    .join(Video, AudioFingerprint.video_id == Video.id)
                    .filter(AudioFingerprint.fingerprint_hash == fp_hash)
                    .limit(10)
                    .all()
                )

                matches = []
                for fp, video in similar_fps:
                    # Deserialize the stored fingerprint to compare
                    try:
                        stored_fp_data = self.fingerprinter.deserialize_fingerprint(
                            fp.fingerprint_data
                        )
                        stored_compact = stored_fp_data.get('compact_fingerprint')

                        # Calculate actual similarity score
                        if stored_compact is not None and compact_fp is not None:
                            similarity_result = self.fingerprinter.compare_fingerprints(
                                compact_fp,
                                stored_compact,
                                return_dict=True
                            )
                            similarity_score = similarity_result.get('combined_score', 0.0)
                        else:
                            # Fallback if fingerprints can't be compared
                            similarity_score = 0.5
                    except Exception as e:
                        logger.warning(f"Error comparing fingerprints: {e}")
                        similarity_score = 0.5

                    matches.append({
                        "video_id": video.video_id,
                        "title": video.title,
                        "url": video.url,
                        "thumbnail_url": video.thumbnail_url,
                        "start_time": fp.start_time,
                        "end_time": fp.end_time,
                        "similarity_score": similarity_score,
                        "confidence": fp.confidence_score or 0.9,
                    })

                return matches

            finally:
                session.close()

        except Exception as e:
            logger.error(f"Error finding matches: {e}")
            return []

    def get_stats(self) -> dict:
        """Get processing statistics."""
        return {
            "buffer_size": len(self.audio_buffer),
            "buffer_capacity": self.buffer_size,
            "samples_processed": self.samples_processed,
            "total_matches": self.total_matches,
            "duration_seconds": self.samples_processed / self.sample_rate if self.sample_rate else 0,
        }


# Global processor instances (one per client)
processors: dict[str, StreamingAudioProcessor] = {}


async def process_audio_chunk(client_id: str, audio_chunk: bytes):
    """
    Process incoming audio chunk for a client.

    Args:
        client_id: Unique client identifier
        audio_chunk: Raw audio data
    """
    from src.api.websocket import manager

    # Create processor if it doesn't exist
    if client_id not in processors:
        processors[client_id] = StreamingAudioProcessor()
        await manager.send_status(client_id, "Streaming processor initialized")

    processor = processors[client_id]

    try:
        # Add audio to buffer
        processor.add_audio(audio_chunk)

        # Process buffer if ready
        if processor.should_process():
            matches = await processor.process_buffer()

            if matches:
                # Send matches to client via WebSocket
                await manager.send_match(client_id, {
                    "matches": matches,
                    "timestamp": time.time(),
                    "stats": processor.get_stats()
                })
    except Exception as e:
        logger.error(f"Error processing audio chunk for {client_id}: {e}")
        await manager.send_error(client_id, f"Processing error: {str(e)}")


def cleanup_processor(client_id: str):
    """Clean up processor when client disconnects."""
    if client_id in processors:
        del processors[client_id]
        logger.info(f"Cleaned up processor for {client_id}")
