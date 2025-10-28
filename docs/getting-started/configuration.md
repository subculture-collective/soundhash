# Configuration

This guide explains all configuration options available in SoundHash.

## Configuration File

SoundHash uses environment variables for configuration, stored in a `.env` file in the project root.

```bash
# Create from example
cp .env.example .env

# Edit with your settings
nano .env  # or vim, code, etc.
```

---

## Database Configuration

### Connection Settings

=== "Using DATABASE_URL"

    ```env
    DATABASE_URL=postgresql://user:password@host:port/database
    ```
    
    Example:
    ```env
    DATABASE_URL=postgresql://soundhash:secret@localhost:5432/soundhash
    ```

=== "Using Individual Settings"

    ```env
    DB_HOST=localhost
    DB_PORT=5432
    DB_NAME=soundhash
    DB_USER=soundhash_user
    DB_PASSWORD=your_password
    ```

### Connection Pooling

Control database connection pool behavior:

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_POOL_SIZE` | 10 | Base connection pool size |
| `DATABASE_MAX_OVERFLOW` | 20 | Additional connections under load |
| `DATABASE_POOL_TIMEOUT` | 30 | Wait time for connection (seconds) |
| `DATABASE_POOL_RECYCLE` | 3600 | Recycle connections after (seconds) |
| `DATABASE_ECHO` | false | Enable SQL query logging |
| `DATABASE_STATEMENT_TIMEOUT` | 30000 | Query timeout (milliseconds) |

!!! tip "Performance Tuning"
    
    For high-traffic deployments:
    
    - Increase `DATABASE_POOL_SIZE` to 20-50
    - Set `DATABASE_MAX_OVERFLOW` to 50-100
    - Enable `DATABASE_ECHO=false` in production
    - Set `DATABASE_STATEMENT_TIMEOUT` based on your queries

---

## YouTube Configuration

### API Credentials

```env
YOUTUBE_API_KEY=your_api_key
YOUTUBE_OAUTH_CLIENT_ID=your_client_id.apps.googleusercontent.com
YOUTUBE_OAUTH_CLIENT_SECRET=your_client_secret
```

→ See [YouTube Setup Guide](../guides/youtube-setup.md) for obtaining credentials.

### Target Channels

```env
TARGET_CHANNELS=UCo_QGM_tJZOkOCIFi2ik5kA,UCDz8WxTg4R7FUTSz7GW2cYA
```

Comma-separated list of YouTube channel IDs to process.

### Download Hardening

Configure yt-dlp for reliability:

=== "Cookie Authentication"

    ```env
    # From file
    YT_COOKIES_FILE=/path/to/cookies.txt
    
    # OR from browser
    YT_COOKIES_FROM_BROWSER=firefox
    YT_BROWSER_PROFILE=default
    
    # Browser options: chrome, chromium, firefox, brave, edge
    ```

=== "Proxy Configuration"

    ```env
    USE_PROXY=true
    PROXY_URL=http://proxy.example.com:8080
    
    # OR use proxy list
    PROXY_LIST=/path/to/proxies.txt
    ```

=== "Player Client Override"

    ```env
    # Use if videos appear restricted
    YT_PLAYER_CLIENT=android
    
    # Options: android, ios, web_safari, tv, web_embedded
    ```

=== "Caching"

    ```env
    YT_DLP_CACHE_DIR=./cache/yt-dlp
    ENABLE_YT_DLP_CACHE=true
    ```

!!! info "Cookie Extraction"
    
    To extract cookies from your browser:
    
    1. Install a browser extension like "Get cookies.txt"
    2. Visit YouTube while logged in
    3. Export cookies to a file
    4. Set `YT_COOKIES_FILE` to the file path

---

## Processing Configuration

### Audio Processing

```env
SEGMENT_LENGTH_SECONDS=90
FINGERPRINT_SAMPLE_RATE=16000

!!! warning "Changing These Values"
    
    Changing these values after processing videos will make new fingerprints incompatible with old ones. Consider:
    
    - Create a new database for different settings
    - Reprocess all existing videos
    - Document the settings used

### Concurrent Processing

```env
MAX_CONCURRENT_DOWNLOADS=3
MAX_CONCURRENT_CHANNELS=2
```

| Variable | Default | Description |
|----------|---------|-------------|
| `MAX_CONCURRENT_DOWNLOADS` | 3 | Parallel video downloads |
| `MAX_CONCURRENT_CHANNELS` | 2 | Channels processed simultaneously |

!!! tip "Performance vs. Rate Limiting"
    
    Higher values = faster processing but increased risk of rate limiting.
    
    - Start with defaults
    - Increase gradually if stable
    - Reduce if encountering errors

### File Management

```env
TEMP_DIR=./temp
KEEP_ORIGINAL_AUDIO=true
CLEANUP_SEGMENTS_AFTER_PROCESSING=true
```

