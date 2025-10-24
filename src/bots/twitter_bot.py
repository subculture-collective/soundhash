import logging
import re

import tweepy
from tweepy.errors import TooManyRequests, TwitterServerError

from config.settings import Config
from src.bots.utils import twitter_retry
from src.core.audio_fingerprinting import AudioFingerprinter
from src.core.video_processor import VideoProcessor
from src.database.repositories import get_video_repository


class TwitterBot:
    """
    Twitter bot for responding to video clip matching requests.
    Listens for mentions and processes video URLs to find matches.
    """

    def __init__(self):
        # Initialize Twitter API
        self.api = tweepy.Client(
            bearer_token=Config.TWITTER_BEARER_TOKEN,
            consumer_key=Config.TWITTER_CONSUMER_KEY,
            consumer_secret=Config.TWITTER_CONSUMER_SECRET,
            access_token=Config.TWITTER_ACCESS_TOKEN,
            access_token_secret=Config.TWITTER_ACCESS_TOKEN_SECRET,
            wait_on_rate_limit=True,
        )

        self.processor = VideoProcessor()
        self.fingerprinter = AudioFingerprinter()
        self.bot_name = Config.BOT_NAME
        self.keywords = Config.BOT_KEYWORDS

        self.logger = logging.getLogger(__name__)

    def listen_for_mentions(self):
        """Listen for bot mentions and process video requests"""
        try:
            # Get recent mentions
            mentions = self.api.get_mentions(
                max_results=50, tweet_fields=["author_id", "created_at", "conversation_id"]
            )

            if not mentions.data:
                self.logger.info("No new mentions found")
                return

            for mention in mentions.data:
                try:
                    if self.should_process_mention(mention):
                        self.process_mention(mention)
                except Exception as e:
                    self.logger.error(f"Error processing mention {mention.id}: {str(e)}")

        except Exception as e:
            self.logger.error(f"Error listening for mentions: {str(e)}")

    def should_process_mention(self, mention) -> bool:
        """Check if mention should be processed"""
        text = mention.text.lower()

        # Check if bot is mentioned
        if self.bot_name.lower() not in text:
            return False

        # Check for relevant keywords
        has_keywords = any(keyword.lower() in text for keyword in self.keywords)

        # Check for video URLs
        has_video_url = bool(self.extract_video_urls(mention.text))

        return has_keywords or has_video_url

    def extract_video_urls(self, text: str) -> list[str]:
        """Extract video URLs from text"""
        patterns = [
            r"https?://(?:www\.)?youtube\.com/watch\?v=[\w\-]+",
            r"https?://youtu\.be/[\w\-]+",
            r"https?://(?:www\.)?tiktok\.com/@[\w\-]+/video/[\w\-]+",
            r"https?://(?:vm\.)?tiktok\.com/[\w\-]+",
            r"https?://twitter\.com/\w+/status/\d+",
            r"https?://(?:www\.)?instagram\.com/reel/[\w\-]+",
        ]

        urls = []
        for pattern in patterns:
            urls.extend(re.findall(pattern, text, re.IGNORECASE))

        return urls

    def process_mention(self, mention):
        """Process a mention and reply with results"""
        self.logger.info(f"Processing mention: {mention.id}")

        try:
            video_urls = self.extract_video_urls(mention.text)

            if not video_urls:
                self.reply_no_video(mention)
                return

            # Process the first video URL
            video_url = video_urls[0]
            matches = self.find_matches(video_url)

            if matches:
                self.reply_with_matches(mention, matches)
            else:
                self.reply_no_matches(mention)

        except Exception as e:
            self.logger.error(f"Error processing mention {mention.id}: {str(e)}")
            self.reply_error(mention)

    def find_matches(self, video_url: str) -> list[dict]:
        """Find matches for a video URL"""
        try:
            # Process video and extract fingerprints
            segments = self.processor.process_video_for_fingerprinting(video_url)

            if not segments:
                return []

            matches = []
            video_repo = get_video_repository()

            # Check each segment against database
            for segment_file, start_time, end_time in segments:
                try:
                    # Extract fingerprint
                    fingerprint_data = self.fingerprinter.extract_fingerprint(segment_file)
                    fingerprint_hash = fingerprint_data["fingerprint_hash"]

                    # Find matches in database
                    db_fingerprints = video_repo.find_matching_fingerprints(fingerprint_hash)

                    for db_fp in db_fingerprints:
                        # Get detailed match info
                        video = db_fp.video
                        match_info = {
                            "video_id": video.video_id,
                            "title": video.title,
                            "url": video.url,
                            "start_time": db_fp.start_time,
                            "end_time": db_fp.end_time,
                            "confidence": db_fp.confidence_score,
                            "query_start": start_time,
                            "query_end": end_time,
                        }
                        matches.append(match_info)

                    # Clean up segment file
                    import os

                    if os.path.exists(segment_file):
                        os.remove(segment_file)

                except Exception as e:
                    self.logger.error(f"Error processing segment {start_time}-{end_time}: {str(e)}")
                    continue

            # Sort matches by confidence and remove duplicates
            unique_matches = {}
            for match in matches:
                video_id = match["video_id"]
                if (
                    video_id not in unique_matches
                    or match["confidence"] > unique_matches[video_id]["confidence"]
                ):
                    unique_matches[video_id] = match

            return list(unique_matches.values())[:5]  # Top 5 matches

        except Exception as e:
            self.logger.error(f"Error finding matches for {video_url}: {str(e)}")
            return []

    def reply_with_matches(self, mention, matches: list[dict]):
        """Reply with found matches"""
        reply_text = f"🎵 Found {len(matches)} match(es):\n\n"

        for i, match in enumerate(matches[:3], 1):  # Show top 3
            title = match["title"][:50] + "..." if len(match["title"]) > 50 else match["title"]
            start_time = int(match["start_time"])
            end_time = int(match["end_time"])

            reply_text += f"{i}. {title}\n"
            reply_text += f"   ⏰ {start_time}s - {end_time}s\n"
            reply_text += f"   🔗 {match['url']}\n\n"

        if len(matches) > 3:
            reply_text += f"... and {len(matches) - 3} more matches found!"

        self.send_reply(mention, reply_text)

    def reply_no_matches(self, mention):
        """Reply when no matches are found"""
        reply_text = "🔍 No matches found in our database. The clip might be from a source we haven't indexed yet."
        self.send_reply(mention, reply_text)

    def reply_no_video(self, mention):
        """Reply when no video URL is found"""
        reply_text = "🤔 Please include a video URL so I can search for matches!"
        self.send_reply(mention, reply_text)

    def reply_error(self, mention):
        """Reply when an error occurs"""
        reply_text = (
            "❌ Sorry, I encountered an error processing your request. Please try again later."
        )
        self.send_reply(mention, reply_text)

    def send_reply(self, mention, text: str, max_retries: int = 3):
        """Send a reply to a mention with retry logic"""
        try:
            self._send_reply_impl(mention, text)
            self.logger.info(f"Replied to mention {mention.id}")
            return True
        except (TooManyRequests, TwitterServerError) as e:
            self.logger.error(f"Failed to send reply to {mention.id} after retries: {str(e)}")
            return False
        except Exception as e:
            self.logger.error(f"Error sending reply to {mention.id}: {str(e)}")
            return False

    @twitter_retry()
    def _send_reply_impl(self, mention, text: str):
        """Internal implementation of send_reply with retry decorator"""
        # Ensure reply fits in tweet length
        if len(text) > 280:
            text = text[:277] + "..."

        self.api.create_tweet(text=text, in_reply_to_tweet_id=mention.id)

    def post_match_summary(self, matches: list[dict], query_url: str | None = None, max_retries: int = 3) -> bool:
        """
        Post a standalone tweet with match summary and links.

        Args:
            matches: List of match dictionaries with video info
            query_url: Optional URL of the query clip
            max_retries: Maximum number of retry attempts

        Returns:
            bool: True if successful, False otherwise
        """
        if not matches:
            self.logger.warning("No matches to post")
            return False

        # Build summary text
        summary = "🎵 Audio Match Results\n\n"

        if query_url:
            summary += f"Query: {query_url}\n\n"

        summary += f"Found {len(matches)} match(es):\n\n"

        for i, match in enumerate(matches[:3], 1):  # Top 3 matches
            title = match["title"][:40] + "..." if len(match["title"]) > 40 else match["title"]
            start_time = int(match["start_time"])
            end_time = int(match["end_time"])

            summary += f"{i}. {title}\n"
            summary += f"   ⏰ {start_time}s-{end_time}s\n"
            summary += f"   🔗 {match['url']}\n\n"

        if len(matches) > 3:
            summary += f"...and {len(matches) - 3} more!"

        try:
            response = self._post_match_summary_impl(summary)
            self.logger.info(f"Posted match summary tweet: {response.data.get('id') if response.data else 'unknown'}")
            return True
        except (TooManyRequests, TwitterServerError) as e:
            self.logger.error(f"Failed to post match summary after retries: {str(e)}")
            return False
        except Exception as e:
            self.logger.error(f"Error posting match summary: {str(e)}")
            return False

    @twitter_retry()
    def _post_match_summary_impl(self, summary: str):
        """Internal implementation of post_match_summary with retry decorator"""
        # Ensure tweet fits in character limit
        if len(summary) > 280:
            summary = summary[:277] + "..."

        return self.api.create_tweet(text=summary)


def main():
    """Main bot loop"""
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    bot = TwitterBot()

    while True:
        try:
            bot.listen_for_mentions()

            # Wait 60 seconds before checking again
            import time

            time.sleep(60)

        except KeyboardInterrupt:
            logging.info("Bot stopped by user")
            break
        except Exception as e:
            logging.error(f"Bot error: {str(e)}")
            import time

            time.sleep(300)  # Wait 5 minutes on error


if __name__ == "__main__":
    main()
