import os
import asyncio
import logging
import time
from aiohttp import web
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from config import Config
from database import db
from force_join import check_force_join
from utils import ProgressTracker, get_progress_bar, humanbytes, time_formatter, get_url_hash
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

# Safely extract Telegram API credentials from Environment Variables
API_ID = int(os.getenv("TELEGRAM_API_ID", "12345"))
API_HASH = os.getenv("TELEGRAM_API_HASH", "abcdef1234567890abcdef1234567890")

# Initialize Pyrogram Client
app = Client(
    "gezx_downloader_session",
    bot_token=Config.BOT_TOKEN,
    api_id=API_ID,
    api_hash=API_HASH,
    in_memory=True
)

# Active user sessions for track/cancel management
ACTIVE_DOWNLOADS = {}


@app.on_message(filters.command("start") & filters.private)
async def start_handler(client: Client, message: Message):
    logger.info(f"Received /start from user: {message.from_user.id}")
    user_id = message.from_user.id
    username = message.from_user.username
    await db.add_user(user_id, username)

    if await db.is_blocked(user_id):
        return

    if not await check_force_join(client, message):
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

    start_img = await db.get_setting("start_image", Config.START_IMAGE)
    try:
        await message.reply_photo(photo=start_img, caption=caption, reply_markup=buttons)
    except Exception:
        await message.reply_text(text=caption, reply_markup=buttons)


@app.on_message(filters.command("help") & filters.private)
async def help_handler(client: Client, message: Message):
    logger.info(f"Received /help from user: {message.from_user.id}")
    if not await check_force_join(client, message):
        return

    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton(constants.BTN_CLOSE, callback_data="btn_close")]
    ])
    
    caption = (
        f"{constants.HEADER_HELP}\n\n"
        "1. Simply paste a supported link (TeraBox, YouTube, Instagram, TikTok, etc.).\n"
        "2. The bot will show file details.\n"
        "3. Download will start automatically with a live progress bar.\n"
        "4. Tap **Cancel** at any time if you wish to stop.\n\n"
        "💡 *Tip: MKV files are preserved and sent as documents to retain all audio/subtitle streams.*"
    )

    help_img = await db.get_setting("help_image", Config.HELP_IMAGE)
    try:
        await message.reply_photo(photo=help_img, caption=caption, reply_markup=buttons)
    except Exception:
        await message.reply_text(text=caption, reply_markup=buttons)


@app.on_message(filters.command("about") & filters.private)
async def about_handler(client: Client, message: Message):
    logger.info(f"Received /about from user: {message.from_user.id}")
    if not await check_force_join(client, message):
        return

    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton(constants.BTN_CLOSE, callback_data="btn_close")]
    ])

    caption = (
        f"{constants.HEADER_ABOUT}\n\n"
        "🤖 **Bot Name:** Gezx Downloader\n"
        "📦 **TeraBox Support:** Up to 2 GB\n"
        "🔊 **Multi-Audio:** Preserved\n"
        "💬 **Subtitles:** Preserved\n"
        "⚡ **Powered By:** Pyrogram & yt-dlp"
    )

    about_img = await db.get_setting("about_image", Config.ABOUT_IMAGE)
    try:
        await message.reply_photo(photo=about_img, caption=caption, reply_markup=buttons)
    except Exception:
        await message.reply_text(text=caption, reply_markup=buttons)


@app.on_message(filters.command("cancel") & filters.private)
async def cancel_handler(client: Client, message: Message):
    user_id = message.from_user.id
    if user_id in ACTIVE_DOWNLOADS:
        tracker = ACTIVE_DOWNLOADS[user_id]
        tracker.cancelled = True
        await message.reply_text(constants.MSG_DOWNLOAD_CANCELLED)
    else:
        await message.reply_text("⚠️ You don't have any active download to cancel.")


@app.on_callback_query()
async def callback_dispatcher(client: Client, callback_query: CallbackQuery):
    data = callback_query.data
    user_id = callback_query.from_user.id

    if data == "check_force_join":
        if await check_force_join(client, callback_query.message):
            await callback_query.answer("✅ Thank you for joining! You can now send links.", show_alert=True)
            await callback_query.message.delete()

    elif data == "btn_help":
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton(constants.BTN_BACK, callback_data="btn_back_home")]
        ])
        await callback_query.message.edit_caption(
            caption=f"{constants.HEADER_HELP}\n\nSend a link to download. Cancel anytime using the button.",
            reply_markup=buttons
        )

    elif data == "btn_about":
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton(constants.BTN_BACK, callback_data="btn_back_home")]
        ])
        await callback_query.message.edit_caption(
            caption=f"{constants.HEADER_ABOUT}\n\nGezx Downloader Bot v1.0",
            reply_markup=buttons
        )

    elif data == "btn_back_home":
        buttons = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("📖 Help", callback_data="btn_help"),
                InlineKeyboardButton("ℹ️ About", callback_data="btn_about")
            ]
        ])
        await callback_query.message.edit_caption(
            caption=f"{constants.HEADER_START}\n\nSend me a supported link to start downloading!",
            reply_markup=buttons
        )

    elif data == "btn_close":
        await callback_query.message.delete()

    elif data == "cancel_download":
        if user_id in ACTIVE_DOWNLOADS:
            ACTIVE_DOWNLOADS[user_id].cancelled = True
            await callback_query.answer("🛑 Cancelling download...")
        else:
            await callback_query.answer("No active download found.")


