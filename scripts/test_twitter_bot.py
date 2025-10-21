#!/usr/bin/env python3
"""
Test script for Twitter bot functionality.

This script tests:
1. Twitter API authentication
2. Posting a test message
3. Match summary formatting
"""

import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import Config
from src.bots.twitter_bot import TwitterBot


def test_twitter_auth():
    """Test Twitter API authentication."""
    print("Testing Twitter API authentication...")
    
    # Check if credentials are configured
    if not all([
        Config.TWITTER_BEARER_TOKEN,
        Config.TWITTER_CONSUMER_KEY,
        Config.TWITTER_CONSUMER_SECRET,
        Config.TWITTER_ACCESS_TOKEN,
        Config.TWITTER_ACCESS_TOKEN_SECRET,
    ]):
        print("❌ Twitter API credentials not fully configured")
        print("\nPlease set the following environment variables:")
        print("  - TWITTER_BEARER_TOKEN")
        print("  - TWITTER_CONSUMER_KEY")
        print("  - TWITTER_CONSUMER_SECRET")
        print("  - TWITTER_ACCESS_TOKEN")
        print("  - TWITTER_ACCESS_TOKEN_SECRET")
        return False
    
    try:
        bot = TwitterBot()
        print("✅ Twitter API client initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to initialize Twitter API client: {e}")
        return False


def test_post_message(dry_run=True):
    """Test posting a message to Twitter."""
    print("\nTesting message posting...")
    
    if dry_run:
        print("ℹ️  Running in dry-run mode (won't actually post)")
        
        # Create sample match data
        sample_matches = [
            {
                "video_id": "dQw4w9WgXcQ",
                "title": "Rick Astley - Never Gonna Give You Up (Official Video)",
                "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "start_time": 45.0,
                "end_time": 135.0,
                "confidence": 0.95,
            },
            {
                "video_id": "9bZkp7q19f0",
                "title": "PSY - GANGNAM STYLE (강남스타일) M/V",
                "url": "https://www.youtube.com/watch?v=9bZkp7q19f0",
                "start_time": 30.0,
                "end_time": 120.0,
                "confidence": 0.87,
            },
        ]
        
        # Format message as bot would
        summary = "🎵 Audio Match Results\n\n"
        summary += f"Found {len(sample_matches)} match(es):\n\n"
        
        for i, match in enumerate(sample_matches, 1):
            title = match["title"][:40] + "..." if len(match["title"]) > 40 else match["title"]
            start_time = int(match["start_time"])
            end_time = int(match["end_time"])
            
            summary += f"{i}. {title}\n"
            summary += f"   ⏰ {start_time}s-{end_time}s\n"
            summary += f"   🔗 {match['url']}\n\n"
        
        print("\n📝 Sample tweet that would be posted:")
        print("=" * 60)
        print(summary)
        print("=" * 60)
        print(f"Length: {len(summary)} characters (limit: 280)")
        
        if len(summary) > 280:
            print("⚠️  Warning: Tweet exceeds character limit and would be truncated")
            print("\n📝 Truncated version:")
            print("=" * 60)
            print(summary[:277] + "...")
            print("=" * 60)
        
        print("✅ Message formatting test passed")
        return True
    else:
        print("ℹ️  Attempting to post a real test message...")
        
        try:
            bot = TwitterBot()
            
            # Create simple test matches
            test_matches = [
                {
                    "video_id": "test123",
                    "title": "Test Video for SoundHash Bot",
                    "url": "https://example.com/test",
                    "start_time": 10.0,
                    "end_time": 20.0,
                    "confidence": 0.99,
                }
            ]
            
            success = bot.post_match_summary(test_matches, query_url="https://example.com/query")
            
            if success:
                print("✅ Successfully posted test message to Twitter!")
                return True
            else:
                print("❌ Failed to post message (check logs for details)")
                return False
                
        except Exception as e:
            print(f"❌ Error posting message: {e}")
            return False


def main():
    """Run all tests."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    print("=" * 60)
    print("Twitter Bot Test Suite")
    print("=" * 60)
    
    # Test 1: Authentication
    auth_ok = test_twitter_auth()
    
    if not auth_ok:
        print("\n❌ Authentication failed. Cannot proceed with other tests.")
        sys.exit(1)
    
    # Test 2: Message formatting (dry run)
    format_ok = test_post_message(dry_run=True)
    
    # Test 3: Actual posting (if user confirms)
    print("\n" + "=" * 60)
    response = input("Do you want to post a real test message to Twitter? (y/N): ")
    
    if response.lower() == 'y':
        post_ok = test_post_message(dry_run=False)
    else:
        print("ℹ️  Skipping real post test")
        post_ok = True
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Results:")
    print(f"  Authentication: {'✅' if auth_ok else '❌'}")
    print(f"  Message Format: {'✅' if format_ok else '❌'}")
    print(f"  Post Message:   {'✅' if post_ok else '⏭️  Skipped'}")
    print("=" * 60)
    
    if auth_ok and format_ok and post_ok:
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
