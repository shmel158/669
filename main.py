import asyncio
import logging
import os
import sys

from src.bot import Bot
from src.config import load_risk_config, load_secrets
from src.hyperliquid_client import HyperliquidClient
from src.paths import path_in_base
from src.position_store import PositionStore
from src.telegram_listener import build_client, list_chats, register_handler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    handlers=[logging.FileHandler(path_in_base("bot.log")), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


async def run_list_chats() -> None:
    """Standalone helper mode: `whale_mirror_bot.exe --list-chats`.

    Only needs TG_API_ID/TG_API_HASH/TG_SESSION_NAME from .env (not
    TG_SOURCE_CHAT_ID, which the user hasn't picked yet at this point).
    """
    from dotenv import load_dotenv

    load_dotenv(path_in_base(".env"))
    api_id = int(os.environ["TG_API_ID"])
    api_hash = os.environ["TG_API_HASH"]
    session_name = os.environ.get("TG_SESSION_NAME", "whale_mirror_bot")

    client = build_client(path_in_base(session_name), api_id, api_hash)
    await list_chats(client)


async def main() -> None:
    risk = load_risk_config(path_in_base("config.yaml"))
    secrets = load_secrets(path_in_base(".env"))

    hl_client = HyperliquidClient(
        agent_private_key=secrets.hl_agent_private_key,
        account_address=secrets.hl_account_address,
        use_testnet=risk.use_testnet,
    )
    store = PositionStore(path_in_base("bot_state.db"))
    bot = Bot(risk, hl_client, store)

    tg_client = build_client(path_in_base(secrets.tg_session_name), secrets.tg_api_id, secrets.tg_api_hash)
    register_handler(tg_client, secrets.tg_source_chat_id, bot.on_telegram_message)

    logger.info(
        "Starting bot: testnet=%s dry_run=%s pct_of_equity=%s leverage=%s",
        risk.use_testnet,
        risk.dry_run,
        risk.pct_of_equity,
        risk.leverage,
    )

    watcher_task = asyncio.create_task(bot.watch_pending_twaps())

    async with tg_client:
        await tg_client.run_until_disconnected()

    watcher_task.cancel()


if __name__ == "__main__":
    if "--list-chats" in sys.argv:
        asyncio.run(run_list_chats())
    else:
        asyncio.run(main())
