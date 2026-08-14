import os

class Config:
    # Telegram Credentials
    BOT_TOKEN = os.getenv("BOT_TOKEN", "")
    TELEGRAM_API_ID = int(os.getenv("TELEGRAM_API_ID", "12345"))
    TELEGRAM_API_HASH = os.getenv("TELEGRAM_API_HASH", "abcdef1234567890abcdef1234567890")
    
    # Bot Ownership & Channels
    ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split() if x.isdigit()]
    FORCE_JOIN_CHANNEL = os.getenv("FORCE_JOIN_CHANNEL", "")
    
    # Limits and Timeouts
    MAX_FILE_SIZE_BYTES = 2 * 1024 * 1024 * 1024  # ~2 GB Limit
    INFO_DELETE_TIMEOUT = int(os.getenv("INFO_DELETE_TIMEOUT", "19"))
    
    # Asset Defaults
    START_IMAGE = os.getenv("START_IMAGE", "https://via.placeholder.com/800x450.png?text=Gezx+Downloader")
    HELP_IMAGE = os.getenv("HELP_IMAGE", "https://via.placeholder.com/800x450.png?text=Help+Guide")
    ABOUT_IMAGE = os.getenv("ABOUT_IMAGE", "https://via.placeholder.com/800x450.png?text=About+Bot")
    
    # Directory Setup
    DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR", "./downloads")
    DB_NAME = os.getenv("DB_NAME", "bot_database.db")

os.makedirs(Config.DOWNLOAD_DIR, exist_ok=True)
