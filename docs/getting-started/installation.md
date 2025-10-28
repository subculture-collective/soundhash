# Installation

This guide will help you install SoundHash on your system. Choose between Docker (recommended) or manual installation.

## Prerequisites

Before installing SoundHash, ensure you have:

=== "All Installations"

    - **Python 3.11 or higher**
    - **Git** for version control
    - **4GB+ RAM** recommended

=== "Docker Installation"

    - **Docker** (20.10+)
    - **Docker Compose** (2.0+)

=== "Manual Installation"

    - **PostgreSQL** (14+)
    - **FFmpeg** for audio processing
    - **Virtual environment** tool (venv or conda)

---

## Docker Installation (Recommended)

Docker provides the easiest and most reliable way to run SoundHash.

### Step 1: Clone the Repository

```bash
git clone https://github.com/subculture-collective/soundhash.git
cd soundhash
```

### Step 2: Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```env title=".env"
# Database (automatically configured for Docker)
DATABASE_URL=postgresql://soundhash:soundhash@db:5432/soundhash

# YouTube Channels (comma-separated channel IDs)
TARGET_CHANNELS=UCo_QGM_tJZOkOCIFi2ik5kA,UCDz8WxTg4R7FUTSz7GW2cYA

# Processing Settings
SEGMENT_LENGTH_SECONDS=90
FINGERPRINT_SAMPLE_RATE=16000
CLEANUP_SEGMENTS_AFTER_PROCESSING=true
```

### Step 3: Start Services

```bash
docker compose up -d
```

This starts:

- PostgreSQL database
- SoundHash application
- (Optional) Redis for caching

### Step 4: Initialize Database

```bash
docker compose exec app python scripts/setup_database.py
```

### Step 5: Setup YouTube API

```bash
docker compose exec app python scripts/setup_youtube_api.py
```

Follow the prompts to authenticate with Google. See [YouTube Setup Guide](../guides/youtube-setup.md) for detailed instructions.

### Step 6: Verify Installation

```bash
# Check logs
docker compose logs app

# Test system
docker compose exec app python scripts/test_system.py
```

✅ **Installation complete!** Continue to [Quick Start](quick-start.md) to ingest your first videos.

---

## Manual Installation

For development or custom deployments, you can install SoundHash manually.

### Step 1: Install System Dependencies

=== "Ubuntu/Debian"

    ```bash
    sudo apt update
    sudo apt install -y postgresql postgresql-contrib ffmpeg python3-pip python3-venv
    ```

=== "macOS"

    ```bash
    brew install postgresql ffmpeg python@3.11
    brew services start postgresql
    ```

=== "Windows"

    1. Install [PostgreSQL](https://www.postgresql.org/download/windows/)
    2. Install [FFmpeg](https://ffmpeg.org/download.html)
    3. Install [Python 3.11+](https://www.python.org/downloads/)

### Step 2: Clone and Setup Virtual Environment

```bash
git clone https://github.com/subculture-collective/soundhash.git
cd soundhash

# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### Step 3: Install Python Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Setup PostgreSQL Database

=== "Quick Setup"

    ```bash
    # Create database
    createdb soundhash
    ```

=== "With Custom User"

    ```bash
    # Create user
    psql -d postgres -c "CREATE USER soundhash_user WITH PASSWORD 'your_secure_password';"
    
    # Create database
    psql -d postgres -c "CREATE DATABASE soundhash OWNER soundhash_user;"
    
    # Grant privileges
    psql -d postgres -c "GRANT ALL PRIVILEGES ON DATABASE soundhash TO soundhash_user;"
    ```

### Step 5: Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your database credentials:

```env title=".env"
# Database Configuration
DATABASE_URL=postgresql://soundhash_user:your_secure_password@localhost:5432/soundhash

# Or use individual settings:
DB_HOST=localhost
DB_PORT=5432
DB_NAME=soundhash
DB_USER=soundhash_user
DB_PASSWORD=your_secure_password

# YouTube Channels
TARGET_CHANNELS=UCo_QGM_tJZOkOCIFi2ik5kA

# Processing Settings
SEGMENT_LENGTH_SECONDS=90
FINGERPRINT_SAMPLE_RATE=16000
TEMP_DIR=/tmp/soundhash
CLEANUP_SEGMENTS_AFTER_PROCESSING=true
```

### Step 6: Initialize Database Schema

```bash
# Run migrations
alembic upgrade head

# Or use the setup script
python scripts/setup_database.py
```

