import os
import sys
import asyncio
import logging
from aiohttp import web
from pyrogram import Client
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors import FloodWait

from config import Config
from database import db
from utils import ProgressTracker, humanbytes, time_formatter, get_url_hash
from metadata import get_media_info, apply_custom_metadata
from downloader import get_media_info_from_url, download_media
import admin
import constants

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

if not Config.BOT_TOKEN:
    logger.critical("❌ FATAL: BOT_TOKEN is missing or empty!")
    sys.exit(1)

app = Client(
    "gezx_downloader_bot_session",
    bot_token=Config.BOT_TOKEN,
    api_id=Config.TELEGRAM_API_ID,
    api_hash=Config.TELEGRAM_API_HASH,
    in_memory=True,
    workers=10
)

ACTIVE_DOWNLOADS = {}

# RAW CATCH-ALL HANDLER (No Filters)
@app.on_message()
async def raw_message_handler(client: Client, message: Message):
    if not message or not message.from_user:
        return

    user_id = message.from_user.id
    text = (message.text or message.caption or "").strip()
    
    logger.info(f"🚨 [RAW TELEGRAM UPDATE] From User: {user_id} | Text: '{text}'")

    # Command Router
    if text.startswith("/start"):
        await db.add_user(user_id, message.from_user.username)
        buttons = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("📖 Help", callback_data="btn_help"),
                InlineKeyboardButton("ℹ️ About", callback_data="btn_about")
            ]
        ])
        caption = (
            f"{constants.HEADER_START}\n\n"
            "Send me any supported media link (including **TeraBox**) and I will download and "
            "send it to you directly in Telegram!"
        )
        await message.reply_text(text=caption, reply_markup=buttons)

    elif text.startswith("http://") or text.startswith("https://"):
        await message.reply_text(f"🔎 **Link Received:** `{text}`\n\nProcessing download...")

@app.on_callback_query()
async def callback_handler(client: Client, callback_query: CallbackQuery):
    logger.info(f"🚨 [RAW CALLBACK UPDATE] Data: {callback_query.data}")
    await callback_query.answer("Button clicked!")

async def health_check(request):
    return web.Response(text="Bot web server running ok.")

async def main():
    await db.init_db()
    await admin.register_admin_handlers(app)
    logger.info("Starting Pyrogram client...")
    
    while True:
        try:
            await app.start()
            break
        except FloodWait as e:
            logger.warning(f"⏳ Telegram FloodWait active! Sleeping for {e.value} seconds...")
            await asyncio.sleep(e.value + 2)
        except Exception as e:
            logger.error(f"Failed to start Pyrogram client: {e}")
            return

    me = await app.get_me()
    logger.info("==========================================")
    logger.info(f"✅ BOT CONNECTED SUCCESSFULLY: @{me.username} (ID: {me.id})")
    logger.info("==========================================")

    server = web.Server(health_check)
    runner = web.ServerRunner(server)
    await runner.setup()
    port = int(os.getenv("PORT", "8080"))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
