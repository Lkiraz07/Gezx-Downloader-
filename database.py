import aiosqlite
from config import Config

class Database:
    def __init__(self, db_path: str = Config.DATABASE_URL):
        self.db_path = db_path

    async def init_db(self):
        """Initialize database tables."""
        async with aiosqlite.connect(self.db_path) as db:
            # Users table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    joined_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_blocked INTEGER DEFAULT 0
                )
            """)

            # Cache table for storing uploaded telegram file_ids
            await db.execute("""
                CREATE TABLE IF NOT EXISTS cache (
                    url_hash TEXT PRIMARY KEY,
                    original_url TEXT,
                    file_id TEXT,
                    file_name TEXT,
                    file_size INTEGER,
                    file_type TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Dynamic Settings table for admin configurations
            await db.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)

            await db.commit()

    # --- User Management ---
    async def add_user(self, user_id: int, username: str = None):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)",
                (user_id, username)
            )
            await db.commit()

    async def get_all_users(self):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT user_id FROM users") as cursor:
                rows = await cursor.fetchall()
                return [row[0] for row in rows]

    async def set_blocked_status(self, user_id: int, is_blocked: bool):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE users SET is_blocked = ? WHERE user_id = ?",
                (1 if is_blocked else 0, user_id)
            )
            await db.commit()

    async def is_blocked(self, user_id: int) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT is_blocked FROM users WHERE user_id = ?", (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return bool(row[0]) if row else False

    # --- Cache Management ---
    async def get_cached_file(self, url_hash: str):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT file_id, file_name, file_size, file_type FROM cache WHERE url_hash = ?",
                (url_hash,)
            ) as cursor:
                return await cursor.fetchone()

    async def set_cached_file(self, url_hash: str, original_url: str, file_id: str, file_name: str, file_size: int, file_type: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """INSERT OR REPLACE INTO cache 
                   (url_hash, original_url, file_id, file_name, file_size, file_type) 
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (url_hash, original_url, file_id, file_name, file_size, file_type)
            )
            await db.commit()

    async def get_cache_stats(self):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT COUNT(*), COALESCE(SUM(file_size), 0) FROM cache") as cursor:
                count, total_bytes = await cursor.fetchone()
                return count, total_bytes

    async def clear_cache(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM cache")
            await db.commit()

    # --- Admin Settings Management ---
    async def get_setting(self, key: str, default: str = None) -> str:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT value FROM settings WHERE key = ?", (key,)) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else default

    async def set_setting(self, key: str, value: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                (key, value)
            )
            await db.commit()

db = Database()
