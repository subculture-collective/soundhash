# SoundHash Installation Guide

## Docker Installation (Recommended)

### Prerequisites for Docker Setup

1. **Docker** (version 20+)
2. **Docker Compose** (version 2+)
3. **Git** (for version control)

### Quick Docker Setup

```bash
# 1. Clone repository
git clone <repository-url> soundhash
cd soundhash

# 2. Copy and configure environment
cp .env.docker.example .env.docker
# Edit .env.docker with your API keys

# 3. Run complete setup
./docker/manage.sh setup

# 4. Start processing channels
./docker/manage.sh ingest

# 5. Start Twitter bot
./docker/manage.sh bot
```

### Docker Management Commands

```bash
# Start services
./docker/manage.sh start

# Stop services
./docker/manage.sh stop

# View service status
./docker/manage.sh status

# View logs
./docker/manage.sh logs [service_name]

# Run channel ingestion
./docker/manage.sh ingest

# Start Twitter bot
./docker/manage.sh bot

# Complete cleanup
./docker/manage.sh cleanup
```

The Docker setup uses PostgreSQL on port **5433** (instead of 5432) to avoid conflicts with existing PostgreSQL instances.

## Manual Installation (Without Docker)

### Prerequisites for Manual Setup

1. **PostgreSQL** (version 12+)
2. **Python** (version 3.8+)
3. **FFmpeg** (for audio processing)
4. **Git** (for version control)### Manual Installation Steps

### 1. Clone and Setup Project

```bash
git clone <repository-url> soundhash
cd soundhash
```

### 2. Install Dependencies

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python packages
pip install -r requirements.txt
```

### 3. Install System Dependencies

**Ubuntu/Debian:**

```bash
sudo apt update
sudo apt install postgresql postgresql-contrib ffmpeg
```

**macOS:**

```bash
brew install postgresql ffmpeg
```

### 4. Setup PostgreSQL Database

```bash
# Start PostgreSQL service
sudo systemctl start postgresql  # Linux
brew services start postgresql   # macOS

# Create database and user
sudo -u postgres psql
```

In PostgreSQL shell:

```sql
CREATE DATABASE soundhash;
CREATE USER soundhash_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE soundhash TO soundhash_user;
\q
```

### 5. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your settings
nano .env
```

Required settings in `.env`:

```env
DATABASE_URL=postgresql://soundhash_user:your_secure_password@localhost:5432/soundhash
YOUTUBE_API_KEY=your_youtube_api_key
TWITTER_BEARER_TOKEN=your_twitter_bearer_token
# ... other API keys
```

### 6. Initialize Database

```bash
python scripts/setup_database.py
```

### 7. Start Channel Ingestion

```bash
python scripts/ingest_channels.py
```

## API Keys Setup

### YouTube Data API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable YouTube Data API v3
4. Create credentials (API Key)
5. Add key to `.env` file

### Twitter API

1. Apply for [Twitter Developer Account](https://developer.twitter.com/)
2. Create a new app
3. Generate API keys and tokens
4. Add to `.env` file

### Reddit API (Optional)

1. Go to [Reddit App Preferences](https://www.reddit.com/prefs/apps)
2. Create new app (script type)
3. Note client ID and secret
4. Add to `.env` file

## Running the System

### Start Channel Processing

```bash
python scripts/ingest_channels.py
```

### Run Twitter Bot

```bash
python src/bots/twitter_bot.py
```

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

-   Check PostgreSQL is running: `sudo systemctl status postgresql`
-   Verify credentials in `.env` file
-   Test connection: `psql -h localhost -U soundhash_user -d soundhash`

**FFmpeg not found:**

-   Install FFmpeg: `sudo apt install ffmpeg` (Ubuntu) or `brew install ffmpeg` (macOS)
-   Verify installation: `ffmpeg -version`

**yt-dlp download errors:**

-   Update yt-dlp: `pip install --upgrade yt-dlp`
-   Check video URL accessibility
-   Some videos may be geo-restricted

**Memory issues during processing:**

-   Reduce `MAX_CONCURRENT_DOWNLOADS` in `.env`
-   Process smaller batches of videos
-   Monitor disk space in temp directory

### Performance Optimization

**Database:**

-   Create indexes for frequently queried columns
-   Use connection pooling for high load
-   Consider read replicas for scaling

**Processing:**

-   Adjust segment length for your use case
-   Tune fingerprinting parameters
-   Use SSD storage for temp files

## Monitoring

### Logs

-   Application logs: Check terminal output
-   Database logs: `/var/log/postgresql/`
-   Processing jobs: Monitor `processing_jobs` table

### Metrics

-   Videos processed per hour
-   Fingerprint match accuracy
-   Database size growth
-   API rate limit usage

## Security Notes

-   Keep `.env` file secure and never commit to git
-   Use strong database passwords
-   Regularly rotate API keys
-   Monitor API usage to prevent abuse
-   Consider rate limiting for public APIs
