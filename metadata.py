import asyncio
import json
import os
import logging
from config import Config
from database import db

logger = logging.getLogger(__name__)

async def get_media_info(filepath: str) -> dict:
    """
    Uses ffprobe to extract detailed information about video, audio, and subtitle streams.
    Returns a dictionary with media attributes.
    """
    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        filepath
    ]

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, _ = await proc.communicate()
        
        if proc.returncode != 0:
            return {}

        data = json.loads(stdout.decode('utf-8'))
        format_info = data.get("format", {})
        streams = data.get("streams", [])

        video_streams = [s for s in streams if s.get("codec_type") == "video"]
        audio_streams = [s for s in streams if s.get("codec_type") == "audio"]
        subtitle_streams = [s for s in streams if s.get("codec_type") == "subtitle"]

        primary_video = video_streams[0] if video_streams else {}
        width = primary_video.get("width")
        height = primary_video.get("height")
        resolution = f"{width}x{height}" if width and height else "Unknown"

        audio_langs = []
        for a in audio_streams:
            lang = a.get("tags", {}).get("language", "und")
            codec = a.get("codec_name", "audio")
            audio_langs.append(f"{codec}({lang})")

        sub_langs = []
        for s in subtitle_streams:
            lang = s.get("tags", {}).get("language", "und")
            sub_langs.append(lang)

        duration = float(format_info.get("duration", 0))

        return {
            "duration": duration,
            "size": int(format_info.get("size", 0)),
            "format_name": format_info.get("format_long_name", "Unknown"),
            "resolution": resolution,
            "video_codec": primary_video.get("codec_name", "None"),
            "audio_count": len(audio_streams),
            "audio_tracks": ", ".join(audio_langs) if audio_langs else "None",
            "subtitle_count": len(subtitle_streams),
            "subtitle_tracks": ", ".join(sub_langs) if sub_langs else "None"
        }

    except Exception as e:
        logger.error(f"Error extracting metadata with ffprobe: {e}")
        return {}


async def apply_custom_metadata(input_path: str, output_path: str) -> str:
    """
    Applies custom metadata (artist, title, encoder, comment) without re-encoding streams.
    Preserves all original audio, video, and subtitle streams.
    Returns path to output file if successful, or original input_path if failed or disabled.
    """
    metadata_enabled = await db.get_setting("metadata_enabled", "true")
    if metadata_enabled.lower() != "true":
        return input_path

    title = await db.get_setting("metadata_title", Config.DEFAULT_METADATA_TITLE)
    artist = await db.get_setting("metadata_artist", Config.DEFAULT_METADATA_TITLE)
    encoder = await db.get_setting("metadata_encoder", Config.DEFAULT_METADATA_TITLE)

    cmd = [
        "ffmpeg",
        "-y",
        "-i", input_path,
        "-map", "0",
        "-c", "copy",
        "-metadata", f"title={title}",
        "-metadata", f"artist={artist}",
        "-metadata", f"encoder={encoder}",
        "-metadata", f"comment={title}",
        output_path
    ]

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        _, stderr = await proc.communicate()

        if proc.returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            return output_path
        else:
            logger.warning(f"FFmpeg metadata tagging failed: {stderr.decode('utf-8')}")
            return input_path
    except Exception as e:
        logger.error(f"Exception while applying metadata: {e}")
        return input_path
