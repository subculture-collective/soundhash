import os

from dotenv import load_dotenv
from sqlalchemy.engine.url import make_url

load_dotenv()


class Config:
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL")
    DATABASE_HOST = os.getenv("DATABASE_HOST", "localhost")
    DATABASE_PORT = int(os.getenv("DATABASE_PORT", 5432))
    DATABASE_NAME = os.getenv("DATABASE_NAME", "soundhash")
    DATABASE_USER = os.getenv("DATABASE_USER")
    DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")

    # Database Connection Pooling
    DATABASE_POOL_SIZE = int(os.getenv("DATABASE_POOL_SIZE", 10))
    DATABASE_MAX_OVERFLOW = int(os.getenv("DATABASE_MAX_OVERFLOW", 20))
    DATABASE_POOL_TIMEOUT = int(os.getenv("DATABASE_POOL_TIMEOUT", 30))
    DATABASE_POOL_RECYCLE = int(os.getenv("DATABASE_POOL_RECYCLE", 3600))
    DATABASE_ECHO = os.getenv("DATABASE_ECHO", "false").lower() == "true"
    DATABASE_STATEMENT_TIMEOUT = int(os.getenv("DATABASE_STATEMENT_TIMEOUT", 30000))  # milliseconds

    # Redis for Caching
    REDIS_ENABLED = os.getenv("REDIS_ENABLED", "false").lower() == "true"
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
    REDIS_DB = int(os.getenv("REDIS_DB", 0))
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
    CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", 300))

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
    REDDIT_SUBREDDITS = (
        os.getenv("REDDIT_SUBREDDITS", "").split(",") if os.getenv("REDDIT_SUBREDDITS") else []
    )

    # OAuth and Authentication
    CALLBACK_BASE_URL = os.getenv("CALLBACK_BASE_URL", "http://localhost:8000")
    AUTH_SERVER_HOST = os.getenv("AUTH_SERVER_HOST", "0.0.0.0")
    AUTH_SERVER_PORT = int(os.getenv("AUTH_SERVER_PORT", 8000))

    # API Configuration
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", 8000))
    API_SECRET_KEY = os.getenv("API_SECRET_KEY", "dev-secret-key-change-in-production")
    API_ALGORITHM = os.getenv("API_ALGORITHM", "HS256")
    API_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("API_ACCESS_TOKEN_EXPIRE_MINUTES", 30))
    API_REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("API_REFRESH_TOKEN_EXPIRE_DAYS", 7))
    API_RATE_LIMIT_PER_MINUTE = int(os.getenv("API_RATE_LIMIT_PER_MINUTE", 60))
    API_CORS_ORIGINS = os.getenv(
        "API_CORS_ORIGINS", "http://localhost:3000,http://localhost:8000"
    ).split(",")
    API_TITLE = os.getenv("API_TITLE", "SoundHash API")
    API_VERSION = os.getenv("API_VERSION", "1.0.0")
    API_DESCRIPTION = os.getenv("API_DESCRIPTION", "Audio fingerprinting and matching API")

    # Multi-tenant Configuration
    BASE_DOMAIN = os.getenv("BASE_DOMAIN", "soundhash.io")
    
    # Enterprise SSO Configuration
    SSO_SESSION_DURATION_HOURS = int(os.getenv("SSO_SESSION_DURATION_HOURS", 24))
    SSO_SESSION_CLEANUP_INTERVAL_HOURS = int(os.getenv("SSO_SESSION_CLEANUP_INTERVAL_HOURS", 1))
    SSO_ENABLED = os.getenv("SSO_ENABLED", "true").lower() == "true"
    
    # MFA Configuration
    MFA_ENABLED = os.getenv("MFA_ENABLED", "true").lower() == "true"
    MFA_TOTP_ISSUER_NAME = os.getenv("MFA_TOTP_ISSUER_NAME", "SoundHash")
    MFA_BACKUP_CODES_COUNT = int(os.getenv("MFA_BACKUP_CODES_COUNT", 10))

    # Processing
    TEMP_DIR = os.getenv("TEMP_DIR", "./temp")
    MAX_CONCURRENT_DOWNLOADS = int(os.getenv("MAX_CONCURRENT_DOWNLOADS", 3))
    MAX_CONCURRENT_CHANNELS = int(os.getenv("MAX_CONCURRENT_CHANNELS", 2))
    SEGMENT_LENGTH_SECONDS = int(
        os.getenv("SEGMENT_LENGTH_SECONDS", 90)
    )  # Longer segments for better accuracy
    FINGERPRINT_SAMPLE_RATE = int(os.getenv("FINGERPRINT_SAMPLE_RATE", 22050))
    
    # Fingerprinting Optimization Settings
    USE_OPTIMIZED_FINGERPRINTING = os.getenv("USE_OPTIMIZED_FINGERPRINTING", "false").lower() == "true"
    FINGERPRINT_USE_GPU = os.getenv("FINGERPRINT_USE_GPU", "auto").lower()  # auto, true, false
    FINGERPRINT_BATCH_SIZE = int(os.getenv("FINGERPRINT_BATCH_SIZE", 10))
    FINGERPRINT_MAX_WORKERS = int(os.getenv("FINGERPRINT_MAX_WORKERS", 4))
    FINGERPRINT_N_FFT = int(os.getenv("FINGERPRINT_N_FFT", 2048))
    FINGERPRINT_HOP_LENGTH = int(os.getenv("FINGERPRINT_HOP_LENGTH", 512))
    
    # LSH Index Settings
    USE_LSH_INDEX = os.getenv("USE_LSH_INDEX", "false").lower() == "true"
    LSH_NUM_TABLES = int(os.getenv("LSH_NUM_TABLES", 5))
    LSH_HASH_SIZE = int(os.getenv("LSH_HASH_SIZE", 12))
    LSH_MAX_CANDIDATES = int(os.getenv("LSH_MAX_CANDIDATES", 100))
    
    # Multi-Resolution Fingerprinting
    USE_MULTI_RESOLUTION = os.getenv("USE_MULTI_RESOLUTION", "false").lower() == "true"

    # Caching
    YT_DLP_CACHE_DIR = os.getenv("YT_DLP_CACHE_DIR", "./cache/yt-dlp")
    ENABLE_YT_DLP_CACHE = os.getenv("ENABLE_YT_DLP_CACHE", "true").lower() == "true"

    # Similarity search thresholds and weights
    # Thresholds for considering a match valid
    SIMILARITY_CORRELATION_THRESHOLD = float(os.getenv("SIMILARITY_CORRELATION_THRESHOLD", "0.70"))
    SIMILARITY_L2_THRESHOLD = float(os.getenv("SIMILARITY_L2_THRESHOLD", "0.70"))
    # Combined minimum score
    SIMILARITY_MIN_SCORE = float(os.getenv("SIMILARITY_MIN_SCORE", "0.70"))

    # Weights for combining correlation and L2 similarity (must sum to 1.0)
    SIMILARITY_CORRELATION_WEIGHT = float(os.getenv("SIMILARITY_CORRELATION_WEIGHT", "0.5"))
    SIMILARITY_L2_WEIGHT = float(os.getenv("SIMILARITY_L2_WEIGHT", "0.5"))

    # Validate that weights sum to 1.0
    @classmethod
    def _validate_similarity_weights(cls):
        """Validate that similarity weights sum to 1.0."""
        weights_sum = cls.SIMILARITY_CORRELATION_WEIGHT + cls.SIMILARITY_L2_WEIGHT
        if not abs(weights_sum - 1.0) < 1e-9:
            raise ValueError(
                f"SIMILARITY_CORRELATION_WEIGHT and SIMILARITY_L2_WEIGHT must sum to 1.0, "
                f"got {cls.SIMILARITY_CORRELATION_WEIGHT} + {cls.SIMILARITY_L2_WEIGHT} = {weights_sum}"
            )

    # Minimum duration (in seconds) for valid matches
    SIMILARITY_MIN_DURATION = float(os.getenv("SIMILARITY_MIN_DURATION", "5.0"))

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

    # Observability settings
    METRICS_ENABLED = os.getenv("METRICS_ENABLED", "true").lower() == "true"
    METRICS_PORT = int(os.getenv("METRICS_PORT", 9090))
    HEALTH_CHECK_INTERVAL = int(os.getenv("HEALTH_CHECK_INTERVAL", 300))  # seconds
    
    # Distributed Tracing (OpenTelemetry + Jaeger)
    TRACING_ENABLED = os.getenv("TRACING_ENABLED", "false").lower() == "true"
    TRACING_SERVICE_NAME = os.getenv("TRACING_SERVICE_NAME", "soundhash")
    TRACING_ENVIRONMENT = os.getenv("TRACING_ENVIRONMENT", "development")
    JAEGER_ENABLED = os.getenv("JAEGER_ENABLED", "false").lower() == "true"
    JAEGER_AGENT_HOST = os.getenv("JAEGER_AGENT_HOST", "localhost")
    JAEGER_AGENT_PORT = int(os.getenv("JAEGER_AGENT_PORT", 6831))
    OTLP_ENABLED = os.getenv("OTLP_ENABLED", "false").lower() == "true"
    OTLP_ENDPOINT = os.getenv("OTLP_ENDPOINT", "http://localhost:4317")
    TRACING_CONSOLE_EXPORT = os.getenv("TRACING_CONSOLE_EXPORT", "false").lower() == "true"
    
    # Error Tracking (Sentry)
    SENTRY_ENABLED = os.getenv("SENTRY_ENABLED", "false").lower() == "true"
    SENTRY_DSN = os.getenv("SENTRY_DSN")
    SENTRY_ENVIRONMENT = os.getenv("SENTRY_ENVIRONMENT", "development")
    SENTRY_TRACES_SAMPLE_RATE = float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1"))
    SENTRY_PROFILES_SAMPLE_RATE = float(os.getenv("SENTRY_PROFILES_SAMPLE_RATE", "0.1"))
    
    # Structured Logging (JSON format for ELK/Loki)
    STRUCTURED_LOGGING_ENABLED = os.getenv("STRUCTURED_LOGGING_ENABLED", "false").lower() == "true"
    LOG_FORMAT = os.getenv("LOG_FORMAT", "text")  # text or json
    LOG_OUTPUT = os.getenv("LOG_OUTPUT", "stdout")  # stdout, file, or both

    # Data retention and cleanup settings
    RETENTION_TEMP_FILES_DAYS = int(
        os.getenv("RETENTION_TEMP_FILES_DAYS", 7)
    )  # Keep temp files for 7 days
    RETENTION_LOG_FILES_DAYS = int(
        os.getenv("RETENTION_LOG_FILES_DAYS", 30)
    )  # Keep log files for 30 days
    RETENTION_COMPLETED_JOBS_DAYS = int(
        os.getenv("RETENTION_COMPLETED_JOBS_DAYS", 30)
    )  # Keep completed jobs for 30 days
    RETENTION_FAILED_JOBS_DAYS = int(
        os.getenv("RETENTION_FAILED_JOBS_DAYS", 90)
    )  # Keep failed jobs longer for debugging
    LOG_DIR = os.getenv("LOG_DIR", "./logs")  # Directory for log files

    # Alerting settings
    ALERTING_ENABLED = os.getenv("ALERTING_ENABLED", "false").lower() == "true"
    SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")  # Slack incoming webhook URL
    DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")  # Discord webhook URL

    # Failure thresholds for alerts
    ALERT_RATE_LIMIT_THRESHOLD = int(
        os.getenv("ALERT_RATE_LIMIT_THRESHOLD", 5)
    )  # 429/403 errors in time window
    ALERT_JOB_FAILURE_THRESHOLD = int(
        os.getenv("ALERT_JOB_FAILURE_THRESHOLD", 10)
    )  # Failed jobs in time window
    ALERT_TIME_WINDOW_MINUTES = int(
        os.getenv("ALERT_TIME_WINDOW_MINUTES", 15)
    )  # Time window for counting failures

    # Backup settings
    BACKUP_DIR = os.getenv("BACKUP_DIR", "./backups")  # Local directory for database backups
    BACKUP_RETENTION_DAYS = int(os.getenv("BACKUP_RETENTION_DAYS", 30))  # Keep backups for 30 days
    BACKUP_S3_ENABLED = (
        os.getenv("BACKUP_S3_ENABLED", "false").lower() == "true"
    )  # Enable S3 backup storage
    BACKUP_S3_BUCKET = os.getenv("BACKUP_S3_BUCKET")  # S3 bucket name for backups
    BACKUP_S3_PREFIX = os.getenv(
        "BACKUP_S3_PREFIX", "soundhash-backups/"
    )  # S3 key prefix for backups
    
    # Advanced backup settings
    # Encrypt backups at rest
    BACKUP_ENCRYPTION_ENABLED = (
        os.getenv("BACKUP_ENCRYPTION_ENABLED", "false").lower() == "true"
    )
    BACKUP_ENCRYPTION_KEY = os.getenv("BACKUP_ENCRYPTION_KEY")  # GPG key ID or encryption password
    BACKUP_ENCRYPTION_METHOD = os.getenv("BACKUP_ENCRYPTION_METHOD", "gpg")  # gpg or age
    
    # Multi-tier retention policies
    BACKUP_RETENTION_STANDARD_DAYS = int(os.getenv("BACKUP_RETENTION_STANDARD_DAYS", 30))  # Standard: 30 days
    BACKUP_RETENTION_EXTENDED_DAYS = int(os.getenv("BACKUP_RETENTION_EXTENDED_DAYS", 90))  # Extended: 90 days
    BACKUP_RETENTION_ARCHIVE_DAYS = int(os.getenv("BACKUP_RETENTION_ARCHIVE_DAYS", 365))  # Archive: 365 days
    
    # Cross-region replication
    BACKUP_GCS_ENABLED = (
        os.getenv("BACKUP_GCS_ENABLED", "false").lower() == "true"
    )  # Enable Google Cloud Storage backup
    BACKUP_GCS_BUCKET = os.getenv("BACKUP_GCS_BUCKET")  # GCS bucket name for backups
    BACKUP_GCS_PREFIX = os.getenv("BACKUP_GCS_PREFIX", "soundhash-backups/")  # GCS prefix for backups
    BACKUP_CROSS_REGION_ENABLED = (
        os.getenv("BACKUP_CROSS_REGION_ENABLED", "false").lower() == "true"
    )  # Enable cross-region replication
    
    # Point-in-time recovery (PITR) settings
    BACKUP_WAL_ARCHIVING_ENABLED = (
        os.getenv("BACKUP_WAL_ARCHIVING_ENABLED", "false").lower() == "true"
    )  # Enable PostgreSQL WAL archiving
    BACKUP_WAL_DIR = os.getenv("BACKUP_WAL_DIR", "./backups/wal")  # Local WAL archive directory
    BACKUP_WAL_S3_ENABLED = (
        os.getenv("BACKUP_WAL_S3_ENABLED", "false").lower() == "true"
    )  # Upload WAL files to S3
    BACKUP_WAL_S3_PREFIX = os.getenv("BACKUP_WAL_S3_PREFIX", "soundhash-wal/")  # S3 prefix for WAL files
    
    # Backup testing and validation
    BACKUP_RESTORE_TEST_ENABLED = (
        os.getenv("BACKUP_RESTORE_TEST_ENABLED", "false").lower() == "true"
    )  # Enable automated restore testing
    BACKUP_RESTORE_TEST_INTERVAL_DAYS = int(
        os.getenv("BACKUP_RESTORE_TEST_INTERVAL_DAYS", 7)
    )  # Test restore every N days
    
    # Disaster recovery settings
    BACKUP_RTO_MINUTES = int(os.getenv("BACKUP_RTO_MINUTES", 60))  # Recovery Time Objective: < 1 hour
    BACKUP_RPO_MINUTES = int(os.getenv("BACKUP_RPO_MINUTES", 15))  # Recovery Point Objective: < 15 min

    # Email Configuration
    EMAIL_ENABLED = os.getenv("EMAIL_ENABLED", "false").lower() == "true"
    EMAIL_PROVIDER = os.getenv("EMAIL_PROVIDER", "sendgrid")  # sendgrid or ses
    SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
    SENDGRID_FROM_EMAIL = os.getenv("SENDGRID_FROM_EMAIL", "noreply@soundhash.io")
    SENDGRID_FROM_NAME = os.getenv("SENDGRID_FROM_NAME", "SoundHash")

    # AWS SES Configuration (alternative to SendGrid)
    AWS_SES_REGION = os.getenv("AWS_SES_REGION", "us-east-1")
    AWS_SES_ACCESS_KEY = os.getenv("AWS_SES_ACCESS_KEY")
    AWS_SES_SECRET_KEY = os.getenv("AWS_SES_SECRET_KEY")
    AWS_SES_FROM_EMAIL = os.getenv("AWS_SES_FROM_EMAIL", "noreply@soundhash.io")

    # Email Templates
    EMAIL_TEMPLATES_DIR = os.getenv("EMAIL_TEMPLATES_DIR", "./templates/email")

    # Email Features
    EMAIL_TRACK_OPENS = os.getenv("EMAIL_TRACK_OPENS", "true").lower() == "true"
    EMAIL_TRACK_CLICKS = os.getenv("EMAIL_TRACK_CLICKS", "true").lower() == "true"
    EMAIL_UNSUBSCRIBE_URL = os.getenv(
        "EMAIL_UNSUBSCRIBE_URL", "http://localhost:8000/api/email/unsubscribe"
    )

    # Digest Email Settings
    DIGEST_DAILY_ENABLED = os.getenv("DIGEST_DAILY_ENABLED", "true").lower() == "true"
    DIGEST_DAILY_TIME = os.getenv("DIGEST_DAILY_TIME", "09:00")  # HH:MM format
    DIGEST_WEEKLY_ENABLED = os.getenv("DIGEST_WEEKLY_ENABLED", "true").lower() == "true"
    DIGEST_WEEKLY_DAY = int(os.getenv("DIGEST_WEEKLY_DAY", 0))  # Monday = 0, Sunday = 6
    DIGEST_WEEKLY_TIME = os.getenv("DIGEST_WEEKLY_TIME", "09:00")  # HH:MM format

    # ==================== Security Configuration ====================
    
    # Rate Limiting
    RATE_LIMITING_ENABLED = os.getenv("RATE_LIMITING_ENABLED", "true").lower() == "true"
    API_RATE_LIMIT_PER_HOUR = int(os.getenv("API_RATE_LIMIT_PER_HOUR", 1000))
    API_RATE_LIMIT_PER_DAY = int(os.getenv("API_RATE_LIMIT_PER_DAY", 10000))
    API_BURST_SIZE = int(os.getenv("API_BURST_SIZE", 10))
    SEARCH_RATE_LIMIT_PER_MINUTE = int(os.getenv("SEARCH_RATE_LIMIT_PER_MINUTE", 30))
    
    # IP Filtering
    IP_FILTERING_ENABLED = os.getenv("IP_FILTERING_ENABLED", "false").lower() == "true"
    IP_ALLOWLIST = os.getenv("IP_ALLOWLIST", "").split(",") if os.getenv("IP_ALLOWLIST") else []
    IP_BLOCKLIST = os.getenv("IP_BLOCKLIST", "").split(",") if os.getenv("IP_BLOCKLIST") else []
    
    # Threat Detection
    THREAT_DETECTION_ENABLED = os.getenv("THREAT_DETECTION_ENABLED", "true").lower() == "true"
    THREAT_AUTO_BLOCK_THRESHOLD = int(os.getenv("THREAT_AUTO_BLOCK_THRESHOLD", 5))
    FAILED_LOGIN_THRESHOLD = int(os.getenv("FAILED_LOGIN_THRESHOLD", 5))
    FAILED_LOGIN_WINDOW = int(os.getenv("FAILED_LOGIN_WINDOW", 900))  # 15 minutes
    MAX_HEADER_SIZE = int(os.getenv("MAX_HEADER_SIZE", 8192))  # 8KB
    
    # Request Signature Verification
    SIGNATURE_VERIFICATION_ENABLED = os.getenv("SIGNATURE_VERIFICATION_ENABLED", "false").lower() == "true"
    SIGNATURE_MAX_TIMESTAMP_DELTA = int(os.getenv("SIGNATURE_MAX_TIMESTAMP_DELTA", 300))  # 5 minutes
    
    # Security Headers
    CSP_ENABLED = os.getenv("CSP_ENABLED", "true").lower() == "true"
    CSP_POLICY = os.getenv(
        "CSP_POLICY",
        "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
        "style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; "
        "font-src 'self' data:; connect-src 'self'; frame-ancestors 'none'"
    )
    HSTS_ENABLED = os.getenv("HSTS_ENABLED", "true").lower() == "true"
    HSTS_MAX_AGE = int(os.getenv("HSTS_MAX_AGE", 31536000))  # 1 year
    X_FRAME_OPTIONS = os.getenv("X_FRAME_OPTIONS", "DENY")
    REFERRER_POLICY = os.getenv("REFERRER_POLICY", "strict-origin-when-cross-origin")
    PERMISSIONS_POLICY = os.getenv(
        "PERMISSIONS_POLICY",
        "geolocation=(), microphone=(), camera=(), payment=(), usb=()"
    )
    
    # API Key Rotation
    API_KEY_ROTATION_DAYS = int(os.getenv("API_KEY_ROTATION_DAYS", 90))
    API_KEY_DEFAULT_EXPIRY_DAYS = int(os.getenv("API_KEY_DEFAULT_EXPIRY_DAYS", 365))
    
    # Security Audit Logging
    SECURITY_AUDIT_ENABLED = os.getenv("SECURITY_AUDIT_ENABLED", "true").lower() == "true"
    SECURITY_LOG_FILE = os.getenv("SECURITY_LOG_FILE", "./logs/security.log")
    
    # DDoS Protection (Documentation/Integration)
    DDOS_PROTECTION_PROVIDER = os.getenv("DDOS_PROTECTION_PROVIDER", "none")  # cloudflare, aws-shield, none
    CLOUDFLARE_ZONE_ID = os.getenv("CLOUDFLARE_ZONE_ID")
    CLOUDFLARE_API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN")
    
    # Compliance
    COMPLIANCE_MODE = os.getenv("COMPLIANCE_MODE", "none")  # soc2, iso27001, hipaa, none
    DATA_RETENTION_POLICY_DAYS = int(os.getenv("DATA_RETENTION_POLICY_DAYS", 365))
    
    # ==================== CDN & Edge Computing Configuration ====================
    
    # CDN Configuration
    CDN_ENABLED = os.getenv("CDN_ENABLED", "false").lower() == "true"
    CDN_PROVIDER = os.getenv("CDN_PROVIDER", "cloudfront")  # cloudfront, cloudflare
    CDN_DOMAIN = os.getenv("CDN_DOMAIN", "")  # e.g., d123456.cloudfront.net or cdn.soundhash.io
    CDN_STATIC_ASSETS_URL = os.getenv("CDN_STATIC_ASSETS_URL", "/static")
    
    # CloudFront Configuration
    CLOUDFRONT_DISTRIBUTION_ID = os.getenv("CLOUDFRONT_DISTRIBUTION_ID", "")
    CLOUDFRONT_ORIGIN_VERIFY_SECRET = os.getenv("CLOUDFRONT_ORIGIN_VERIFY_SECRET", "")
    
    # Cloudflare Configuration (alternative to CloudFront)
    CLOUDFLARE_ZONE_ID = os.getenv("CLOUDFLARE_ZONE_ID", "")
    CLOUDFLARE_API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN", "")
    
    # Edge Caching
    EDGE_CACHE_ENABLED = os.getenv("EDGE_CACHE_ENABLED", "false").lower() == "true"
    EDGE_CACHE_TTL_SECONDS = int(os.getenv("EDGE_CACHE_TTL_SECONDS", 1800))  # 30 minutes
    EDGE_FINGERPRINT_CACHE_ENABLED = os.getenv("EDGE_FINGERPRINT_CACHE_ENABLED", "false").lower() == "true"
    
    # Image Optimization
    IMAGE_OPTIMIZATION_ENABLED = os.getenv("IMAGE_OPTIMIZATION_ENABLED", "true").lower() == "true"
    IMAGE_WEBP_CONVERSION = os.getenv("IMAGE_WEBP_CONVERSION", "true").lower() == "true"
    IMAGE_DEFAULT_QUALITY = int(os.getenv("IMAGE_DEFAULT_QUALITY", 85))
    IMAGE_MAX_WIDTH = int(os.getenv("IMAGE_MAX_WIDTH", 2048))
    IMAGE_MAX_HEIGHT = int(os.getenv("IMAGE_MAX_HEIGHT", 2048))
    
    # Multi-Region Configuration
    MULTI_REGION_ENABLED = os.getenv("MULTI_REGION_ENABLED", "false").lower() == "true"
    PRIMARY_REGION = os.getenv("PRIMARY_REGION", "us-east-1")
    REGIONS = os.getenv("REGIONS", "us-east-1,eu-west-1,ap-southeast-1").split(",")
    
    # Regional Database Endpoints
    DATABASE_READER_ENDPOINTS = os.getenv("DATABASE_READER_ENDPOINTS", "").split(",") if os.getenv("DATABASE_READER_ENDPOINTS") else []
    DATABASE_REPLICA_EU_ENDPOINT = os.getenv("DATABASE_REPLICA_EU_ENDPOINT", "")
    DATABASE_REPLICA_APAC_ENDPOINT = os.getenv("DATABASE_REPLICA_APAC_ENDPOINT", "")
    
    # Geographic Routing
    GEO_ROUTING_ENABLED = os.getenv("GEO_ROUTING_ENABLED", "false").lower() == "true"
    LATENCY_ROUTING_ENABLED = os.getenv("LATENCY_ROUTING_ENABLED", "false").lower() == "true"
    
    # Regional Data Compliance
    DATA_RESIDENCY_ENFORCEMENT = os.getenv("DATA_RESIDENCY_ENFORCEMENT", "false").lower() == "true"
    EU_DATA_RESIDENCY = os.getenv("EU_DATA_RESIDENCY", "false").lower() == "true"  # GDPR compliance
    APAC_DATA_RESIDENCY = os.getenv("APAC_DATA_RESIDENCY", "false").lower() == "true"
    
    # Latency Monitoring
    LATENCY_MONITORING_ENABLED = os.getenv("LATENCY_MONITORING_ENABLED", "true").lower() == "true"
    LATENCY_THRESHOLD_MS = int(os.getenv("LATENCY_THRESHOLD_MS", 500))
    LATENCY_ALERT_THRESHOLD_MS = int(os.getenv("LATENCY_ALERT_THRESHOLD_MS", 1000))
    
    # Automatic Failover
    AUTO_FAILOVER_ENABLED = os.getenv("AUTO_FAILOVER_ENABLED", "false").lower() == "true"
    FAILOVER_HEALTH_CHECK_INTERVAL = int(os.getenv("FAILOVER_HEALTH_CHECK_INTERVAL", 30))  # seconds
    FAILOVER_UNHEALTHY_THRESHOLD = int(os.getenv("FAILOVER_UNHEALTHY_THRESHOLD", 3))
    
    # Edge Function Configuration
    EDGE_FUNCTIONS_ENABLED = os.getenv("EDGE_FUNCTIONS_ENABLED", "false").lower() == "true"
    EDGE_MATCHING_ENABLED = os.getenv("EDGE_MATCHING_ENABLED", "false").lower() == "true"
    EDGE_MATCHING_THRESHOLD = float(os.getenv("EDGE_MATCHING_THRESHOLD", 0.70))
    
    # ==================== Billing & Payments Configuration ====================
    
    # Stripe Configuration
    STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
    STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY", "")
    STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    
    # Frontend URL for redirects
    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
    
    # Billing Settings
    DEFAULT_TRIAL_DAYS = int(os.getenv("DEFAULT_TRIAL_DAYS", 14))
    BILLING_GRACE_PERIOD_DAYS = int(os.getenv("BILLING_GRACE_PERIOD_DAYS", 3))
    
    @classmethod
    def get_database_url(cls):
        if cls.DATABASE_URL:
            return cls.DATABASE_URL
        return (
            f"postgresql://{cls.DATABASE_USER}:{cls.DATABASE_PASSWORD}"
            f"@{cls.DATABASE_HOST}:{cls.DATABASE_PORT}/{cls.DATABASE_NAME}"
        )

    @classmethod
    def get_database_url_safe(cls):
        """Get database URL with password masked for safe logging."""
        url = cls.get_database_url()
        return make_url(url).render_as_string(hide_password=True)


# Validate configuration on module import
Config._validate_similarity_weights()
