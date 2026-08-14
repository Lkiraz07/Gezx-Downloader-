import os
import sys
import logging
import asyncio
from aiohttp import web
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

import constants
from config import Config
from database import db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

if not Config.BOT_TOKEN:
    logger.critical("❌ BOT_TOKEN is missing!")
    sys.exit(1)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    logger.info(f"📩 RECEIVED /start from {user.id}")
    await db.add_user(user.id, user.username)

    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📖 Help", callback_data="help"),
            InlineKeyboardButton("ℹ️ About", callback_data="about")
        ]
    ])
    await update.message.reply_text(
        text=f"{constants.HEADER_START}\n\nSend me any media link and I will download it for you!",
        reply_markup=buttons
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text
    logger.info(f"📩 RECEIVED MESSAGE from {user.id}: {text}")
    
    if text.startswith("http://") or text.startswith("https://"):
        await update.message.reply_text(f"⚡ **Link Received!**\n`{text}`\n\nProcessing download...")
    else:
        await update.message.reply_text("Please send a valid HTTP/HTTPS media link.")

async def health_check(request):
    return web.Response(text="Bot is running!")

async def main():
    await db.init_db()
    
    # Initialize HTTP Web Server for Render
    server = web.Server(health_check)
    runner = web.ServerRunner(server)
    await runner.setup()
    port = int(os.getenv("PORT", "8080"))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"Health server live on port {port}")

    # Build Telegram Application
    application = Application.builder().token(Config.BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("🤖 Starting Telegram Polling...")
    await application.initialize()
    await application.start()
    await application.updater.start_polling(drop_pending_updates=True)
    
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
