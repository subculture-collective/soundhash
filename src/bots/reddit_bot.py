"""
Reddit bot for responding to video clip matching requests.

This bot monitors specified subreddits for posts/comments containing video URLs
and responds with matching results from the SoundHash database.

TODO: Complete implementation
- [ ] Implement subreddit monitoring
- [ ] Add comment parsing and URL extraction
- [ ] Integrate with audio fingerprinting pipeline
- [ ] Add rate limiting and retry logic
- [ ] Implement proper error handling
- [ ] Add configuration for monitored subreddits
- [ ] Add OAuth token refresh logic
- [ ] Add unit tests
"""

import logging
import re
import time
from typing import List, Optional

import praw
from praw.exceptions import RedditAPIException
from prawcore.exceptions import (
    Forbidden,
    NotFound,
    RequestException,
    ResponseException,
    ServerError,
    TooManyRequests,
)

from config.settings import Config
from src.core.audio_fingerprinting import AudioFingerprinter
from src.core.video_processor import VideoProcessor
from src.database.repositories import get_video_repository


class RedditBot:
    """
    Reddit bot for responding to video clip matching requests.
    
    Features:
    - Monitors specified subreddits for video URLs
    - Extracts and processes video clips
    - Replies with match results and links
    - Handles rate limiting and errors gracefully
    """

    def __init__(self):
        """
        Initialize Reddit bot with PRAW.
        
        TODO:
        - Add configuration validation
        - Implement OAuth token refresh
        - Add connection retry logic
        """
        # Initialize Reddit API with PRAW
        # See: https://praw.readthedocs.io/en/stable/getting_started/authentication.html
        self.reddit = praw.Reddit(
            client_id=Config.REDDIT_CLIENT_ID,
            client_secret=Config.REDDIT_CLIENT_SECRET,
            user_agent=Config.REDDIT_USER_AGENT,
            refresh_token=Config.REDDIT_REFRESH_TOKEN,
        )

        # TODO: Initialize with proper configuration
        self.processor = VideoProcessor()
        self.fingerprinter = AudioFingerprinter()
        
        # TODO: Make these configurable via environment variables
        self.monitored_subreddits = []  # e.g., ['musicid', 'tipofmytongue']
        self.bot_username = None  # Will be set after authentication
        
        self.logger = logging.getLogger(__name__)
        
        # Verify authentication
        try:
            self.bot_username = self.reddit.user.me().name
            self.logger.info(f"Reddit bot authenticated as u/{self.bot_username}")
        except Exception as e:
            self.logger.error(f"Failed to authenticate with Reddit: {e}")
            raise

    def monitor_subreddits(self, subreddits: List[str], limit: int = 10):
        """
        Monitor specified subreddits for new posts and comments.
        
        Args:
            subreddits: List of subreddit names to monitor
            limit: Number of recent items to check
            
        TODO:
        - Implement streaming for real-time monitoring
        - Add post/comment filtering logic
        - Track processed items to avoid duplicates
        - Add keyword matching
        """
        if not subreddits:
            self.logger.warning("No subreddits specified for monitoring")
            return
        
        subreddit_names = "+".join(subreddits)
        subreddit = self.reddit.subreddit(subreddit_names)
        
        try:
            # Check recent submissions
            for submission in subreddit.new(limit=limit):
                if self.should_process_submission(submission):
                    self.process_submission(submission)
            
            # Check recent comments
            for comment in subreddit.comments(limit=limit):
                if self.should_process_comment(comment):
                    self.process_comment(comment)
                    
        except Exception as e:
            self.logger.error(f"Error monitoring subreddits: {e}")

    def should_process_submission(self, submission) -> bool:
        """
        Check if a submission should be processed.
        
        TODO:
        - Add keyword matching
        - Check if already processed
        - Add flair filtering
        - Add score threshold
        """
        # TODO: Implement filtering logic
        return False

    def should_process_comment(self, comment) -> bool:
        """
        Check if a comment should be processed.
        
        TODO:
        - Add keyword matching
        - Check if already processed
        - Check if it's a reply to bot
        - Add parent context checking
        """
        # TODO: Implement filtering logic
        return False

    def extract_video_urls(self, text: str) -> List[str]:
        """
        Extract video URLs from text.
        
        TODO:
        - Add more video platforms
        - Handle shortened URLs
        - Add URL validation
        """
        patterns = [
            r"https?://(?:www\.)?youtube\.com/watch\?v=[\w\-]+",
            r"https?://youtu\.be/[\w\-]+",
            r"https?://(?:www\.)?tiktok\.com/@[\w\-]+/video/[\w\-]+",
            r"https?://(?:vm\.)?tiktok\.com/[\w\-]+",
            r"https?://(?:www\.)?instagram\.com/reel/[\w\-]+",
            r"https?://(?:v\.)?redd\.it/[\w\-]+",
        ]
        
        urls = []
        for pattern in patterns:
            urls.extend(re.findall(pattern, text, re.IGNORECASE))
        
        return urls

    def process_submission(self, submission):
        """
        Process a Reddit submission and reply with results.
        
        TODO:
        - Implement video processing
        - Add match finding
        - Format reply
        - Handle errors
        """
        self.logger.info(f"Processing submission: {submission.id}")
        # TODO: Implement

    def process_comment(self, comment):
        """
        Process a Reddit comment and reply with results.
        
        TODO:
        - Implement video processing
        - Add match finding
        - Format reply
        - Handle errors
        """
        self.logger.info(f"Processing comment: {comment.id}")
        # TODO: Implement

    def find_matches(self, video_url: str) -> List[dict]:
        """
        Find matches for a video URL.
        
        TODO:
        - Implement fingerprinting integration
        - Add database queries
        - Handle errors
        - Add caching
        """
        # TODO: Implement similar to TwitterBot.find_matches
        return []

    def format_reply(self, matches: List[dict]) -> str:
        """
        Format matches into a Reddit comment.
        
        TODO:
        - Use Reddit markdown formatting
        - Add proper links
        - Include confidence scores
        - Add bot signature
        """
        if not matches:
            return "No matches found in our database."
        
        reply = "## 🎵 Audio Match Results\n\n"
        reply += f"Found **{len(matches)}** match(es):\n\n"
        
        for i, match in enumerate(matches[:5], 1):  # Top 5 matches
            title = match["title"]
            start_time = int(match["start_time"])
            end_time = int(match["end_time"])
            
            reply += f"{i}. **{title}**\n"
            reply += f"   - Time: {start_time}s - {end_time}s\n"
            reply += f"   - Link: {match['url']}\n\n"
        
        if len(matches) > 5:
            reply += f"...and {len(matches) - 5} more matches!\n\n"
        
        # TODO: Add bot signature and help info
        reply += "\n---\n"
        reply += "*^(I'm a bot that identifies audio clips. | )[^(Learn more)](https://github.com/subculture-collective/soundhash)*"
        
        return reply

    def reply_to_submission(self, submission, text: str, max_retries: int = 3) -> bool:
        """
        Reply to a submission with retry logic.
        
        TODO:
        - Implement retry logic
        - Add rate limit handling
        - Add error recovery
        """
        retry_count = 0
        retry_delay = 5
        
        while retry_count < max_retries:
            try:
                submission.reply(text)
                self.logger.info(f"Replied to submission {submission.id}")
                return True
                
            except TooManyRequests as e:
                # TODO: Implement proper rate limit handling
                retry_count += 1
                wait_time = retry_delay * (2 ** (retry_count - 1))
                self.logger.warning(f"Rate limited. Waiting {wait_time}s ({retry_count}/{max_retries})")
                time.sleep(wait_time)
                
            except (Forbidden, NotFound) as e:
                self.logger.error(f"Cannot reply to submission {submission.id}: {e}")
                return False
                
            except (ServerError, ResponseException, RequestException) as e:
                # TODO: Implement server error handling
                retry_count += 1
                wait_time = retry_delay * (2 ** (retry_count - 1))
                self.logger.warning(f"Server error. Retrying in {wait_time}s ({retry_count}/{max_retries})")
                time.sleep(wait_time)
                
            except Exception as e:
                self.logger.error(f"Error replying to submission {submission.id}: {e}")
                return False
        
        return False

    def reply_to_comment(self, comment, text: str, max_retries: int = 3) -> bool:
        """
        Reply to a comment with retry logic.
        
        TODO:
        - Implement retry logic
        - Add rate limit handling
        - Add error recovery
        """
        retry_count = 0
        retry_delay = 5
        
        while retry_count < max_retries:
            try:
                comment.reply(text)
                self.logger.info(f"Replied to comment {comment.id}")
                return True
                
            except TooManyRequests as e:
                # TODO: Implement proper rate limit handling
                retry_count += 1
                wait_time = retry_delay * (2 ** (retry_count - 1))
                self.logger.warning(f"Rate limited. Waiting {wait_time}s ({retry_count}/{max_retries})")
                time.sleep(wait_time)
                
            except (Forbidden, NotFound) as e:
                self.logger.error(f"Cannot reply to comment {comment.id}: {e}")
                return False
                
            except (ServerError, ResponseException, RequestException) as e:
                # TODO: Implement server error handling
                retry_count += 1
                wait_time = retry_delay * (2 ** (retry_count - 1))
                self.logger.warning(f"Server error. Retrying in {wait_time}s ({retry_count}/{max_retries})")
                time.sleep(wait_time)
                
            except Exception as e:
                self.logger.error(f"Error replying to comment {comment.id}: {e}")
                return False
        
        return False


def main():
    """
    Main bot loop.
    
    TODO:
    - Implement continuous monitoring
    - Add graceful shutdown
    - Add health checks
    - Add metrics/logging
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    logger = logging.getLogger(__name__)
    
    # Load monitored subreddits from configuration
    monitored_subreddits = getattr(Config, "REDDIT_SUBREDDITS", []) or []
    
    if not monitored_subreddits:
        logger.error("No subreddits configured for monitoring. Set REDDIT_SUBREDDITS environment variable.")
        return
    
    try:
        bot = RedditBot()
        
        logger.info(f"Starting Reddit bot monitoring: {', '.join(monitored_subreddits)}")
        
        while True:
            try:
                bot.monitor_subreddits(monitored_subreddits)
                
                # Wait before checking again
                time.sleep(60)  # Check every 60 seconds
                
            except KeyboardInterrupt:
                logger.info("Bot stopped by user")
                break
            except Exception as e:
                logger.error(f"Bot error: {e}")
                time.sleep(300)  # Wait 5 minutes on error
                
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        raise


if __name__ == "__main__":
    main()
