import asyncio
import json
import logging

logger = logging.getLogger(__name__)

async def get_media_info(file_path: str) -> dict:
    cmd = [
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_format", "-show_streams", file_path
    ]
    try:
        proc = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        stdout, _ = await proc.communicate()
        data = json.loads(stdout.decode())
        
        format_info = data.get("format", {})
        duration = float(format_info.get("duration", 0))
        
        res = "Original"
        for stream in data.get("streams", []):
            if stream.get("codec_type") == "video":
                res = f"{stream.get('width', 0)}x{stream.get('height', 0)}"
                break
                
        return {"duration": int(duration), "resolution": res}
    except Exception as e:
        logger.error(f"Error reading media metadata: {e}")
        return {"duration": 0, "resolution": "Original"}

async def apply_custom_metadata(input_path: str, output_path: str) -> str:
    cmd = [
        "ffmpeg", "-y", "-i", input_path,
        "-metadata", "title=Downloaded via Gezx Bot",
        "-metadata", "comment=Powered by Pyrogram & yt-dlp",
        "-c", "copy", output_path
    ]
    try:
        proc = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        await proc.communicate()
        return output_path if proc.returncode == 0 else input_path
    except Exception as e:
        logger.error(f"FFmpeg processing failed: {e}")
        return input_path
