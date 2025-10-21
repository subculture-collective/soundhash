#!/usr/bin/env python3
"""
Fresh Start Script for SoundHash
Clears all data and prepares for a fresh ingestion run.
"""

import argparse
import os
import shutil
import sys
from pathlib import Path

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from config.logging_config import create_section_logger, setup_logging
from config.settings import Config
from src.database.connection import db_manager
from src.database.models import AudioFingerprint, Channel, MatchResult, ProcessingJob, Video


def clear_temp_files(logger):
    """Clear all temporary files"""
    temp_dir = Path(Config.TEMP_DIR)
    if temp_dir.exists():
        logger.info(f"Clearing temporary files from: {temp_dir}")
        file_count = len(list(temp_dir.iterdir()))
        shutil.rmtree(temp_dir)
        temp_dir.mkdir(exist_ok=True)
        logger.log_success(f"Removed {file_count} temporary files")
    else:
        logger.log_success("Temp directory doesn't exist, creating it")
        temp_dir.mkdir(parents=True, exist_ok=True)


def clear_logs(logger):
    """Clear log files"""
    log_files = [
        "ingestion.log",
        "fresh_start.log",
        "logs/app.log",
        "logs/ingestion.log",
        "logs/error.log",
    ]

    cleared_count = 0
    for log_file in log_files:
        if os.path.exists(log_file):
            os.remove(log_file)
            cleared_count += 1
            logger.info(f"Removed log file: {log_file}")

    logger.log_success(f"Cleared {cleared_count} log files")


def clear_database_data(logger):
    """Clear all data from database tables"""
    try:
        db_manager.initialize()
        session = db_manager.get_session()

        try:
            # Get table counts before clearing
            counts = {
                "match_results": session.query(MatchResult).count(),
                "audio_fingerprints": session.query(AudioFingerprint).count(),
                "processing_jobs": session.query(ProcessingJob).count(),
                "videos": session.query(Video).count(),
                "channels": session.query(Channel).count(),
            }

            # Clear tables in correct order (respecting foreign keys)
            logger.info("Clearing database tables...")

            session.query(MatchResult).delete()
            logger.info(f"Cleared {counts['match_results']} match results")

            session.query(AudioFingerprint).delete()
            logger.info(f"Cleared {counts['audio_fingerprints']} audio fingerprints")

            session.query(ProcessingJob).delete()
            logger.info(f"Cleared {counts['processing_jobs']} processing jobs")

            session.query(Video).delete()
            logger.info(f"Cleared {counts['videos']} videos")

            session.query(Channel).delete()
            logger.info(f"Cleared {counts['channels']} channels")

            session.commit()
            logger.log_success("Database cleared successfully")

            # Show summary
            total_records = sum(counts.values())
            logger.info(f"📊 Total records removed: {total_records}")
            for table, count in counts.items():
                if count > 0:
                    logger.info(f"   - {table}: {count}")

        finally:
            session.close()

    except Exception as e:
        logger.log_error_box("Error clearing database", str(e))
        raise


def clear_python_cache(logger):
    """Clear Python cache files"""
    cache_patterns = ["**/__pycache__", "**/*.pyc", "**/*.pyo"]
    cleared_count = 0

    for pattern in cache_patterns:
        for cache_path in Path(".").glob(pattern):
            if cache_path.is_file():
                cache_path.unlink()
                cleared_count += 1
            elif cache_path.is_dir():
                shutil.rmtree(cache_path)
                cleared_count += 1

    logger.log_success(f"Cleared {cleared_count} Python cache files")


def verify_system_ready(logger):
    """Verify the system is ready for fresh ingestion"""
    logger.info("🔍 Verifying system readiness...")

    # Check database connection
    try:
        db_manager.initialize()
        session = db_manager.get_session()
        from sqlalchemy import text

        session.execute(text("SELECT 1"))
        session.close()
        logger.log_success("Database connection working")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False

    # Check temp directory
    temp_dir = Path(Config.TEMP_DIR)
    if temp_dir.exists() and temp_dir.is_dir():
        logger.log_success("Temp directory ready")
    else:
        logger.error(f"Temp directory not accessible: {temp_dir}")
        return False

    # Check yt-dlp
    try:
        import subprocess

        result = subprocess.run(["yt-dlp", "--version"], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            logger.log_success(f"yt-dlp ready (version: {result.stdout.strip()})")
        else:
            logger.error("yt-dlp not working")
            return False
    except Exception as e:
        logger.error(f"yt-dlp check failed: {e}")
        return False

    # Check ffmpeg
    try:
        result = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            logger.log_success("FFmpeg ready")
        else:
            logger.error("FFmpeg not working")
            return False
    except Exception as e:
        logger.error(f"FFmpeg check failed: {e}")
        return False

    logger.log_success("System is ready for fresh ingestion!")
    return True


def main():
    """Main fresh start function"""
    # Parse CLI arguments
    parser = argparse.ArgumentParser(description="Clear all data and prepare for fresh ingestion")
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Set logging level",
    )
    parser.add_argument("--no-colors", action="store_true", help="Disable colored output")
    args = parser.parse_args()

    # Setup enhanced logging
    setup_logging(log_level=args.log_level, log_file="fresh_start.log", use_colors=not args.no_colors)
    logger = create_section_logger(__name__)

    logger.log_section_start("Fresh Start", "Clearing all data for a clean slate")

    try:
        # Confirm with user
        logger.log_warning_box("This will permanently delete all data!")
        logger.warning("   - All videos, channels, and audio segments")
        logger.warning("   - All temporary files and logs")
        logger.warning("   - All processing cache")

        response = input("\nAre you sure you want to continue? (type 'yes' to confirm): ")
        if response.lower() != "yes":
            logger.error("Operation cancelled")
            logger.log_section_end("Fresh Start", success=False)
            return

        logger.info("\n🧹 Starting cleanup...")

        # Step 1: Clear temp files
        logger.log_step(1, "Clearing temporary files")
        clear_temp_files(logger)

        # Step 2: Clear logs
        logger.log_step(2, "Clearing log files")
        clear_logs(logger)

        # Step 3: Clear Python cache
        logger.log_step(3, "Clearing Python cache")
        clear_python_cache(logger)

        # Step 4: Clear database
        logger.log_step(4, "Clearing database data")
        clear_database_data(logger)

        # Step 5: Verify system
        logger.log_step(5, "Verifying system readiness")
        if not verify_system_ready(logger):
            logger.error("System verification failed!")
            logger.log_section_end("Fresh Start", success=False)
            return

        logger.log_success("Fresh start completed successfully!")
        logger.info("🎯 System is ready for a fresh ingestion run")
        logger.info("Run: python scripts/ingest_channels.py --max-videos 10")
        logger.log_section_end("Fresh Start", success=True)

    except Exception as e:
        logger.log_error_box("Fresh start failed", str(e))
        logger.log_section_end("Fresh Start", success=False)
        sys.exit(1)


if __name__ == "__main__":
    main()
