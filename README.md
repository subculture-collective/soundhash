# SoundHash - Video Clip Matching System

[![CI](https://github.com/onnwee/soundhash/actions/workflows/ci.yml/badge.svg)](https://github.com/onnwee/soundhash/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/onnwee/soundhash/branch/main/graph/badge.svg)](https://codecov.io/gh/onnwee/soundhash)

A sophisticated system for matching audio clips from videos across social media platforms using audio fingerprinting and PostgreSQL.

## Table of Contents

- [Quick Start](#quick-start-target-15-minutes) - Get running in <15 minutes
- [Architecture Overview](#architecture-overview) - System design and data flow
- [Troubleshooting](#troubleshooting-common-issues) - Solutions to common problems
- [Usage](#usage) - Command-line options and examples
- [Security](#security-and-secrets-management) - Credential management

## Project Status

📋 **Roadmap**: [Issue #34](https://github.com/onnwee/soundhash/issues/34) | 🗂️ **Project Board**: [@onnwee's soundhash](https://github.com/users/onnwee/projects) | 🏁 **Milestones**: [View all](https://github.com/onnwee/soundhash/milestones)

## Features

- Audio fingerprinting using spectral analysis
- PostgreSQL database for scalable storage
- Social media bot integration (Twitter, Reddit)
- YouTube channel ingestion
- Real-time clip matching
- Beautiful colored logging with progress tracking

## Architecture Overview

SoundHash processes videos through a multi-stage pipeline:

```
┌─────────────────────────────────────────────────────────────────────┐
│                         SoundHash Pipeline                           │
└─────────────────────────────────────────────────────────────────────┘

1. INGESTION (channel_ingester.py)
   ├─ YouTube API → Fetch channel videos
   ├─ Create ProcessingJob entries (idempotent)
   └─ Store metadata in PostgreSQL
          ↓
2. VIDEO PROCESSING (video_processor.py)
   ├─ yt-dlp → Download best audio stream
   ├─ ffmpeg → Convert to mono WAV @ 16kHz
   └─ Segment into 90-second chunks
          ↓
3. FINGERPRINTING (audio_fingerprinting.py)
   ├─ STFT → Spectral analysis
   ├─ Peak detection → Extract features
   ├─ Normalize → Compact vector + MD5 hash
   └─ Store in PostgreSQL (audio_fingerprints table)
          ↓
4. MATCHING (future)
   ├─ Query clip → Extract fingerprint
   ├─ Compare → Correlation + Euclidean similarity
   └─ Return matched videos with confidence scores
```

### Key Components

- **Ingestion**: `src/ingestion/channel_ingester.py` - Async orchestration, idempotent job creation
- **Video I/O**: `src/core/video_processor.py` - yt-dlp + ffmpeg pipeline with cookie/proxy support
- **Fingerprints**: `src/core/audio_fingerprinting.py` - STFT, spectral peaks → compact vector + MD5
- **Database**: `src/database/{connection,models,repositories}.py` - SQLAlchemy engine/schema/DAOs
- **YouTube API**: `src/api/youtube_service.py` - OAuth flow, channel/video metadata
- **Config/Logging**: `config/{settings.py,logging_config.py}` - Centralized configuration

### Database Schema

- **channels**: YouTube channel metadata
- **videos**: Video information and processing status
- **audio_fingerprints**: Spectral fingerprint data for audio segments (vector + hash)
- **match_results**: Query results and similarity scores
- **processing_jobs**: Background job queue with status tracking

## Quick Start (🎯 Target: <15 minutes)

Choose your preferred setup method:

### Option A: Docker (Recommended - Fastest Setup)

**Prerequisites**: Docker and Docker Compose installed

**⏱️ Estimated time**: 5-10 minutes

```bash
# 1. Clone repository
git clone <repository-url> soundhash
cd soundhash

# 2. Configure environment
cp .env.example .env
# Edit .env with your settings (DATABASE_URL will be overridden for Docker)

# 3. Start services (PostgreSQL + App)
docker compose up -d

# 4. Initialize database
docker compose exec app python scripts/setup_database.py

# 5. Setup YouTube API (interactive OAuth flow)
docker compose exec app python scripts/setup_youtube_api.py

# 6. Test with limited videos
docker compose exec app python scripts/ingest_channels.py --dry-run --max-videos 5

# 7. View logs
docker compose logs -f app
```

**✅ Advantages**:
- No manual PostgreSQL or ffmpeg installation
- Isolated environment
- Production-like setup
- Easy cleanup with `docker compose down -v`

### Option B: Local Development

**Prerequisites**: Python 3.12+, PostgreSQL 12+, ffmpeg

**⏱️ Estimated time**: 10-15 minutes

```bash
# 1. Clone and setup virtual environment
git clone <repository-url> soundhash
cd soundhash
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Install system dependencies
# Ubuntu/Debian:
sudo apt update && sudo apt install postgresql postgresql-contrib ffmpeg
# macOS:
brew install postgresql ffmpeg

# 4. Setup PostgreSQL
createdb soundhash
# Optional: Create dedicated user
# psql -c "CREATE USER soundhash_user WITH PASSWORD 'your_password';"
# psql -c "GRANT ALL PRIVILEGES ON DATABASE soundhash TO soundhash_user;"

# 5. Configure environment
cp .env.example .env
# Edit .env with your database credentials and settings

# 6. Initialize database
python scripts/setup_database.py

# 7. Setup YouTube API (required)
python scripts/setup_youtube_api.py

# 8. Test with limited videos
python scripts/ingest_channels.py --dry-run --max-videos 5 --log-level DEBUG
```

**✅ Advantages**:
- Direct access to Python environment for debugging
- Faster iteration during development
- Full control over dependencies

### Comparison: Docker vs Local

| Feature | Docker 🐳 | Local 💻 |
|---------|-----------|---------|
| **Setup time** | 5-10 min | 10-15 min |
| **Prerequisites** | Docker only | Python, PostgreSQL, ffmpeg |
| **Isolation** | ✅ Full | ❌ System-wide |
| **Production parity** | ✅ High | ⚠️ Varies |
| **Debugging** | ⚠️ Via logs/exec | ✅ Direct |
| **Cleanup** | ✅ `docker compose down -v` | ⚠️ Manual |
| **Best for** | Quick start, CI/CD | Active development |

### What Happens After Setup?

After completing either setup method:

1. **Database Initialized**: Tables created (`channels`, `videos`, `audio_fingerprints`, `processing_jobs`)
2. **YouTube API Ready**: OAuth token stored in `token.json` for API access
3. **System Ready**: Can now ingest channels and process videos

**Next Steps**:

```bash
# 1. Configure target channels in .env
TARGET_CHANNELS=UCo_QGM_tJZOkOCIFi2ik5kA,UCDz8WxTg4R7FUTSz7GW2cYA

# 2. Ingest and process channels (start small!)
python scripts/ingest_channels.py --max-videos 10

# 3. Monitor progress in logs
tail -f logs/soundhash.log

# 4. Query database to see results
psql soundhash -c "SELECT COUNT(*) FROM audio_fingerprints;"
```

> **⚠️ Security Note**: See the [Security and Secrets Management](#security-and-secrets-management) section below for important information about handling credentials safely.

## Troubleshooting Common Issues

### 🚫 YouTube Download Failures / Rate Limiting

**Symptoms**: Downloads fail with "HTTP Error 429", "HTTP Error 403", "Video unavailable", or frequent timeouts

**Solutions** (in order of effectiveness):

1. **Use browser cookies** (Recommended):
   ```bash
   # Option 1: Export cookies to file
   # Use browser extension "Get cookies.txt LOCALLY" (Firefox/Chrome)
   # Save to cookies.txt in project root
   YT_COOKIES_FILE=./cookies.txt
   
   # Option 2: Extract from browser directly (easier)
   YT_COOKIES_FROM_BROWSER=firefox
   # Or with specific profile:
   YT_COOKIES_FROM_BROWSER=chrome:Profile 1
   # Or specify a different browser profile
   YT_COOKIES_FROM_BROWSER=chrome
   YT_BROWSER_PROFILE=Profile 1
   ```

2. **Configure proxy**:
   ```bash
   # Single proxy
   USE_PROXY=true
   PROXY_URL=http://proxy.example.com:8080
   
   # Or rotating proxy list (comma-separated)
   USE_PROXY=true
   PROXY_LIST=http://proxy1.example.com:8080,http://proxy2.example.com:8080
   ```

3. **Change player client** (if videos appear restricted):
   ```bash
   YT_PLAYER_CLIENT=android  # or ios, web_safari, tv, web_embedded
   ```

4. **Reduce concurrent downloads**:
   ```bash
   MAX_CONCURRENT_DOWNLOADS=1  # Default is 3
   ```

5. **Update yt-dlp** (fixes many issues):
   ```bash
   pip install --upgrade yt-dlp
   ```

**Understanding Error Messages**:

The system now provides specific remediation advice for common errors:

- **HTTP 403 Forbidden**: Video may be geo-restricted, age-restricted, or YouTube detected automation
  - ✅ Use authenticated cookies (YT_COOKIES_FILE or YT_COOKIES_FROM_BROWSER)
  - ✅ Configure proxy to change apparent location
  - ✅ Try different player client (YT_PLAYER_CLIENT=android)
  
- **HTTP 429 Too Many Requests**: YouTube rate limit exceeded
  - ✅ Reduce MAX_CONCURRENT_DOWNLOADS
  - ✅ Use authenticated cookies to get higher quota
  - ✅ Configure proxy rotation (PROXY_LIST)
  - ⏱️ System auto-retries with exponential backoff
  
- **HTTP 410 Gone**: Video has been removed or is no longer available
  - ⚠️ This is permanent - video cannot be retrieved
  - System will skip without retrying
  
- **Bot Detection**: "Sign in to confirm you're not a bot"
  - ✅ Set YT_COOKIES_FILE or YT_COOKIES_FROM_BROWSER
  - ✅ Update yt-dlp: `pip install --upgrade yt-dlp`

### 🎵 ffmpeg Issues

**Symptoms**: "ffmpeg not found", audio conversion fails, or "codec not supported"

**Solutions**:

1. **Verify ffmpeg installation**:
   ```bash
   ffmpeg -version
   # Should show version 4.0+ with libopus, libvorbis
   ```

2. **Install/reinstall ffmpeg**:
   ```bash
   # Ubuntu/Debian
   sudo apt update && sudo apt install ffmpeg
   
   # macOS
   brew install ffmpeg
   
   # Windows - Download from https://ffmpeg.org/download.html
   # Add to PATH environment variable
   ```

3. **Check PATH** (if installed but not found):
   ```bash
   which ffmpeg  # Linux/macOS
   where ffmpeg  # Windows
   ```

4. **Docker users**: ffmpeg is included in the Docker image, no action needed

### 🗄️ Database Connection Issues

**Symptoms**: "Connection refused", "Authentication failed", "Database does not exist"

**Solutions**:

1. **Check PostgreSQL is running**:
   ```bash
   # Linux
   sudo systemctl status postgresql
   sudo systemctl start postgresql
   
   # macOS
   brew services list
   brew services start postgresql
   
   # Docker
   docker compose ps
   ```

2. **Verify connection string** in `.env`:
   ```bash
   # Format: postgresql://user:password@host:port/dbname
   DATABASE_URL=postgresql://soundhash_user:password@localhost:5432/soundhash
   
   # Or use individual vars:
   DATABASE_HOST=localhost  # Use 'postgres' in Docker
   DATABASE_PORT=5432       # Use 5435 for Docker host access
   DATABASE_NAME=soundhash
   DATABASE_USER=soundhash_user
   DATABASE_PASSWORD=your_password
   ```

3. **Test connection manually**:
   ```bash
   psql -h localhost -U soundhash_user -d soundhash
   ```

4. **Create database if missing**:
   ```bash
   createdb soundhash
   # Or: psql -c "CREATE DATABASE soundhash;"
   ```

5. **Docker networking**:
   - From host: use `localhost:5435` (as configured in docker-compose.yml)
   - From app container: use `postgres:5432` (service name as host)

### 📦 Import/Dependency Errors

**Symptoms**: "ModuleNotFoundError", "No module named 'X'"

**Solutions**:

1. **Ensure virtual environment is activated**:
   ```bash
   source .venv/bin/activate  # Linux/macOS
   .venv\Scripts\activate     # Windows
   ```

2. **Reinstall dependencies**:
   ```bash
   pip install -r requirements.txt --upgrade
   ```

3. **Check Python version** (requires 3.12+):
   ```bash
   python --version
   ```

### 💾 Disk Space Issues

**Symptoms**: "No space left on device", temp directory fills up

**Solutions**:

1. **Enable automatic cleanup** in `.env`:
   ```bash
   CLEANUP_SEGMENTS_AFTER_PROCESSING=true
   ```

2. **Manually clean temp directory**:
   ```bash
   rm -rf ./temp/*  # or your TEMP_DIR path
   ```

3. **Monitor disk usage**:
   ```bash
   df -h .  # Check available space
   du -sh temp/  # Check temp directory size
   ```

4. **Process fewer videos at once**:
   ```bash
   python scripts/ingest_channels.py --max-videos 10
   ```

### 🔐 YouTube API Authentication Issues

**Symptoms**: "Invalid credentials", "Quota exceeded", "Unauthorized"

**Solutions**:

1. **Follow OAuth setup guide**: 
   - Create OAuth credentials in Google Cloud Console (type: Desktop App)
   - Download `credentials.json` and place it in the project root
   - Run `python scripts/setup_youtube_api.py` to generate `token.json`
   - For detailed steps, see [Google's official guide](https://developers.google.com/youtube/v3/guides/auth/client-side-web-apps)

2. **Regenerate token** if expired:
   ```bash
   rm token.json
   python scripts/setup_youtube_api.py
   ```

3. **Check credentials.json** is valid JSON from Google Cloud Console

4. **Verify API is enabled** in Google Cloud Console:
   - YouTube Data API v3 must be enabled for your project

5. **Check quota limits**:
   - Default: 10,000 units/day
   - 1 video = ~7 units, 1 channel = ~3 units
   - Monitor at: https://console.cloud.google.com/apis/dashboard

### 🐛 General Debugging Tips

1. **Enable debug logging**:
   ```bash
   python scripts/ingest_channels.py --log-level DEBUG
   ```

2. **Start with dry run**:
   ```bash
   python scripts/ingest_channels.py --dry-run --max-videos 5
   ```

3. **Test individual components**:
   ```python
   from src.core.video_processor import VideoProcessor
   from src.core.audio_fingerprinting import AudioFingerprinter
   
   processor = VideoProcessor()
   audio_file = processor.download_video_audio("https://youtube.com/watch?v=...")
   
   fingerprinter = AudioFingerprinter()
   fp = fingerprinter.extract_fingerprint(audio_file)
   print(f"Confidence: {fp['confidence_score']}")
   ```

4. **Check logs directory**: `./logs/` contains detailed error traces

5. **Verify environment variables**:
   ```bash
   python -c "from config.settings import Config; print(Config.DATABASE_URL)"
   ```

## Usage

### Command Line Options

The ingestion script supports various options for flexible processing:

```bash
# Basic ingestion (unlimited videos per channel)
python scripts/ingest_channels.py

# Process specific channels with all their videos
python scripts/ingest_channels.py --channels "UCo_QGM_tJZOkOCIFi2ik5kA,UCDz8WxTg4R7FUTSz7GW2cYA"

# Limit videos per channel (useful for testing)
python scripts/ingest_channels.py --max-videos 10

# Dry run (no actual processing, shows what would be ingested)
python scripts/ingest_channels.py --dry-run

# Set log level
python scripts/ingest_channels.py --log-level DEBUG

# Disable colored output
python scripts/ingest_channels.py --no-colors
```

**⚠️ Important**: By default, the system will fetch **ALL videos** from each channel. For channels with thousands of videos, this can take a very long time and generate a lot of processing jobs. Use `--max-videos` to limit the number if you want to test or process only recent content.

### Bot Deployment

- Configure API keys in `.env`
- Run Twitter bot: `python src/bots/twitter_bot.py`
- Run Reddit bot: `python src/bots/reddit_bot.py`

### Manual Testing

```python
from src.core.audio_fingerprinting import AudioFingerprinter
from src.core.video_processor import VideoProcessor

processor = VideoProcessor()
fingerprinter = AudioFingerprinter()

# Process a video
audio_file = processor.download_video_audio("https://youtube.com/watch?v=...")
fingerprint = fingerprinter.extract_fingerprint(audio_file)
```

## Detailed Architecture

For architecture overview and flow diagram, see the [Architecture Overview](#architecture-overview) section above.

### Directory Structure

- `src/core/` - Core audio processing and fingerprinting
- `src/database/` - Database models and operations  
- `src/bots/` - Social media bot implementations
- `src/ingestion/` - Channel data ingestion system
- `src/api/` - External API integrations (YouTube)
- `src/auth/` - Authentication and OAuth flows
- `config/` - Configuration management and logging
- `scripts/` - Utility scripts for setup and maintenance
- `tests/` - Test suite

### Additional Documentation

- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Detailed project structure
- **[INSTALL.md](INSTALL.md)** - Comprehensive installation guide with Docker and manual options
- **[YOUTUBE_OAUTH_SETUP.md](YOUTUBE_OAUTH_SETUP.md)** - YouTube API setup guide
- **[AUTH_SETUP.md](AUTH_SETUP.md)** - Twitter & Reddit authentication
- **[SECURITY.md](SECURITY.md)** - Security best practices and secrets management

## Security and Secrets Management

> 📖 **Quick Reference:** See [SECURITY.md](SECURITY.md) for a condensed checklist and quick reference guide.

### Overview

SoundHash requires various API credentials and tokens to function. It's critical to handle these securely to prevent unauthorized access to your accounts and services.

### Protected Files

The following files contain sensitive information and are automatically excluded from version control via `.gitignore`:

- **`.env`** - Environment variables including API keys, database passwords, and tokens
- **`credentials.json`** - Google OAuth 2.0 client credentials for YouTube API
- **`token.json`** - OAuth refresh tokens (generated after authentication)
- **`cookies.txt`** - Browser cookies for yt-dlp (if used)

### Safe Credential Handling

#### Local Development

1. **Use `.env` for configuration**:
   ```bash
   cp .env.example .env
   # Edit .env with your actual credentials
   ```

2. **YouTube OAuth Setup**:
   - Download `credentials.json` from [Google Cloud Console](https://console.cloud.google.com/)
   - Place it in the project root (it's automatically ignored by git)
   - Run `python scripts/setup_youtube_api.py` to generate `token.json`
   - Both files remain local only - never commit them

3. **Verify `.gitignore` protection**:
   ```bash
   git status --ignored
   # Your secret files should appear in the ignored list
   ```

#### GitHub Actions / CI

For running workflows that need credentials:

1. **Use GitHub Secrets** (Settings → Secrets and variables → Actions):
   - `DATABASE_URL` - PostgreSQL connection string
   - `YOUTUBE_API_KEY` - For YouTube Data API (if using API key method)
   - `TWITTER_*` - Twitter API credentials
   - `REDDIT_*` - Reddit API credentials

2. **Reference in workflows**:
   ```yaml
   env:
     DATABASE_URL: ${{ secrets.DATABASE_URL }}
     YOUTUBE_API_KEY: ${{ secrets.YOUTUBE_API_KEY }}
   ```

#### Production Deployment

For production deployments, use proper secrets management:

- **Docker**: Use Docker secrets or environment variables
- **Cloud Platforms**: Use AWS Secrets Manager, Google Secret Manager, or Azure Key Vault
- **Kubernetes**: Use Kubernetes Secrets with proper RBAC

### Secret Scanning

This repository uses [Gitleaks](https://github.com/gitleaks/gitleaks) in CI to automatically scan for accidentally committed secrets:

- **Automatic scanning** on every push and pull request
- **CI fails** if secrets are detected
- **Custom rules** for YouTube API keys, Twitter tokens, Reddit credentials, etc.
- **Weekly scheduled scans** to catch issues early

If the CI fails due to detected secrets:

1. **Rotate the compromised credential** immediately
2. **Remove the secret** from all commits (use `git filter-branch` or `BFG Repo-Cleaner`)
3. **Update your local `.env`** with the new credential
4. **Never commit the secret again**

### Best Practices

✅ **DO**:
- Use `.env` for all secrets and credentials
- Add sensitive files to `.gitignore` before creating them
- Use GitHub Secrets for CI/CD credentials
- Rotate credentials regularly
- Use least-privilege access principles
- Review `.gitignore` before committing new files

❌ **DON'T**:
- Commit `.env`, `credentials.json`, `token.json`, or `cookies.txt`
- Store secrets in code, comments, or documentation
- Share credentials via email, chat, or unsecured channels
- Use production credentials in development
- Hardcode API keys or passwords in Python files

### Credential Rotation

If you suspect a credential has been compromised:

1. **Immediately revoke** the credential at the service provider
2. **Generate a new** credential
3. **Update** your `.env` and/or GitHub Secrets
4. **Audit** access logs for unauthorized usage
5. **Notify** team members if applicable

### Additional Resources

- [YouTube OAuth Setup Guide](YOUTUBE_OAUTH_SETUP.md)
- [Twitter & Reddit Auth Setup](AUTH_SETUP.md)
- [GitHub Secrets Documentation](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [OWASP Secrets Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)

## Performance Tips & Best Practices

### Development Workflow

1. **Start Small**: Always test with `--max-videos 5` and `--dry-run` first
2. **Use Debug Logging**: Add `--log-level DEBUG` when troubleshooting
3. **Monitor Resources**: Watch disk space (`du -sh temp/`) and database size
4. **Enable Cleanup**: Set `CLEANUP_SEGMENTS_AFTER_PROCESSING=true` to save disk space

### Production Considerations

1. **Rate Limiting**: 
   - Use cookies from authenticated session
   - Configure proxy rotation for high-volume processing
   - Respect YouTube API quotas (10,000 units/day default)

2. **Resource Management**:
   - Set appropriate `MAX_CONCURRENT_DOWNLOADS` (1-3 recommended)
   - Monitor PostgreSQL performance with `EXPLAIN ANALYZE`
   - Consider connection pooling for multiple workers

3. **Reliability**:
   - Enable automatic cleanup to prevent disk exhaustion
   - Use Docker for consistent deployment environment
   - Implement monitoring and alerting for job failures

4. **Security**:
   - Never commit `.env`, `credentials.json`, `token.json`, or `cookies.txt`
   - Use GitHub Secrets for CI/CD credentials
   - Rotate API keys regularly
   - Use least-privilege database users

### Common Gotchas

⚠️ **Unlimited ingestion is expensive**: Without `--max-videos`, the system fetches ALL videos from each channel (potentially thousands). This can take hours and consume significant resources.

⚠️ **Cookie authentication**: yt-dlp works better with authenticated cookies. Use `YT_COOKIES_FROM_BROWSER=firefox` for automatic extraction.

⚠️ **Database driver**: The system auto-selects the `psycopg` driver. No manual installation needed.

⚠️ **Temp directory bloat**: Without cleanup enabled, audio segments accumulate. Enable `CLEANUP_SEGMENTS_AFTER_PROCESSING` or manually clean `./temp/` periodically.

### Useful Commands

```bash
# Check database size
psql soundhash -c "SELECT pg_size_pretty(pg_database_size('soundhash'));"

# List processing job statuses
psql soundhash -c "SELECT status, COUNT(*) FROM processing_jobs GROUP BY status;"

# Find failed jobs
psql soundhash -c "SELECT * FROM processing_jobs WHERE status = 'failed' LIMIT 10;"

# Clean up old jobs (careful!)
psql soundhash -c "DELETE FROM processing_jobs WHERE status = 'completed' AND updated_at < NOW() - INTERVAL '7 days';"

# Monitor real-time logs
tail -f logs/soundhash.log

# Test a single video manually
python -c "from src.core.video_processor import VideoProcessor; print(VideoProcessor().download_video_audio('https://youtube.com/watch?v=...'))"
```

## FAQ

**Q: How long does it take to process one video?**  
A: Depends on video length and your hardware. Typically 30-60 seconds per video (download + segmentation + fingerprinting).

**Q: Can I process multiple channels simultaneously?**  
A: Yes, the system processes channels concurrently. Control concurrency with `MAX_CONCURRENT_DOWNLOADS` in `.env`.

**Q: What happens if ingestion is interrupted?**  
A: The system is idempotent - rerunning will skip already-created jobs. Use `--only-process` to process existing jobs without re-ingesting.

**Q: How do I reset everything?**  
A: Run `fresh_start.sh` or manually: `dropdb soundhash && createdb soundhash && python scripts/setup_database.py`

**Q: Can I use API key instead of OAuth?**  
A: OAuth is required for channel listing. API key alone has limited functionality.

**Q: How much disk space do I need?**  
A: Varies by usage. Estimate ~50MB per video (audio + segments). Enable cleanup to reduce footprint.

**Q: Does this work with private/unlisted videos?**  
A: Only if your authenticated cookies have access to those videos.
