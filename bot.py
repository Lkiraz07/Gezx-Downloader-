import os
import sys
import shutil
import asyncio
import logging
from aiohttp import web
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors import FloodWait

from config import Config
from downloader import get_media_info_advanced, download_media_advanced
from utils import ProgressTracker, humanbytes, time_formatter

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

if not Config.BOT_TOKEN:
    logger.critical("FATAL: BOT_TOKEN is missing!")
    sys.exit(1)

app = Client(
    "gezx_downloader_bot",
    bot_token=Config.BOT_TOKEN,
    api_id=Config.TELEGRAM_API_ID,
    api_hash=Config.TELEGRAM_API_HASH,
    in_memory=True
)

PENDING_URLS = {}
ACTIVE_DOWNLOADS = {}

# ==========================================
# UI TEXT & KEYBOARDS
# ==========================================

START_TEXT = (
    "Dᴏᴡɴʟᴏᴀᴅ IT — Dᴏᴡɴʟᴏᴀᴅ ᴀʟᴍᴏsᴛ ᴀɴʏ ᴍᴇᴅɪᴀ ᴛᴏ ʏᴏᴜʀ ᴍᴏʙɪʟᴇ ᴏʀ ᴄᴏᴍᴘᴜᴛᴇʀ.\n\n"
    "🔒 Dᴏᴡɴʟᴏᴀᴅ ʀᴇsᴛʀɪᴄᴛᴇᴅ ᴍᴇᴅɪᴀ sᴀᴠᴇᴅ ᴛᴏ Tᴇʟᴇɢʀᴀᴍ\n"
    "⚡ Iɴsᴛᴀɴᴛ ᴅᴇʟɪᴠᴇʀʏ ғʀᴏᴍ ᴏᴜʀ ᴄᴀᴄʜᴇ\n"
    "🗃 Sᴛᴏʀᴀɢᴇ ᴏғ sᴀᴠᴇᴅ ᴀɴᴅ ᴜᴘʟᴏᴀᴅᴇᴅ ғɪʟᴇs\n"
    "🔀 Aᴜᴅɪᴏ ᴇxᴛʀᴀᴄᴛɪᴏɴ ᴀɴᴅ ᴄᴏɴᴠᴇʀsɪᴏɴ (ᴍᴘ3, ᴍ4ᴀ)\n"
    "⏲ Pᴀʀᴛɪᴀʟ ᴅᴏᴡɴʟᴏᴀᴅ sᴜᴘᴘᴏʀᴛ\n"
    "👥 Wᴏʀᴋs ɪɴ ɢʀᴏᴜᴘs ᴀɴᴅ ᴘʀɪᴠᴀᴛᴇ ᴄʜᴀᴛs\n\n"
    "📌 Hᴏᴡ ᴛᴏ Usᴇ:\n"
    "— Sᴇɴᴅ ᴀ ʟɪɴᴋ ᴛᴏ ᴀɴʏ sᴜᴘᴘᴏʀᴛᴇᴅ sᴇʀᴠɪᴄᴇ\n"
    "— Cʜᴏᴏsᴇ ғᴏʀᴍᴀᴛ ᴀɴᴅ qᴜᴀʟɪᴛʏ\n"
    "— Gᴇᴛ ʏᴏᴜʀ ғɪʟᴇ ɪɴ sᴇᴄᴏɴᴅs!"
)

HELP_TEXT = (
    "💡 Hᴇʟᴘ Mᴇɴᴜ & Sᴜᴘᴘᴏʀᴛᴇᴅ Sᴇʀᴠɪᴄᴇs:\n\n"
    "• Vɪᴅᴇᴏ: YᴏᴜTᴜʙᴇ, Iɴsᴛᴀɢʀᴀᴍ, TɪᴋTᴏᴋ, Tᴡɪᴛᴛᴇʀ/X, Fᴀᴄᴇʙᴏᴏᴋ, VK, Pɪɴᴛᴇʀᴇsᴛ, Rᴇᴅᴅɪᴛ\n"
    "• Cʟᴏᴜᴅ: TᴇʀᴀBᴏᴏᴋ, Gᴏᴏɢʟᴇ Dʀɪᴠᴇ (Pᴜʙʟɪᴄ Lɪɴᴋs)\n"
    "• Aᴜᴅɪᴏ: SᴏᴜɴᴅCʟᴏᴜᴅ, Sᴘᴏᴛɪғʏ (YᴏᴜTᴜʙᴇ ᴠᴇʀsɪᴏɴs)\n\n"
    "✨ Sɪᴍᴘʟʏ ᴘᴀsᴛᴇ ᴀɴʏ URL ᴅɪʀᴇᴄᴛʟʏ ɪɴᴛᴏ ᴛʜɪs ᴄʜᴀᴛ!"
)

