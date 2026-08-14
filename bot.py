import os
import asyncio
import logging
from aiohttp import web
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from config import Config
from database import db
from force_join import check_force_join
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

# Safely extract Telegram API credentials
API_ID = int(os.getenv("TELEGRAM_API_ID", "2040"))
API_HASH = os.getenv("TELEGRAM_API_HASH", "b18441a1ed609e12613d9b2310264e82")

# Initialize Pyrogram Client with workers and clean session
app = Client(
    "gezx_downloader_bot",
    bot_token=Config.BOT_TOKEN,
    api_id=API_ID,
    api_hash=API_HASH,
    workers=20
)

ACTIVE_DOWNLOADS = {}


# GLOBAL CATCH-ALL HANDLER: Catches EVERY SINGLE MESSAGE sent to the bot
@app.on_message(group=-1)
async def global_message_handler(client: Client, message: Message):
    user_id = message.from_user.id if message.from_user else "Unknown"
    text = message.text or "[Non-text message]"
    logger.info(f"🚨 [GLOBAL UPDATE] Received message from User ID {user_id}: {text}")

    # Handle /start command explicitly
    if text.startswith("/start"):
        await handle_start(client, message)
    # Handle URLs explicitly
    elif "http://" in text or "https://" in text:
        await handle_link(client, message)


async def handle_start(client: Client, message: Message):
    user_id = message.from_user.id
    username = message.from_user.username
    logger.info(f"Processing /start for user {user_id}")
    await db.add_user(user_id, username)

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

    try:
        await message.reply_text(text=caption, reply_markup=buttons)
    except Exception as e:
        logger.error(f"Error replying to /start: {e}")


async def handle_link(client: Client, message: Message):
    user_id = message.from_user.id
    logger.info(f"Processing link from user {user_id}: {message.text}")
    await db.add_user(user_id, message.from_user.username)

    if await db.is_blocked(user_id):
        return

    if user_id in ACTIVE_DOWNLOADS:
        await message.reply_text(constants.MSG_ALREADY_IN_QUEUE)
        return

    url = message.text.strip()
    url_hash = get_url_hash(url)

    # Check cache
    cached = await db.get_cached_file(url_hash)
    if cached:
        file_id, file_name, file_size, file_type = cached
        try:
            caption = f"📄 **{file_name}**\n💾 **Sɪᴢᴇ:** {humanbytes(file_size)}\n\n⚡ *Retrieved from cache!*"
            if file_type == "video":
                await message.reply_video(video=file_id, caption=caption)
            elif file_type == "audio":
                await message.reply_audio(audio=file_id, caption=caption)
            else:
                await message.reply_document(document=file_id, caption=caption)
            return
        except Exception as e:
            logger.warning(f"Cache hit failed, downloading fresh: {e}")

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
        elif ext in [".m4a", ".mp3", ".ogg", ".flac"]:
            sent_msg = await message.reply_audio(audio=final_file, caption=caption)
        else:
            sent_msg = await message.reply_document(document=final_file, caption=caption)

        await progress_msg.delete()

    except Exception as e:
        logger.error(f"Error handling link {url}: {e}")
        await progress_msg.edit_text(f"❌ **An error occurred during processing:**\n`{str(e)}`")

    finally:
        ACTIVE_DOWNLOADS.pop(user_id, None)


async def health_check(request):
    return web.Response(text="Gezx Downloader Bot is live!")


async def main():
    await db.init_db()
    await admin.register_admin_handlers(app)
    logger.info("Bot starting...")
    await app.start()

    me = await app.get_me()
    logger.info("==========================================")
    logger.info(f"🤖 BOT IS LIVE AS: @{me.username} (ID: {me.id})")
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
