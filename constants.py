# UI Constants and Text Templates for Gezx Downloader

# UI Emojis & Headers
HEADER_START = "👋 **Wᴇʟᴄᴏᴍᴇ ᴛᴏ Gᴇᴢx Dᴏᴡɴʟᴏᴀᴅᴇʀ!**"
HEADER_HELP = "📖 **Gᴇᴢx Dᴏᴡɴʟᴏᴀᴅᴇʀ - Hᴇʟᴘ Gᴜɪᴅᴇ**"
HEADER_ABOUT = "ℹ️ **Aʙᴏᴜᴛ Gᴇᴢx Dᴏᴡɴʟᴏᴀᴅᴇʀ**"

# Download & Progress Text Constants
TEXT_DOWNLOAD_STARTING = "⏳ Dᴏᴡɴʟᴏᴀᴅ sᴛᴀʀᴛɪɴɢ..."
TEXT_DOWNLOADING_HEADER = "⚡Dᴏᴡɴʟᴏᴀᴅɪɴɢ..."
TEXT_UPLOADING_HEADER = "⚡Uᴘʟᴏᴀᴅɪɴɢ..."

PROGRESS_TEMPLATE = """{header}

[{bar}]

Sɪᴢᴇ : {current} | {total}
Dᴏɴᴇ : {percentage:.2f}%
Sᴘᴇᴇᴅ : {speed}
ETA : {eta}"""

INFO_TEMPLATE = """🎥 **Vɪᴅᴇᴏ Iɴғᴏʀᴍᴀᴛɪᴏɴ**

**Nᴀᴍᴇ:** {filename}
**Sɪᴢᴇ:** {size}
**Dᴜʀᴀᴛɪᴏɴ:** {duration}
**Qᴜᴀʟɪᴛʏ:** {quality}
**Fᴏʀᴍᴀᴛ:** {format}
**Vɪᴅᴇᴏ:** {video_codec}
**Aᴜᴅɪᴏ:** {audio_tracks}
**Sᴜʙᴛɪᴛʟᴇs:** {subtitle_tracks}"""

DEFAULT_CAPTION_TEMPLATE = """📄 **{filename}**
💾 **Sɪᴢᴇ:** {filesize} | ⏱ **Dᴜʀᴀᴛɪᴏɴ:** {duration}
🎬 **Qᴜᴀʟɪᴛʏ:** {quality} ({format})
📢 **Sᴏᴜʀᴄᴇ:** {source}

🤖 **Bʏ:** {bot}"""

FORCE_JOIN_TEXT = """⚠️ **Aᴄᴄᴇss Dᴇɴɪᴇᴅ!**

Yᴏᴜ ᴍᴜsᴛ ᴊᴏɪɴ ᴏᴜʀ Cʜᴀɴɴᴇʟ ᴛᴏ ᴜsᴇ ᴛʜɪs ʙᴏᴛ. 
Pʟᴇᴀsᴇ ᴊᴏɪɴ dynamic updates and try again!"""

# System Messages
MSG_URL_UNSUPPORTED = "❌ Unsupported URL or source platform not recognized."
MSG_FILE_TOO_LARGE = "❌ File size exceeds Telegram limits (~2 GB max)."
MSG_DOWNLOAD_CANCELLED = "🛑 Download cancelled successfully."
MSG_ALREADY_IN_QUEUE = "⏳ You already have an active or queued download."

# Button Text Labels
BTN_CANCEL = "Cancel"
BTN_BACK = "« Back"
BTN_CLOSE = "✖ Close"
BTN_JOIN_CHANNEL = "📢 Join Channel"
BTN_REFRESH_JOIN = "🔄 Check Again"
