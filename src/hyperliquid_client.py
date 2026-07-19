import logging

import eth_account
from hyperliquid.exchange import Exchange
from hyperliquid.info import Info
from hyperliquid.utils.constants import MAINNET_API_URL, TESTNET_API_URL
from hyperliquid.utils.signing import get_timestamp_ms, sign_l1_action

logger = logging.getLogger(__name__)


class HyperliquidClient:
    """Thin wrapper around the official SDK.

    Adds a raw `twapOrder` action, which the SDK does not expose as of
    version 0.24.0 (it only has `Info.user_twap_slice_fills` for reading
    history). The action is built and signed the same way the SDK signs
    every other L1 action internally (`sign_l1_action`), so this is not
    bypassing anything - just filling a gap in the SDK's coverage.
    """

    def __init__(self, agent_private_key: str, account_address: str, use_testnet: bool):
        base_url = TESTNET_API_URL if use_testnet else MAINNET_API_URL
        wallet = eth_account.Account.from_key(agent_private_key)
        self.exchange = Exchange(wallet, base_url=base_url, account_address=account_address)
        self.info: Info = self.exchange.info
        self.account_address = account_address
        self.is_mainnet = not use_testnet

    def get_equity_usd(self) -> float:
        state = self.info.user_state(self.account_address)
        return float(state["marginSummary"]["accountValue"])

    def get_mid_price(self, coin: str) -> float:
        mids = self.info.all_mids()
        return float(mids[coin])

    def get_sz_decimals(self, coin: str) -> int:
        asset = self.info.coin_to_asset[coin]
        return self.info.asset_to_sz_decimals[asset]

    def coin_exists(self, coin: str) -> bool:
        return coin in self.info.coin_to_asset

    def set_leverage(self, coin: str, leverage: int, is_cross: bool) -> dict:
        return self.exchange.update_leverage(leverage, coin, is_cross)

    def place_twap_order(
        self,
        coin: str,
        is_buy: bool,
        size: float,
        duration_minutes: int,
        randomize: bool,
        reduce_only: bool = False,
    ) -> dict:
        asset = self.info.name_to_asset(coin)
        action = {
            "type": "twapOrder",
            "twap": {
                "a": asset,
                "b": is_buy,
                "s": str(size),
                "r": reduce_only,
                "m": duration_minutes,
                "t": randomize,
            },
        }
        timestamp = get_timestamp_ms()
        signature = sign_l1_action(
            self.exchange.wallet,
            action,
            self.exchange.vault_address,
            timestamp,
            self.exchange.expires_after,
            self.is_mainnet,
        )
        logger.info("Placing TWAP order: %s", action)
        return self.exchange._post_action(action, signature, timestamp)

    def place_reduce_only_trigger(
        self,
        coin: str,
        is_buy: bool,
        size: float,
        trigger_px: float,
        tpsl: str,
    ) -> dict:
        """tpsl: 'sl' for stop-loss, 'tp' for take-profit. is_buy is the side
        of THIS closing order, i.e. the opposite of the position's side."""
        order_type = {"trigger": {"triggerPx": trigger_px, "isMarket": True, "tpsl": tpsl}}
        return self.exchange.order(
            coin,
            is_buy,
            size,
            trigger_px,
            order_type=order_type,
            reduce_only=True,
        )

    def get_position_size(self, coin: str) -> float:
        """Returns signed size (positive = long, negative = short, 0 = flat)."""
        state = self.info.user_state(self.account_address)
        for position in state["assetPositions"]:
            item = position["position"]
            if item["coin"] == coin:
                return float(item["szi"])
        return 0.0
