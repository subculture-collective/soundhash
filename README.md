# SoundHash - Video Clip Matching System

A sophisticated system for matching audio clips from videos across social media platforms using audio fingerprinting and PostgreSQL.

## Project Status

📋 **Roadmap**: [Issue #34](https://github.com/onnwee/soundhash/issues/34) | 🗂️ **Project Board**: [@onnwee's soundhash](https://github.com/users/onnwee/projects) | 🏁 **Milestones**: [View all](https://github.com/onnwee/soundhash/milestones)

## Features

-   Audio fingerprinting using spectral analysis
-   PostgreSQL database for scalable storage
-   Social media bot integration (Twitter, Reddit)
-   YouTube channel ingestion
-   Real-time clip matching
-   Beautiful colored logging with progress tracking

## Target Channels

The system is initially configured to process videos from:

-   UCo_QGM_tJZOkOCIFi2ik5kA
-   UCDz8WxTg4R7FUTSz7GW2cYA
-   UCBvc2dNfp1AC0VBVU0vRagw

## Quick Start

1. Clone and setup:

```bash
git clone <repository-url> soundhash
cd soundhash
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Setup PostgreSQL database:

```bash
createdb soundhash
```

4. Configure environment:

```bash
cp .env.example .env
# Edit .env with your API keys and database credentials
```

5. Run database setup:

```bash
python scripts/setup_database.py
```

6. Start processing channels:

```bash
python scripts/ingest_channels.py
```

7. Start Twitter bot:

```bash
python src/bots/twitter_bot.py
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

-   Configure API keys in `.env`
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
