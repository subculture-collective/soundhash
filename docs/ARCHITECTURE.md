# SoundHash Project Structure

```text
soundhash/
├── README.md                           # Project documentation
├── requirements.txt                    # Python dependencies
├── .env.example                       # Environment variables template
├── config/
│   └── settings.py                    # Configuration management
├── src/
│   ├── core/
│   │   ├── audio_fingerprinting.py   # Audio fingerprinting system
│   │   └── video_processor.py        # Video download and processing
│   ├── database/
│   │   ├── models.py                  # SQLAlchemy database models
│   │   ├── connection.py              # Database connection management
│   │   └── repositories.py           # Data access layer
│   ├── bots/
│   │   ├── twitter_bot.py            # Twitter bot implementation
│   │   └── reddit_bot.py             # Reddit bot (future)
│   └── ingestion/
│       └── channel_ingester.py       # YouTube channel processing
├── scripts/
│   ├── setup_database.py             # Database initialization
│   └── ingest_channels.py            # Channel ingestion runner
└── temp/                              # Temporary files directory
```

## Database Schema

### Tables

- **channels**: YouTube channel metadata
- **videos**: Video information and processing status
- **audio_fingerprints**: Spectral fingerprint data for audio segments
- **match_results**: Query results and similarity scores
- **processing_jobs**: Background job queue and status

## Key Features

- Spectral peak-based audio fingerprinting
- PostgreSQL for scalable storage
- Async processing pipeline
- Social media bot integration
- Multi-channel video ingestion

## Target Channels

- UCo_QGM_tJZOkOCIFi2ik5kA
- UCDz8WxTg4R7FUTSz7GW2cYA
- UCBvc2dNfp1AC0VBVU0vRagw
