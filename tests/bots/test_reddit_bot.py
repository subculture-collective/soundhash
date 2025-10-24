"""Tests for Reddit bot functionality."""

import pytest
from unittest.mock import MagicMock, Mock, patch
import urllib.parse
from src.bots.reddit_bot import RedditBot


class TestRedditBot:
    """Test suite for RedditBot class."""

    @patch("src.bots.reddit_bot.praw.Reddit")
    def test_reddit_bot_initialization(self, mock_reddit):
        """Test that RedditBot initializes correctly."""
        # Mock the user.me() call for authentication
        mock_user = Mock()
        mock_user.name = "test_bot"
        mock_reddit.return_value.user.me.return_value = mock_user
        
        bot = RedditBot()
        
        assert bot is not None
        assert bot.processor is not None
        assert bot.fingerprinter is not None
        assert bot.logger is not None
        assert bot.bot_username == "test_bot"
        mock_reddit.assert_called_once()

    def test_extract_video_urls(self):
        """Test video URL extraction from text."""
        with patch("src.bots.reddit_bot.praw.Reddit") as mock_reddit:
            mock_user = Mock()
            mock_user.name = "test_bot"
            mock_reddit.return_value.user.me.return_value = mock_user
            
            bot = RedditBot()
        
        # Test YouTube URLs
        text = "Check out this video https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        urls = bot.extract_video_urls(text)
        assert len(urls) == 1
        host = urllib.parse.urlparse(urls[0]).hostname
        assert host and ("youtube.com" == host or host.endswith(".youtube.com"))
        
        # Test Reddit video URLs
        text = "Here's the video https://v.redd.it/abc123xyz"
        urls = bot.extract_video_urls(text)
        assert len(urls) == 1
        host = urllib.parse.urlparse(urls[0]).hostname
        assert host and ("redd.it" == host or host.endswith(".redd.it"))
        
        # Test Instagram reels
        text = "Check this reel https://www.instagram.com/reel/abc123/"
        urls = bot.extract_video_urls(text)
        assert len(urls) == 1
        host = urllib.parse.urlparse(urls[0]).hostname
        assert host and ("instagram.com" == host or host.endswith(".instagram.com"))
        
        # Test multiple URLs
        text = "Compare https://www.youtube.com/watch?v=abc123 and https://youtu.be/xyz789"
        urls = bot.extract_video_urls(text)
        assert len(urls) == 2
        
        # Test no URLs
        text = "Just some text without any URLs"
        urls = bot.extract_video_urls(text)
        assert len(urls) == 0

    def test_format_reply(self):
        """Test reply formatting for Reddit."""
        with patch("src.bots.reddit_bot.praw.Reddit") as mock_reddit:
            mock_user = Mock()
            mock_user.name = "test_bot"
            mock_reddit.return_value.user.me.return_value = mock_user
            
            bot = RedditBot()
        
        # Test with matches
        matches = [
            {
                "video_id": "test1",
                "title": "Test Video One",
                "url": "https://youtube.com/watch?v=test1",
                "start_time": 10.0,
                "end_time": 20.0,
                "confidence": 0.95,
            },
            {
                "video_id": "test2",
                "title": "Test Video Two",
                "url": "https://youtube.com/watch?v=test2",
                "start_time": 30.0,
                "end_time": 40.0,
                "confidence": 0.87,
            },
        ]
        
        reply = bot.format_reply(matches)
        
        assert "🎵" in reply
        assert "Audio Match Results" in reply
        assert "Test Video One" in reply
        assert "Test Video Two" in reply
        assert "10s - 20s" in reply
        assert "30s - 40s" in reply
        assert "I'm a bot" in reply
        
        # Test with no matches
        reply = bot.format_reply([])
        assert "No matches found" in reply

    def test_format_reply_many_matches(self):
        """Test reply formatting with more than 5 matches."""
        with patch("src.bots.reddit_bot.praw.Reddit") as mock_reddit:
            mock_user = Mock()
            mock_user.name = "test_bot"
            mock_reddit.return_value.user.me.return_value = mock_user
            
            bot = RedditBot()
        
        # Create 10 matches
        matches = [
            {
                "video_id": f"test{i}",
                "title": f"Test Video {i}",
                "url": f"https://youtube.com/watch?v=test{i}",
                "start_time": float(i * 10),
                "end_time": float(i * 10 + 10),
                "confidence": 0.9,
            }
            for i in range(10)
        ]
        
        reply = bot.format_reply(matches)
        
        # Should only show top 5
        assert "Test Video 0" in reply
        assert "Test Video 4" in reply
        assert "and 5 more matches" in reply

    @patch("src.bots.reddit_bot.time.sleep")
    def test_reply_to_submission_with_retry(self, mock_sleep):
        """Test reply to submission with retry logic."""
        from prawcore.exceptions import ServerError
        
        with patch("src.bots.reddit_bot.praw.Reddit") as mock_reddit:
            mock_user = Mock()
            mock_user.name = "test_bot"
            mock_reddit.return_value.user.me.return_value = mock_user
            
            bot = RedditBot()
            
            submission = Mock()
            submission.id = "submission123"
            
            # Simulate server error on first call, success on second
            submission.reply.side_effect = [
                ServerError(Mock()),
                Mock()
            ]
            
            result = bot.reply_to_submission(submission, "Test reply")
            
            # Should succeed after retry
            assert result is True
            assert submission.reply.call_count == 2
            assert mock_sleep.called

    @patch("src.bots.reddit_bot.time.sleep")
    def test_reply_to_comment_with_retry(self, mock_sleep):
        """Test reply to comment with retry logic."""
        from prawcore.exceptions import ServerError
        
        with patch("src.bots.reddit_bot.praw.Reddit") as mock_reddit:
            mock_user = Mock()
            mock_user.name = "test_bot"
            mock_reddit.return_value.user.me.return_value = mock_user
            
            bot = RedditBot()
            
            comment = Mock()
            comment.id = "comment123"
            
            # Simulate server error on first call, success on second
            comment.reply.side_effect = [
                ServerError(Mock()),
                Mock()
            ]
            
            result = bot.reply_to_comment(comment, "Test reply")
            
            # Should succeed after retry
            assert result is True
            assert comment.reply.call_count == 2
            assert mock_sleep.called

    def test_reply_forbidden_error(self):
        """Test handling of forbidden errors."""
        from prawcore.exceptions import Forbidden
        
        with patch("src.bots.reddit_bot.praw.Reddit") as mock_reddit:
            mock_user = Mock()
            mock_user.name = "test_bot"
            mock_reddit.return_value.user.me.return_value = mock_user
            
            bot = RedditBot()
            
            submission = Mock()
            submission.id = "submission123"
            submission.reply.side_effect = Forbidden(Mock())
            
            result = bot.reply_to_submission(submission, "Test reply")
            
            # Should fail without retry
            assert result is False
            assert submission.reply.call_count == 1

    def test_monitor_subreddits_empty_list(self):
        """Test monitoring with empty subreddit list."""
        with patch("src.bots.reddit_bot.praw.Reddit") as mock_reddit:
            mock_user = Mock()
            mock_user.name = "test_bot"
            mock_reddit.return_value.user.me.return_value = mock_user
            
            bot = RedditBot()
            
            # Should handle empty list gracefully
            bot.monitor_subreddits([])
            
            # Should not make any API calls
            mock_reddit.return_value.subreddit.assert_not_called()
