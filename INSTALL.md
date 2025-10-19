# SoundHash Installation Guide

## Prerequisites

1. **Python 3.12+**

2. **PostgreSQL** (version 12+)

3. **ffmpeg** (for audio processing)

4. **Git** (for version control)

## Installation Steps

### 1. Clone Repository

```bash
git clone <repository-url> soundhash
cd soundhash
```

### 2. Create Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Install System Dependencies

**Ubuntu/Debian:**

```bash
sudo apt update
sudo apt install postgresql postgresql-contrib ffmpeg
```

**macOS:**

```bash
brew install postgresql ffmpeg
```

**Windows:**

- Install PostgreSQL from [official website](https://www.postgresql.org/download/windows/)
- Install ffmpeg from [official website](https://ffmpeg.org/download.html)

### 5. Setup PostgreSQL Database

```bash
# Start PostgreSQL service (if not already running)
sudo systemctl start postgresql  # Linux
brew services start postgresql   # macOS

# Create database
createdb soundhash

# Create user (optional)
psql -d soundhash -c "CREATE USER soundhash_user WITH PASSWORD 'your_password';"
psql -d soundhash -c "GRANT ALL PRIVILEGES ON DATABASE soundhash TO soundhash_user;"
```

### 6. Configure Environment

```bash
cp .env.example .env
# Edit .env with your settings
```

Key environment variables:

- `DATABASE_URL` - PostgreSQL connection string
- `TARGET_CHANNELS` - YouTube channel IDs to process
- `YT_COOKIES_FILE` - Path to YouTube cookies (optional)
- `PROXY_URL` - Proxy configuration (optional)

### 7. Initialize Database

The database schema is managed using Alembic migrations for safe schema evolution:

```bash
# Apply all migrations to create/update the database schema
alembic upgrade head
```

Alternatively, use the setup script which runs migrations automatically:

```bash
python scripts/setup_database.py
```

**For developers**: When making changes to database models in `src/database/models.py`, you must create a new migration:

```bash
# Generate a new migration after model changes
alembic revision --autogenerate -m "Description of your changes"

# Review the generated migration file in alembic/versions/
# Then apply it
alembic upgrade head
```

### 8. Setup YouTube API (Required)

Follow the instructions in `YOUTUBE_OAUTH_SETUP.md` to:

1. Create a Google Cloud project
2. Enable YouTube Data API v3
3. Create OAuth2 credentials
4. Run the authentication flow

```bash
python scripts/setup_youtube_api.py
```

### 9. Test Installation

```bash
# Test database connection
python scripts/test_system.py

# Test with a small batch
python scripts/ingest_channels.py --dry-run --max-videos 5
```

## Docker Installation (Recommended)

### Prerequisites

- Docker
- Docker Compose

### Steps

1. Clone repository:

```bash
git clone <repository-url> soundhash
cd soundhash
```

2. Configure environment:

```bash
cp .env.example .env
# Edit .env with your settings
```

3. Start services:

```bash
docker compose up -d
```

4. Initialize database:

```bash
docker compose exec app python scripts/setup_database.py
```

5. Setup YouTube API:

```bash
docker compose exec app python scripts/setup_youtube_api.py
```

6. Verify installation:

```bash
docker compose logs app
```

## Manual Installation (Without Docker)

### Prerequisites for Manual Setup

1. **PostgreSQL** (version 12+)
2. **Python** (version 3.8+)
3. **FFmpeg** (for audio processing)
4. **Git** (for version control)

### Manual Installation Steps

```bash
cp .env.example .env
# Edit .env with database credentials, API keys, etc.
```

Important environment variables:

- `DATABASE_URL` or individual DB settings (`DB_HOST`, `DB_PORT`, etc.)
- `TARGET_CHANNELS` - Comma-separated YouTube channel IDs
- `SEGMENT_LENGTH_SECONDS` - Audio segment length (default: 10)
- `FINGERPRINT_SAMPLE_RATE` - Audio sample rate (default: 16000)
- `TEMP_DIR` - Temporary files directory
- `CLEANUP_SEGMENTS_AFTER_PROCESSING` - Auto-cleanup flag

## Configuration

### Database Configuration

Edit `.env` file:

```env
DATABASE_URL=postgresql://soundhash_user:your_password@localhost:5432/soundhash

# Or use individual settings:
DB_HOST=localhost
DB_PORT=5432
DB_NAME=soundhash
DB_USER=soundhash_user
DB_PASSWORD=your_password
```

### YouTube Access Configuration

For better reliability, configure cookies and/or proxy:

```env
# Cookie authentication (recommended)
YT_COOKIES_FILE=/path/to/cookies.txt
# OR
YT_COOKIES_FROM_BROWSER=firefox
# OR with profile
YT_COOKIES_FROM_BROWSER=chrome:Profile 1

# Proxy configuration (optional)
USE_PROXY=true
PROXY_URL=http://proxy.example.com:8080
# OR proxy list
PROXY_LIST=/path/to/proxies.txt

# Client override (if needed)
YT_PLAYER_CLIENT=android
```

### Processing Configuration

```env
SEGMENT_LENGTH_SECONDS=10
FINGERPRINT_SAMPLE_RATE=16000
TEMP_DIR=/tmp/soundhash
CLEANUP_SEGMENTS_AFTER_PROCESSING=true
MAX_CONCURRENT_DOWNLOADS=3
```

## Running the System

### Ingestion

```bash
# Process all configured channels
python scripts/ingest_channels.py

# Process specific channels
python scripts/ingest_channels.py --channels "UCo_QGM_tJZOkOCIFi2ik5kA,UCDz8WxTg4R7FUTSz7GW2cYA"

# Limit number of videos per channel
python scripts/ingest_channels.py --max-videos 10

# Dry run (no actual processing)
python scripts/ingest_channels.py --dry-run

# Only process existing jobs (skip ingestion)
python scripts/ingest_channels.py --only-process

# Adjust log level
python scripts/ingest_channels.py --log-level DEBUG

# Disable colored output
python scripts/ingest_channels.py --no-colors
```

### Bots

```bash
# Twitter bot
python src/bots/twitter_bot.py

# Reddit bot
python src/bots/reddit_bot.py
```

## Testing

### Manual Testing

```python
from src.core.audio_fingerprinting import AudioFingerprinter
from src.core.video_processor import VideoProcessor

processor = VideoProcessor()
fingerprinter = AudioFingerprinter()

# Test with a video
audio_file = processor.download_video_audio("https://youtube.com/watch?v=...")
fingerprint = fingerprinter.extract_fingerprint(audio_file)

print(f"Fingerprint confidence: {fingerprint['confidence_score']}")
```

## Troubleshooting

### Common Issues

**Database connection fails:**

- Check PostgreSQL is running: `sudo systemctl status postgresql`
- Verify credentials in `.env` file
- Test connection: `psql -h localhost -U soundhash_user -d soundhash`

**FFmpeg not found:**

- Install FFmpeg: `sudo apt install ffmpeg` (Ubuntu) or `brew install ffmpeg` (macOS)
- Verify installation: `ffmpeg -version`

**YouTube download fails:**

- Update yt-dlp: `pip install --upgrade yt-dlp`
- Configure cookies: See YouTube Access Configuration section
- Check rate limits: Consider using proxy or reducing concurrent downloads

**Import errors:**

- Ensure virtual environment is activated
- Reinstall dependencies: `pip install -r requirements.txt`
- Check Python version: `python --version` (requires 3.8+)

### Performance Issues

- Reduce `MAX_CONCURRENT_DOWNLOADS` in `.env`
- Process smaller batches of videos
- Monitor disk space in temp directory
- Enable `CLEANUP_SEGMENTS_AFTER_PROCESSING`

### Database Performance

- Add indexes on frequently queried columns (migrations handle this automatically)
- Use connection pooling (configured in `src/database/connection.py`)
- Monitor query performance with EXPLAIN
- Consider batch operations for bulk inserts

### Database Migrations

SoundHash uses Alembic for database schema management:

```bash
# Check current migration version
alembic current

# View migration history
alembic history

# Upgrade to latest version
alembic upgrade head

# Downgrade to previous version (use with caution)
alembic downgrade -1

# Rollback all migrations
alembic downgrade base
```

**CI Integration**: The CI pipeline automatically checks that migrations are in sync with models. If you modify models without creating a migration, CI will fail.

## Maintenance

### Database Backup

```bash
# Backup
pg_dump soundhash > backup.sql

# Restore
psql soundhash < backup.sql
```

### Cleanup

```bash
# Clean temporary files
rm -rf $TEMP_DIR/*

# Clean old processing jobs (optional)
# This requires a custom cleanup script
```

### Updates

```bash
# Pull latest changes
git pull origin main

# Update dependencies
pip install -r requirements.txt --upgrade

# Run database migrations to update schema
alembic upgrade head

# Or use the setup script
python scripts/setup_database.py
```

**Important**: Always run migrations after pulling changes that may include database schema updates.

## Fresh Start

If you need to completely reset the system:

```bash
# Stop all services
docker compose down  # If using Docker

# Drop and recreate database
dropdb soundhash
createdb soundhash

# Reinitialize with migrations
alembic upgrade head
# Or use: python scripts/setup_database.py
```

## Additional Resources

- **Architecture**: See `ARCHITECTURE.md`
- **YouTube OAuth Setup**: See `YOUTUBE_OAUTH_SETUP.md`
- **Authentication**: See `AUTH_SETUP.md`
- **Roadmap**: See `ROADMAP.md` or [Issue #34](https://github.com/onnwee/soundhash/issues/34)

## Support

For issues and questions:

- Check existing [GitHub Issues](https://github.com/onnwee/soundhash/issues)
- Review the [project roadmap](https://github.com/onnwee/soundhash/issues/34)
- See troubleshooting section above
