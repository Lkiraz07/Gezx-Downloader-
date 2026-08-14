import hashlib
import time

class ProgressTracker:
    def __init__(self):
        self.cancelled = False
        self.start_time = time.time()
        self.last_update_time = 0

def humanbytes(size: int) -> str:
    if not size:
        return "0 B"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} PB"

def time_formatter(seconds: int) -> str:
    if not seconds:
        return "00:00"
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"

def get_progress_bar(current: int, total: int) -> str:
    percentage = (current / total) * 100 if total else 0
    filled = int(percentage // 10)
    bar = "█" * filled + "░" * (10 - filled)
    return f"[{bar}] {percentage:.1f}%"

def get_url_hash(url: str) -> str:
    return hashlib.md5(url.strip().encode('utf-8')).hexdigest()
