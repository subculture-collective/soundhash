#!/usr/bin/env python3
"""
Quick test script to verify the system is working correctly.
"""

import argparse
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.logging_config import create_section_logger, setup_logging
from config.settings import Config
from src.core.audio_fingerprinting import AudioFingerprinter
from src.core.video_processor import VideoProcessor
from src.database.connection import db_manager


def test_database_connection(logger):
    """Test database connectivity"""
    logger.info("Testing database connection...")
    try:
        db_manager.initialize()
        session = db_manager.get_session()
        from sqlalchemy import text

        result = session.execute(text("SELECT version()")).scalar()
        logger.log_success(f"Database connected: {result}")
        session.close()
        return True
    except Exception as e:
        logger.log_error_box("Database connection failed", str(e))
        return False


def test_video_processing(logger):
    """Test video processing with a short sample"""
    logger.info("\nTesting video processing...")
    try:
        processor = VideoProcessor()

        # Test with a short video (replace with actual test URL)
        test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Rick Roll - 3:32

        logger.info(f"Downloading video info from: {test_url}")
        info = processor.download_video_info(test_url)

        if info:
            logger.log_success(f"Video info extracted: {info['title'][:50]}...")
            logger.info(f"   Duration: {info.get('duration', 'Unknown')} seconds")
            return True
        else:
            logger.error("Failed to extract video info")
            return False

    except Exception as e:
        logger.log_error_box("Video processing test failed", str(e))
        return False


def test_audio_fingerprinting(logger):
    """Test audio fingerprinting"""
    logger.info("\nTesting audio fingerprinting...")
    try:
        fingerprinter = AudioFingerprinter()

        # Test fingerprinting parameters
        logger.log_success("Fingerprinter initialized")
        logger.info(f"   Sample rate: {fingerprinter.sample_rate}")
        logger.info(f"   Frequency ranges: {len(fingerprinter.freq_ranges)}")

        return True

    except Exception as e:
        logger.log_error_box("Audio fingerprinting test failed", str(e))
        return False


def test_configuration(logger):
    """Test configuration loading"""
    logger.info("Testing configuration...")
    try:
        logger.log_success(f"Database URL configured: {bool(Config.get_database_url())}")
        logger.log_success(f"Target channels: {len(Config.TARGET_CHANNELS)}")
        logger.info(f"   Channels: {Config.TARGET_CHANNELS}")
        logger.log_success(f"Temp directory: {Config.TEMP_DIR}")

        # Check if temp directory exists
        import os

        if not os.path.exists(Config.TEMP_DIR):
            os.makedirs(Config.TEMP_DIR)
            logger.log_success(f"Created temp directory: {Config.TEMP_DIR}")

        return True
    except Exception as e:
        logger.log_error_box("Configuration test failed", str(e))
        return False


def main():
    """Run all tests"""
    # Parse CLI arguments
    parser = argparse.ArgumentParser(description="Run SoundHash system tests")
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
    setup_logging(log_level=args.log_level, log_file=None, use_colors=not args.no_colors)
    logger = create_section_logger(__name__)

    logger.log_section_start("SoundHash System Test", "Verifying system components")

    tests = [
        ("Configuration", test_configuration),
        ("Database Connection", test_database_connection),
        ("Audio Fingerprinting", test_audio_fingerprinting),
        ("Video Processing", test_video_processing),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            result = test_func(logger)
            results.append((test_name, result))
        except Exception as e:
            logger.log_error_box(f"{test_name} test crashed", str(e))
            results.append((test_name, False))

    logger.info("\n" + "=" * 50)
    logger.info("Test Results Summary:")

    passed = 0
    for test_name, result in results:
        if result:
            logger.log_success(f"PASS: {test_name}")
            passed += 1
        else:
            logger.error(f"FAIL: {test_name}")

    logger.info(f"\nOverall: {passed}/{len(results)} tests passed")

    if passed == len(results):
        logger.info("\n🎉 All tests passed! System is ready to use.")
        logger.info("\nNext steps:")
        logger.info("1. Copy .env.example to .env and configure API keys")
        logger.info("2. Run: python scripts/setup_database.py")
        logger.info("3. Run: python scripts/ingest_channels.py")
    else:
        logger.log_warning_box(f"{len(results) - passed} test(s) failed. Please check configuration.")

    logger.log_section_end("SoundHash System Test", success=passed == len(results))

    return passed == len(results)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
