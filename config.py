import os

class Config:
    # Telegram Bot Token from @BotFather
    BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
    
    # Safely extract TELEGRAM_API_ID without throwing ValueError
    raw_api_id = os.getenv("TELEGRAM_API_ID", "2040").strip()
    TELEGRAM_API_ID = int(raw_api_id) if raw_api_id.isdigit() else 2040
    
    # Telegram API Hash
    TELEGRAM_API_HASH = os.getenv("TELEGRAM_API_HASH", "b18441a1ed609e12613d9b2310264e82").strip()
    
    # Admin User IDs
    ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split() if x.strip().isdigit()]
    
    # Channel username for force join check
    FORCE_JOIN_CHANNEL = os.getenv("FORCE_JOIN_CHANNEL", "").strip()
    
    # File Limits & Timeouts
    MAX_FILE_SIZE_BYTES = 2 * 1024 * 1024 * 1024  # 2 GB limit
    INFO_DELETE_TIMEOUT = int(os.getenv("INFO_DELETE_TIMEOUT", "19"))
    
    # Image Placeholders / Custom Media Settings
    START_IMAGE = os.getenv("START_IMAGE", "https://via.placeholder.com/800x450.png?text=Gezx+Downloader")
    HELP_IMAGE = os.getenv("HELP_IMAGE", "https://via.placeholder.com/800x450.png?text=Help+Guide")
    ABOUT_IMAGE = os.getenv("ABOUT_IMAGE", "https://via.placeholder.com/800x450.png?text=About+Bot")
    
    # Directories and SQLite File
    DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR", "./downloads")
    DB_NAME = os.getenv("DB_NAME", "bot_database.db")

# Ensure download directory exists on startup
os.makedirs(Config.DOWNLOAD_DIR, exist_ok=True)
