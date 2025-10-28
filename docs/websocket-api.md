# WebSocket Real-Time Matching API

## Overview

The SoundHash WebSocket API enables real-time audio streaming and instant match notifications. This allows applications to identify audio as it's being played or recorded, with sub-second latency.

## Architecture

```
Client (Browser/Python) 
    ↓ WebSocket (audio stream)
Connection Manager
    ↓
Streaming Audio Processor
    ↓ (buffer + fingerprint extraction)
Database Query (similarity search)
    ↓
Match Results
    ↓ WebSocket (JSON response)
Client (match notification)
```

## WebSocket Endpoint

### Connect to Stream

```
WS /ws/stream/{client_id}
```

**Parameters:**
- `client_id` (path): Unique identifier for the client connection

**Example:**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/stream/my-unique-id');
```

## Message Protocol

### Client → Server

**Audio Data (Binary)**

Send raw audio data as binary WebSocket messages:

```javascript
// JavaScript
const audioData = new Float32Array([...]);
ws.send(audioData.buffer);
```

```python
# Python
audio_bytes = audio_array.tobytes()
await websocket.send(audio_bytes)
```

**Audio Format:**
- **Type**: Binary
- **Encoding**: Float32 (32-bit floating point)
- **Channels**: 1 (mono)
- **Sample Rate**: 22050 Hz
- **Byte Order**: Native/little-endian

### Server → Client

All server messages are JSON with a `type` field:

#### Match Notification

Sent when audio matches are found:

```json
{
  "type": "match",
  "data": {
    "matches": [
      {
        "video_id": "abc123",
        "title": "Song Title",
        "url": "https://youtube.com/watch?v=abc123",
        "thumbnail_url": "https://i.ytimg.com/vi/abc123/default.jpg",
        "start_time": 0.0,
        "end_time": 90.0,
        "similarity_score": 0.95,
        "confidence": 0.92
      }
    ],
    "timestamp": 1234567890.123,
    "stats": {
      "buffer_size": 44100,
      "buffer_capacity": 66150,
      "samples_processed": 352800,
      "total_matches": 3,
      "duration_seconds": 16.0
    }
  }
}
```

#### Status Update

Informational messages about processing state:

```json
{
  "type": "status",
  "message": "Streaming processor initialized"
}
```

#### Error Message

Error notifications:

```json
{
  "type": "error",
  "message": "Processing error: Invalid audio format"
}
```

## Processing Flow

### 1. Client Connection

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/stream/client-123');

ws.onopen = () => {
  console.log('Connected');
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  handleMessage(message);
};
```

### 2. Audio Streaming

The client streams audio in chunks:

```javascript
// Capture from microphone
navigator.mediaDevices.getUserMedia({ audio: true })
  .then(stream => {
    const audioContext = new AudioContext({ sampleRate: 22050 });
    const source = audioContext.createMediaStreamSource(stream);
    const processor = audioContext.createScriptProcessor(4096, 1, 1);
    
    processor.onaudioprocess = (e) => {
      const audioData = e.inputBuffer.getChannelData(0);
      ws.send(audioData.buffer);
    };
    
    source.connect(processor);
    processor.connect(audioContext.destination);
  });
```

### 3. Server Processing

1. **Buffer Management**: Audio chunks are added to a sliding buffer (default 3 seconds)
2. **Periodic Processing**: Every 0.5 seconds, extract fingerprint from buffer
3. **Database Query**: Compare fingerprint against database
4. **Match Notification**: Send results back to client if matches found

### 4. Client Handling

```javascript
ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  
  switch(message.type) {
    case 'match':
      displayMatches(message.data.matches);
      break;
    case 'status':
      console.log(message.message);
      break;
    case 'error':
      console.error(message.message);
      break;
  }
};
```

## Configuration

### Server Configuration

Environment variables for tuning:

```bash
# Buffer duration (seconds)
STREAMING_BUFFER_DURATION=3.0

# Processing interval (seconds)
STREAMING_HOP_DURATION=0.5

# Sample rate (Hz)
FINGERPRINT_SAMPLE_RATE=22050

# Maximum concurrent connections
WEBSOCKET_MAX_CONNECTIONS=100
```

### Client Configuration

```javascript
const client = new SoundHashClient(
  'ws://localhost:8000',  // API URL
  'your-api-key',          // API key
  'client-123',            // Client ID (optional)
  22050                    // Sample rate
);
```

