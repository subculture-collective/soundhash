"""
SoundHash Python Client SDK

Real-time audio streaming client for SoundHash API.
Captures audio from microphone and streams to server for live matching.

Installation:
    pip install websockets pyaudio numpy

Usage:
    import asyncio
    from soundhash_client import SoundHashClient
    
    async def main():
        client = SoundHashClient('ws://localhost:8000', 'your-api-key')
        
        # Override callback to handle matches
        client.on_match = lambda match_data: print(f"Match found: {match_data}")
        
        await client.connect()
        await client.start_microphone()
        
        # Listen for matches (blocks until disconnected)
        await client.listen_for_matches()
    
    if __name__ == "__main__":
        asyncio.run(main())
"""

import asyncio
import json
import logging
import uuid
from typing import Optional

try:
    import websockets
except ImportError:
    raise ImportError("websockets library required. Install with: pip install websockets")

try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False
    logging.warning("PyAudio not available. Microphone functionality disabled.")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SoundHashClient:
    """Client for streaming audio to SoundHash API."""
    
    def __init__(
        self,
        api_url: str,
        api_key: str,
        client_id: Optional[str] = None,
        sample_rate: int = 22050,
    ):
        """
        Initialize SoundHash client.
        
        Args:
            api_url: WebSocket API URL (e.g., 'ws://localhost:8000')
            api_key: API authentication key
            client_id: Unique client identifier (auto-generated if not provided)
            sample_rate: Audio sample rate in Hz
        """
        if api_url.startswith('https://'):
            self.api_url = 'wss://' + api_url[len('https://'):]
        elif api_url.startswith('http://'):
            self.api_url = 'ws://' + api_url[len('http://'):]
        else:
            self.api_url = api_url
        self.api_key = api_key
        self.client_id = client_id or str(uuid.uuid4())
        self.sample_rate = sample_rate
        
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.audio: Optional[pyaudio.PyAudio] = None
        self.stream: Optional[pyaudio.Stream] = None
        self._running = False
    
    async def connect(self):
        """Connect to SoundHash WebSocket."""
        uri = f"{self.api_url}/ws/stream/{self.client_id}"
        
        try:
            self.ws = await websockets.connect(uri)
            logger.info("Connected to SoundHash")
            self._running = True
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            raise
    
    async def start_microphone(self):
        """Start capturing audio from microphone."""
        if not PYAUDIO_AVAILABLE:
            raise RuntimeError("PyAudio not available. Install with: pip install pyaudio")
        
        self.audio = pyaudio.PyAudio()
        
        # Open audio stream
        self.stream = self.audio.open(
            format=pyaudio.paFloat32,
            channels=1,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=4096,
            stream_callback=None,  # We'll read manually in async loop
        )
        
        logger.info("Microphone started")
        
        # Start async task to send audio
        asyncio.create_task(self._send_audio_loop())
    
    async def _send_audio_loop(self):
        """Continuously read from microphone and send to server."""
        try:
            while self._running and self.stream and self.stream.is_active():
                # Read audio data
                audio_data = self.stream.read(4096, exception_on_overflow=False)
                
                # Send to server
                if self.ws and not self.ws.closed:
                    await self.ws.send(audio_data)
                
                # Small delay to prevent overwhelming the server
                await asyncio.sleep(0.01)
        except Exception as e:
            logger.error(f"Error in audio loop: {e}")
    
    async def send_audio_file(self, file_path: str, chunk_size: int = 4096):
        """
        Send audio from a file instead of microphone.
        
        Args:
            file_path: Path to audio file
            chunk_size: Size of chunks to send
        """
        try:
            import wave
            
            with wave.open(file_path, 'rb') as wav_file:
                logger.info(f"Streaming audio file: {file_path}")
                
                while True:
                    data = wav_file.readframes(chunk_size)
                    if not data:
                        break
                    
                    if self.ws and not self.ws.closed:
                        await self.ws.send(data)
                    
                    # Delay to simulate real-time streaming
                    await asyncio.sleep(chunk_size / self.sample_rate)
                
                logger.info("Finished streaming audio file")
        except Exception as e:
            logger.error(f"Error streaming file: {e}")
            raise
    
    async def listen_for_matches(self):
        """Listen for match notifications from server."""
        try:
            async for message in self.ws:
                data = json.loads(message)
                
                if data['type'] == 'match':
                    self.on_match(data['data'])
                elif data['type'] == 'status':
                    self.on_status(data['message'])
                elif data['type'] == 'error':
                    self.on_error(data['message'])
        except websockets.exceptions.ConnectionClosed:
            logger.info("Connection closed by server")
        except Exception as e:
            logger.error(f"Error listening for matches: {e}")
    
    def on_match(self, match_data: dict):
        """
        Override this method to handle matches.
        
        Args:
            match_data: Match information including videos and confidence scores
        """
        logger.info(f"Match found: {match_data}")
    
    def on_status(self, status: str):
        """
        Override this method to handle status updates.
        
        Args:
            status: Status message from server
        """
        logger.info(f"Status: {status}")
    
    def on_error(self, error_message: str):
        """
        Override this method to handle errors.
        
        Args:
            error_message: Error message from server
        """
        logger.error(f"Server error: {error_message}")
    
    async def disconnect(self):
        """Disconnect and cleanup resources."""
        self._running = False
        
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            logger.info("Microphone stopped")
        
        if self.audio:
            self.audio.terminate()
        
        if self.ws and not self.ws.closed:
            await self.ws.close()
            logger.info("Disconnected from SoundHash")


# Example usage
async def main():
    """Example usage of SoundHash client."""
    client = SoundHashClient('ws://localhost:8000', 'your-api-key')
    
    # Custom match handler
    def handle_match(match_data):
        matches = match_data.get('matches', [])
        for match in matches:
            print(f"🎵 Match: {match.get('title')} - {match.get('similarity_score', 0):.2%}")
    
    client.on_match = handle_match
    
    try:
        await client.connect()
        await client.start_microphone()
        
        # Listen for matches
        await client.listen_for_matches()
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
