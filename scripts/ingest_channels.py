#!/usr/bin/env python3
"""
Channel ingestion script for SoundHash.
Downloads and processes videos from configured YouTube channels.
"""

import sys
import os
import asyncio
import logging
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ingestion.channel_ingester import ChannelIngester, VideoProcessor
from config.settings import Config

async def main():
    """Main ingestion process for the configured channels"""
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('ingestion.log'),
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger(__name__)
    
    logger.info("Starting SoundHash channel ingestion...")
    logger.info(f"Target channels: {Config.TARGET_CHANNELS}")
    
    try:
        # Create ingester and processor
        ingester = ChannelIngester()
        processor = VideoProcessor()
        
        # Phase 1: Ingest channel metadata and create video records
        logger.info("Phase 1: Ingesting channel data...")
        await ingester.ingest_all_channels()
        
        # Phase 2: Process videos and create fingerprints
        logger.info("Phase 2: Processing videos for fingerprinting...")
        await processor.process_pending_videos()
        
        logger.info("Channel ingestion completed successfully!")
        
    except Exception as e:
        logger.error(f"Ingestion failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())