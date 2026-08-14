import os
import sys
import asyncio
import logging
from aiohttp import web
from pyrogram import Client, filters
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

# Validate credentials prior to client creation
if not Config.BOT_TOKEN:
    logger.critical("❌ FATAL: BOT_TOKEN is missing or empty! Please set BOT_TOKEN in Render environment variables.")
    sys.exit(1)

# Initialize Pyrogram client in memory
app = Client(
    "gezx_downloader_bot_session",
    bot_token=Config.BOT_TOKEN,
    api_id=Config.TELEGRAM_API_ID,
    api_hash=Config.TELEGRAM_API_HASH,
    in_memory=True,
    workers=10
)

ACTIVE_DOWNLOADS = {}


@app.on_message(filters.command("start"))
async def start_handler(client: Client, message: Message):
    user_id = message.from_user.id
    logger.info(f"📩 RECEIVED COMMAND /start from user {user_id}")
    await db.add_user(user_id, message.from_user.username)

    if await db.is_blocked(user_id):
        return

    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📖 Help", callback_data="btn_help"),
            InlineKeyboardButton("ℹ️ About", callback_data="btn_about")
        ]
    ])

    caption = (
        f"{constants.HEADER_START}\n\n"
        "Send me any supported media link (including **TeraBox**) and I will download and "
        "send it to you directly in Telegram!\n\n"
        "⚡ *Preserves original audio tracks, subtitles, and video quality.*"
    )

    await message.reply_text(text=caption, reply_markup=buttons)


@app.on_message(filters.command("help"))
async def help_handler(client: Client, message: Message):
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton(constants.BTN_CLOSE, callback_data="btn_close")]
    ])
    caption = (
        f"{constants.HEADER_HELP}\n\n"
        "1. Paste a supported link (TeraBox, YouTube, Instagram, etc.).\n"
        "2. The bot will fetch file details.\n"
        "3. Download starts automatically with progress status.\n"
    )
    await message.reply_text(text=caption, reply_markup=buttons)


@app.on_message(filters.command("about"))
async def about_handler(client: Client, message: Message):
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton(constants.BTN_CLOSE, callback_data="btn_close")]
    ])
    caption = (
        f"{constants.HEADER_ABOUT}\n\n"
        "🤖 **Bot Name:** Gezx Downloader\n"
        "📦 **TeraBox Support:** Up to 2 GB\n"
    )
    await message.reply_text(text=caption, reply_markup=buttons)


@app.on_message(filters.regex(r'https?://[^\s]+'))
async def link_handler(client: Client, message: Message):
    user_id = message.from_user.id
    url = message.text.strip()
    logger.info(f"📩 RECEIVED LINK from user {user_id}: {url}")
    await db.add_user(user_id, message.from_user.username)

    if await db.is_blocked(user_id):
        return

    if user_id in ACTIVE_DOWNLOADS:
        await message.reply_text(constants.MSG_ALREADY_IN_QUEUE)
        return

    url_hash = get_url_hash(url)

    cached = await db.get_cached_file(url_hash)
    if cached:
        file_id, file_name, file_size, file_type = cached
        try:
            caption = f"📄 **{file_name}**\n💾 **Sɪᴢᴇ:** {humanbytes(file_size)}\n\n⚡ *Retrieved from cache!*"
            if file_type == "video":
                await message.reply_video(video=file_id, caption=caption)
            else:
                await message.reply_document(document=file_id, caption=caption)
            return
        except Exception as e:
            logger.warning(f"Cache delivery failed, downloading fresh: {e}")

    info_msg = await message.reply_text("🔎 **Fetching media information...**")
    web_info = await get_media_info_from_url(url)

    info_text = constants.INFO_TEMPLATE.format(
        filename=web_info.get("title", "Media File"),
        size=humanbytes(web_info.get("filesize", 0)),
        duration=time_formatter(web_info.get("duration", 0)),
        quality=web_info.get("resolution", "Original"),
        format=web_info.get("format", "MP4"),
        video_codec=web_info.get("video_codec", "Original"),
        audio_tracks="Preserved",
        subtitle_tracks="Preserved"
    )
    await info_msg.edit_text(info_text)

    progress_msg = await message.reply_text(
        constants.TEXT_DOWNLOAD_STARTING,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Cancel", callback_data="cancel_download")]])
    )

    tracker = ProgressTracker()
    ACTIVE_DOWNLOADS[user_id] = tracker

    async def update_progress_ui(text: str):
        try:
            await progress_msg.edit_text(
                text,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Cancel", callback_data="cancel_download")]])
            )
        except Exception:
            pass

    user_dir = os.path.join(Config.DOWNLOAD_DIR, str(user_id))

    try:
        downloaded_file = await download_media(
            url=url,
            output_dir=user_dir,
            progress_tracker=tracker,
            progress_callback=update_progress_ui
        )

        if tracker.cancelled:
            await progress_msg.edit_text(constants.MSG_DOWNLOAD_CANCELLED)
            return

        file_size = os.path.getsize(downloaded_file)
        if file_size > Config.MAX_FILE_SIZE_BYTES:
            await progress_msg.edit_text(constants.MSG_FILE_TOO_LARGE)
            return

        await progress_msg.edit_text("🏷 **Aᴘᴘʟʏɪɴɢ Mᴇᴅɪᴀ Mᴇᴛᴀᴅᴀᴛᴀ...**")
        tagged_output = os.path.join(user_dir, f"tagged_{os.path.basename(downloaded_file)}")
        final_file = await apply_custom_metadata(downloaded_file, tagged_output)

        media_stats = await get_media_info(final_file)
        await progress_msg.edit_text("⚡ **Uᴘʟᴏᴀᴅɪɴɢ ᴛᴏ Tᴇʟᴇɢʀᴀᴍ...**")

        ext = os.path.splitext(final_file)[1].lower()
        file_name = os.path.basename(downloaded_file)
        caption = constants.DEFAULT_CAPTION_TEMPLATE.format(
            filename=file_name,
            filesize=humanbytes(file_size),
            duration=time_formatter(media_stats.get("duration", 0)),
            quality=media_stats.get("resolution", "Original"),
            format=ext.replace(".", "").upper(),
            source=web_info.get("source", "Web"),
            bot="@Gezx_Niso_bot"
        )

        if ext == ".mp4":
            sent_msg = await message.reply_video(video=final_file, caption=caption)
        else:
            sent_msg = await message.reply_document(document=final_file, caption=caption)

        await progress_msg.delete()

    except Exception as e:
        logger.error(f"Error handling link: {e}")
        await progress_msg.edit_text(f"❌ **An error occurred:**\n`{str(e)}`")

    finally:
        ACTIVE_DOWNLOADS.pop(user_id, None)


@app.on_callback_query()
async def callback_handler(client: Client, callback_query: CallbackQuery):
    data = callback_query.data
    if data == "btn_close":
        await callback_query.message.delete()


async def health_check(request):
    return web.Response(text="Bot web server running ok.")


async def main():
    await db.init_db()
    await admin.register_admin_handlers(app)
    logger.info("Starting Pyrogram client...")
    
    # Handle FloodWait error automatically
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

    # Web server startup to satisfy Render web service health check
    server = web.Server(health_check)
    runner = web.ServerRunner(server)
    await runner.setup()
    port = int(os.getenv("PORT", "8080"))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"Health-check HTTP server listening on port {port}")

    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
