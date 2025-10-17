# SoundHash - Video Clip Matching System

A sophisticated system for matching audio clips from videos across social media platforms using audio fingerprinting and PostgreSQL.

## Project Status

📋 **Roadmap**: [Issue #34](https://github.com/onnwee/soundhash/issues/34) | 🗂️ **Project Board**: [@onnwee's soundhash](https://github.com/users/onnwee/projects) | 🏁 **Milestones**: [View all](https://github.com/onnwee/soundhash/milestones)

## Features

- Audio fingerprinting using spectral analysis
- PostgreSQL database for scalable storage
- Social media bot integration (Twitter, Reddit)
- YouTube channel ingestion
- Real-time clip matching
- Beautiful colored logging with progress tracking

## Target Channels

The system is initially configured to process videos from:

- UCo_QGM_tJZOkOCIFi2ik5kA
- UCDz8WxTg4R7FUTSz7GW2cYA
- UCBvc2dNfp1AC0VBVU0vRagw

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
# IMPORTANT: Never commit .env or any files containing secrets
```

> **⚠️ Security Note**: See the [Security and Secrets Management](#security-and-secrets-management) section below for important information about handling credentials safely.

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

## Architecture

- `src/core/` - Core audio processing and fingerprinting
- `src/database/` - Database models and operations
- `src/bots/` - Social media bot implementations
- `src/ingestion/` - Channel data ingestion system
- `scripts/` - Utility scripts for setup and maintenance

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

