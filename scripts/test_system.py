#!/usr/bin/env python3
"""
Quick test script to verify the system is working correctly.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from src.core.audio_fingerprinting import AudioFingerprinter
from src.core.video_processor import VideoProcessor
from src.database.connection import db_manager
from config.settings import Config

def test_database_connection():
    """Test database connectivity"""
    print("Testing database connection...")
    try:
        db_manager.initialize()
        session = db_manager.get_session()
        from sqlalchemy import text
        result = session.execute(text("SELECT version()")).scalar()
        print(f"✅ Database connected: {result}")
        session.close()
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_video_processing():
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
            return True
        else:
            print("❌ Failed to extract video info")
            return False
            
    except Exception as e:
        print(f"❌ Video processing test failed: {e}")
        return False

def test_audio_fingerprinting():
    """Test audio fingerprinting"""
    print("\nTesting audio fingerprinting...")
    try:
        fingerprinter = AudioFingerprinter()
        
        # Test fingerprinting parameters
        print(f"✅ Fingerprinter initialized")
        print(f"   Sample rate: {fingerprinter.sample_rate}")
        print(f"   Frequency ranges: {len(fingerprinter.freq_ranges)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Audio fingerprinting test failed: {e}")
        return False

def test_configuration():
    """Test configuration loading"""
    print("Testing configuration...")
    try:
        print(f"✅ Database URL configured: {bool(Config.get_database_url())}")
        print(f"✅ Target channels: {len(Config.TARGET_CHANNELS)}")
        print(f"   Channels: {Config.TARGET_CHANNELS}")
        print(f"✅ Temp directory: {Config.TEMP_DIR}")
        
        # Check if temp directory exists
        import os
        if not os.path.exists(Config.TEMP_DIR):
            os.makedirs(Config.TEMP_DIR)
            print(f"✅ Created temp directory: {Config.TEMP_DIR}")
        
        return True
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("SoundHash System Test")
    print("=" * 50)
    
    tests = [
        ("Configuration", test_configuration),
        ("Database Connection", test_database_connection),
        ("Audio Fingerprinting", test_audio_fingerprinting),
        ("Video Processing", test_video_processing),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("Test Results Summary:")
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\n🎉 All tests passed! System is ready to use.")
        print("\nNext steps:")
        print("1. Copy .env.example to .env and configure API keys")
        print("2. Run: python scripts/setup_database.py")
        print("3. Run: python scripts/ingest_channels.py")
    else:
        print(f"\n⚠️  {len(results) - passed} test(s) failed. Please check configuration.")
        
    return passed == len(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)