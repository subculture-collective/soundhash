# SoundHash Developer Portal

Welcome to the SoundHash Developer Portal! This is your one-stop resource for integrating audio fingerprinting and matching capabilities into your applications.

## 🚀 Quick Start

Get started with SoundHash API in minutes:

1. **Sign up** for a free account at [api.soundhash.io/signup](https://api.soundhash.io/signup)
2. **Get your API key** from the [dashboard](https://api.soundhash.io/dashboard)
3. **Install** an SDK or use the REST API directly
4. **Make your first request** to match audio

### Your First API Call

=== "Python"
    ```python
    from soundhash import ApiClient, Configuration, VideosApi
    
    # Configure API client
    config = Configuration()
    config.host = "https://api.soundhash.io"
    config.access_token = "YOUR_API_TOKEN"
    
    # Create API client
    with ApiClient(config) as client:
        api = VideosApi(client)
        videos = api.list_videos(limit=10)
        
        for video in videos:
            print(f"{video.title} - {video.duration}s")
    ```

=== "JavaScript"
    ```javascript
    const SoundHash = require('@soundhash/client');
    
    const client = new SoundHash.ApiClient();
    client.basePath = 'https://api.soundhash.io';
    client.authentications['bearerAuth'].accessToken = 'YOUR_API_TOKEN';
    
    const videosApi = new SoundHash.VideosApi(client);
    
    videosApi.listVideos({ limit: 10 }, (error, data) => {
      if (error) {
        console.error(error);
      } else {
        data.forEach(video => {
          console.log(`${video.title} - ${video.duration}s`);
        });
      }
    });
    ```

=== "cURL"
    ```bash
    curl -X GET "https://api.soundhash.io/api/v1/videos?limit=10" \
      -H "Authorization: Bearer YOUR_API_TOKEN" \
      -H "Accept: application/json"
    ```

## 📚 Resources

### Interactive Documentation

- **[Swagger UI](https://api.soundhash.io/docs)** - Interactive API explorer
- **[ReDoc](https://api.soundhash.io/redoc)** - Beautiful API reference
- **[OpenAPI Spec](https://api.soundhash.io/openapi.json)** - Machine-readable specification

### SDKs & Libraries

Official client libraries for your favorite language:

| Language | Package Manager | Installation | Documentation |
|----------|----------------|--------------|---------------|
| Python | PyPI | `pip install soundhash-client` | [Docs](sdks/python.md) |
| JavaScript | npm | `npm install @soundhash/client` | [Docs](sdks/javascript.md) |
| TypeScript | npm | `npm install @soundhash/client-ts` | [Docs](sdks/typescript.md) |
| PHP | Packagist | `composer require soundhash/client` | [Docs](sdks/php.md) |
| Ruby | RubyGems | `gem install soundhash-client` | [Docs](sdks/ruby.md) |
| Go | GitHub | `go get github.com/subculture-collective/soundhash-client-go` | [Docs](sdks/go.md) |

### Tools & Collections

- **[Postman Collection](https://api.soundhash.io/postman_collection.json)** - Import into Postman for easy testing
- **[Code Generators](code-generators.md)** - Generate code snippets in any language
- **[Webhook Tester](webhooks/testing.md)** - Test webhook integrations

## 🎯 Core Features

### Audio Matching

Match audio clips to videos in your database:

```python
from soundhash import MatchesApi

matches_api = MatchesApi(client)
result = matches_api.find_matches(
    audio_file=open('clip.wav', 'rb'),
    min_confidence=0.8
)

for match in result.matches:
    print(f"Match: {match.video.title} ({match.confidence:.1%})")
```

### Video Processing

Upload and process videos to extract audio fingerprints:

```python
from soundhash import VideosApi

videos_api = VideosApi(client)
video = videos_api.upload_video(
    file=open('video.mp4', 'rb'),
    title='My Video'
)

print(f"Processing job ID: {video.processing_job_id}")
```

### Real-time Streaming

Stream audio in real-time for instant matching:

```javascript
const ws = new WebSocket('wss://api.soundhash.io/ws/stream/client123');

ws.onopen = () => {
  // Start streaming audio data
  microphone.ondata = (audioChunk) => {
    ws.send(audioChunk);
  };
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'match') {
    console.log('Match found!', data.matches);
  }
};
```

### Webhooks

Get notified when events occur:

```python
from soundhash import WebhooksApi

webhooks_api = WebhooksApi(client)
webhook = webhooks_api.create_webhook(
    url='https://myapp.com/webhooks/soundhash',
    events=['video.processed', 'match.found'],
    secret='webhook-secret-key'
)
```

## 📖 Guides & Tutorials

### Getting Started

- [Authentication Guide](authentication.md) - API keys, JWT tokens, and OAuth
- [First Match Tutorial](tutorials/first-match.md) - Complete walkthrough
- [Error Handling](guides/error-handling.md) - Handling API errors gracefully

### Common Use Cases

- [Content ID System](tutorials/content-id.md) - Build a YouTube-like Content ID
- [Social Media Bot](tutorials/social-bot.md) - Create a Twitter/Discord bot
- [Copyright Detection](tutorials/copyright.md) - Detect unauthorized use
- [Music Recognition App](tutorials/shazam-clone.md) - Build a Shazam-like app

### Advanced Topics

- [Batch Processing](guides/batch-processing.md) - Process multiple files efficiently
- [Custom Fingerprints](guides/custom-fingerprints.md) - Advanced fingerprinting
- [Performance Optimization](guides/performance.md) - Scale to millions of queries
- [Multi-Region Deployment](guides/multi-region.md) - Global deployment

## 🔐 Authentication

SoundHash API supports multiple authentication methods:

### API Keys (Recommended for server-to-server)

```bash
curl -X GET "https://api.soundhash.io/api/v1/videos" \
  -H "X-API-Key: your_api_key_here"
```

### JWT Tokens (Recommended for user applications)

```bash
# 1. Get access token
curl -X POST "https://api.soundhash.io/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "password": "password"}'

# 2. Use token
curl -X GET "https://api.soundhash.io/api/v1/videos" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

See the [Authentication Guide](authentication.md) for complete details.

## 📊 Rate Limits & Quotas

All API endpoints are rate limited to ensure fair usage:

| Plan | Requests/min | Requests/day | Concurrent Connections |
|------|--------------|--------------|----------------------|
| Free | 60 | 1,000 | 2 |
| Starter | 300 | 10,000 | 5 |
| Pro | 1,200 | 100,000 | 20 |
| Enterprise | Custom | Custom | Custom |

Rate limit headers are included in every response:

```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 59
X-RateLimit-Reset: 1638360000
```

See [Rate Limits](rate-limits.md) for complete details.

## 🎤 Webhooks

Configure webhooks to receive real-time notifications:

### Available Events

- `video.uploaded` - Video file uploaded
- `video.processing` - Video processing started
- `video.processed` - Video processing completed
- `video.failed` - Video processing failed
- `match.found` - Audio match detected
- `fingerprint.created` - Fingerprint extracted
- `channel.ingested` - Channel ingestion completed

### Webhook Payload Example

```json
{
  "event": "video.processed",
  "timestamp": "2024-01-15T10:30:00Z",
  "data": {
    "video_id": 123,
    "title": "My Video",
    "duration": 180,
    "fingerprints_count": 2,
    "processing_time": 45.2
  }
}
```

See [Webhooks Guide](webhooks/index.md) for setup instructions.

## 📈 Analytics & Monitoring

Track your API usage and performance:

- **[Dashboard](https://api.soundhash.io/dashboard)** - Real-time metrics
- **[Usage Reports](https://api.soundhash.io/analytics)** - Detailed analytics
- **[API Status](https://status.soundhash.io)** - Service health monitoring

## 🆘 Support

Need help? We're here for you:

- **[Documentation](https://docs.soundhash.io)** - Comprehensive guides
- **[API Reference](reference.md)** - Complete endpoint documentation
- **[GitHub Issues](https://github.com/subculture-collective/soundhash/issues)** - Bug reports and feature requests
- **[Discord Community](https://discord.gg/soundhash)** - Chat with developers
- **[Email Support](mailto:support@soundhash.io)** - Direct support

## 📝 Changelog

Stay updated with the latest changes:

- [API Changelog](changelog.md) - Version history
- [Breaking Changes](breaking-changes.md) - Important updates
- [Deprecation Notice](deprecations.md) - Upcoming changes

## 🤝 Contributing

Help improve SoundHash:

- [Contribute Code](https://github.com/subculture-collective/soundhash/blob/main/CONTRIBUTING.md)
- [Report Bugs](https://github.com/subculture-collective/soundhash/issues/new?template=bug_report.md)
- [Request Features](https://github.com/subculture-collective/soundhash/issues/new?template=feature_request.md)
- [Improve Documentation](https://github.com/subculture-collective/soundhash/blob/main/docs/README.md)

## 📄 License

SoundHash is released under the [MIT License](https://github.com/subculture-collective/soundhash/blob/main/LICENSE).

---

Ready to get started? [Create your account](https://api.soundhash.io/signup) or [try the API playground](https://api.soundhash.io/docs)!
