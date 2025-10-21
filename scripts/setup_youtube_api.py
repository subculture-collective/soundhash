#!/usr/bin/env python3
"""
YouTube API Setup and Test Script

This script helps set up YouTube Data API v3 OAuth authentication
and tests the connection.

Prerequisites:
1. Create a project in Google Cloud Console
2. Enable YouTube Data API v3
3. Create OAuth 2.0 credentials (Desktop Application)
4. Download the credentials JSON file as 'credentials.json'

Usage:
    python scripts/setup_youtube_api.py
"""

import argparse
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from config.logging_config import create_section_logger
from config.logging_config import setup_logging as setup_enhanced_logging
from src.api.youtube_service import YouTubeAPIService


def check_credentials_file(logger):
    """Check if credentials.json exists"""
    credentials_path = Path("credentials.json")
    if not credentials_path.exists():
        logger.error("credentials.json not found!")
        logger.info("")
        logger.info("To set up YouTube Data API:")
        logger.info("1. Go to Google Cloud Console: https://console.cloud.google.com/")
        logger.info("2. Create a new project or select existing one")
        logger.info("3. Enable YouTube Data API v3")
        logger.info("4. Go to 'Credentials' section")
        logger.info("5. Create OAuth 2.0 Client ID (Desktop Application)")
        logger.info("6. Download the JSON file and save as 'credentials.json' in this directory")
        logger.info("")
        return False

    logger.log_success("credentials.json found")
    return True


def test_youtube_api(logger):
    """Test YouTube API connection and basic functionality"""
    try:
        logger.info("Initializing YouTube API service...")
        service = YouTubeAPIService()

        logger.info("Testing API connection...")
        if service.test_connection():
            logger.log_success("YouTube API connection successful!")
        else:
            logger.error("YouTube API connection failed")
            return False

        # Test getting channel info for a known channel
        test_channel_id = "UCo_QGM_tJZOkOCIFi2ik5kA"  # From your config
        logger.info(f"Testing channel info retrieval for {test_channel_id}...")

        channel_info = service.get_channel_info(test_channel_id)
        if channel_info:
            logger.log_success(f"Channel info retrieved: {channel_info['title']}")
            logger.info(f"   Subscriber count: {channel_info.get('subscriber_count', 'N/A')}")
        else:
            logger.error("Failed to retrieve channel info")
            return False

        # Test getting channel videos
        logger.info("Testing video list retrieval (max 5 videos)...")
        videos = service.get_channel_videos(test_channel_id, max_results=5)
        if videos:
            logger.log_success(f"Retrieved {len(videos)} videos")
            for i, video in enumerate(videos[:3], 1):
                logger.info(f"   {i}. {video['title'][:50]}...")
        else:
            logger.warning("No videos retrieved (may be due to channel settings)")

        return True

    except FileNotFoundError as e:
        logger.log_error_box("Credentials file error", str(e))
        logger.error("Make sure credentials.json is in the current directory")
        return False
    except Exception as e:
        logger.log_error_box("Error testing YouTube API", str(e))
        return False


def main():
    # Parse CLI arguments
    parser = argparse.ArgumentParser(description="Setup and test YouTube Data API")
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
    setup_enhanced_logging(log_level=args.log_level, log_file=None, use_colors=not args.no_colors)
    logger = create_section_logger(__name__)

    logger.log_section_start("YouTube Data API Setup", "Testing OAuth and API connectivity")

    # Check credentials file
    if not check_credentials_file(logger):
        logger.log_section_end("YouTube Data API Setup", success=False)
        return 1

    # Test YouTube API
    if test_youtube_api(logger):
        logger.info("")
        logger.log_success("YouTube Data API setup successful!")
        logger.info("")
        logger.info("Next steps:")
        logger.info("1. Run the ingestion script: python scripts/ingest_channels.py --dry-run")
        logger.info("2. The system will now use YouTube Data API for metadata")
        logger.info("3. Audio downloads will still use yt-dlp (may require cookies for some videos)")
        logger.log_section_end("YouTube Data API Setup", success=True)
        return 0
    else:
        logger.info("")
        logger.error("YouTube Data API setup failed")
        logger.error("Please check your credentials and try again")
        logger.log_section_end("YouTube Data API Setup", success=False)
        return 1


if __name__ == "__main__":
    exit(main())
