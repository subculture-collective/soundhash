# SoundHash Installation Guide# SoundHash Installation Guide# SoundHash Installation Guide

## Prerequisites## Prerequisites## Prerequisites

1. **Python 3.12+**1. **Python 3.12+**1. **Python 3.12+**

2. **PostgreSQL** (version 12+)

3. **ffmpeg** (for audio processing)2. **PostgreSQL** (version 12+)2. **PostgreSQL** (version 12+)

4. **Git** (for version control)

5. **ffmpeg** (for audio processing)3. **ffmpeg** (for audio processing)

## Installation Steps

4. **Git** (for version control)4. **Git** (for version control)

### 1. Clone Repository

## Installation Steps## Installation Steps

`````bash

git clone <repository-url> soundhash### 1. Clone Repository### 1. Clone Repository

cd soundhash

````bash`bash



### 2. Create Virtual Environmentgit clone <repository-url> soundhashgit clone <repository-url> soundhash



```bashcd soundhashcd soundhash

python3 -m venv .venv

source .venv/bin/activate  # On Windows: .venv\Scripts\activate````

`````

### 3. Install Dependencies

### 2. Create Virtual Environment### 2. Create Virtual Environment

```bash

pip install -r requirements.txt

```

`bash`bash

### 4. Install System Dependencies

python3 -m venv .venvpython3 -m venv .venv

**Ubuntu/Debian:**

source .venv/bin/activate # On Windows: .venv\Scripts\activatesource .venv/bin/activate # On Windows: .venv\Scripts\activate

`````bash

sudo apt update````

sudo apt install postgresql postgresql-contrib ffmpeg

```### 3. Install Dependencies### 3. Install Dependencies



**macOS:**`bash`bash



```bashpip install -r requirements.txtpip install -r requirements.txt

brew install postgresql ffmpeg

`````

**Windows:**

