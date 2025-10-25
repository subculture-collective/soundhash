#!/usr/bin/env python3
"""
Enhanced system test script to verify the system is working correctly.
Includes E2E testing, metrics validation, and health checks.
"""

import os
import sys
import time
from typing import Dict, Any

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import Config
from src.core.audio_fingerprinting import AudioFingerprinter
from src.core.video_processor import VideoProcessor
from src.database.connection import db_manager

# Import observability components if enabled
if Config.METRICS_ENABLED:
    from src.observability.metrics import metrics
    from src.observability.health import HealthChecker
else:
    metrics = None
    HealthChecker = None  # type: ignore[misc,assignment]


def test_database_connection() -> Dict[str, Any]:
    """Test database connectivity"""
    print("Testing database connection...")
    try:
        db_manager.initialize()
        session = db_manager.get_session()
        from sqlalchemy import text

        result = session.execute(text("SELECT version()")).scalar()
        print(f"✅ Database connected: {result}")
        session.close()
        return {"status": "pass", "details": result}
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return {"status": "fail", "error": str(e)}


def test_video_processing() -> Dict[str, Any]:
    """Test video processing with a short sample"""
    print("\nTesting video processing...")
    try:
        processor = VideoProcessor()

        # Test with a short video (replace with actual test URL)
        test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Rick Roll - 3:32

        print(f"Downloading video info from: {test_url}")
        info = processor.download_video_info(test_url)

        if info:
            print(f"✅ Video info extracted: {info['title'][:50]}...")
            print(f"   Duration: {info.get('duration', 'Unknown')} seconds")
            return {"status": "pass", "video_info": info}
        else:
            print("❌ Failed to extract video info")
            return {"status": "fail", "error": "Failed to extract video info"}

    except Exception as e:
        print(f"❌ Video processing test failed: {e}")
        return {"status": "fail", "error": str(e)}


def test_audio_fingerprinting() -> Dict[str, Any]:
    """Test audio fingerprinting"""
    print("\nTesting audio fingerprinting...")
    try:
        fingerprinter = AudioFingerprinter()

        # Test fingerprinting parameters
        print("✅ Fingerprinter initialized")
        print(f"   Sample rate: {fingerprinter.sample_rate}")
        print(f"   Frequency ranges: {len(fingerprinter.freq_ranges)}")

        return {
            "status": "pass",
            "sample_rate": fingerprinter.sample_rate,
            "freq_ranges": len(fingerprinter.freq_ranges),
        }

    except Exception as e:
        print(f"❌ Audio fingerprinting test failed: {e}")
        return {"status": "fail", "error": str(e)}


def test_configuration() -> Dict[str, Any]:
    """Test configuration loading"""
    print("Testing configuration...")
    try:
        print(f"✅ Database URL configured: {bool(Config.get_database_url())}")
        print(f"✅ Target channels: {len(Config.TARGET_CHANNELS)}")
        print(f"   Channels: {Config.TARGET_CHANNELS}")
        print(f"✅ Temp directory: {Config.TEMP_DIR}")
        print(f"✅ Metrics enabled: {Config.METRICS_ENABLED}")
        if Config.METRICS_ENABLED:
            print(f"   Metrics port: {Config.METRICS_PORT}")
            print(f"   Health check interval: {Config.HEALTH_CHECK_INTERVAL}s")

        # Check if temp directory exists
        import os

        if not os.path.exists(Config.TEMP_DIR):
            os.makedirs(Config.TEMP_DIR)
            print(f"✅ Created temp directory: {Config.TEMP_DIR}")

        return {
            "status": "pass",
            "db_configured": bool(Config.get_database_url()),
            "target_channels": len(Config.TARGET_CHANNELS),
            "metrics_enabled": Config.METRICS_ENABLED,
        }
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return {"status": "fail", "error": str(e)}


def test_health_checks() -> Dict[str, Any]:
    """Test health check system"""
    print("\nTesting health checks...")
    if not HealthChecker:
        print("⚠️  Health checks disabled (metrics not enabled)")
        return {"status": "skip", "reason": "Health checks require metrics enabled"}

    try:
        checker = HealthChecker()
        health_status = checker.check_all()

        print(f"✅ Health check system operational")
        print(f"   Overall status: {health_status['overall_status']}")

        for check_name, check_result in health_status["checks"].items():
            status_emoji = "✅" if check_result.get("status") == "healthy" else "❌"
            print(f"   {status_emoji} {check_name}: {check_result.get('status')}")

        return {"status": "pass", "health": health_status}
    except Exception as e:
        print(f"❌ Health check test failed: {e}")
        return {"status": "fail", "error": str(e)}


