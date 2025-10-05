# SoundHash - Video Clip Matching System

A sophisticated system for matching audio clips from videos across social media platforms using audio fingerprinting and PostgreSQL.

## Features

-   Audio fingerprinting using spectral analysis
-   PostgreSQL database for scalable storage
-   Social media bot integration (Twitter, Reddit)
-   YouTube channel ingestion
-   Real-time clip matching

## Target Channels

The system is initially configured to process videos from:

-   UCo_QGM_tJZOkOCIFi2ik5kA
-   UCDz8WxTg4R7FUTSz7GW2cYA
-   UCBvc2dNfp1AC0VBVU0vRagw

## Quick Start with Docker (Recommended)

1. Clone and setup:

```bash
git clone <repository-url> soundhash
cd soundhash
```

2. Configure environment:

```bash
cp .env.docker.example .env.docker
# Edit .env.docker with your API keys
```

3. Run complete setup:

```bash
./docker/manage.sh setup
```

4. Start processing channels:

```bash
./docker/manage.sh ingest
```

5. Start Twitter bot:

```bash
./docker/manage.sh bot
```

## Manual Setup (Without Docker)

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Setup PostgreSQL database:

```bash
createdb soundhash
```

3. Copy environment file and configure:

```bash
cp .env.example .env
# Edit .env with your API keys and database credentials
```

4. Run database migrations:

```bash
python scripts/setup_database.py
```

5. Start ingesting channel data:

```bash
python scripts/ingest_channels.py
```

## Usage

### Docker Commands

```bash
# Start all services
./docker/manage.sh start

# Check service status
./docker/manage.sh status

# View logs
./docker/manage.sh logs

# Stop services
./docker/manage.sh stop

# Run channel ingestion
./docker/manage.sh ingest

# Start Twitter bot
./docker/manage.sh bot
```

### Manual Bot Deployment

-   Configure API keys in `.env` or `.env.docker`
-   Run Twitter bot: `python src/bots/twitter_bot.py`
-   Run Reddit bot: `python src/bots/reddit_bot.py`

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

## Architecture

-   `src/core/` - Core audio processing and fingerprinting
-   `src/database/` - Database models and operations
-   `src/bots/` - Social media bot implementations
-   `src/ingestion/` - Channel data ingestion system
-   `scripts/` - Utility scripts for setup and maintenance