-   Install PostgreSQL from [official website](https://www.postgresql.org/download/windows/)### 4. Install System Dependencies### 4. Setup PostgreSQL Database

-   Install ffmpeg from [official website](https://ffmpeg.org/download.html)

### 5. Setup PostgreSQL Database

**Ubuntu/Debian:**```bash

````bash

# Start PostgreSQL service (if not already running)# Create database

sudo systemctl start postgresql  # Linux

brew services start postgresql   # macOS```bashcreatedb soundhash



# Create database and usersudo apt update

sudo -u postgres psql

```sudo apt install postgresql postgresql-contrib ffmpeg# Or using psql



```sql```psql -c "CREATE DATABASE soundhash;"

CREATE DATABASE soundhash;

CREATE USER soundhash_user WITH PASSWORD 'your_password';```

GRANT ALL PRIVILEGES ON DATABASE soundhash TO soundhash_user;

\q**macOS:**

````

### 5. Configure Environment

### 6. Configure Environment

```````bash

```bash

cp .env.example .envbrew install postgresql ffmpeg```bash

# Edit .env with your configuration

``````cp .env.example .env



Required environment variables:# Edit .env with your configuration



```bash**Windows:**```

# Database

DATABASE_URL=postgresql://soundhash_user:your_password@localhost:5432/soundhash



# YouTube API (Required)- Install PostgreSQL from [official website](https://www.postgresql.org/download/windows/)Required environment variables:

YOUTUBE_API_KEY=your_youtube_api_key

- Install ffmpeg from [official website](https://ffmpeg.org/download.html)

# Optional: Social Media APIs

TWITTER_API_KEY=your_twitter_api_key-   `DATABASE_URL` - PostgreSQL connection string

TWITTER_API_SECRET=your_twitter_api_secret

TWITTER_ACCESS_TOKEN=your_access_token### 5. Setup PostgreSQL Database-   `YOUTUBE_API_KEY` - YouTube Data API key

TWITTER_ACCESS_SECRET=your_access_secret

-   `TWITTER_API_KEY` - Twitter API credentials (optional)

REDDIT_CLIENT_ID=your_reddit_client_id

REDDIT_CLIENT_SECRET=your_reddit_client_secret```bash-   `REDDIT_CLIENT_ID` - Reddit API credentials (optional)

REDDIT_USER_AGENT=your_user_agent

# Start PostgreSQL service (if not already running)    ./docker/manage.sh bot

# Processing Configuration

SEGMENT_LENGTH_SECONDS=120sudo systemctl start postgresql  # Linux

MAX_CONCURRENT_DOWNLOADS=3

KEEP_ORIGINAL_AUDIO=falsebrew services start postgresql   # macOS# Complete cleanup

CLEANUP_SEGMENTS_AFTER_PROCESSING=true



# Target channels (comma-separated)

TARGET_CHANNELS=UCo_QGM_tJZOkOCIFi2ik5kA,UCDz8WxTg4R7FUTSz7GW2cYA,UCBvc2dNfp1AC0VBVU0vRagw# Create database and user./docker/manage.sh cleanup

```````

sudo -u postgres psql

### 7. Initialize Database

````

```bash

python scripts/setup_database.py```sqlThe Docker setup uses PostgreSQL on port **5433** (instead of 5432) to avoid conflicts with existing PostgreSQL instances.

```

CREATE DATABASE soundhash;

### 8. Setup YouTube API (Required)

CREATE USER soundhash_user WITH PASSWORD 'your_password';## Manual Installation (Without Docker)

Follow the instructions in `YOUTUBE_OAUTH_SETUP.md` to:

GRANT ALL PRIVILEGES ON DATABASE soundhash TO soundhash_user;

1. Create a Google Cloud project

2. Enable YouTube Data API v3\q### Prerequisites for Manual Setup

3. Create OAuth2 credentials

4. Run the authentication flow```



```bash1. **PostgreSQL** (version 12+)

python scripts/setup_youtube_api.py

```### 6. Configure Environment2. **Python** (version 3.8+)



### 9. Test Installation3. **FFmpeg** (for audio processing)



```bash```bash4. **Git** (for version control)### Manual Installation Steps

# Test database connection

python scripts/test_system.pycp .env.example .env



# Test with a dry run (limited videos)# Edit .env with your configuration### 1. Clone and Setup Project

python scripts/ingest_channels.py --dry-run --max-videos 5

````

### 10. Start Processing```````bash

```````bashRequired environment variables:git clone <repository-url> soundhash

# Process all configured channels (unlimited videos - this may take a very long time!)

python scripts/ingest_channels.pycd soundhash



# Process specific channels with all videos- `DATABASE_URL` - PostgreSQL connection string````

python scripts/ingest_channels.py --channels "UCo_QGM_tJZOkOCIFi2ik5kA"

- `YOUTUBE_API_KEY` - YouTube Data API key

# Limit videos for testing (recommended for first run)

python scripts/ingest_channels.py --max-videos 10- `TWITTER_API_KEY` - Twitter API credentials (optional)### 2. Install Dependencies



# Start Twitter bot (optional)- `REDDIT_CLIENT_ID` - Reddit API credentials (optional)

python src/bots/twitter_bot.py

``````bash



## Configuration OptionsExample `.env` configuration:# Create virtual environment



### Command Line Argumentspython -m venv venv



```bash```bashsource venv/bin/activate  # On Windows: venv\Scripts\activate

# Show all available options

python scripts/ingest_channels.py --help# Database



# Common optionsDATABASE_URL=postgresql://soundhash_user:your_password@localhost:5432/soundhash# Install Python packages

--channels "CHANNEL_ID1,CHANNEL_ID2"  # Specific channels

--max-videos 10                       # Limit videos per channel (default: unlimited)pip install -r requirements.txt

--dry-run                            # Test without processing

--log-level DEBUG                    # Increase verbosity# YouTube API```

--no-colors                          # Disable colored output

--skip-processing                    # Only ingest metadataYOUTUBE_API_KEY=your_youtube_api_key

--only-process                       # Only process existing jobs

```### 3. Install System Dependencies



**⚠️ Performance Note**: The default behavior fetches **ALL videos** from each channel. Large channels may have thousands of videos (we've seen channels with 1000+ videos), which will take significant time and storage. Consider using `--max-videos` for initial testing.# Optional: Twitter API



### Environment VariablesTWITTER_API_KEY=your_twitter_api_key**Ubuntu/Debian:**



Key configuration options in `.env`:TWITTER_API_SECRET=your_twitter_api_secret



```bashTWITTER_ACCESS_TOKEN=your_access_token```bash

# Segment length for audio fingerprinting (seconds)

SEGMENT_LENGTH_SECONDS=120TWITTER_ACCESS_SECRET=your_access_secretsudo apt update



# Number of concurrent downloadssudo apt install postgresql postgresql-contrib ffmpeg

MAX_CONCURRENT_DOWNLOADS=3

# Optional: Reddit API```

# File management

KEEP_ORIGINAL_AUDIO=falseREDDIT_CLIENT_ID=your_reddit_client_id

CLEANUP_SEGMENTS_AFTER_PROCESSING=true

REDDIT_CLIENT_SECRET=your_reddit_client_secret**macOS:**

# Target channels (comma-separated)

TARGET_CHANNELS=UCo_QGM_tJZOkOCIFi2ik5kA,UCDz8WxTg4R7FUTSz7GW2cYA,UCBvc2dNfp1AC0VBVU0vRagwREDDIT_USER_AGENT=your_user_agent

```````

````````bash

## Troubleshooting

# Processing Configurationbrew install postgresql ffmpeg

### Database Connection Issues

SEGMENT_LENGTH_SECONDS=120```

- Check PostgreSQL is running: `sudo systemctl status postgresql`

- Verify credentials in `.env` fileMAX_CONCURRENT_DOWNLOADS=3

- Test connection: `psql -h localhost -U soundhash_user -d soundhash`

KEEP_ORIGINAL_AUDIO=false### 4. Setup PostgreSQL Database

### FFmpeg Issues

CLEANUP_SEGMENTS_AFTER_PROCESSING=true

- Install FFmpeg: `sudo apt install ffmpeg` (Ubuntu) or `brew install ffmpeg` (macOS)

- Verify installation: `ffmpeg -version```````bash



### Video Download Issues# Start PostgreSQL service



- Update yt-dlp: `pip install --upgrade yt-dlp`### 7. Initialize Databasesudo systemctl start postgresql  # Linux

- Check video URL accessibility

- Some videos may be geo-restrictedbrew services start postgresql   # macOS



### Performance Issues```bash



- Reduce `MAX_CONCURRENT_DOWNLOADS` in `.env`python scripts/setup_database.py# Create database and user

- Process smaller batches of videos using `--max-videos`

- Monitor disk space in temp directory```sudo -u postgres psql



### Database Performance```````



- Create indexes for frequently queried columns### 8. Setup YouTube API (Required)

- Monitor database size and consider partitioning for large datasets

- Use connection pooling for high-throughput scenariosIn PostgreSQL shell:



## Fresh StartFollow the instructions in `YOUTUBE_OAUTH_SETUP.md` to:



If you need to completely reset the system:```sql



```bash1. Create a Google Cloud projectCREATE DATABASE soundhash;

python scripts/fresh_start.py

```2. Enable YouTube Data API v3CREATE USER soundhash_user WITH PASSWORD 'your_secure_password';



This will:3. Create OAuth2 credentialsGRANT ALL PRIVILEGES ON DATABASE soundhash TO soundhash_user;



- Clear all database data4. Run the authentication flow\q

- Remove temporary files

- Reset processing state```

- Verify system readiness

```bash

## Logging

python scripts/setup_youtube_api.py### 5. Configure Environment

The system features enhanced logging with:

````````

-   Colored output with emojis

-   Progress bars with ETA````bash

-   Structured section logging

-   Configurable log levels### 9. Test Installation# Copy environment template

Log files are written to `ingestion.log` for debugging purposes.cp .env.example .env

## Processing Scale Expectations```bash

### Channel Sizes (Approximate)# Test database connection# Edit .env file with your settings

-   Small channels: 50-200 videos

-   Medium channels: 200-1000 videos python scripts/test_system.pynano .env

-   Large channels: 1000+ videos (some have 5000+)

```

### Processing Time Estimates

- **Video ingestion**: ~0.1 seconds per video# Test with a dry run

- **Audio download**: ~10-30 seconds per video

- **Audio segmentation**: ~1-5 seconds per videopython scripts/ingest_channels.py --dry-run --max-videos 5Required settings in `.env`:

- **Fingerprint generation**: ~5-15 seconds per video

```

For a channel with 1000 videos, expect:

-   Ingestion: ~2 minutes```env

-   Full processing: 4-12 hours (depending on video lengths)

### 10. Start ProcessingDATABASE_URL=postgresql://soundhash_user:your_secure_password@localhost:5432/soundhash

## Next Steps

YOUTUBE_API_KEY=your_youtube_api_key

1. Configure your target channels in `.env`

2. Set up YouTube API authentication```bashTWITTER_BEARER_TOKEN=your_twitter_bearer_token

3. Run initial ingestion with `--dry-run --max-videos 10` to test

4. Start with limited processing: `--max-videos 50`# Process all configured channels# ... other API keys

5. Monitor logs for any issues

6. Scale up to full channel processing when confidentpython scripts/ingest_channels.py```

7. Set up social media bots (optional)

For more details, see:

# Process specific channels### 6. Initialize Database

-   `YOUTUBE_OAUTH_SETUP.md` - YouTube API setup

-   `AUTH_SETUP.md` - Social media API setuppython scripts/ingest_channels.py --channels "UCo_QGM_tJZOkOCIFi2ik5kA"

-   `ARCHITECTURE.md` - System architecture overview

````bash

# Start Twitter bot (optional)python scripts/setup_database.py

python src/bots/twitter_bot.py```

````

### 7. Start Channel Ingestion

## Configuration Options

```bash

### Command Line Argumentspython scripts/ingest_channels.py

```

```bash

# Show all available options## API Keys Setup

python scripts/ingest_channels.py --help

### YouTube Data API

# Common options

--channels "CHANNEL_ID1,CHANNEL_ID2"  # Specific channels1. Go to [Google Cloud Console](https://console.cloud.google.com/)

--max-videos 10                       # Limit videos per channel2. Create a new project or select existing

--dry-run                            # Test without processing3. Enable YouTube Data API v3

--log-level DEBUG                    # Increase verbosity4. Create credentials (API Key)

--no-colors                          # Disable colored output5. Add key to `.env` file

--skip-processing                    # Only ingest metadata

--only-process                       # Only process existing jobs### Twitter API

```

1. Apply for [Twitter Developer Account](https://developer.twitter.com/)

### Environment Variables2. Create a new app

3. Generate API keys and tokens

Key configuration options in `.env`:4. Add to `.env` file

````bash### Reddit API (Optional)

# Segment length for audio fingerprinting (seconds)

SEGMENT_LENGTH_SECONDS=1201. Go to [Reddit App Preferences](https://www.reddit.com/prefs/apps)

2. Create new app (script type)

# Number of concurrent downloads3. Note client ID and secret

MAX_CONCURRENT_DOWNLOADS=34. Add to `.env` file



# File management## Running the System

KEEP_ORIGINAL_AUDIO=false

CLEANUP_SEGMENTS_AFTER_PROCESSING=true### Start Channel Processing



# Target channels (comma-separated)```bash

TARGET_CHANNELS=UCo_QGM_tJZOkOCIFi2ik5kA,UCDz8WxTg4R7FUTSz7GW2cYA,UCBvc2dNfp1AC0VBVU0vRagwpython scripts/ingest_channels.py

````

## Troubleshooting### Run Twitter Bot

### Database Connection Issues```bash

python src/bots/twitter_bot.py

-   Check PostgreSQL is running: `sudo systemctl status postgresql````

-   Verify credentials in `.env` file

-   Test connection: `psql -h localhost -U soundhash_user -d soundhash`### Manual Testing

### FFmpeg Issues```python

from src.core.audio_fingerprinting import AudioFingerprinter

-   Install FFmpeg: `sudo apt install ffmpeg` (Ubuntu) or `brew install ffmpeg` (macOS)from src.core.video_processor import VideoProcessor

-   Verify installation: `ffmpeg -version`

processor = VideoProcessor()

### Video Download Issuesfingerprinter = AudioFingerprinter()

-   Update yt-dlp: `pip install --upgrade yt-dlp`# Test with a video

-   Check video URL accessibilityaudio_file = processor.download_video_audio("https://youtube.com/watch?v=...")

-   Some videos may be geo-restrictedfingerprint = fingerprinter.extract_fingerprint(audio_file)

print(f"Fingerprint confidence: {fingerprint['confidence_score']}")

### Performance Issues```

-   Reduce `MAX_CONCURRENT_DOWNLOADS` in `.env`## Troubleshooting

-   Process smaller batches of videos

-   Monitor disk space in temp directory### Common Issues

### Database Performance**Database connection fails:**

-   Create indexes for frequently queried columns- Check PostgreSQL is running: `sudo systemctl status postgresql`

-   Monitor database size and consider partitioning for large datasets- Verify credentials in `.env` file

-   Use connection pooling for high-throughput scenarios- Test connection: `psql -h localhost -U soundhash_user -d soundhash`

## Fresh Start**FFmpeg not found:**

If you need to completely reset the system:- Install FFmpeg: `sudo apt install ffmpeg` (Ubuntu) or `brew install ffmpeg` (macOS)

-   Verify installation: `ffmpeg -version`

```bash

python scripts/fresh_start.py**yt-dlp download errors:**

```

-   Update yt-dlp: `pip install --upgrade yt-dlp`

This will:- Check video URL accessibility

-   Some videos may be geo-restricted

-   Clear all database data

-   Remove temporary files**Memory issues during processing:**

-   Reset processing state

-   Verify system readiness- Reduce `MAX_CONCURRENT_DOWNLOADS` in `.env`

-   Process smaller batches of videos

## Logging- Monitor disk space in temp directory

The system features enhanced logging with:### Performance Optimization

-   Colored output with emojis**Database:**

-   Progress bars with ETA

-   Structured section logging- Create indexes for frequently queried columns

-   Configurable log levels- Use connection pooling for high load

-   Consider read replicas for scaling

Log files are written to `ingestion.log` for debugging purposes.

**Processing:**

## Next Steps

-   Adjust segment length for your use case

1. Configure your target channels in `.env`- Tune fingerprinting parameters

2. Set up YouTube API authentication- Use SSD storage for temp files

3. Run initial ingestion with `--dry-run` to test

4. Start full processing## Monitoring

5. Monitor logs for any issues

6. Set up social media bots (optional)### Logs

For more details, see:- Application logs: Check terminal output

-   Database logs: `/var/log/postgresql/`

-   `YOUTUBE_OAUTH_SETUP.md` - YouTube API setup- Processing jobs: Monitor `processing_jobs` table

-   `AUTH_SETUP.md` - Social media API setup

-   `ARCHITECTURE.md` - System architecture overview### Metrics

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