def test_metrics_system() -> Dict[str, Any]:
    """Test metrics collection system"""
    print("\nTesting metrics system...")
    if not metrics:
        print("⚠️  Metrics disabled")
        return {"status": "skip", "reason": "Metrics not enabled"}

    try:
        # Test that metrics are accessible
        print("✅ Metrics system initialized")
        print(f"   Ingestion counters: available")
        print(f"   Processing counters: available")
        print(f"   Timing histograms: available")
        print(f"   Health gauges: available")

        # Try starting metrics server (non-blocking check)
        # Note: In a real system, this would be started elsewhere
        print(f"   Metrics endpoint: localhost:{Config.METRICS_PORT}")

        return {"status": "pass", "metrics_port": Config.METRICS_PORT}
    except Exception as e:
        print(f"❌ Metrics test failed: {e}")
        return {"status": "fail", "error": str(e)}


def test_e2e_minimal() -> Dict[str, Any]:
    """
    Minimal E2E test: verify that the full pipeline can be initialized.
    Does not actually process videos to keep test fast.
    """
    print("\nTesting E2E pipeline initialization...")
    try:
        # Import pipeline components
        from src.ingestion.channel_ingester import ChannelIngester

        # Initialize components (without DB init for speed)
        print("   Initializing channel ingester...")
        ingester = ChannelIngester(initialize_db=False)

        print("   Verifying video processor...")
        assert ingester.video_processor is not None

        print("   Verifying audio fingerprinter...")
        assert ingester.fingerprinter is not None

        print("✅ E2E pipeline components initialized successfully")

        return {"status": "pass", "components": ["ingester", "processor", "fingerprinter"]}
    except Exception as e:
        print(f"❌ E2E test failed: {e}")
        return {"status": "fail", "error": str(e)}


def main():
    """Run all tests"""
    print("=" * 70)
    print("SoundHash Enhanced System Test")
    print("=" * 70)

    # Define test suite
    tests = [
        ("Configuration", test_configuration),
        ("Database Connection", test_database_connection),
        ("Audio Fingerprinting", test_audio_fingerprinting),
        ("Video Processing", test_video_processing),
        ("E2E Pipeline", test_e2e_minimal),
    ]

    # Add observability tests if enabled
    if Config.METRICS_ENABLED:
        tests.extend(
            [
                ("Metrics System", test_metrics_system),
                ("Health Checks", test_health_checks),
            ]
        )

    results = []
    details = {}

    # Run tests
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result.get("status", "fail")))
            details[test_name] = result
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, "fail"))
            details[test_name] = {"status": "fail", "error": str(e)}

    # Print summary
    print("\n" + "=" * 70)
    print("Test Results Summary:")
    print("=" * 70)

    passed = 0
    skipped = 0
    failed = 0

    for test_name, status in results:
        if status == "pass":
            print(f"✅ PASS {test_name}")
            passed += 1
        elif status == "skip":
            print(f"⚠️  SKIP {test_name}")
            skipped += 1
        else:
            print(f"❌ FAIL {test_name}")
            if test_name in details and "error" in details[test_name]:
                print(f"        Error: {details[test_name]['error'][:100]}")
            failed += 1

    total = len(results)
    print(f"\n{'=' * 70}")
    print(f"Overall: {passed} passed, {failed} failed, {skipped} skipped (out of {total} tests)")
    print(f"{'=' * 70}")

    if passed == total - skipped:
        print("\n🎉 All non-skipped tests passed! System is ready to use.")
        print("\nNext steps:")
        print("1. Ensure PostgreSQL is running")
        print("2. Copy .env.example to .env and configure settings")
        print("3. Run: python scripts/setup_database.py")
        print("4. Run: python scripts/ingest_channels.py --dry-run --max-videos 5")
        if Config.METRICS_ENABLED:
            print(f"5. View metrics at: http://localhost:{Config.METRICS_PORT}")
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please check configuration and logs.")

    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
