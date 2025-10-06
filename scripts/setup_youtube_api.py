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

import os
import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.api.youtube_service import YouTubeAPIService

def setup_logging():
    """Setup basic logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def check_credentials_file():
    """Check if credentials.json exists"""
    credentials_path = Path('credentials.json')
    if not credentials_path.exists():
        print("❌ credentials.json not found!")
        print()
        print("To set up YouTube Data API:")
        print("1. Go to Google Cloud Console: https://console.cloud.google.com/")
        print("2. Create a new project or select existing one")
        print("3. Enable YouTube Data API v3")
        print("4. Go to 'Credentials' section")
        print("5. Create OAuth 2.0 Client ID (Desktop Application)")
        print("6. Download the JSON file and save as 'credentials.json' in this directory")
        print()
        return False
    
    print("✅ credentials.json found")
    return True

def test_youtube_api():
    """Test YouTube API connection and basic functionality"""
    try:
        print("🔄 Initializing YouTube API service...")
        service = YouTubeAPIService()
        
        print("🔄 Testing API connection...")
        if service.test_connection():
            print("✅ YouTube API connection successful!")
        else:
            print("❌ YouTube API connection failed")
            return False
        
        # Test getting channel info for a known channel
        test_channel_id = "UCo_QGM_tJZOkOCIFi2ik5kA"  # From your config
        print(f"🔄 Testing channel info retrieval for {test_channel_id}...")
        
        channel_info = service.get_channel_info(test_channel_id)
        if channel_info:
            print(f"✅ Channel info retrieved: {channel_info['title']}")
            print(f"   Subscriber count: {channel_info.get('subscriber_count', 'N/A')}")
        else:
            print("❌ Failed to retrieve channel info")
            return False
        
        # Test getting channel videos
        print(f"🔄 Testing video list retrieval (max 5 videos)...")
        videos = service.get_channel_videos(test_channel_id, max_results=5)
        if videos:
            print(f"✅ Retrieved {len(videos)} videos")
            for i, video in enumerate(videos[:3], 1):
                print(f"   {i}. {video['title'][:50]}...")
        else:
            print("⚠️  No videos retrieved (may be due to channel settings)")
        
        return True
        
    except FileNotFoundError as e:
        print(f"❌ Credentials file error: {e}")
        print("Make sure credentials.json is in the current directory")
        return False
    except Exception as e:
        print(f"❌ Error testing YouTube API: {e}")
        return False

def main():
    setup_logging()
    
    print("YouTube Data API Setup and Test")
    print("=" * 40)
    
    # Check credentials file
    if not check_credentials_file():
        return 1
    
    # Test YouTube API
    if test_youtube_api():
        print()
        print("🎉 YouTube Data API setup successful!")
        print()
        print("Next steps:")
        print("1. Run the ingestion script: python scripts/ingest_channels.py --dry-run")
        print("2. The system will now use YouTube Data API for metadata")
        print("3. Audio downloads will still use yt-dlp (may require cookies for some videos)")
        return 0
    else:
        print()
        print("❌ YouTube Data API setup failed")
        print("Please check your credentials and try again")
        return 1

if __name__ == "__main__":
    exit(main())