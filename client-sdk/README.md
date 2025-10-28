# SoundHash Client SDKs

Client libraries for streaming audio to SoundHash API for real-time matching.

## Python Client

### Installation

```bash
pip install websockets pyaudio numpy
```

### Usage

```python
import asyncio
from soundhash_client import SoundHashClient

async def main():
    # Initialize client
    client = SoundHashClient('ws://localhost:8000', 'your-api-key')
    
    # Handle matches
    def on_match(match_data):
        matches = match_data.get('matches', [])
        for match in matches:
            print(f"🎵 {match['title']} - {match['similarity_score']:.1%}")
    
    client.on_match = on_match
    
    # Connect and start streaming
    await client.connect()
    await client.start_microphone()
    
    # Listen for matches (blocks until disconnected)
    await client.listen_for_matches()

if __name__ == "__main__":
    asyncio.run(main())
```

### Streaming Audio File

```python
await client.connect()
await client.send_audio_file('path/to/audio.wav')
await client.listen_for_matches()
```

## JavaScript Client

### Installation

Include in your HTML:

```html
<script src="soundhash.js"></script>
```

Or use as ES module:

```javascript
import SoundHashClient from './soundhash.js';
```

### Usage

```javascript
// Initialize client
const client = new SoundHashClient('wss://api.soundhash.io', 'your-api-key');

// Handle matches
client.onMatch = (matchData) => {
  const matches = matchData.matches || [];
  matches.forEach(match => {
    console.log(`🎵 ${match.title} - ${(match.similarity_score * 100).toFixed(1)}%`);
    
    // Update UI with match
    displayMatch(match);
  });
};

// Handle status updates
client.onStatus = (status) => {
  console.log('Status:', status);
};

// Handle errors
client.onError = (error) => {
  console.error('Error:', error);
};

// Connect and start streaming
async function start() {
  try {
    await client.connect();
    await client.startMicrophone();
  } catch (error) {
    console.error('Failed to start:', error);
  }
}

// Start streaming
start();

// Stop streaming
// client.disconnect();
```

### Browser Example

```html
<!DOCTYPE html>
<html>
<head>
  <title>SoundHash Live Matching</title>
  <script src="soundhash.js"></script>
</head>
<body>
  <h1>SoundHash Live Matching</h1>
  
  <button id="start-btn">Start Listening</button>
  <button id="stop-btn" disabled>Stop</button>
  
  <div id="status"></div>
  <div id="matches"></div>
  
  <script>
    const client = new SoundHashClient('ws://localhost:8000', 'demo-key');
    
    client.onMatch = (matchData) => {
      const matchesDiv = document.getElementById('matches');
      const matches = matchData.matches || [];
      
      matches.forEach(match => {
        const div = document.createElement('div');
        div.className = 'match';
        div.innerHTML = `
          <h3>${match.title}</h3>
          <p>Confidence: ${(match.similarity_score * 100).toFixed(1)}%</p>
          <p>Time: ${match.start_time}s - ${match.end_time}s</p>
        `;
        matchesDiv.insertBefore(div, matchesDiv.firstChild);
      });
    };
    
    client.onStatus = (status) => {
      document.getElementById('status').textContent = status;
    };
    
    document.getElementById('start-btn').onclick = async () => {
      try {
        await client.connect();
        await client.startMicrophone();
        document.getElementById('start-btn').disabled = true;
        document.getElementById('stop-btn').disabled = false;
      } catch (error) {
        alert('Failed to start: ' + error.message);
      }
    };
    
    document.getElementById('stop-btn').onclick = () => {
      client.disconnect();
      document.getElementById('start-btn').disabled = false;
      document.getElementById('stop-btn').disabled = true;
    };
  </script>
</body>
</html>
```

## Features

- **Real-time streaming**: Stream audio directly from microphone
- **Auto-reconnection**: Automatically reconnects on connection loss
- **Match notifications**: Receive instant notifications when matches are found
- **Status updates**: Get real-time status updates from the server
- **Error handling**: Comprehensive error handling and callbacks
- **Cross-platform**: Works in browsers and Node.js (JavaScript) or any Python environment

## Configuration

Both clients support the following configuration options:

- `apiUrl`: WebSocket API endpoint (required)
- `apiKey`: API authentication key (required)
- `clientId`: Unique client identifier (optional, auto-generated)
- `sampleRate`: Audio sample rate in Hz (default: 22050)

## Audio Format

The clients stream audio in the following format:

- **Encoding**: Float32 (32-bit floating point)
- **Channels**: 1 (mono)
- **Sample Rate**: 22050 Hz (configurable)
- **Chunk Size**: 4096 samples

## Rate Limiting

The WebSocket connection has rate limits to prevent abuse. If you exceed the limits, you will receive an error message and the connection will be closed.

## Support

For issues or questions, please open an issue on GitHub or contact support.