### Step 7: Setup YouTube API

```bash
python scripts/setup_youtube_api.py
```

This will guide you through:

1. Creating a Google Cloud project
2. Enabling YouTube Data API v3
3. Setting up OAuth2 credentials
4. Authenticating your application

→ See [YouTube Setup Guide](../guides/youtube-setup.md) for detailed instructions.

### Step 8: Verify Installation

```bash
# Test database connection
python scripts/test_system.py

# Test with a dry run
python scripts/ingest_channels.py --dry-run --max-videos 5
```

✅ **Installation complete!** Continue to [Quick Start](quick-start.md).

---

## Post-Installation Configuration

### YouTube Access Hardening

For better reliability and to avoid rate limiting:

```env title=".env"
# Cookie-based authentication (recommended)
YT_COOKIES_FILE=/path/to/cookies.txt
# OR extract from browser
YT_COOKIES_FROM_BROWSER=firefox
# OR with specific profile
YT_COOKIES_FROM_BROWSER=chrome:Profile 1

# Proxy configuration (optional)
USE_PROXY=true
PROXY_URL=http://proxy.example.com:8080
# OR use proxy list
PROXY_LIST=/path/to/proxies.txt

# Client override (if needed)
YT_PLAYER_CLIENT=android
```

→ See [YouTube Setup Guide](../guides/youtube-setup.md) for cookie extraction.

### Performance Tuning

```env title=".env"
# Concurrent downloads
MAX_CONCURRENT_DOWNLOADS=3

# Processing settings
SEGMENT_LENGTH_SECONDS=90
FINGERPRINT_SAMPLE_RATE=16000

# Storage
TEMP_DIR=/tmp/soundhash
CLEANUP_SEGMENTS_AFTER_PROCESSING=true
```

### API Configuration

```env title=".env"
# API Server
API_HOST=0.0.0.0
API_PORT=8000
API_TITLE=SoundHash API
API_VERSION=1.0.0

# Authentication
JWT_SECRET_KEY=your-secret-key-change-this-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=60
```

---

## Troubleshooting

### Database Connection Issues

!!! failure "Error: Could not connect to database"

    **Symptoms**: Database connection errors during startup
    
    **Solutions**:
    
    1. Check PostgreSQL is running:
       ```bash
       sudo systemctl status postgresql  # Linux
       brew services list                 # macOS
       ```
    
    2. Verify credentials in `.env`
    
    3. Test connection manually:
       ```bash
       psql -h localhost -U soundhash_user -d soundhash
       ```

### FFmpeg Not Found

!!! failure "Error: FFmpeg not found"

    **Symptoms**: Video processing fails with FFmpeg errors
    
    **Solutions**:
    
    1. Verify FFmpeg installation:
       ```bash
       ffmpeg -version
       ```
    
    2. Install if missing:
       ```bash
       sudo apt install ffmpeg     # Ubuntu/Debian
       brew install ffmpeg         # macOS
       ```

### YouTube Download Failures

!!! failure "Error: Unable to download video"

    **Symptoms**: 403 errors or rate limiting during video downloads
    
    **Solutions**:
    
    1. Update yt-dlp:
       ```bash
       pip install --upgrade yt-dlp
       ```
    
    2. Configure cookies (see YouTube Access Hardening above)
    
    3. Use a proxy to avoid rate limiting
    
    4. Reduce `MAX_CONCURRENT_DOWNLOADS` in `.env`

### Import Errors

!!! failure "Error: ModuleNotFoundError"

    **Symptoms**: Python module import errors
    
    **Solutions**:
    
    1. Ensure virtual environment is activated:
       ```bash
       source .venv/bin/activate
       ```
    
    2. Reinstall dependencies:
       ```bash
       pip install -r requirements.txt
       ```
    
    3. Check Python version:
       ```bash
       python --version  # Should be 3.11+
       ```

---

## Next Steps

Now that you have SoundHash installed:

1. **[Quick Start](quick-start.md)** - Run your first ingestion
2. **[Configuration](configuration.md)** - Understand all configuration options
3. **[First Match](first-match.md)** - Find your first audio match

## Additional Resources

- [Architecture Overview](../architecture/overview.md)
- [Deployment Guide](../deployment/docker.md)
- [Troubleshooting Guide](../reference/troubleshooting.md)
- [GitHub Issues](https://github.com/subculture-collective/soundhash/issues)
