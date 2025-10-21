from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine.url import make_url


class Config(BaseSettings):
    """
    Centralized configuration management for SoundHash.

    This class uses pydantic-settings to:
    - Load settings from environment variables
    - Provide sensible defaults
    - Validate configuration at startup
    - Raise clear errors for missing critical settings

    All modules should import from this class rather than reading os.environ directly.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
        # Don't try to parse as JSON - use our custom parsers
        env_parse_none_str=None,
    )

    # Database
    DATABASE_URL: str | None = None
    DATABASE_HOST: str = "localhost"
    DATABASE_PORT: int = 5432
    DATABASE_NAME: str = "soundhash"
    DATABASE_USER: str | None = None
    DATABASE_PASSWORD: str | None = None

    # API Keys
    YOUTUBE_API_KEY: str | None = None
    TWITTER_BEARER_TOKEN: str | None = None
    TWITTER_CONSUMER_KEY: str | None = None
    TWITTER_CONSUMER_SECRET: str | None = None
    TWITTER_ACCESS_TOKEN: str | None = None
    TWITTER_ACCESS_TOKEN_SECRET: str | None = None

    REDDIT_CLIENT_ID: str | None = None
    REDDIT_CLIENT_SECRET: str | None = None
    REDDIT_USER_AGENT: str = "soundhash_bot_v1.0"
    REDDIT_REFRESH_TOKEN: str | None = None

    # OAuth and Authentication
    CALLBACK_BASE_URL: str = "http://localhost:8000"
    AUTH_SERVER_HOST: str = "0.0.0.0"
    AUTH_SERVER_PORT: int = 8000

    # Processing
    TEMP_DIR: str = "./temp"
    MAX_CONCURRENT_DOWNLOADS: int = 3
    MAX_CONCURRENT_CHANNELS: int = 2
    SEGMENT_LENGTH_SECONDS: int = Field(
        default=90, description="Longer segments for better accuracy"
    )
    FINGERPRINT_SAMPLE_RATE: int = 22050

    # Similarity search thresholds and weights
    # Thresholds for considering a match valid
    SIMILARITY_CORRELATION_THRESHOLD: float = 0.70
    SIMILARITY_L2_THRESHOLD: float = 0.70
    # Combined minimum score
    SIMILARITY_MIN_SCORE: float = 0.70

    # Weights for combining correlation and L2 similarity (must sum to 1.0)
    SIMILARITY_CORRELATION_WEIGHT: float = 0.5
    SIMILARITY_L2_WEIGHT: float = 0.5

    # Minimum duration (in seconds) for valid matches
    SIMILARITY_MIN_DURATION: float = 5.0

    # Ingestion backoff settings
    CHANNEL_RETRY_DELAY: int = Field(default=5, description="Delay in seconds between retries")
    CHANNEL_MAX_RETRIES: int = 3

    # File management
    KEEP_ORIGINAL_AUDIO: bool = True
    CLEANUP_SEGMENTS_AFTER_PROCESSING: bool = True

    # Download configuration (for yt-dlp)
    USE_PROXY: bool = False
    PROXY_URL: str | None = Field(default=None, description="Format: http://proxy.example.com:8080")
    PROXY_LIST_STR: str = Field(default="", validation_alias="PROXY_LIST")

    # YouTube cookies & extractor behavior
    YT_COOKIES_FILE: str | None = Field(
        default=None, description="Path to a Netscape cookies.txt exported file"
    )
    YT_COOKIES_FROM_BROWSER: str | None = Field(
        default=None, description="e.g., 'chrome', 'chromium', 'firefox', 'brave', 'edge'"
    )
    YT_BROWSER_PROFILE: str | None = Field(
        default=None, description="e.g., 'Default', 'Profile 1', or a Firefox profile name"
    )
    YT_PLAYER_CLIENT: str | None = Field(
        default=None, description="e.g., 'android', 'web_safari', 'tv'"
    )

    # Target channels
    TARGET_CHANNELS_STR: str = Field(default="", validation_alias="TARGET_CHANNELS")

    # Bot settings
    BOT_NAME: str = "@soundhash_bot"
    BOT_KEYWORDS_STR: str = Field(
        default="find clip,source video,original,what song", validation_alias="BOT_KEYWORDS"
    )

    @computed_field
    @property
    def PROXY_LIST(self) -> list[str]:
        """Parse comma-separated proxy list from environment variable."""
        if not self.PROXY_LIST_STR or not self.PROXY_LIST_STR.strip():
            return []
        return [proxy.strip() for proxy in self.PROXY_LIST_STR.split(",") if proxy.strip()]

    @computed_field
    @property
    def TARGET_CHANNELS(self) -> list[str]:
        """Parse comma-separated channel list from environment variable."""
        if not self.TARGET_CHANNELS_STR or not self.TARGET_CHANNELS_STR.strip():
            return []
        return [
            channel.strip() for channel in self.TARGET_CHANNELS_STR.split(",") if channel.strip()
        ]

    @computed_field
    @property
    def BOT_KEYWORDS(self) -> list[str]:
        """Parse comma-separated keywords from environment variable."""
        if not self.BOT_KEYWORDS_STR or not self.BOT_KEYWORDS_STR.strip():
            return ["find clip", "source video", "original", "what song"]
        return [keyword.strip() for keyword in self.BOT_KEYWORDS_STR.split(",") if keyword.strip()]

    def get_database_url(self) -> str:
        """
        Get the database connection URL.

        Raises:
            ValueError: If database configuration is incomplete.
        """
        if self.DATABASE_URL:
            return self.DATABASE_URL

        # Validate we have required credentials
        if not self.DATABASE_USER or not self.DATABASE_PASSWORD:
            raise ValueError(
                "Database configuration incomplete. Either set DATABASE_URL or "
                "provide DATABASE_USER and DATABASE_PASSWORD (with optional "
                "DATABASE_HOST, DATABASE_PORT, DATABASE_NAME)."
            )

        return f"postgresql://{self.DATABASE_USER}:{self.DATABASE_PASSWORD}@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"

    def get_database_url_safe(self) -> str:
        """Get database URL with password masked for safe logging."""
        url = self.get_database_url()
        return make_url(url).render_as_string(hide_password=True)


# Create a singleton instance that loads settings once
Config = Config()
