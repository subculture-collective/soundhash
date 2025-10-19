import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL")
    DATABASE_HOST = os.getenv("DATABASE_HOST", "localhost")
    DATABASE_PORT = int(os.getenv("DATABASE_PORT", 5432))
    DATABASE_NAME = os.getenv("DATABASE_NAME", "soundhash")
    DATABASE_USER = os.getenv("DATABASE_USER")
    DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")

    # API Keys
    YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
    TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")
    TWITTER_CONSUMER_KEY = os.getenv("TWITTER_CONSUMER_KEY")
    TWITTER_CONSUMER_SECRET = os.getenv("TWITTER_CONSUMER_SECRET")
    TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
    TWITTER_ACCESS_TOKEN_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")

    REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
    REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
    REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "soundhash_bot_v1.0")
    REDDIT_REFRESH_TOKEN = os.getenv("REDDIT_REFRESH_TOKEN")

    # OAuth and Authentication
    CALLBACK_BASE_URL = os.getenv("CALLBACK_BASE_URL", "http://localhost:8000")
    AUTH_SERVER_HOST = os.getenv("AUTH_SERVER_HOST", "0.0.0.0")
    AUTH_SERVER_PORT = int(os.getenv("AUTH_SERVER_PORT", 8000))

    # Processing
    TEMP_DIR = os.getenv("TEMP_DIR", "./temp")
    MAX_CONCURRENT_DOWNLOADS = int(os.getenv("MAX_CONCURRENT_DOWNLOADS", 3))
    MAX_CONCURRENT_CHANNELS = int(os.getenv("MAX_CONCURRENT_CHANNELS", 2))
    SEGMENT_LENGTH_SECONDS = int(
        os.getenv("SEGMENT_LENGTH_SECONDS", 90)
    )  # Longer segments for better accuracy
    FINGERPRINT_SAMPLE_RATE = int(os.getenv("FINGERPRINT_SAMPLE_RATE", 22050))

    # Ingestion backoff settings
    CHANNEL_RETRY_DELAY = int(os.getenv("CHANNEL_RETRY_DELAY", 5))  # seconds
    CHANNEL_MAX_RETRIES = int(os.getenv("CHANNEL_MAX_RETRIES", 3))

    # File management
    KEEP_ORIGINAL_AUDIO = os.getenv("KEEP_ORIGINAL_AUDIO", "true").lower() == "true"
    CLEANUP_SEGMENTS_AFTER_PROCESSING = (
        os.getenv("CLEANUP_SEGMENTS_AFTER_PROCESSING", "true").lower() == "true"
    )

    # Download configuration (for yt-dlp)
    USE_PROXY = os.getenv("USE_PROXY", "false").lower() == "true"
    PROXY_URL = os.getenv("PROXY_URL")  # Format: http://proxy.example.com:8080
    PROXY_LIST = os.getenv("PROXY_LIST", "").split(",") if os.getenv("PROXY_LIST") else []
    # YouTube cookies & extractor behavior
    YT_COOKIES_FILE = os.getenv("YT_COOKIES_FILE")  # Path to a Netscape cookies.txt exported file
    YT_COOKIES_FROM_BROWSER = os.getenv(
        "YT_COOKIES_FROM_BROWSER"
    )  # e.g., 'chrome', 'chromium', 'firefox', 'brave', 'edge'
    YT_BROWSER_PROFILE = os.getenv(
        "YT_BROWSER_PROFILE"
    )  # e.g., 'Default', 'Profile 1', or a Firefox profile name
    YT_PLAYER_CLIENT = os.getenv("YT_PLAYER_CLIENT")  # e.g., 'android', 'web_safari', 'tv'

    # Target channels
    TARGET_CHANNELS = os.getenv("TARGET_CHANNELS", "").split(",")

    # Bot settings
    BOT_NAME = os.getenv("BOT_NAME", "@soundhash_bot")
    BOT_KEYWORDS = os.getenv("BOT_KEYWORDS", "find clip,source video,original,what song").split(",")

    @classmethod
    def get_database_url(cls):
        if cls.DATABASE_URL:
            return cls.DATABASE_URL
        return f"postgresql://{cls.DATABASE_USER}:{cls.DATABASE_PASSWORD}@{cls.DATABASE_HOST}:{cls.DATABASE_PORT}/{cls.DATABASE_NAME}"
