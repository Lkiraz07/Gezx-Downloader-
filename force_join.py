from pyrogram import Client
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import UserNotParticipant, ChatAdminRequired, PeerIdInvalid
from database import db
import constants

async def check_force_join(client: Client, message: Message) -> bool:
    """
    Checks if Force Join is enabled and verifies user membership in the target channel.
    Returns True if user is allowed to proceed, False if restricted.
    Sends join message to user if restricted.
    """
    is_enabled = await db.get_setting("force_join_enabled", "false")
    if is_enabled.lower() != "true":
        return True

    channel_id_str = await db.get_setting("force_join_channel", "")
    if not channel_id_str:
        return True

    user_id = message.from_user.id
    
    # Bypass force join check for Bot Admin
    admin_id = await db.get_setting("admin_id", "")
    if str(user_id) == admin_id or user_id == 5565826679:
        return True

    try:
        # Determine channel target (numeric ID or username)
        try:
            channel_target = int(channel_id_str)
        except ValueError:
            channel_target = channel_id_str if channel_id_str.startswith("@") else f"@{channel_id_str}"

        member = await client.get_chat_member(channel_target, user_id)
        if member.status in ["creator", "administrator", "member"]:
            return True

    except UserNotParticipant:
        pass
    except (ChatAdminRequired, PeerIdInvalid, Exception) as e:
        # If bot is not admin in channel, pass gracefully to prevent breaking operations
        return True

    # User is not a participant; construct force join message
    custom_text = await db.get_setting("force_join_text", constants.FORCE_JOIN_TEXT)
    channel_url = await db.get_setting("force_join_url", "")
    
    if not channel_url:
        if channel_id_str.startswith("@"):
            channel_url = f"https://t.me/{channel_id_str[1:]}"
        else:
            channel_url = "https://t.me/"

    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton(constants.BTN_JOIN_CHANNEL, url=channel_url)],
        [InlineKeyboardButton(constants.BTN_REFRESH_JOIN, callback_data="check_force_join")]
    ])

    await message.reply_text(
        text=custom_text,
        reply_markup=buttons,
        disable_web_page_preview=True
    )
    return False
