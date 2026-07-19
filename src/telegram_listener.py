import asyncio
import logging
import sys
from typing import Awaitable, Callable

from telethon import TelegramClient, events

logger = logging.getLogger(__name__)

OnMessage = Callable[[int, str], Awaitable[None]]


def build_client(session_name: str, api_id: int, api_hash: str) -> TelegramClient:
    return TelegramClient(session_name, api_id, api_hash)


def register_handler(client: TelegramClient, source_chat_id: int, on_message: OnMessage) -> None:
    @client.on(events.NewMessage(chats=source_chat_id, incoming=True))
    async def _handler(event):
        text = event.raw_text or ""
        try:
            await on_message(event.message.id, text)
        except Exception:
            logger.exception("Error handling Telegram message id=%s", event.message.id)

    logger.info("Registered listener for chat_id=%s", source_chat_id)


async def list_chats(client: TelegramClient) -> None:
    """Utility to help the user find TG_SOURCE_CHAT_ID: run this module with --list-chats."""
    async with client:
        async for dialog in client.iter_dialogs():
            print(f"{dialog.id}\t{dialog.name}")


if __name__ == "__main__":
    import os

    from dotenv import load_dotenv

    load_dotenv()
    if "--list-chats" not in sys.argv:
        print("Usage: python -m src.telegram_listener --list-chats")
        sys.exit(1)

    api_id = int(os.environ["TG_API_ID"])
    api_hash = os.environ["TG_API_HASH"]
    session_name = os.environ.get("TG_SESSION_NAME", "whale_mirror_bot")

    client = build_client(session_name, api_id, api_hash)
    with client:
        client.loop.run_until_complete(list_chats(client))
