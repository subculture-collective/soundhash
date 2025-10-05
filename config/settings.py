import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Database
    DATABASE_URL = os.getenv('DATABASE_URL')
    DATABASE_HOST = os.getenv('DATABASE_HOST', 'localhost')
    DATABASE_PORT = int(os.getenv('DATABASE_PORT', 5432))
    DATABASE_NAME = os.getenv('DATABASE_NAME', 'soundhash')
    DATABASE_USER = os.getenv('DATABASE_USER')
    DATABASE_PASSWORD = os.getenv('DATABASE_PASSWORD')
    
    # API Keys
    YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
    TWITTER_BEARER_TOKEN = os.getenv('TWITTER_BEARER_TOKEN')
    TWITTER_CONSUMER_KEY = os.getenv('TWITTER_CONSUMER_KEY')
    TWITTER_CONSUMER_SECRET = os.getenv('TWITTER_CONSUMER_SECRET')
    TWITTER_ACCESS_TOKEN = os.getenv('TWITTER_ACCESS_TOKEN')
    TWITTER_ACCESS_TOKEN_SECRET = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
    
    REDDIT_CLIENT_ID = os.getenv('REDDIT_CLIENT_ID')
    REDDIT_CLIENT_SECRET = os.getenv('REDDIT_CLIENT_SECRET')
    REDDIT_USER_AGENT = os.getenv('REDDIT_USER_AGENT', 'soundhash_bot_v1.0')
    REDDIT_REFRESH_TOKEN = os.getenv('REDDIT_REFRESH_TOKEN')
    
    # OAuth and Authentication
    CALLBACK_BASE_URL = os.getenv('CALLBACK_BASE_URL', 'http://localhost:8000')
    AUTH_SERVER_HOST = os.getenv('AUTH_SERVER_HOST', '0.0.0.0')
    AUTH_SERVER_PORT = int(os.getenv('AUTH_SERVER_PORT', 8000))
    
    # Processing
    TEMP_DIR = os.getenv('TEMP_DIR', './temp')
    MAX_CONCURRENT_DOWNLOADS = int(os.getenv('MAX_CONCURRENT_DOWNLOADS', 3))
    SEGMENT_LENGTH_SECONDS = int(os.getenv('SEGMENT_LENGTH_SECONDS', 30))
    FINGERPRINT_SAMPLE_RATE = int(os.getenv('FINGERPRINT_SAMPLE_RATE', 22050))
    
    # Target channels
    TARGET_CHANNELS = os.getenv('TARGET_CHANNELS', '').split(',')
    
    # Bot settings
    BOT_NAME = os.getenv('BOT_NAME', '@soundhash_bot')
    BOT_KEYWORDS = os.getenv('BOT_KEYWORDS', 'find clip,source video,original,what song').split(',')
    
    @classmethod
    def get_database_url(cls):
        if cls.DATABASE_URL:
            return cls.DATABASE_URL
        return f"postgresql://{cls.DATABASE_USER}:{cls.DATABASE_PASSWORD}@{cls.DATABASE_HOST}:{cls.DATABASE_PORT}/{cls.DATABASE_NAME}"