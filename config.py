import os

class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
    
    raw_api_id = os.getenv("TELEGRAM_API_ID", "2040").strip()
    TELEGRAM_API_ID = int(raw_api_id) if raw_api_id.isdigit() else 2040
    TELEGRAM_API_HASH = os.getenv("TELEGRAM_API_HASH", "b18441a1ed609e12613d9b2310264e82").strip()
    
    # 2.0 GB Telegram Upload Limit
    MAX_FILE_SIZE_BYTES = 2000 * 1024 * 1024 
    
    # Custom Telegram Photo File IDs
    START_PHOTO = "AgACAgUAAxkBAAENY3VqQQEqulI64CnujsprZ0PqHpXVfQACIRFrG3yt2FUuReEp9Pm5zgEAAwIAA3cAAzwE"
    HELP_PHOTO = "AgACAgUAAxkBAAENY_JqQpBlR1JO3a8RVOwwHZwo0kXx0AACThNrGzDcEFYq8kL7x-DB4QEAAwIAA3cAAzwE"
    ABOUT_PHOTO = "AgACAgUAAxkBAAENY_JqQpBlR1JO3a8RVOwwHZwo0kXx0AACThNrGzDcEFYq8kL7x-DB4QEAAwIAA3cAAzwE"
    
    DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR", "./downloads")
    DB_NAME = os.getenv("DB_NAME", "bot_database.db")

os.makedirs(Config.DOWNLOAD_DIR, exist_ok=True)