| Variable | Default | Description |
|----------|---------|-------------|
| `TEMP_DIR` | ./temp | Temporary file directory |
| `KEEP_ORIGINAL_AUDIO` | true | Keep downloaded audio files |
| `CLEANUP_SEGMENTS_AFTER_PROCESSING` | true | Delete segments after fingerprinting |

---

## API Configuration

### Server Settings

```env
API_HOST=0.0.0.0
API_PORT=8000
API_TITLE=SoundHash API
API_VERSION=1.0.0
API_DESCRIPTION=Audio fingerprinting and matching API
```

### Authentication

```env
API_SECRET_KEY=your-secret-key-change-this-in-production
API_ALGORITHM=HS256
API_ACCESS_TOKEN_EXPIRE_MINUTES=30
API_REFRESH_TOKEN_EXPIRE_DAYS=7
```

!!! danger "Security"
    
    Generate a secure secret key:
    
    ```bash
    openssl rand -hex 32
    ```
    
    **Never** commit your secret key to version control!

### Rate Limiting

```env
API_RATE_LIMIT_PER_MINUTE=60
```

| Variable | Default | Description |
|----------|---------|-------------|
| `API_RATE_LIMIT_PER_MINUTE` | 60 | Requests per minute per API key/IP |

### CORS

```env
API_CORS_ORIGINS=http://localhost:3000,http://localhost:8000
```

Comma-separated list of allowed origins for CORS.

---

## Social Media Bots

### Twitter

```env
TWITTER_BEARER_TOKEN=your_bearer_token
TWITTER_CONSUMER_KEY=your_consumer_key
TWITTER_CONSUMER_SECRET=your_consumer_secret
TWITTER_ACCESS_TOKEN=your_access_token
TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret
```

### Reddit

```env
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
REDDIT_USER_AGENT=soundhash_bot_v1.0
REDDIT_REFRESH_TOKEN=your_refresh_token
REDDIT_SUBREDDITS=musicid,tipofmytongue
```

→ See [Bot Setup Guide](../guides/bots.md) for configuration details.

---

## Caching Configuration

### Redis

```env
REDIS_ENABLED=false
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
CACHE_TTL_SECONDS=300
```

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_ENABLED` | false | Enable Redis caching |
| `REDIS_HOST` | localhost | Redis server host |
| `REDIS_PORT` | 6379 | Redis server port |
| `REDIS_DB` | 0 | Redis database number |
| `CACHE_TTL_SECONDS` | 300 | Cache expiration (seconds) |

!!! info "When to Enable Redis"
    
    Enable Redis caching if:
    
    - You have frequent repeated queries
    - Response time is critical
    - You're running in production with multiple workers

---

## Environment-Specific Configurations

### Development

```env title=".env.development"
DATABASE_ECHO=true
MAX_CONCURRENT_DOWNLOADS=1
API_RATE_LIMIT_PER_MINUTE=1000
CLEANUP_SEGMENTS_AFTER_PROCESSING=false
```

### Production

```env title=".env.production"
DATABASE_ECHO=false
DATABASE_POOL_SIZE=20
MAX_CONCURRENT_DOWNLOADS=5
API_RATE_LIMIT_PER_MINUTE=60
CLEANUP_SEGMENTS_AFTER_PROCESSING=true
REDIS_ENABLED=true
```

---

## Validation

Validate your configuration:

```bash
python scripts/test_system.py
```

This checks:

- Database connectivity
- YouTube API access
- FFmpeg availability
- File system permissions

---

## Configuration Best Practices

### Security

1. **Never commit `.env` files** to version control
2. **Use strong passwords** for database and API keys
3. **Rotate credentials** regularly
4. **Restrict file permissions**: `chmod 600 .env`

### Performance

1. **Tune connection pools** based on workload
2. **Enable caching** for production
3. **Monitor resource usage** and adjust accordingly
4. **Use proxies** for rate-limited APIs

### Reliability

1. **Configure cookies** for YouTube downloads
2. **Set appropriate timeouts** to avoid hanging
3. **Enable cleanup** to prevent disk space issues
4. **Use retries** with exponential backoff

---

## Troubleshooting

### Configuration Not Loading

!!! failure "Environment variables not recognized"

    **Solution**: Ensure `.env` file is in project root
    
    ```bash
    ls -la .env
    # Should show the file
    
    # Check for syntax errors
    cat .env | grep -v '^#' | grep -v '^$'
    ```

### Invalid Values

!!! failure "ValueError: invalid literal for int()"

    **Solution**: Check numeric values in `.env`
    
    - Remove quotes around numbers
    - Ensure boolean values are lowercase: `true`/`false`

---

## Next Steps

- [First Match Tutorial](first-match.md)
- [API Reference](../api/index.md)
- [Deployment Guide](../deployment/docker.md)
- [Troubleshooting](../reference/troubleshooting.md)
