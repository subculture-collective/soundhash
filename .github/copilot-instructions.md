# Copilot Instructions for SoundHash

Purpose: Give AI coding agents the minimum context to be productive in this repo.

## Big picture

- Goal: match short audio clips to YouTube videos via audio fingerprints stored in PostgreSQL.
- Flow: ingest channels → create ProcessingJob rows → download + segment audio → extract/store fingerprints → compare for matches.
- Key modules/files:
  - Ingestion: `src/ingestion/channel_ingester.py` (async orchestration, idempotent job creation)
  - Video IO: `src/core/video_processor.py` (yt-dlp + ffmpeg; cookies/proxy/env-driven)
  - Fingerprints: `src/core/audio_fingerprinting.py` (STFT, spectral peaks → compact vector + MD5; (de)serialize)
  - DB: `src/database/{connection,models,repositories}.py` (SQLAlchemy engine/schema/DAOs)
  - YouTube API: `src/api/youtube_service.py` (OAuth flow, channel/videos, details)
  - Config/Logging: `config/{settings.py,logging_config.py}`

## How to run locally (zsh)

- DB init: `python scripts/setup_database.py`
- Ingest + process: `python scripts/ingest_channels.py [--channels CH1,CH2] [--max-videos N] [--dry-run] [--only-process] [--skip-processing] [--log-level DEBUG] [--no-colors]`
- YouTube OAuth (optional but recommended): `python scripts/setup_youtube_api.py`
- Note: without `--max-videos`, ingestion fetches ALL videos; prefer `--dry-run --max-videos 5` while iterating.

## Configuration conventions

- Central config: `Config` in `config/settings.py` (loads `.env`). Import it; don’t re-read env directly.
- Important envs: DB (`DATABASE_URL` or discrete vars), `TARGET_CHANNELS`; yt-dlp hardening (`USE_PROXY`, `PROXY_URL|PROXY_LIST`, `YT_COOKIES_FILE`, `YT_COOKIES_FROM_BROWSER[:PROFILE]`, `YT_PLAYER_CLIENT`); processing (`SEGMENT_LENGTH_SECONDS`, `FINGERPRINT_SAMPLE_RATE`, `TEMP_DIR`, cleanup flags).
- Logging: use `setup_logging` and `create_section_logger(__name__)` + `get_progress_logger`; avoid raw `print`.

## Data access + jobs

- Get repositories via helpers: `get_video_repository()`, `get_job_repository()` from `src/database/repositories.py` (these wrap `db_manager.get_session()`).
- Job lifecycle: check `job_repo.job_exists('video_process', video_id, statuses=['pending','running'])` before `create_job`; update with `update_job_status(job_id, status, progress, current_step, error_message)`.
- Engine: `db_manager.initialize()` builds engine; auto-selects psycopg driver if not specified.

## Audio pipeline specifics

- `VideoProcessor`: download best audio with yt-dlp → convert to mono WAV at `FINGERPRINT_SAMPLE_RATE` via ffmpeg → segment into `SEGMENT_LENGTH_SECONDS` chunks.
- `AudioFingerprinter`: `extract_fingerprint(path)` → returns compact normalized vector and metadata; store `fingerprint_hash` + `serialize_fingerprint(...)` in DB.
- Similarity = mean of |corr| and normalized Euclidean similarity; tune thresholds at call sites.

## Examples

- Manual quick test:
  - `wav = VideoProcessor().download_video_audio("https://www.youtube.com/watch?v=...")`
  - `fp = AudioFingerprinter().extract_fingerprint(wav)`
- Script entrypoint: `python scripts/ingest_channels.py --dry-run --max-videos 5`

## Gotchas

- YouTube may rate-limit: use `YT_COOKIES_FILE` or `YT_COOKIES_FROM_BROWSER` (optionally with profile) and/or proxy config.
- Unlimited ingestion is expensive; always bound with `--max-videos` for dev.
- Clean temp segments or enable `CLEANUP_SEGMENTS_AFTER_PROCESSING` to prevent disk bloat.

Reference: see files above; these are the canonical patterns to follow when adding sources, jobs, or queries.
