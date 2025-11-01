# Quick Start Tutorial

Get started with SoundHash API in 5 minutes! This tutorial will guide you through your first API integration.

## Prerequisites

- A SoundHash account (sign up at [api.soundhash.io/signup](https://api.soundhash.io/signup))
- Python 3.8+ or Node.js 14+ installed
- An audio file or video URL to test with

## Step 1: Get Your API Key

1. Log in to the [SoundHash Dashboard](https://api.soundhash.io/dashboard)
2. Navigate to **API Keys**
3. Click **Create New API Key**
4. Copy your API key (you won't see it again!)

## Step 2: Install the SDK

=== "Python"
    ```bash
    pip install soundhash-client
    ```

=== "JavaScript"
    ```bash
    npm install @soundhash/client
    ```

=== "cURL"
    No installation needed - use cURL directly!

## Step 3: Make Your First Request

### List Videos

=== "Python"
    ```python
    from soundhash import ApiClient, Configuration, VideosApi
    
    # Configure API client
    config = Configuration()
    config.host = "https://api.soundhash.io"
    config.access_token = "YOUR_API_KEY"
    
    # Create API instance
    with ApiClient(config) as client:
        videos_api = VideosApi(client)
        
        # List videos
        videos = videos_api.list_videos(limit=5)
        
        print(f"Found {len(videos)} videos:")
        for video in videos:
            print(f"  - {video.title} ({video.duration}s)")
    ```

=== "JavaScript"
    ```javascript
    const SoundHash = require('@soundhash/client');
    
    // Configure API client
    const client = new SoundHash.ApiClient();
    client.basePath = 'https://api.soundhash.io';
    client.authentications['bearerAuth'].accessToken = 'YOUR_API_KEY';
    
    // Create API instance
    const videosApi = new SoundHash.VideosApi(client);
    
    // List videos
    videosApi.listVideos({ limit: 5 }, (error, videos) => {
      if (error) {
        console.error('Error:', error);
        return;
      }
      
      console.log(`Found ${videos.length} videos:`);
      videos.forEach(video => {
        console.log(`  - ${video.title} (${video.duration}s)`);
      });
    });
    ```

=== "cURL"
    ```bash
    curl -X GET "https://api.soundhash.io/api/v1/videos?limit=5" \
      -H "Authorization: Bearer YOUR_API_KEY" \
      -H "Accept: application/json"
    ```

**Expected Response:**
```json
{
  "data": [
    {
      "id": 1,
      "title": "Example Video",
      "duration": 180,
      "status": "processed",
      "created_at": "2024-01-15T10:00:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "per_page": 5
}
```

## Step 4: Upload and Process a Video

=== "Python"
    ```python
    # Upload a video
    with open('video.mp4', 'rb') as f:
        video = videos_api.upload_video(
            file=f,
            title='My Test Video'
        )
    
    print(f"Video uploaded: {video.id}")
    print(f"Processing job: {video.processing_job_id}")
    
    # Check processing status
    import time
    while video.status != 'processed':
        time.sleep(5)
        video = videos_api.get_video(video.id)
        print(f"Status: {video.status}")
    
    print("✅ Video processed successfully!")
    print(f"Fingerprints: {len(video.fingerprints)}")
    ```

=== "JavaScript"
    ```javascript
    const fs = require('fs');
    
    // Upload a video
    const file = fs.readFileSync('video.mp4');
    videosApi.uploadVideo(
      { file, title: 'My Test Video' },
      async (error, video) => {
        if (error) {
          console.error('Error:', error);
          return;
        }
        
        console.log(`Video uploaded: ${video.id}`);
        console.log(`Processing job: ${video.processing_job_id}`);
        
        // Poll for completion (simplified for example)
        const checkStatus = () => {
          videosApi.getVideo(video.id, (error, updatedVideo) => {
            if (error) {
              console.error('Error:', error);
              return;
            }
            
            console.log(`Status: ${updatedVideo.status}`);
            if (updatedVideo.status !== 'processed') {
              setTimeout(checkStatus, 5000);
            } else {
              console.log('✅ Video processed successfully!');
              console.log(`Fingerprints: ${updatedVideo.fingerprints.length}`);
            }
          });
        };
        
        checkStatus();
      }
    );
    ```

=== "cURL"
    ```bash
    # Upload video
    curl -X POST "https://api.soundhash.io/api/v1/videos" \
      -H "Authorization: Bearer YOUR_API_KEY" \
      -F "file=@video.mp4" \
      -F "title=My Test Video"
    
    # Check status (replace VIDEO_ID)
    curl -X GET "https://api.soundhash.io/api/v1/videos/VIDEO_ID" \
      -H "Authorization: Bearer YOUR_API_KEY"
    ```

## Step 5: Find Matches

Once you have videos processed, you can search for matches:

=== "Python"
    ```python
    from soundhash import MatchesApi
    
    matches_api = MatchesApi(client)
    
    # Find matches for an audio clip
    with open('audio_clip.wav', 'rb') as f:
        result = matches_api.find_matches(
            audio_file=f,
            min_confidence=0.8
        )
    
    if result.matches:
        print(f"Found {len(result.matches)} matches:")
        for match in result.matches:
            print(f"  - {match.video.title}")
            print(f"    Confidence: {match.confidence:.1%}")
            print(f"    Time: {match.start_time}s - {match.end_time}s")
    else:
        print("No matches found")
    ```

=== "JavaScript"
    ```javascript
    const matchesApi = new SoundHash.MatchesApi(client);
    
    // Find matches for an audio clip
    const audioFile = fs.readFileSync('audio_clip.wav');
    matchesApi.findMatches(
      { audio_file: audioFile, min_confidence: 0.8 },
      (error, result) => {
        if (error) {
          console.error('Error:', error);
          return;
        }
        
        if (result.matches && result.matches.length > 0) {
          console.log(`Found ${result.matches.length} matches:`);
          result.matches.forEach(match => {
            console.log(`  - ${match.video.title}`);
            console.log(`    Confidence: ${(match.confidence * 100).toFixed(1)}%`);
            console.log(`    Time: ${match.start_time}s - ${match.end_time}s`);
          });
        } else {
          console.log('No matches found');
        }
      }
    );
    ```

=== "cURL"
    ```bash
    curl -X POST "https://api.soundhash.io/api/v1/matches/find" \
      -H "Authorization: Bearer YOUR_API_KEY" \
      -F "audio_file=@audio_clip.wav" \
      -F "min_confidence=0.8"
    ```

**Expected Response:**
```json
{
  "query_id": "q_abc123",
  "matches": [
    {
      "video_id": 1,
      "title": "Example Video",
      "confidence": 0.95,
      "start_time": 45,
      "end_time": 60,
      "similarity_score": 0.94
    }
  ],
  "processing_time": 0.25
}
```

## Step 6: Set Up Webhooks (Optional)

Get notified when videos are processed:

=== "Python"
    ```python
    from soundhash import WebhooksApi
    
    webhooks_api = WebhooksApi(client)
    
    # Create a webhook
    webhook = webhooks_api.create_webhook(
        url='https://myapp.com/webhooks/soundhash',
        events=['video.processed', 'match.found'],
        secret='my-webhook-secret'
    )
    
    print(f"Webhook created: {webhook.id}")
    print(f"URL: {webhook.url}")
    ```

=== "JavaScript"
    ```javascript
    const webhooksApi = new SoundHash.WebhooksApi(client);
    
    // Create a webhook
    webhooksApi.createWebhook({
      url: 'https://myapp.com/webhooks/soundhash',
      events: ['video.processed', 'match.found'],
      secret: 'my-webhook-secret'
    }, (error, webhook) => {
      if (error) {
        console.error('Error:', error);
        return;
      }
      
      console.log(`Webhook created: ${webhook.id}`);
      console.log(`URL: ${webhook.url}`);
    });
    ```

=== "cURL"
    ```bash
    curl -X POST "https://api.soundhash.io/api/v1/webhooks" \
      -H "Authorization: Bearer YOUR_API_KEY" \
      -H "Content-Type: application/json" \
      -d '{
        "url": "https://myapp.com/webhooks/soundhash",
        "events": ["video.processed", "match.found"],
        "secret": "my-webhook-secret"
      }'
    ```

See [Webhook Documentation](../webhooks/index.md) for implementation details.

## Next Steps

Congratulations! You've completed the quick start tutorial. Here's what to explore next:

1. **[Authentication Guide](../authentication.md)** - Learn about JWT tokens and API keys
2. **[Rate Limits](../rate-limits.md)** - Understand rate limiting and best practices
3. **[Webhooks](../webhooks/index.md)** - Set up event notifications
4. **[API Reference](../reference.md)** - Explore all available endpoints
5. **[Code Examples](examples.md)** - See real-world implementations

## Common Issues

### "Unauthorized" Error

Make sure your API key is correct and included in the request:
```
Authorization: Bearer YOUR_API_KEY
```

### Rate Limited

If you get a 429 error, you've exceeded your rate limit. Wait a few seconds and try again. See [Rate Limits](../rate-limits.md) for details.

### Video Processing Takes Too Long

Video processing time depends on video length and server load. Use webhooks to get notified when processing completes instead of polling.

## Need Help?

- [API Documentation](../index.md)
- [GitHub Issues](https://github.com/subculture-collective/soundhash/issues)
- [Discord Community](https://discord.gg/soundhash)
- [Email Support](mailto:support@soundhash.io)
