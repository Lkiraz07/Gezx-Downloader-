HEADER_START = "✨ **Welcome to Gezx Downloader Bot!**"
HEADER_HELP = "📖 **How to Use Gezx Downloader**"
HEADER_ABOUT = "ℹ️ **About Gezx Downloader Bot**"

BTN_BACK = "🔙 Back"
BTN_CLOSE = "❌ Close"

MSG_DOWNLOAD_CANCELLED = "🛑 **Download process has been cancelled.**"
MSG_ALREADY_IN_QUEUE = "⚠️ **You already have an active download in progress!** Please wait or cancel it using `/cancel`."
MSG_FILE_TOO_LARGE = "❌ **File exceeds Telegram's 2 GB limit!**"

TEXT_DOWNLOAD_STARTING = "⏳ **Initializing download session...**"

INFO_TEMPLATE = (
    "📋 **Media Summary Details**\n\n"
    "📄 **Name:** `{filename}`\n"
    "💾 **Size:** {size}\n"
    "⏱ **Duration:** {duration}\n"
    "📐 **Resolution:** {quality}\n"
    "🎞 **Format:** {format}\n"
    "🎥 **Codec:** {video_codec}\n"
    "🔊 **Audio Tracks:** {audio_tracks}\n"
    "💬 **Subtitles:** {subtitle_tracks}"
)

DEFAULT_CAPTION_TEMPLATE = (
    "📄 **{filename}**\n"
    "💾 **Size:** {filesize}\n"
    "⏱ **Duration:** {duration}\n"
    "📐 **Quality:** {quality}\n"
    "📦 **Format:** {format}\n"
    "🌐 **Source:** {source}\n\n"
    "⚡ *Downloaded by {bot}*"
)

