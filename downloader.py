import os
import re
import asyncio
import logging
import aiohttp
import yt_dlp
from config import Config
from database import db
from utils import ProgressTracker, get_progress_bar
import constants

logger = logging.getLogger(__name__)

TERABOX_DOMAINS = [
    "terabox.com", "neox.com", "freeterabox.com", "1024tera.com", 
    "teraboxapp.com", "4funbox.com", "mirrobox.com", "momerybox.com", "tibabox.com"
]

def is_terabox_url(url: str) -> bool:
    """Checks if a URL belongs to TeraBox or its mirror domains."""
    return any(domain in url.lower() for domain in TERABOX_DOMAINS)


async def get_media_info_from_url(url: str) -> dict:
    """Extracts media metadata using yt-dlp or direct headers."""
    if is_terabox_url(url):
        return {
            "source": "TeraBox",
            "title": "TeraBox File",
            "filesize": 0,
            "ext": "mp4"
        }

    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
    }
    
    try:
        loop = asyncio.get_event_loop()
        def _extract():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(url, download=False)

        info = await loop.run_in_executor(None, _extract)
        return {
            "source": info.get("extractor_key", "Web Media"),
            "title": info.get("title", "Media File"),
            "filesize": info.get("filesize") or info.get("filesize_approx") or 0,
            "duration": info.get("duration", 0),
            "format": info.get("ext", "mp4"),
            "resolution": f"{info.get('width', 'N/A')}x{info.get('height', 'N/A')}",
            "video_codec": info.get("vcodec", "Unknown"),
            "audio_codec": info.get("acodec", "Unknown")
        }
    except Exception as e:
        logger.error(f"Failed to fetch media info via yt-dlp: {e}")
        return {
            "source": "Direct Link",
            "title": "Media Download",
            "filesize": 0,
            "ext": "mp4"
        }


async def download_file_http(
    url: str, 
    dest_path: str, 
    progress_tracker: ProgressTracker, 
    progress_callback=None,
    headers: dict = None
) -> str:
    """Asynchronously downloads a direct file URL with progress callback and cancel check."""
    default_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    if headers:
        default_headers.update(headers)

    cookie = await db.get_setting("terabox_cookie", Config.TERABOX_COOKIE)
    if is_terabox_url(url) and cookie:
        default_headers["Cookie"] = cookie

    async with aiohttp.ClientSession(headers=default_headers) as session:
        async with session.get(url) as response:
            if response.status != 200:
                raise Exception(f"HTTP Download failed with status {response.status}")

            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0

            with open(dest_path, "wb") as f:
                async for chunk in response.content.iter_chunked(1024 * 512):
                    if progress_tracker.cancelled:
                        if os.path.exists(dest_path):
                            os.remove(dest_path)
                        raise asyncio.CancelledError("Download cancelled by user.")

                    f.write(chunk)
                    downloaded += len(chunk)

                    if progress_callback and progress_tracker.should_edit():
                        stats = progress_tracker.get_stats(downloaded, total_size or downloaded)
                        bar = get_progress_bar(stats["percentage"])
                        msg_text = constants.PROGRESS_TEMPLATE.format(
                            header=constants.TEXT_DOWNLOADING_HEADER,
                            bar=bar,
                            current=stats["current_str"],
                            total=stats["total_str"],
                            percentage=stats["percentage"],
                            speed=stats["speed"],
                            eta=stats["eta"]
                        )
                        await progress_callback(msg_text)

    return dest_path


async def download_media(
    url: str, 
    output_dir: str, 
    progress_tracker: ProgressTracker, 
    progress_callback=None,
    format_id: str = None
) -> str:
    """Downloads media from YouTube, Instagram, TikTok, TeraBox, or direct links."""
    os.makedirs(output_dir, exist_ok=True)
    
    if is_terabox_url(url):
        # Direct chunked download for TeraBox links
        file_name = "terabox_download.mp4"
        dest_path = os.path.join(output_dir, file_name)
        return await download_file_http(url, dest_path, progress_tracker, progress_callback)

    outtmpl = os.path.join(output_dir, '%(title).100s.%(ext)s')
    
    ydl_opts = {
        'outtmpl': outtmpl,
        'quiet': True,
        'no_warnings': True,
        'format': format_id if format_id else 'bestvideo+bestaudio/best',
        'merge_output_format': 'mkv',
    }

    def ydl_progress_hook(d):
        if progress_tracker.cancelled:
            raise yt_dlp.utils.DownloadError("Cancelled by user.")
            
        if d['status'] == 'downloading':
            downloaded = d.get('downloaded_bytes', 0)
            total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
            if progress_callback and progress_tracker.should_edit() and total > 0:
                stats = progress_tracker.get_stats(downloaded, total)
                bar = get_progress_bar(stats["percentage"])
                msg_text = constants.PROGRESS_TEMPLATE.format(
                    header=constants.TEXT_DOWNLOADING_HEADER,
                    bar=bar,
                    current=stats["current_str"],
                    total=stats["total_str"],
                    percentage=stats["percentage"],
                    speed=stats["speed"],
                    eta=stats["eta"]
                )
                asyncio.run_coroutine_threadsafe(
                    progress_callback(msg_text), 
                    asyncio.get_event_loop()
                )

    ydl_opts['progress_hooks'] = [ydl_progress_hook]

    loop = asyncio.get_event_loop()
    def _run_ydl():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return ydl.prepare_filename(info)

    return await loop.run_in_executor(None, _run_ydl)
