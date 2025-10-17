#!/usr/bin/env python3
"""
Channel ingestion script for SoundHash.
Downloads and processes videos from configured YouTube channels.
"""

import argparse
import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.logging_config import create_section_logger, setup_logging
from config.settings import Config
from src.ingestion.channel_ingester import ChannelIngester, VideoJobProcessor


async def main():
    """Main ingestion process for the configured channels"""
    # Parse CLI arguments
    parser = argparse.ArgumentParser(
        description="Ingest YouTube channels and process videos for fingerprinting"
    )
    parser.add_argument(
        "--channels",
        type=str,
        default=None,
        help="Comma-separated list of YouTube channel IDs to ingest (overrides TARGET_CHANNELS)",
    )
    parser.add_argument(
        "--max-videos",
        type=int,
        default=None,
        help="Maximum number of recent videos to fetch per channel (default: unlimited)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Ingest metadata without creating jobs or processing videos",
    )
    parser.add_argument(
        "--skip-processing", action="store_true", help="Ingest metadata but skip processing videos"
    )
    parser.add_argument(
        "--only-process",
        action="store_true",
        help="Skip ingestion and only process pending video jobs",
    )
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
    setup_logging(log_level=args.log_level, log_file="ingestion.log", use_colors=not args.no_colors)

    logger = create_section_logger(__name__)

    # Determine channels list
    channels = [
        c.strip()
        for c in (args.channels.split(",") if args.channels else Config.TARGET_CHANNELS)
        if c.strip()
    ]

    logger.log_section_start(
        "SoundHash Channel Ingestion", "Processing YouTube channels for audio fingerprinting"
    )
    logger.info(f"🎯 Target channels: {channels}")
    logger.info(f"📊 Max videos per channel: {args.max_videos if args.max_videos else 'unlimited'}")

    if args.dry_run:
        logger.log_warning_box("DRY RUN MODE - No actual processing will occur")

    try:
        # Create ingester and processor
        init_db = not args.dry_run and not args.only_process

        logger.log_step(1, "Initializing components", "Setting up ingester and video processor")
        ingester = ChannelIngester(initialize_db=init_db)
        processor = VideoJobProcessor()

        if not args.only_process:
            # Phase 1: Ingest channel metadata and create video/job records
            logger.log_step(
                2, "Channel Data Ingestion", "Fetching metadata and creating video records"
            )
            await ingester.ingest_all_channels(
                channels_override=channels, max_videos=args.max_videos, dry_run=args.dry_run
            )

        if not args.dry_run and not args.skip_processing:
            # Phase 2: Process videos and create fingerprints
            logger.log_step(3, "Video Processing", "Downloading audio and generating fingerprints")
            await processor.process_pending_videos()

        logger.log_section_end("SoundHash Channel Ingestion", success=True)

    except Exception as e:
        logger.log_error_box("Ingestion failed", str(e))
        logger.log_section_end("SoundHash Channel Ingestion", success=False)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