@app.on_message(filters.private & filters.regex(r'https?://[^\s]+'))
async def link_handler(client: Client, message: Message):
    user_id = message.from_user.id
    logger.info(f"Received link from user {user_id}: {message.text}")
    await db.add_user(user_id, message.from_user.username)

    if await db.is_blocked(user_id):
        return

    if not await check_force_join(client, message):
        return

    if user_id in ACTIVE_DOWNLOADS:
        await message.reply_text(constants.MSG_ALREADY_IN_QUEUE)
        return

    url = message.text.strip()
    url_hash = get_url_hash(url)

    # 1. Check local cache first
    cached = await db.get_cached_file(url_hash)
    if cached:
        file_id, file_name, file_size, file_type = cached
        try:
            caption = f"📄 **{file_name}**\n💾 **Sɪᴢᴇ:** {humanbytes(file_size)}\n\n⚡ *Retrieved from cache!*"
            if file_type == "video":
                await message.reply_video(video=file_id, caption=caption)
            elif file_type == "audio":
                await message.reply_audio(audio=file_id, caption=caption)
            elif file_type == "photo":
                await message.reply_photo(photo=file_id, caption=caption)
            else:
                await message.reply_document(document=file_id, caption=caption)
            return
        except Exception as e:
            logger.warning(f"Cache hit failed to send, proceeding to fresh download: {e}")

    # 2. Show media information message
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

    # Auto-delete info card after configured seconds (default 19s)
    async def auto_delete_info(msg: Message, delay: int):
        await asyncio.sleep(delay)
        try:
            await msg.delete()
        except Exception:
            pass

    asyncio.create_task(auto_delete_info(info_msg, Config.INFO_DELETE_TIMEOUT))

    # 3. Prepare Progress Bar & Download Session
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
        # 4. Download file
        downloaded_file = await download_media(
            url=url,
            output_dir=user_dir,
            progress_tracker=tracker,
            progress_callback=update_progress_ui
        )

        if tracker.cancelled:
            await progress_msg.edit_text(constants.MSG_DOWNLOAD_CANCELLED)
            return

        # Check max size limit (~2 GB)
        file_size = os.path.getsize(downloaded_file)
        if file_size > Config.MAX_FILE_SIZE_BYTES:
            await progress_msg.edit_text(constants.MSG_FILE_TOO_LARGE)
            return

        # 5. Apply Metadata
        await progress_msg.edit_text("🏷 **Aᴘᴘʟʏɪɴɢ Mᴇᴅɪᴀ Mᴇᴛᴀᴅᴀᴛᴀ...**")
        tagged_output = os.path.join(user_dir, f"tagged_{os.path.basename(downloaded_file)}")
        final_file = await apply_custom_metadata(downloaded_file, tagged_output)

        # 6. Analyze Media Streams
        media_stats = await get_media_info(final_file)

        # 7. Upload to Telegram
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
            bot="@Gezx_botz"
        )

        sent_msg = None
        file_type = "document"

        # Format rules check
        if ext == ".mp4":
            file_type = "video"
            sent_msg = await message.reply_video(video=final_file, caption=caption)
        elif ext in [".m4a", ".mp3", ".ogg", ".flac"]:
            file_type = "audio"
            sent_msg = await message.reply_audio(audio=final_file, caption=caption)
        elif ext in [".jpg", ".jpeg", ".png", ".webp"]:
            file_type = "photo"
            sent_msg = await message.reply_photo(photo=final_file, caption=caption)
        else:
            # Send as document for MKV and other formats to preserve all streams
            file_type = "document"
            sent_msg = await message.reply_document(document=final_file, caption=caption)

        # 8. Cache uploaded file_id
        if sent_msg:
            file_id = None
            if sent_msg.video:
                file_id = sent_msg.video.file_id
            elif sent_msg.audio:
                file_id = sent_msg.audio.file_id
            elif sent_msg.photo:
                file_id = sent_msg.photo[-1].file_id
            elif sent_msg.document:
                file_id = sent_msg.document.file_id

            if file_id:
                await db.set_cached_file(
                    url_hash=url_hash,
                    original_url=url,
                    file_id=file_id,
                    file_name=file_name,
                    file_size=file_size,
                    file_type=file_type
                )

        await progress_msg.delete()

    except asyncio.CancelledError:
        await progress_msg.edit_text(constants.MSG_DOWNLOAD_CANCELLED)
    except Exception as e:
        logger.error(f"Error handling link {url}: {e}")
        await progress_msg.edit_text(f"❌ **An error occurred during processing:**\n`{str(e)}`")

    finally:
        # Clean session and temporary local files
        ACTIVE_DOWNLOADS.pop(user_id, None)
        if os.path.exists(user_dir):
            for f in os.listdir(user_dir):
                try:
                    os.remove(os.path.join(user_dir, f))
                except Exception:
                    pass


async def health_check(request):
    """Simple HTTP response to satisfy Render's port check."""
    return web.Response(text="Gezx Downloader Bot is live and running!")


async def main():
    await db.init_db()
    await admin.register_admin_handlers(app)
    logger.info("Bot starting...")
    await app.start()
    logger.info("Gezx Downloader Bot is running!")

    # Start a lightweight web server on the port Render expects
    server = web.Server(health_check)
    runner = web.ServerRunner(server)
    await runner.setup()
    port = int(os.getenv("PORT", "8080"))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"Health-check web server bound to port {port}")

    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
