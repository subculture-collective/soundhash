"""Tests for Twitter bot functionality."""

import pytest
from unittest.mock import MagicMock, Mock, patch

from src.bots.twitter_bot import TwitterBot


class TestTwitterBot:
    """Test suite for TwitterBot class."""

    @patch("src.bots.twitter_bot.tweepy.Client")
    def test_twitter_bot_initialization(self, mock_client):
        """Test that TwitterBot initializes correctly."""
        bot = TwitterBot()
        
        assert bot is not None
        assert bot.processor is not None
        assert bot.fingerprinter is not None
        assert bot.logger is not None
        mock_client.assert_called_once()

    def test_extract_video_urls(self):
        """Test video URL extraction from text."""
        with patch("src.bots.twitter_bot.tweepy.Client"):
            bot = TwitterBot()
        
        # Test YouTube URLs
        text = "Check out this video https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        urls = bot.extract_video_urls(text)
        assert len(urls) == 1
        assert "youtube.com" in urls[0]
        
        # Test short YouTube URLs
        text = "Check out https://youtu.be/dQw4w9WgXcQ"
        urls = bot.extract_video_urls(text)
        assert len(urls) == 1
        assert "youtu.be" in urls[0]
        
        # Test multiple URLs
        text = "Compare https://www.youtube.com/watch?v=abc123 and https://youtu.be/xyz789"
        urls = bot.extract_video_urls(text)
        assert len(urls) == 2
        
        # Test no URLs
        text = "Just some text without any URLs"
        urls = bot.extract_video_urls(text)
        assert len(urls) == 0

    def test_should_process_mention(self):
        """Test mention filtering logic."""
        with patch("src.bots.twitter_bot.tweepy.Client"):
            bot = TwitterBot()
        
        # Mock mention with bot name and keyword
        mention = Mock()
        mention.text = "@soundhash_bot can you find clip from this video?"
        assert bot.should_process_mention(mention) is True
        
        # Mock mention with bot name and URL
        mention.text = "@soundhash_bot https://www.youtube.com/watch?v=test123"
        assert bot.should_process_mention(mention) is True
        
        # Mock mention without bot name
        mention.text = "Hey someone help me find this clip"
        assert bot.should_process_mention(mention) is False

    def test_post_match_summary(self):
        """Test posting match summary."""
        with patch("src.bots.twitter_bot.tweepy.Client") as mock_client:
            mock_api = MagicMock()
            mock_client.return_value = mock_api
            
            bot = TwitterBot()
            
            # Test with valid matches
            matches = [
                {
                    "video_id": "test123",
                    "title": "Test Video",
                    "url": "https://youtube.com/watch?v=test123",
                    "start_time": 10.0,
                    "end_time": 20.0,
                    "confidence": 0.95,
                }
            ]
            
            mock_response = Mock()
            mock_response.data = {"id": "tweet123"}
            mock_api.create_tweet.return_value = mock_response
            
            result = bot.post_match_summary(matches)
            assert result is True
            mock_api.create_tweet.assert_called_once()
            
            # Check that the tweet text was formatted correctly
            call_args = mock_api.create_tweet.call_args
            tweet_text = call_args.kwargs['text']
            assert "🎵" in tweet_text
            assert "Test Video" in tweet_text
            assert "https://youtube.com/watch?v=test123" in tweet_text

    def test_post_match_summary_empty_matches(self):
        """Test posting with no matches."""
        with patch("src.bots.twitter_bot.tweepy.Client"):
            bot = TwitterBot()
            
            result = bot.post_match_summary([])
            assert result is False

    def test_post_match_summary_truncation(self):
        """Test that long summaries are truncated."""
        with patch("src.bots.twitter_bot.tweepy.Client") as mock_client:
            mock_api = MagicMock()
            mock_client.return_value = mock_api
            
            bot = TwitterBot()
            
            # Create matches with very long title
            matches = [
                {
                    "video_id": "test123",
                    "title": "A" * 200,  # Very long title
                    "url": "https://youtube.com/watch?v=test123",
                    "start_time": 10.0,
                    "end_time": 20.0,
                    "confidence": 0.95,
                }
            ]
            
            mock_response = Mock()
            mock_response.data = {"id": "tweet123"}
            mock_api.create_tweet.return_value = mock_response
            
            result = bot.post_match_summary(matches)
            assert result is True
            
            # Check that tweet was truncated to 280 characters
            call_args = mock_api.create_tweet.call_args
            tweet_text = call_args.kwargs['text']
            assert len(tweet_text) <= 280

    @patch("src.bots.twitter_bot.time.sleep")
    def test_send_reply_with_retry(self, mock_sleep):
        """Test reply with retry logic on rate limit."""
        from tweepy.errors import TooManyRequests
        
        with patch("src.bots.twitter_bot.tweepy.Client") as mock_client:
            mock_api = MagicMock()
            mock_client.return_value = mock_api
            
            bot = TwitterBot()
            
            mention = Mock()
            mention.id = "mention123"
            
            # Create a proper mock response for TooManyRequests
            mock_response = Mock()
            mock_response.json.return_value = {}
            
            # Simulate rate limit on first call, success on second
            mock_api.create_tweet.side_effect = [
                TooManyRequests(mock_response, response_json={}),
                Mock()
            ]
            
            result = bot.send_reply(mention, "Test reply")
            
            # Should succeed after retry
            assert result is True
            assert mock_api.create_tweet.call_count == 2
            assert mock_sleep.called

    def test_format_reply_text(self):
        """Test reply text formatting."""
        with patch("src.bots.twitter_bot.tweepy.Client"):
            bot = TwitterBot()
        
        matches = [
            {
                "video_id": "test1",
                "title": "Video One",
                "url": "https://youtube.com/watch?v=test1",
                "start_time": 10.0,
                "end_time": 20.0,
                "confidence": 0.95,
            },
            {
                "video_id": "test2",
                "title": "Video Two",
                "url": "https://youtube.com/watch?v=test2",
                "start_time": 30.0,
                "end_time": 40.0,
                "confidence": 0.87,
            },
        ]
        
        # Use the bot's formatting method instead of duplicating logic
        reply_text = bot.format_reply_text(matches)
        
        # Verify formatting
        assert "🎵" in reply_text
        assert "Video One" in reply_text
        assert "Video Two" in reply_text
        assert "10s - 20s" in reply_text
        assert len(reply_text.split("\n")) > 5  # Multiple lines