ABOUT_TEXT = (
    "ℹ️ Gᴇzx Dᴏᴡɴʟᴏᴀᴅᴇʀ Eɴɢɪɴᴇ\n\n"
    "⚡ Vᴇʀsɪᴏɴ: 4.0 Mᴀx Uʟᴛʀᴀ\n"
    "📦 Fʀᴀᴍᴇᴡᴏʀᴋ: Pʏᴛʜᴏɴ Asʏɴᴄ + Pʏʀᴏɢʀᴀᴍ + Yᴛ-Dʟᴘ\n"
    "🚀 Mᴀx Fɪʟᴇ Sɪᴢᴇ: Uᴘ ᴛᴏ 2.0 GB ᴘᴇʀ ғɪʟᴇ\n"
    "🛡 Sᴇᴄᴜʀɪᴛʏ: Dɪʀᴇᴄᴛ Tᴇʟᴇɢʀᴀᴍ ᴛʀᴀɴsᴘᴏʀᴛ ᴡɪᴛʜᴏᴜᴛ ʟɪɴᴋ ᴛʀᴀᴄᴋɪɴɢ"
)

START_BUTTONS = InlineKeyboardMarkup([
    [InlineKeyboardButton("⚙️ Sᴇᴛᴛɪɴɢs", callback_data="btn_settings"), InlineKeyboardButton("🔍 Iɴʟɪɴᴇ sᴇᴀʀᴄʜ", switch_inline_query="")],
    [InlineKeyboardButton("📖 Hᴇʟᴘ", callback_data="btn_help"), InlineKeyboardButton("ℹ️ Aʙᴏᴜᴛ", callback_data="btn_about")]
])

BACK_BUTTON = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Bᴀᴄᴋ", callback_data="btn_back")]])

# ==========================================
# COMMAND HANDLERS
# ==========================================

@app.on_message(filters.command("start"))
async def start_cmd(client: Client, message: Message):
    try:
        await message.reply_photo(photo=Config.START_PHOTO, caption=START_TEXT, reply_markup=START_BUTTONS)
    except Exception as e:
        logger.warning(f"Failed to send photo: {e}")
        await message.reply_text(START_TEXT, reply_markup=START_BUTTONS, disable_web_page_preview=True)


@app.on_message(filters.command("help"))
async def help_cmd(client: Client, message: Message):
    try:
        await message.reply_photo(photo=Config.HELP_PHOTO, caption=HELP_TEXT, reply_markup=BACK_BUTTON)
    except Exception:
        await message.reply_text(HELP_TEXT, reply_markup=BACK_BUTTON)


@app.on_message(filters.command("about"))
async def about_cmd(client: Client, message: Message):
    try:
        await message.reply_photo(photo=Config.ABOUT_PHOTO, caption=ABOUT_TEXT, reply_markup=BACK_BUTTON)
    except Exception:
        await message.reply_text(ABOUT_TEXT, reply_markup=BACK_BUTTON)

# ==========================================
# LINK PROCESSOR & UI GENERATOR
# ==========================================

