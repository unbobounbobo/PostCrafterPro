"""
Configuration settings for PostCrafterPro
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Base configuration"""

    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')

    # Claude API
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
    CLAUDE_MODEL = os.getenv('CLAUDE_MODEL', 'claude-sonnet-4-5-20250929')

    # Pinecone
    PINECONE_API_KEY = os.getenv('PINECONE_API_KEY')
    PINECONE_INDEX_NAME = os.getenv('PINECONE_INDEX_NAME', 'midori-anzen-v2')
    PINECONE_HOST = os.getenv('PINECONE_HOST')

    # Google Sheets
    GOOGLE_SHEETS_DRAFT_ID = os.getenv('GOOGLE_SHEETS_DRAFT_ID')
    GOOGLE_SHEETS_PUBLISHED_ID = os.getenv('GOOGLE_SHEETS_PUBLISHED_ID')
    GOOGLE_SHEETS_ANALYTICS_ID = os.getenv('GOOGLE_SHEETS_ANALYTICS_ID')

    # Firecrawl
    FIRECRAWL_API_KEY = os.getenv('FIRECRAWL_API_KEY')

    # Application Settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload
    JSON_SORT_KEYS = False

    @staticmethod
    def validate():
        """Validate required environment variables"""
        required_vars = [
            'ANTHROPIC_API_KEY',
            'PINECONE_API_KEY',
            'GOOGLE_SHEETS_ANALYTICS_ID'
        ]

        missing = [var for var in required_vars if not os.getenv(var)]

        if missing:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing)}\n"
                f"Please check your .env file."
            )


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
