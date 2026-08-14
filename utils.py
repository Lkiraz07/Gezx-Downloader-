import time
import math
import hashlib

def humanbytes(size: int) -> str:
    """Format bytes into a human-readable string."""
    if not size:
        return "0 B"
    power = 2**10
    n = 0
    power_labels = {0: 'B', 1: 'KB', 2: 'MB', 3: 'GB', 4: 'TB'}
    while size > power and n < 4:
        size /= power
        n += 1
    return f"{size:.2f} {power_labels[n]}"


def time_formatter(seconds: float) -> str:
    """Format seconds into readable time string like 1 min, 16 sec or 02:15:30."""
    if seconds is None or math.isnan(seconds) or seconds < 0:
        return "00:00"
    
    seconds = int(seconds)
    minutes, secs = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    
    if hours > 0:
        return f"{hours}h, {minutes}m, {secs}s"
    elif minutes > 0:
        return f"{minutes} min, {secs} sec"
    else:
        return f"{secs} sec"


def get_url_hash(url: str) -> str:
    """Generate SHA256 hash string for caching standard URLs."""
    return hashlib.sha256(url.strip().encode('utf-8')).hexdigest()


def get_progress_bar(percentage: float, length: int = 18) -> str:
    """Construct progress bar matching requested style [■■■■□□□□□□□□□□□□□□]."""
    filled_length = int(round(length * percentage / 100))
    bar = '■' * filled_length + '□' * (length - filled_length)
    return bar


class ProgressTracker:
    """Helper class to track speed, ETA, and prevent Telegram edit rate limits."""
    
    def __init__(self, edit_interval: float = 2.5):
        self.start_time = time.time()
        self.last_edit_time = 0
        self.edit_interval = edit_interval
        self.cancelled = False

    def should_edit(self) -> bool:
        """Check if enough time has passed to send a progress update to Telegram."""
        now = time.time()
        if now - self.last_edit_time >= self.edit_interval:
            self.last_edit_time = now
            return True
        return False

    def get_stats(self, current: int, total: int):
        """Calculate download statistics."""
        now = time.time()
        elapsed = now - self.start_time
        
        percentage = (current / total * 100) if total > 0 else 0
        speed_bytes = (current / elapsed) if elapsed > 0 else 0
        
        remaining_bytes = total - current
        eta_seconds = (remaining_bytes / speed_bytes) if speed_bytes > 0 else 0
        
        return {
            "percentage": percentage,
            "speed": f"{humanbytes(speed_bytes)}/s",
            "eta": time_formatter(eta_seconds) if eta_seconds > 0 else "0 sec",
            "current_str": humanbytes(current),
            "total_str": humanbytes(total)
      }