## Monitoring API

### List Active Streams

```http
GET /api/v1/monitoring/live-streams
Authorization: Bearer <token>
```

**Response:**
```json
{
  "total_streams": 2,
  "streams": [
    {
      "client_id": "client-123",
      "connected_at": 1234567890.0,
      "duration_seconds": 45.2,
      "has_processor": true,
      "buffer_size": 33075,
      "buffer_capacity": 66150,
      "samples_processed": 992250,
      "total_matches": 5,
      "duration_seconds": 45.0
    }
  ]
}
```

### Get Stream Details

```http
GET /api/v1/monitoring/live-streams/{client_id}
Authorization: Bearer <token>
```

### Disconnect Stream

```http
DELETE /api/v1/monitoring/live-streams/{client_id}
Authorization: Bearer <token>
```

## Performance Characteristics

### Latency

- **Buffer Duration**: 3 seconds (configurable)
- **Processing Interval**: 0.5 seconds (configurable)
- **Database Query**: ~50-200ms (depends on database size and hardware)
- **Total Latency**: ~3.5-4 seconds from audio start to match notification

### Throughput

- **Audio Data Rate**: ~86 KB/s (22050 Hz × 4 bytes)
- **Concurrent Connections**: 100+ (depends on server resources)
- **Database Queries**: Limited by database performance

### Resource Usage

Per active stream:
- **Memory**: ~1 MB (buffer + overhead)
- **CPU**: Minimal (fingerprint extraction happens periodically)
- **Network**: ~86 KB/s upstream, <1 KB/s downstream (bursty)

## Rate Limiting

WebSocket connections are subject to rate limits:

- **Connections per IP**: 10 concurrent
- **Connection attempts**: 30 per minute
- **Audio data rate**: 200 KB/s max
- **Message rate**: 1000 messages/minute

Exceeding limits results in connection closure with error message.

## Error Handling

### Connection Errors

```javascript
ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

ws.onclose = (event) => {
  console.log('Connection closed:', event.code, event.reason);
  // Implement reconnection logic
};
```

### Automatic Reconnection

```javascript
class ReconnectingClient {
  constructor(url) {
    this.url = url;
    this.reconnectDelay = 1000;
    this.maxReconnectDelay = 30000;
    this.connect();
  }
  
  connect() {
    this.ws = new WebSocket(this.url);
    
    this.ws.onopen = () => {
      this.reconnectDelay = 1000;
    };
    
    this.ws.onclose = () => {
      setTimeout(() => {
        this.reconnectDelay = Math.min(
          this.reconnectDelay * 2,
          this.maxReconnectDelay
        );
        this.connect();
      }, this.reconnectDelay);
    };
  }
}
```

## Security

### Authentication

WebSocket connections can be authenticated via:

1. **Query Parameter**: `?token=<jwt>`
2. **Authorization Header**: `Authorization: Bearer <jwt>`

Example:
```javascript
const ws = new WebSocket(
  'ws://localhost:8000/ws/stream/client-123?token=' + apiKey
);
```

### Best Practices

1. **Use WSS**: Always use `wss://` (WebSocket Secure) in production
2. **Validate Client ID**: Use unique, unpredictable client IDs
3. **Implement Timeouts**: Close inactive connections after 5 minutes
4. **Rate Limiting**: Respect rate limits to avoid service disruption
5. **Error Handling**: Always implement reconnection logic

## Examples

See the [examples](../examples/README.md) directory for:
- Simple console demo (Python)
- Web browser demo (HTML/JavaScript)
- Custom integrations

## Troubleshooting

### No Matches Found

- Ensure audio is clear and loud enough
- Check that database contains fingerprints for the audio
- Verify sample rate matches (22050 Hz)
- Check server logs for processing errors

### High Latency

- Reduce buffer duration (trade accuracy for speed)
- Optimize database queries (add indexes)
- Use faster hardware
- Reduce concurrent connections

### Connection Drops

- Check network stability
- Implement reconnection logic
- Verify rate limits not exceeded
- Check server resource usage

## API Reference

For complete API documentation, see:
- [Client SDK Documentation](../client-sdk/README.md)
- [REST API Documentation](../docs/api.md)
- [Examples](../examples/README.md)
