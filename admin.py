from pyrogram import Client, filters
from pyrogram.types import Message
from config import Config

async def register_admin_handlers(app: Client):
    @app.on_message(filters.command("stats") & filters.user(Config.ADMIN_IDS))
    async def stats_handler(client: Client, message: Message):
        await message.reply_text("📊 **Bot Status:** Operational and Online!")
