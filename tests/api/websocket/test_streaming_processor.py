"""Tests for streaming audio processor."""

import pytest
import numpy as np
from unittest.mock import AsyncMock, patch

from src.core.streaming_processor import StreamingAudioProcessor, processors, cleanup_processor


@pytest.fixture
def processor():
    """Create a fresh processor for each test."""
    return StreamingAudioProcessor(sample_rate=22050, buffer_duration=3.0, hop_duration=0.5)


class TestStreamingAudioProcessor:
    """Test suite for StreamingAudioProcessor."""

    def test_initialization(self, processor):
        """Test processor initialization."""
        assert processor.sample_rate == 22050
        assert processor.buffer_size == int(22050 * 3.0)
        assert processor.hop_size == int(22050 * 0.5)
        assert len(processor.audio_buffer) == 0
        assert processor.total_matches == 0
        assert processor.samples_processed == 0

    def test_add_audio(self, processor):
        """Test adding audio to buffer."""
        # Create test audio data
        audio_array = np.random.rand(1024).astype(np.float32)
        audio_bytes = audio_array.tobytes()
        
        # Add to buffer
        processor.add_audio(audio_bytes)
        
        # Verify buffer has data
        assert len(processor.audio_buffer) == 1024
        assert processor.samples_processed == 1024

    def test_add_multiple_chunks(self, processor):
        """Test adding multiple audio chunks."""
        chunk_size = 512
        num_chunks = 5
        
        for _ in range(num_chunks):
            audio_array = np.random.rand(chunk_size).astype(np.float32)
            audio_bytes = audio_array.tobytes()
            processor.add_audio(audio_bytes)
        
        # Verify total samples
        assert processor.samples_processed == chunk_size * num_chunks
        assert len(processor.audio_buffer) == chunk_size * num_chunks

    def test_buffer_overflow(self, processor):
        """Test buffer overflow handling."""
        # Fill buffer beyond capacity
        samples_to_add = processor.buffer_size + 5000
        
        audio_array = np.random.rand(samples_to_add).astype(np.float32)
        audio_bytes = audio_array.tobytes()
        processor.add_audio(audio_bytes)
        
        # Buffer should be at max capacity (deque maxlen)
        assert len(processor.audio_buffer) == processor.buffer_size
        assert processor.samples_processed == samples_to_add

    def test_should_process(self, processor):
        """Test should_process logic."""
        # Initially should not process
        assert not processor.should_process()
        
        # Add enough samples to reach hop size
        audio_array = np.random.rand(processor.hop_size).astype(np.float32)
        audio_bytes = audio_array.tobytes()
        processor.add_audio(audio_bytes)
        
        # Should now be ready to process
        assert processor.should_process()

    def test_get_buffer_array(self, processor):
        """Test converting buffer to numpy array."""
        # Add some data
        audio_array = np.random.rand(1024).astype(np.float32)
        audio_bytes = audio_array.tobytes()
        processor.add_audio(audio_bytes)
        
        # Get buffer array
        buffer_array = processor.get_buffer_array()
        
        assert isinstance(buffer_array, np.ndarray)
        assert buffer_array.dtype == np.float32
        assert len(buffer_array) == 1024

    @pytest.mark.asyncio
    async def test_process_buffer_not_ready(self, processor):
        """Test processing when buffer doesn't have enough data."""
        matches = await processor.process_buffer()
        
        # Should return empty list
        assert matches == []

    @pytest.mark.asyncio
    @patch('src.core.streaming_processor.StreamingAudioProcessor.find_matches')
    async def test_process_buffer_with_data(self, mock_find_matches, processor):
        """Test processing buffer with sufficient data."""
        # Mock find_matches to return test matches
        test_matches = [
            {"video_id": "123", "title": "Test Video", "similarity_score": 0.95}
        ]
        mock_find_matches.return_value = test_matches
        
        # Add enough data to process
        audio_array = np.random.rand(processor.hop_size + 1000).astype(np.float32)
        audio_bytes = audio_array.tobytes()
        processor.add_audio(audio_bytes)
        
        # Process buffer
        matches = await processor.process_buffer()
        
        # Verify matches returned
        assert matches == test_matches
        assert processor.total_matches == len(test_matches)
        mock_find_matches.assert_called_once()

    @pytest.mark.asyncio
    async def test_find_matches_no_hash(self, processor):
        """Test find_matches with invalid fingerprint."""
        # Fingerprint without hash
        fingerprint = {"compact_fingerprint": np.array([1, 2, 3])}
        
        matches = await processor.find_matches(fingerprint)
        
        # Should return empty list
        assert matches == []

    def test_get_stats(self, processor):
        """Test getting processor statistics."""
        # Add some data
        audio_array = np.random.rand(5000).astype(np.float32)
        audio_bytes = audio_array.tobytes()
        processor.add_audio(audio_bytes)
        
        # Get stats
        stats = processor.get_stats()
        
        assert "buffer_size" in stats
        assert "buffer_capacity" in stats
        assert "samples_processed" in stats
        assert "total_matches" in stats
        assert "duration_seconds" in stats
        
        assert stats["buffer_size"] == 5000
        assert stats["buffer_capacity"] == processor.buffer_size
        assert stats["samples_processed"] == 5000
        assert stats["duration_seconds"] > 0


def test_cleanup_processor():
    """Test processor cleanup."""
    client_id = "test-client"
    
    # Add processor
    processors[client_id] = StreamingAudioProcessor()
    
    # Cleanup
    cleanup_processor(client_id)
    
    # Verify removed
    assert client_id not in processors


def test_cleanup_nonexistent_processor():
    """Test cleaning up processor that doesn't exist."""
    # Should not raise exception
    cleanup_processor("nonexistent-client")


@pytest.mark.asyncio
@patch('src.api.websocket.manager')
async def test_process_audio_chunk_new_client(mock_manager):
    """Test processing audio chunk for new client."""
    from src.core.streaming_processor import process_audio_chunk
    
    client_id = "new-client"
    audio_array = np.random.rand(1024).astype(np.float32)
    audio_bytes = audio_array.tobytes()
    
    mock_manager.send_status = AsyncMock()
    
    await process_audio_chunk(client_id, audio_bytes)
    
    # Verify processor was created
    assert client_id in processors
    
    # Verify status was sent
    mock_manager.send_status.assert_called_once()
    
    # Cleanup
    cleanup_processor(client_id)


@pytest.mark.asyncio
@patch('src.api.websocket.manager')
async def test_process_audio_chunk_existing_client(mock_manager):
    """Test processing audio chunk for existing client."""
    from src.core.streaming_processor import process_audio_chunk
    
    client_id = "existing-client"
    
    # Create processor first
    processors[client_id] = StreamingAudioProcessor()
    
    audio_array = np.random.rand(1024).astype(np.float32)
    audio_bytes = audio_array.tobytes()
    
    mock_manager.send_status = AsyncMock()
    
    await process_audio_chunk(client_id, audio_bytes)
    
    # Verify processor still exists
    assert client_id in processors
    
    # Cleanup
    cleanup_processor(client_id)
