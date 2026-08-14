import os
from dotenv import load_dotenv

# Load environment variables from .env file if available
load_dotenv()

class Config:

    # Bot Setup
    BOT_TOKEN = os.getenv("BOT_TOKEN", "")
    ADMIN_ID = int(os.getenv("ADMIN_ID", "5565826679"))
    
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "gezx_bot.db")
    
    # Storage & Temporary Directories
    DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR", "./downloads")
    CACHE_DIR = os.getenv("CACHE_DIR", "./cache")
    
    # Telegram Limits
    MAX_FILE_SIZE_BYTES = 2 * 1024 * 1024 * 1024  # 2 GB
    
    # Default Image File IDs
    START_IMAGE = os.getenv(
        "START_IMAGE",
        "AgACAgUAAxkBAAENYRhqOpwQnzrbNn2aX4FomOuuWmRJTAACFBFrG3yt2FXgRNU82rCpgQEAAwIAA3cAAzwE"
    )
    HELP_IMAGE = os.getenv(
        "HELP_IMAGE",
        "AgACAgUAAxkBAAENY_JqQpBlR1JO3a8RVOwwHZwo0kXx0AACThNrGzDcEFYq8kL7x-DB4QEAAwIAA3cAAzwE"
    )
    ABOUT_IMAGE = os.getenv(
        "ABOUT_IMAGE",
        "AgACAgUAAxkBAAENY1FqQLd8qz5c9_evoQ5aYNUAAaOYLL4AAtYPaxtH9ghWqlQ_xO7_VVwBAAMCAAN3AAM8BA"
    )
    
    # TeraBox Configuration
    TERABOX_COOKIE = os.getenv("TERABOX_COOKIE", "")
    
    # Queue & Concurrency
    MAX_CONCURRENT_DOWNLOADS = int(os.getenv("MAX_CONCURRENT_DOWNLOADS", "3"))
    USER_MAX_ACTIVE_DOWNLOADS = int(os.getenv("USER_MAX_ACTIVE_DOWNLOADS", "1"))
    
    # Info Message Auto-Delete Time (seconds)
    INFO_DELETE_TIMEOUT = int(os.getenv("INFO_DELETE_TIMEOUT", "19"))
    
    # Default Metadata Tag
    DEFAULT_METADATA_TITLE = "@Gezx_botz"

# Ensure required local directories exist
os.makedirs(Config.DOWNLOAD_DIR, exist_ok=True)
os.makedirs(Config.CACHE_DIR, exist_ok=True)