@app.on_message(filters.regex(r'https?://[^\s]+'))
async def link_handler(client: Client, message: Message):
    url = message.text.strip()
    status_msg = await message.reply_text("🔎 Fᴇᴛᴄʜɪɴɢ ᴍᴇᴅɪᴀ ғᴏʀᴍᴀᴛs...")
    
    info = await get_media_info_advanced(url)
    if not info:
        await status_msg.edit_text("❌ Fᴀɪʟᴇᴅ ᴛᴏ ғᴇᴛᴄʜ ᴍᴇᴅɪᴀ ᴍᴇᴛᴀᴅᴀᴛᴀ. Tʜᴇ ʟɪɴᴋ ᴍɪɢʜᴛ ʙᴇ ᴘʀɪᴠᴀᴛᴇ ᴏʀ ᴜɴsᴜᴘᴘᴏʀᴛᴇᴅ.")
        return

    PENDING_URLS[message.from_user.id] = {"url": url, "info": info}

    ui_text = "🎥 Vɪᴅᴇᴏ\n"
    res_list = [2160, 1440, 1080, 720, 480, 360, 240, 144]
    
    count = 1
    for r in res_list:
        icon = "⭐" if r >= 1440 else "⚡"
        ui_text += f"{count}. mp4, {r}p {icon}\n"
        count += 1

    ui_text += "\n🎧 Aᴜᴅɪᴏ\n"
    ui_text += f"{count}. m4a, 128kbps, 44kHz\n"
    ui_text += f"{count+1}. m4a, 64kbps, 22kHz\n\n"
    ui_text += "🛡 Fᴏʀᴍᴀᴛs 2160ᴘ, 1440ᴘ ɴᴏᴛ ᴄᴏᴍᴘᴀᴛɪʙʟᴇ ᴡɪᴛʜ Apple iPhone\n"

    keyboard = [
        [
            InlineKeyboardButton("🎥 2160ᴘ", callback_data="dl_v_2160"),
            InlineKeyboardButton("🎥 1440ᴘ", callback_data="dl_v_1440"),
            InlineKeyboardButton("🎥 1080ᴘ", callback_data="dl_v_1080")
        ],
        [
            InlineKeyboardButton("🎥 720ᴘ", callback_data="dl_v_720"),
            InlineKeyboardButton("🎥 480ᴘ", callback_data="dl_v_480"),
            InlineKeyboardButton("🎥 360ᴘ", callback_data="dl_v_360")
        ],
        [
            InlineKeyboardButton("🎥 240ᴘ", callback_data="dl_v_240"),
            InlineKeyboardButton("🎥 144ᴘ", callback_data="dl_v_144")
        ],
        [
            InlineKeyboardButton("🎵 128ᴋʙᴘs", callback_data="dl_a_128"),
            InlineKeyboardButton("🎵 64ᴋʙᴘs", callback_data="dl_a_64")
        ],
        [InlineKeyboardButton("💬 Dᴏᴡɴʟᴏᴀᴅ sᴜʙᴛɪᴛʟᴇs", callback_data="dl_sub")],
        [InlineKeyboardButton("📝 Dᴏᴡɴʟᴏᴀᴅ ᴄᴀᴘᴛɪᴏɴ", callback_data="dl_cap")],
        [InlineKeyboardButton("⬅️ Bᴀᴄᴋ", callback_data="btn_close")]
    ]

    await status_msg.edit_text(ui_text, reply_markup=InlineKeyboardMarkup(keyboard))

# ==========================================
# CALLBACK ROUTER & DOWNLOAD ENGINE
# ==========================================

