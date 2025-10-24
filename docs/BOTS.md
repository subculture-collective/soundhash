# SoundHash Bots Documentation

This document provides information on setting up and using the SoundHash social media bots for Twitter and Reddit.

## Overview

SoundHash includes two social media bots that help users identify audio clips from videos:

- **Twitter Bot**: Responds to mentions and posts match summaries
- **Reddit Bot**: Monitors subreddits for video clip identification requests (work in progress)

## Twitter Bot

### Features

- ✅ Listens for mentions containing video URLs or keywords
- ✅ Processes video clips to find matches in the database
- ✅ Replies with match results including video titles, timestamps, and links
- ✅ Posts standalone match summary tweets
- ✅ Automatic rate limiting with exponential backoff retry logic
- ✅ Robust error handling for API failures

### Setup

#### 1. Create a Twitter Developer Account

1. Go to [Twitter Developer Portal](https://developer.twitter.com/)
2. Create a new app or use an existing one
3. Navigate to the app's Keys and Tokens section

#### 2. Generate API Credentials

You'll need:
- **Bearer Token** (for v2 API access)
- **API Key** (Consumer Key)
- **API Secret** (Consumer Secret)
- **Access Token**
- **Access Token Secret**

#### 3. Configure Environment Variables

Add the following to your `.env` file:

```bash
# Twitter API Credentials
TWITTER_BEARER_TOKEN=your_bearer_token_here
TWITTER_CONSUMER_KEY=your_consumer_key_here
TWITTER_CONSUMER_SECRET=your_consumer_secret_here
TWITTER_ACCESS_TOKEN=your_access_token_here
TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret_here

# Bot Settings
BOT_NAME=@your_bot_username
BOT_KEYWORDS=find clip,source video,original,what song
```

#### 4. Test the Bot

Run the test script to verify your setup:

```bash
python scripts/test_twitter_bot.py
```

This will:
- ✅ Test authentication
- ✅ Show sample tweet formatting
- ✅ Optionally post a test message (if you confirm)

### Usage

#### Running the Bot

Start the bot to listen for mentions:

```bash
python -m src.bots.twitter_bot
```

The bot will:
1. Check for new mentions every 60 seconds
2. Process mentions that include the bot name or keywords
3. Extract video URLs from the text
4. Find matching clips in the database
5. Reply with results

#### Programmatic Usage

You can also use the bot programmatically:

```python
from src.bots.twitter_bot import TwitterBot

bot = TwitterBot()

# Post a match summary
matches = [
    {
        "video_id": "abc123",
        "title": "Original Video Title",
        "url": "https://youtube.com/watch?v=abc123",
        "start_time": 45.0,
        "end_time": 135.0,
        "confidence": 0.95,
    }
]

bot.post_match_summary(matches, query_url="https://example.com/query")
```

### API Methods

#### `listen_for_mentions()`
Fetches recent mentions and processes them.

#### `should_process_mention(mention) -> bool`
Determines if a mention should be processed based on keywords and URLs.

#### `extract_video_urls(text: str) -> list[str]`
Extracts video URLs from text. Supports:
- YouTube (youtube.com/watch, youtu.be)
- TikTok
- Instagram Reels
- Twitter videos

#### `find_matches(video_url: str) -> list[dict]`
Processes a video URL and returns matching clips from the database.

#### `post_match_summary(matches: list[dict], query_url: Optional[str] = None, max_retries: int = 3) -> bool`
Posts a standalone tweet with match results.

#### `send_reply(mention, text: str, max_retries: int = 3) -> bool`
Sends a reply to a mention with automatic retry logic.

### Rate Limiting

The bot handles rate limiting automatically:

- **Automatic waiting**: `wait_on_rate_limit=True` in the Tweepy client
- **Retry logic**: Exponential backoff (5s, 10s, 20s) for failed requests
- **Rate limit detection**: Automatically waits for rate limit reset time
- **Max retries**: 3 attempts by default (configurable)

### Error Handling

The bot gracefully handles:
- `TooManyRequests`: Rate limit exceeded
- `TwitterServerError`: Twitter API server errors
- General exceptions with logging

---

## Reddit Bot

### Status: 🚧 Work in Progress

The Reddit bot is currently a stub with planned functionality outlined.

### Planned Features

- [ ] Monitor specified subreddits for posts/comments
- [ ] Extract video URLs from text
- [ ] Process clips and find matches
- [ ] Reply with formatted match results
- [ ] Rate limiting and retry logic
- [ ] Keyword filtering
- [ ] Duplicate detection

### Setup (When Completed)

#### 1. Create a Reddit App

1. Go to [Reddit App Preferences](https://www.reddit.com/prefs/apps)
2. Create a new app (select "script" type)
3. Note your Client ID and Client Secret

#### 2. Get a Refresh Token

Follow the PRAW OAuth guide to obtain a refresh token:
https://praw.readthedocs.io/en/stable/getting_started/authentication.html

#### 3. Configure Environment Variables

```bash
# Reddit API Credentials
REDDIT_CLIENT_ID=your_client_id_here
REDDIT_CLIENT_SECRET=your_client_secret_here
REDDIT_USER_AGENT=soundhash_bot_v1.0
REDDIT_REFRESH_TOKEN=your_refresh_token_here

# Subreddits to monitor (comma-separated)
REDDIT_SUBREDDITS=musicid,tipofmytongue,NameThatSong
```

### Implementation TODOs

The following tasks need to be completed:

#### Core Functionality
- [ ] Implement `monitor_subreddits()` streaming
- [ ] Add `should_process_submission()` filtering logic
- [ ] Add `should_process_comment()` filtering logic
- [ ] Implement `find_matches()` integration
- [ ] Add processed items tracking (database)

#### Configuration
- [ ] Add `REDDIT_SUBREDDITS` environment variable support
- [ ] Add keyword filtering configuration
- [ ] Add score threshold configuration
- [ ] OAuth token refresh logic

#### Error Handling
- [ ] Complete rate limit handling implementation
- [ ] Add server error recovery
- [ ] Add logging for all operations

#### Testing
- [ ] Add integration tests
- [ ] Create test script similar to Twitter bot
- [ ] Add mock Reddit responses

### Current Structure

The bot stub includes:

```python
from src.bots.reddit_bot import RedditBot

bot = RedditBot()

# Monitor subreddits (not yet functional)
bot.monitor_subreddits(['musicid', 'tipofmytongue'], limit=10)

# Format a reply (functional)
matches = [...]
reply_text = bot.format_reply(matches)
```

### Planned API Methods

- `monitor_subreddits(subreddits: List[str], limit: int)` - Monitor for new posts/comments
- `should_process_submission(submission) -> bool` - Filter submissions
- `should_process_comment(comment) -> bool` - Filter comments
- `extract_video_urls(text: str) -> List[str]` - Extract URLs
- `find_matches(video_url: str) -> List[dict]` - Find matches
- `format_reply(matches: List[dict]) -> str` - Format Reddit markdown reply
- `reply_to_submission(submission, text: str) -> bool` - Post reply with retry
- `reply_to_comment(comment, text: str) -> bool` - Post reply with retry

---

## Common Configuration

Both bots share these settings:

```bash
# Bot Behavior
BOT_NAME=@soundhash_bot
BOT_KEYWORDS=find clip,source video,original,what song

# Processing (affects match finding)
SEGMENT_LENGTH_SECONDS=90
FINGERPRINT_SAMPLE_RATE=22050
SIMILARITY_MIN_SCORE=0.70
```

## Security Best Practices

1. **Never commit API keys**: Always use environment variables
2. **Use .gitignore**: Ensure `.env` is in `.gitignore`
3. **Rotate keys regularly**: Change API keys periodically
4. **Monitor usage**: Check your API usage dashboards regularly
5. **Use least privilege**: Only grant necessary permissions

## Troubleshooting

### Twitter Bot

**Issue**: `401 Unauthorized`
- Check that all credentials are correct
- Verify your app has read/write permissions
- Regenerate access tokens if needed

**Issue**: `429 Rate Limit Exceeded`
- The bot handles this automatically with retry logic
- If persistent, reduce polling frequency or increase retry delay

**Issue**: `403 Forbidden`
- Check app permissions in Twitter Developer Portal
- Verify Essential/Elevated access level

### Reddit Bot

**Issue**: `Authentication failed`
- Verify Client ID and Secret
- Check refresh token is valid
- Ensure User Agent string is set

**Issue**: `Forbidden` when replying
- Check if subreddit allows bot comments
- Verify account has enough karma
- Check if account is shadowbanned

## Testing

Run the test suites:

```bash
# Test both bots
pytest tests/bots/ -v

# Test Twitter bot only
pytest tests/bots/test_twitter_bot.py -v

# Test Reddit bot only
pytest tests/bots/test_reddit_bot.py -v
```

Run the Twitter bot test script:

```bash
python scripts/test_twitter_bot.py
```

## Contributing

When contributing to the bots:

1. Follow existing code patterns
2. Add tests for new functionality
3. Update documentation
4. Handle errors gracefully
5. Log important events
6. Respect rate limits

## Support

For issues or questions:
- Open an issue on GitHub
- Check existing documentation
- Review bot logs for error details
