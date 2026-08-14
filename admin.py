import os
import asyncio
import logging
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from config import Config
from database import db
from utils import humanbytes

logger = logging.getLogger(__name__)

def is_admin(user_id: int) -> bool:
    """Verify if user is authorized as Admin."""
    return user_id == Config.ADMIN_ID or user_id == 5565826679


async def get_admin_panel_keyboard() -> InlineKeyboardMarkup:
    """Generate main admin control panel buttons."""
    force_join = await db.get_setting("force_join_enabled", "false")
    metadata = await db.get_setting("metadata_enabled", "true")
    
    fj_status = "✅ ON" if force_join.lower() == "true" else "❌ OFF"
    meta_status = "✅ ON" if metadata.lower() == "true" else "❌ OFF"

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📊 Stats", callback_data="admin_stats"),
            InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast")
        ],
        [
            InlineKeyboardButton(f"🔒 Force Join [{fj_status}]", callback_data="admin_toggle_fj"),
            InlineKeyboardButton(f"🏷 Metadata [{meta_status}]", callback_data="admin_toggle_meta")
        ],
        [
            InlineKeyboardButton("⚙️ TeraBox Cookie", callback_data="admin_set_cookie"),
            InlineKeyboardButton("🧹 Clear Cache", callback_data="admin_clear_cache")
        ],
        [
            InlineKeyboardButton("🚫 Block User", callback_data="admin_block_user"),
            InlineKeyboardButton("✅ Unblock User", callback_data="admin_unblock_user")
        ],
        [
            InlineKeyboardButton("✖ Close Panel", callback_data="admin_close")
        ]
    ])
    return keyboard


async def register_admin_handlers(app: Client):
    
    @app.on_message(filters.command("admin") & filters.private)
    async def admin_command(client: Client, message: Message):
        if not is_admin(message.from_user.id):
            return  # Silently ignore unauthorized users
            
        kb = await get_admin_panel_keyboard()
        await message.reply_text(
            "🛠 **Gᴇᴢx Dᴏᴡɴʟᴏᴀᴅᴇʀ — Aᴅᴍɪɴ Cᴏɴᴛʀᴏʟ Pᴀɴᴇʟ**\n\nChoose an administrative action below:",
            reply_markup=kb
        )

    @app.on_callback_query(filters.regex("^admin_"))
    async def admin_callbacks(client: Client, callback_query: CallbackQuery):
        user_id = callback_query.from_user.id
        if not is_admin(user_id):
            await callback_query.answer("⚠️ Unauthorized access.", show_alert=True)
            return

        data = callback_query.data

        if data == "admin_stats":
            users = await db.get_all_users()
            cache_count, cache_bytes = await db.get_cache_stats()
            
            # Disk space
            total, used, free = 0, 0, 0
            if hasattr(os, 'statvfs'):
                st = os.statvfs('/')
                free = st.f_bavail * st.f_frsize
                total = st.f_blocks * st.f_frsize
                used = (st.f_blocks - st.f_bfree) * st.f_frsize

            stats_msg = (
                "📊 **Gᴇᴢx Dᴏᴡɴʟᴏᴀᴅᴇʀ Sᴛᴀᴛɪsᴛɪᴄs**\n\n"
                f"👤 **Total Users:** `{len(users)}` users\n"
                f"💾 **Cached Files:** `{cache_count}` files ({humanbytes(cache_bytes)})\n"
                f"🖥 **Storage Used:** `{humanbytes(used)}` / `{humanbytes(total)}` (Free: `{humanbytes(free)}`)\n"
            )
            await callback_query.answer()
            await callback_query.message.edit_text(
                stats_msg,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("« Back to Panel", callback_data="admin_back")]])
            )

        elif data == "admin_toggle_fj":
            current = await db.get_setting("force_join_enabled", "false")
            new_val = "false" if current.lower() == "true" else "true"
            await db.set_setting("force_join_enabled", new_val)
            await callback_query.answer(f"Force Join set to {new_val.upper()}")
            kb = await get_admin_panel_keyboard()
            await callback_query.message.edit_reply_markup(reply_markup=kb)

        elif data == "admin_toggle_meta":
            current = await db.get_setting("metadata_enabled", "true")
            new_val = "false" if current.lower() == "true" else "true"
            await db.set_setting("metadata_enabled", new_val)
            await callback_query.answer(f"Metadata Tagging set to {new_val.upper()}")
            kb = await get_admin_panel_keyboard()
            await callback_query.message.edit_reply_markup(reply_markup=kb)

        elif data == "admin_clear_cache":
            await db.clear_cache()
            await callback_query.answer("🧹 Cache database records cleared successfully!", show_alert=True)
            kb = await get_admin_panel_keyboard()
            await callback_query.message.edit_reply_markup(reply_markup=kb)

        elif data == "admin_set_cookie":
            await callback_query.answer()
            await callback_query.message.reply_text(
                "💬 To update the TeraBox cookie, send a message in this format:\n\n`/setcookie YOUR_COOKIE_STRING_HERE`"
            )

        elif data == "admin_back":
            kb = await get_admin_panel_keyboard()
            await callback_query.message.edit_text(
                "🛠 **Gᴇᴢx Dᴏᴡɴʟᴏᴀᴅᴇʀ — Aᴅᴍɪɴ Cᴏɴᴛʀᴏʟ Pᴀɴᴇʟ**\n\nChoose an administrative action below:",
                reply_markup=kb
            )

        elif data == "admin_close":
            await callback_query.message.delete()

    @app.on_message(filters.command("setcookie") & filters.private)
    async def set_cookie_cmd(client: Client, message: Message):
        if not is_admin(message.from_user.id):
            return
            
        parts = message.text.split(" ", 1)
        if len(parts) < 2:
            await message.reply_text("⚠️ Please provide a cookie string. Usage: `/setcookie <cookie_string>`")
            return
            
        cookie_str = parts[1].strip()
        await db.set_setting("terabox_cookie", cookie_str)
        await message.reply_text("✅ TeraBox cookie updated successfully!")

    @app.on_message(filters.command("broadcast") & filters.private)
    async def broadcast_cmd(client: Client, message: Message):
        if not is_admin(message.from_user.id):
            return
            
        if not message.reply_to_message:
            await message.reply_text("⚠️ Reply to a message with `/broadcast` to send it to all users.")
            return

        users = await db.get_all_users()
        sent, failed = 0, 0
        progress_msg = await message.reply_text(f"⏳ Broadcasting to `{len(users)}` users...")

        for uid in users:
            try:
                await message.reply_to_message.copy(uid)
                sent += 1
                await asyncio.sleep(0.05)  # Rate limit safety
            except Exception:
                failed += 1

        await progress_msg.edit_text(f"✅ **Broadcast Completed!**\n\n📤 Sent: `{sent}`\n❌ Failed: `{failed}`")
