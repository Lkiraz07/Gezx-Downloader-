import os
import asyncio
import logging
import yt_dlp
from utils import ProgressTracker, get_progress_bar, humanbytes

logger = logging.getLogger(__name__)

def extract_info_sync(url: str):
    """Extracts metadata safely in a thread."""
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
        'extract_flat': False,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(url, download=False)

async def get_media_info_advanced(url: str) -> dict:
    """Executes metadata extraction asynchronously."""
    loop = asyncio.get_running_loop()
    try:
        info = await loop.run_in_executor(None, extract_info_sync, url)
        
        formats = info.get("formats", [])
        available_resolutions = []
        for f in formats:
            height = f.get("height")
            if height and height not in available_resolutions:
                available_resolutions.append(height)
        
        return {
            "title": info.get("title", "Uɴᴋɴᴏᴡɴ Mᴇᴅɪᴀ"),
            "duration": int(info.get("duration", 0) or 0),
            "thumbnail": info.get("thumbnail", None),
            "source": info.get("extractor_key", "Wᴇʙ Platform"),
            "description": info.get("description", "Nᴏ ᴄᴀᴘᴛɪᴏɴ ᴀᴠᴀɪʟᴀʙʟᴇ."),
            "resolutions": sorted(available_resolutions, reverse=True),
            "raw_info": info
        }
    except Exception as e:
        logger.error(f"Extraction Error: {e}")
        return None

def download_sync(url: str, output_dir: str, dl_type: str, quality: str, progress_tracker: ProgressTracker, progress_callback, loop):
    """Executes media downloading in a thread pool."""
    os.makedirs(output_dir, exist_ok=True)
    out_template = os.path.join(output_dir, '%(title).100s.%(ext)s')

    def progress_hook(d):
        if progress_tracker.cancelled:
            raise Exception("Download Cancelled by User")
        if d['status'] == 'downloading':
            downloaded = d.get('downloaded_bytes', 0)
            total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
            speed = d.get('speed', 0)
            
            bar = get_progress_bar(downloaded, total)
            text = (
                f"⚡ Dᴏᴡɴʟᴏᴀᴅɪɴɢ...\n\n"
                f"{bar}\n"
                f"💾 Sɪᴢᴇ: `{humanbytes(downloaded)} / {humanbytes(total)}`\n"
                f"🚀 Sᴘᴇᴇᴅ: `{humanbytes(speed)}/s`"
            )
            asyncio.run_coroutine_threadsafe(progress_callback(text), loop)

    ydl_opts = {
        'outtmpl': out_template,
        'quiet': True,
        'progress_hooks': [progress_hook],
    }

    if dl_type == "video":
        ydl_opts['format'] = f"bestvideo[height<={quality}]+bestaudio/best"
        ydl_opts['merge_output_format'] = 'mp4'
    elif dl_type == "audio":
        ydl_opts['format'] = "bestaudio/best"
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3' if quality == "128" else 'm4a',
            'preferredquality': quality,
        }]
    elif dl_type == "subtitle":
        ydl_opts['writesubtitles'] = True
        ydl_opts['subtitleslangs'] = ['en', 'all']
        ydl_opts['skip_download'] = True

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)

async def download_media_advanced(url: str, output_dir: str, dl_type: str, quality: str, progress_tracker: ProgressTracker, progress_callback) -> str:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        None, download_sync, url, output_dir, dl_type, quality, progress_tracker, progress_callback, loop
    )
