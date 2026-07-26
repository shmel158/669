import asyncio
import logging
import sys

from telethon import TelegramClient, events
from telethon.errors import FloodWaitError

from src.config import ForwardConfig
from src.state_store import StateStore
from src.transformer import render

logger = logging.getLogger(__name__)


def build_client(session_name: str, api_id: int, api_hash: str) -> TelegramClient:
    return TelegramClient(session_name, api_id, api_hash)


async def _send_to_target(client: TelegramClient, target, text: str, media, dry_run: bool) -> None:
    if dry_run:
        logger.info("[DRY RUN] Would send to target=%s: %r", target.name, text)
        return

    try:
        if media is not None:
            await client.send_file(target.chat_id, file=media, caption=text)
        else:
            await client.send_message(target.chat_id, text)
    except FloodWaitError as e:
        logger.warning("FloodWait %ss while sending to target=%s, retrying once", e.seconds, target.name)
        await asyncio.sleep(e.seconds)
        try:
            if media is not None:
                await client.send_file(target.chat_id, file=media, caption=text)
            else:
                await client.send_message(target.chat_id, text)
        except Exception:
            logger.exception("Retry failed while sending to target=%s", target.name)
    except Exception:
        logger.exception("Failed to send to target=%s", target.name)


def register_handlers(client: TelegramClient, config: ForwardConfig, state: StateStore) -> None:
    sources_by_chat_id = config.sources_by_chat_id()
    source_chat_ids = list(sources_by_chat_id.keys())

    @client.on(events.NewMessage(chats=source_chat_ids, incoming=True))
    async def _handler(event):
        source = sources_by_chat_id.get(event.chat_id)
        if source is None:
            return

        if state.has_seen(source.chat_id, event.message.id):
            return
        state.mark_seen(source.chat_id, event.message.id)

        text = event.raw_text or ""
        targets = config.targets_for_source(source.name)
        if not targets:
            return

        media = event.message.media

        await asyncio.gather(
            *(
                _send_to_target(client, target, render(text, target), media, config.dry_run)
                for target in targets
            )
        )

    logger.info(
        "Registered forwarder for %d source(s) -> %d target(s)",
        len(config.sources),
        len(config.targets),
    )


async def list_chats(client: TelegramClient) -> None:
    """Utility to help the user find chat_ids: run with --list-chats."""
    async with client:
        async for dialog in client.iter_dialogs():
            print(f"{dialog.id}\t{dialog.name}")


if __name__ == "__main__":
    import os

    from dotenv import load_dotenv

    load_dotenv()
    if "--list-chats" not in sys.argv:
        print("Usage: python -m src.forwarder --list-chats")
        sys.exit(1)

    api_id = int(os.environ["TG_API_ID"])
    api_hash = os.environ["TG_API_HASH"]
    session_name = os.environ.get("TG_SESSION_NAME", "signal_forwarder")

    client = build_client(session_name, api_id, api_hash)
    with client:
        client.loop.run_until_complete(list_chats(client))
