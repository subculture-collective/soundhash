# Quick Start Guide - WebSocket Real-Time Matching

Get started with real-time audio matching in under 5 minutes!

## Prerequisites

- Python 3.8+
- SoundHash API server
- Microphone (for live demos)

## Option 1: Web Demo (Easiest)

1. **Start the API server:**
   ```bash
   cd /path/to/soundhash
   python scripts/start_api.py
   ```

2. **Open the web demo:**
   ```bash
   open examples/web_demo.html
   # Or navigate to file:///path/to/soundhash/examples/web_demo.html
   ```

3. **Configure and start:**
   - API URL: `ws://localhost:8000`
   - API Key: `demo-key`
   - Click "Start Listening"
   - Allow microphone access
   - Play some music!

## Option 2: Console Demo

1. **Install dependencies:**
   ```bash
   pip install websockets pyaudio numpy
   ```

2. **Start the API server:**
   ```bash
   python scripts/start_api.py
   ```

3. **Run the console demo:**
   ```bash
   python examples/simple_demo.py
   ```

4. **Play music near your microphone** and watch matches appear!

## Option 3: Custom Integration (Python)

```python
import asyncio
import sys
sys.path.insert(0, 'client-sdk')
from soundhash_client import SoundHashClient

async def main():
    # Create client
    client = SoundHashClient('ws://localhost:8000', 'demo-key')
    
    # Handle matches
    def on_match(match_data):
        for match in match_data.get('matches', []):
            print(f"🎵 {match['title']} - {match['similarity_score']:.1%}")
    
    client.on_match = on_match
    
    # Connect and stream
    await client.connect()
    await client.start_microphone()
    await client.listen_for_matches()

asyncio.run(main())
```

## Option 4: Custom Integration (JavaScript)

```html
<!DOCTYPE html>
<html>
<head>
    <script src="client-sdk/soundhash.js"></script>
</head>
<body>
    <button id="start">Start Matching</button>
    <div id="results"></div>
    
    <script>
        const client = new SoundHashClient('ws://localhost:8000', 'demo-key');
        
        client.onMatch = (data) => {
            data.matches.forEach(match => {
                document.getElementById('results').innerHTML += 
                    `<p>🎵 ${match.title} - ${(match.similarity_score * 100).toFixed(1)}%</p>`;
            });
        };
        
        document.getElementById('start').onclick = async () => {
            await client.connect();
            await client.startMicrophone();
        };
    </script>
</body>
</html>
```

## Troubleshooting

### "Connection refused"
- Make sure the API server is running: `python scripts/start_api.py`
- Check the URL is correct: `ws://localhost:8000`

### "No module named 'pyaudio'"
```bash
# Linux
sudo apt-get install python3-pyaudio portaudio19-dev
pip install pyaudio

# macOS
brew install portaudio
pip install pyaudio

# Windows
pip install pipwin
pipwin install pyaudio
```

### "NotAllowedError: Permission denied"
- Grant microphone permissions in your browser
- Check browser console for detailed errors

### No matches appearing
- Ensure database has fingerprints: `python scripts/ingest_channels.py --max-videos 10`
- Play music clearly and loudly
- Check server logs for errors

## What's Next?

- Read the [WebSocket API documentation](../docs/websocket-api.md)
- Explore the [examples](../examples/README.md)
- Check out the [client SDK documentation](../client-sdk/README.md)
- Review the [implementation summary](../docs/WEBSOCKET_IMPLEMENTATION_SUMMARY.md)

## Support

- **Issues**: Open an issue on GitHub
- **Documentation**: See `docs/` directory
- **Examples**: See `examples/` directory

## Quick Reference

**Server:**
```bash
python scripts/start_api.py
```

**Console Demo:**
```bash
python examples/simple_demo.py --api-url ws://localhost:8000
```

**Web Demo:**
```bash
open examples/web_demo.html
```

**Monitor Streams:**
```bash
curl http://localhost:8000/api/v1/monitoring/live-streams
```

Happy matching! 🎵
