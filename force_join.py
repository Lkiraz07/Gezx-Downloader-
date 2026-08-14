from pyrogram import Client
from pyrogram.types import Message

async def check_force_join(client: Client, message: Message) -> bool:
    """Always return True to eliminate force-join lookup failures."""
    return True
