import asyncio
import logging
import sys

from src.config import load_config, load_secrets
from src.forwarder import build_client, list_chats, register_handlers
from src.paths import path_in_base
from src.state_store import StateStore

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    handlers=[logging.FileHandler(path_in_base("forwarder.log")), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


async def run_list_chats() -> None:
    """Standalone helper mode: `signal_forwarder.exe --list-chats`.

    Only needs TG_API_ID/TG_API_HASH/TG_SESSION_NAME from .env — chat_ids for
    sources/targets haven't been picked yet at this point.
    """
    import os

    from dotenv import load_dotenv

    load_dotenv(path_in_base(".env"))
    api_id = int(os.environ["TG_API_ID"])
    api_hash = os.environ["TG_API_HASH"]
    session_name = os.environ.get("TG_SESSION_NAME", "signal_forwarder")

    client = build_client(path_in_base(session_name), api_id, api_hash)
    await list_chats(client)


async def main() -> None:
    config = load_config(path_in_base("config.yaml"))
    secrets = load_secrets(path_in_base(".env"))

    state = StateStore(path_in_base("forward_state.db"))
    client = build_client(path_in_base(secrets.tg_session_name), secrets.tg_api_id, secrets.tg_api_hash)
    register_handlers(client, config, state)

    logger.info(
        "Starting signal_forwarder: dry_run=%s sources=%d targets=%d",
        config.dry_run,
        len(config.sources),
        len(config.targets),
    )

    async with client:
        await client.run_until_disconnected()


if __name__ == "__main__":
    if "--list-chats" in sys.argv:
        asyncio.run(run_list_chats())
    else:
        asyncio.run(main())