@app.on_callback_query()
async def callback_router(client: Client, query: CallbackQuery):
    await query.answer()
    data = query.data
    user_id = query.from_user.id

    if data in ["btn_close"]:
        await query.message.delete()
        return

    if data == "btn_back":
        try:
            await query.message.edit_caption(caption=START_TEXT, reply_markup=START_BUTTONS)
        except Exception:
            await query.message.edit_text(text=START_TEXT, reply_markup=START_BUTTONS)
        return

    if data == "btn_help":
        try:
            await query.message.edit_caption(caption=HELP_TEXT, reply_markup=BACK_BUTTON)
        except Exception:
            await query.message.edit_text(text=HELP_TEXT, reply_markup=BACK_BUTTON)
        return

    if data == "btn_about":
        try:
            await query.message.edit_caption(caption=ABOUT_TEXT, reply_markup=BACK_BUTTON)
        except Exception:
            await query.message.edit_text(text=ABOUT_TEXT, reply_markup=BACK_BUTTON)
        return

    if data == "btn_settings":
        await query.answer("⚙️ Settings menu feature coming in next update!", show_alert=True)
        return

    if user_id not in PENDING_URLS:
        await query.answer("Sᴇssɪᴏɴ ᴇxᴘɪʀᴇᴅ. Sᴇɴᴅ ᴛʜᴇ ʟɪɴᴋ ᴀɢᴀɪɴ.", show_alert=True)
        return

    session = PENDING_URLS[user_id]
    url = session["url"]
    info = session["info"]

    if data == "dl_cap":
        cap_text = info.get("description", "Nᴏ ᴄᴀᴘᴛɪᴏɴ ғᴏᴜɴᴅ.")
        if len(cap_text) > 4000:
            cap_text = cap_text[:4000] + "..."
        await query.message.reply_text(f"📝 Cᴀᴘᴛɪᴏɴ:\n\n{cap_text}")
        return

    dl_type = "video"
    quality = "1080"
    
    if data.startswith("dl_v_"):
        dl_type = "video"
        quality = data.split("_")[2]
    elif data.startswith("dl_a_"):
        dl_type = "audio"
        quality = data.split("_")[2]
    elif data == "dl_sub":
        dl_type = "subtitle"

    await query.message.edit_text("⏳ Iɴɪᴛɪᴀʟɪᴢɪɴɢ ᴅᴏᴡɴʟᴏᴀᴅ...")
    
    tracker = ProgressTracker()
    ACTIVE_DOWNLOADS[user_id] = tracker
    user_dir = os.path.join(Config.DOWNLOAD_DIR, str(user_id))
    last_update = [0]

    async def update_ui(text: str):
        now = asyncio.get_event_loop().time()
        if now - last_update[0] > 3.0:
            last_update[0] = now
            try:
                await query.message.edit_text(text)
            except Exception:
                pass

    try:
        file_path = await download_media_advanced(url, user_dir, dl_type, quality, tracker, update_ui)
        
        if dl_type == "video":
            await query.message.edit_text("🚀 Uᴘʟᴏᴀᴅɪɴɢ Vɪᴅᴇᴏ...")
            await query.message.reply_video(video=file_path, caption=f"📹 Vɪᴅᴇᴏ: {quality}p")
        elif dl_type == "audio":
            await query.message.edit_text("🚀 Uᴘʟᴏᴀᴅɪɴɢ Aᴜᴅɪᴏ...")
            audio_path = file_path.rsplit(".", 1)[0] + (".mp3" if quality == "128" else ".m4a")
            if not os.path.exists(audio_path):
                audio_path = file_path
            await query.message.reply_audio(audio=audio_path, caption=f"🎵 Aᴜᴅɪᴏ: {quality}kbps")
        elif dl_type == "subtitle":
            await query.message.edit_text("🚀 Uᴘʟᴏᴀᴅɪɴɢ Sᴜʙᴛɪᴛʟᴇs...")
            for file in os.listdir(user_dir):
                if file.endswith(".vtt") or file.endswith(".srt"):
                    await query.message.reply_document(document=os.path.join(user_dir, file), caption="💬 Sᴜʙᴛɪᴛʟᴇs")
                    break

        await query.message.delete()
    except Exception as e:
        logger.error(f"Download Error: {e}")
        await query.message.edit_text(f"❌ Error: {str(e)}")
    finally:
        ACTIVE_DOWNLOADS.pop(user_id, None)
        if os.path.exists(user_dir):
            shutil.rmtree(user_dir, ignore_errors=True)

# ==========================================
# RENDER SERVER STARTUP
# ==========================================

async def health_check(request):
    return web.Response(text="Bot is running!")

async def main():
    logger.info("Starting Pyrogram client...")
    
    while True:
        try:
            await app.start()
            break
        except FloodWait as e:
            logger.warning(f"⏳ FloodWait active! Sleeping for {e.value} seconds...")
            await asyncio.sleep(e.value + 2)
        except Exception as e:
            logger.error(f"Failed to start Pyrogram client: {e}")
            return

    me = await app.get_me()
    logger.info(f"✅ Bot connected successfully as @{me.username}")

    server = web.Server(health_check)
    runner = web.ServerRunner(server)
    await runner.setup()
    port = int(os.getenv("PORT", "8080"))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
