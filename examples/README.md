# SoundHash Examples

Example applications demonstrating real-time audio matching with SoundHash.

## Examples

### 1. Simple Console Demo (`simple_demo.py`)

A command-line demo that captures audio from your microphone and displays matches in real-time with colored output.

**Requirements:**
```bash
pip install websockets pyaudio numpy
```

**Usage:**
```bash
python simple_demo.py --api-url ws://localhost:8000 --api-key your-api-key
```

**Features:**
- Real-time microphone capture
- Colored console output
- Match statistics
- Connection status monitoring

### 2. Web Browser Demo (`web_demo.html`)

A beautiful web interface for real-time audio matching. Simply open in a browser and click "Start Listening".

**Usage:**
1. Start the SoundHash API server:
   ```bash
   python scripts/start_api.py
   ```

2. Open `web_demo.html` in your web browser

3. Configure the API URL and key, then click "Start Listening"

**Features:**
- Modern, responsive UI
- Real-time match display
- Visual connection status indicators
- Match history with confidence scores
- Audio visualization (coming soon)

## Running the Examples

### Prerequisites

1. **Start the SoundHash API server:**
   ```bash
   cd /path/to/soundhash
   python scripts/start_api.py
   ```
   The server will start on `http://localhost:8000`

2. **Ensure you have audio data in the database:**
   ```bash
   python scripts/ingest_channels.py --max-videos 10
   ```

### Console Demo

```bash
# Basic usage
python examples/simple_demo.py

# Custom API URL
python examples/simple_demo.py --api-url ws://your-server:8000

# With API key
python examples/simple_demo.py --api-key your-secret-key
```

**Example Output:**
```
============================================================
🎵 SoundHash Real-Time Matching Demo 🎵
============================================================

ℹ️  Connecting to SoundHash API...
✓ Connected!
ℹ️  Starting microphone...
✓ Microphone active!

🎤 Listening for audio... (Press Ctrl+C to stop)

────────────────────────────────────────────────────────────
🎯 MATCH FOUND #1
────────────────────────────────────────────────────────────
  Title: Amazing Song Title
  Confidence: 95.3%
  URL: https://youtube.com/watch?v=...
────────────────────────────────────────────────────────────

📊 Stats: Buffer 67% | Duration 3.2s | Total matches: 1
```

### Web Demo

1. Open `web_demo.html` in any modern web browser
2. Enter your API URL (default: `ws://localhost:8000`)
3. Enter your API key (default: `demo-key`)
4. Click "Start Listening"
5. Allow microphone access when prompted
6. Matches will appear as cards in real-time

## Troubleshooting

### Console Demo

**Error: "ModuleNotFoundError: No module named 'pyaudio'"**
- Install PyAudio: `pip install pyaudio`
- On Linux: `sudo apt-get install python3-pyaudio portaudio19-dev`
- On macOS: `brew install portaudio && pip install pyaudio`

**Error: "No module named 'websockets'"**
- Install websockets: `pip install websockets`

**Error: "Connection refused"**
- Ensure the SoundHash API server is running
- Check the API URL is correct

### Web Demo

**Error: "Failed to start: NotAllowedError"**
- Grant microphone permissions in your browser
- Check browser console for detailed errors

**Error: "WebSocket connection failed"**
- Ensure the API server is running
- Check the API URL in the configuration
- Verify CORS settings allow your domain

**No matches appearing:**
- Ensure there is audio data in the database
- Play music clearly near the microphone
- Check server logs for processing errors

## Development

### Customizing the Console Demo

Edit `simple_demo.py` to customize the output or add features:

```python
def handle_match(self, match_data: dict):
    """Custom match handler."""
    matches = match_data.get('matches', [])
    for match in matches:
        # Add your custom logic here
        print(f"Custom: {match['title']}")
```

### Customizing the Web Demo

Edit `web_demo.html` to change the appearance or add features:

- Modify CSS in the `<style>` section
- Add JavaScript functionality in the `<script>` section
- Customize the match card layout in `createMatchCard()`

## Performance Tips

1. **Buffer Settings:**
   - Larger buffers = better accuracy but higher latency
   - Smaller buffers = lower latency but may miss short audio

2. **Network:**
   - Use a local API server for lowest latency
   - Consider WebSocket compression for remote servers

3. **Audio Quality:**
   - Use a good quality microphone
   - Minimize background noise
   - Ensure clear audio playback

## Next Steps

- Try the Python client SDK for custom applications
- Build your own integration using the JavaScript SDK
- Explore the monitoring API at `/api/v1/monitoring/live-streams`

## Support

For issues or questions:
- Check the main [README](../README.md)
- Open an issue on GitHub
- Review the [client SDK documentation](../client-sdk/README.md)
