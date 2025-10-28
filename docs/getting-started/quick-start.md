# Quick Start

Get SoundHash up and running in under 15 minutes with this quick start guide.

## What You'll Build

In this guide, you will:

1. Ingest videos from a YouTube channel
2. Process and fingerprint the audio
3. Query for matching clips
4. View results

**Estimated time:** 15 minutes

---

## Prerequisites

Make sure you've completed the [Installation](installation.md) and have:

- ✅ SoundHash installed
- ✅ Database initialized
- ✅ YouTube API configured

---

## Step 1: Verify Installation

First, let's verify everything is working:

```bash
# Test system
python scripts/test_system.py
```

You should see:

```
✓ Database connection: OK
✓ YouTube API: OK
✓ FFmpeg: OK
✓ System ready
```

---

## Step 2: Ingest Your First Channel

Let's ingest a few videos from a YouTube channel. We'll use the `--max-videos` flag to limit the number of videos.

```bash
python scripts/ingest_channels.py \
    --channels UCo_QGM_tJZOkOCIFi2ik5kA \
    --max-videos 5 \
    --log-level INFO
```

!!! tip "Choosing a Channel"
    
    You can use any YouTube channel ID. To find a channel ID:
    
    1. Go to the channel page on YouTube
    2. The ID is in the URL: `youtube.com/channel/CHANNEL_ID`
    3. Or use the channel handle: `youtube.com/@channelhandle`

### What's Happening?

The ingestion script:

1. **Fetches** video metadata from YouTube API
2. **Creates** database entries for each video
3. **Schedules** processing jobs
4. **Downloads** audio from each video
5. **Segments** audio into chunks
6. **Extracts** fingerprints using spectral analysis
7. **Stores** fingerprints in PostgreSQL

### Expected Output

```
[INFO] Starting channel ingestion...
[INFO] Processing channel: UCo_QGM_tJZOkOCIFi2ik5kA
[INFO] Found 5 videos to process
[INFO] ┌─────────────────────────────────────────────────┐
[INFO] │ Video: Example Video Title                     │
[INFO] │ Duration: 3:45                                  │
[INFO] │ Status: downloading                             │
[INFO] └─────────────────────────────────────────────────┘
[INFO] Processing: ████████████████████ 100% (1/5)
[INFO] ✓ Fingerprint extracted: 12 segments
[INFO] ✓ Stored in database
[INFO] All videos processed successfully!
```

---

## Step 3: Check Processing Status

View the status of your processed videos:

```python
from src.database.repositories import get_video_repository

repo = get_video_repository()
videos = repo.get_all_videos(limit=10)

for video in videos:
    status = "✓ Processed" if video.processed else "⧗ Pending"
    print(f"{status} - {video.title}")
```

Or using the CLI:

```bash
python scripts/test_system.py --check-status
```

---

## Step 4: Start the API Server

Now let's start the REST API server to query for matches:

```bash
python scripts/start_api.py
```

The server will start on `http://localhost:8000`

!!! success "API Server Started"
    
    Visit these endpoints:
    
    - **Interactive docs**: http://localhost:8000/docs
    - **ReDoc**: http://localhost:8000/redoc
    - **Health check**: http://localhost:8000/health

---

## Step 5: Register a User

Before querying, you need to register a user account:

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "demo_user",
    "email": "demo@example.com",
    "password": "SecurePass123!"
  }'
```

Response:

```json
{
  "id": 1,
  "username": "demo_user",
  "email": "demo@example.com",
  "created_at": "2024-01-01T12:00:00Z"
}
```

---

## Step 6: Login and Get Access Token

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=demo_user&password=SecurePass123!"
```

Response:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

Save the `access_token` - you'll need it for authenticated requests.

---

## Step 7: Query for Matches

Now let's find matches for a video clip:

```bash
curl -X POST http://localhost:8000/api/v1/matches/find \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "video_url": "https://youtube.com/watch?v=example",
    "start_time": 30,
    "end_time": 45
  }'
```

!!! tip "Using the Interactive Docs"
    
    The easiest way to test the API is using the interactive documentation at `/docs`:
    
    1. Click the **Authorize** button
    2. Enter your access token
    3. Try out the `/api/v1/matches/find` endpoint

### Expected Response

```json
{
  "query_id": "abc123",
  "matches": [
    {
      "video_id": "xyz789",
      "title": "Matching Video Title",
      "confidence": 0.95,
      "timestamp": 125.5,
      "similarity_score": 0.92
    }
  ],
  "processing_time": 0.234
}
```

---

## Step 8: View All Videos

List all processed videos:

```bash
curl -X GET http://localhost:8000/api/v1/videos \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

## What's Next?

Congratulations! You've successfully:

- ✅ Ingested videos from YouTube
- ✅ Processed and fingerprinted audio
- ✅ Started the API server
- ✅ Found audio matches

### Next Steps

<div class="grid cards" markdown>

-   :material-cog:{ .lg } **Configuration**
    
    ---
    
    Learn about all configuration options
    
    [Configuration Guide →](configuration.md)

-   :material-target:{ .lg } **First Match**
    
    ---
    
    Detailed tutorial on finding matches
    
    [First Match Guide →](first-match.md)

-   :material-api:{ .lg } **API Reference**
    
    ---
    
    Complete API documentation
    
    [API Docs →](../api/index.md)

-   :material-robot:{ .lg } **Social Media Bots**
    
    ---
    
    Set up Twitter and Reddit bots
    
    [Bot Setup →](../guides/bots.md)

</div>

---

## Common Issues

### Ingestion Fails

!!! failure "Error: Failed to download video"

    **Solution**: Configure YouTube cookies
    
    ```bash
    # Export cookies from your browser
    # See: https://github.com/yt-dlp/yt-dlp#how-do-i-pass-cookies-to-yt-dlp
    
    # Then set in .env:
    YT_COOKIES_FILE=/path/to/cookies.txt
    ```

### No Matches Found

!!! warning "No matches returned"

    **Possible causes**:
    
    1. **Insufficient data**: Process more videos
    2. **Time range too short**: Use at least 10-15 seconds
    3. **Quality issues**: Ensure audio is clear and not heavily modified

### API Authentication Fails

!!! failure "Error: 401 Unauthorized"

    **Solution**: Verify your access token is valid
    
    ```bash
    # Get a fresh token
    curl -X POST http://localhost:8000/api/v1/auth/login \
      -H "Content-Type: application/x-www-form-urlencoded" \
      -d "username=demo_user&password=SecurePass123!"
    ```

---

## Additional Resources

- [Configuration Reference](configuration.md)
- [API Authentication Guide](../api/authentication.md)
- [Troubleshooting Guide](../reference/troubleshooting.md)
- [Architecture Overview](../architecture/overview.md)
