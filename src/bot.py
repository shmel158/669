import asyncio
import logging

from src.config import RiskConfig
from src.hyperliquid_client import HyperliquidClient
from src.position_store import PositionStore
from src.risk import clamp_duration_minutes, compute_position_size
from src.signal_parser import Signal, parse_signal

logger = logging.getLogger(__name__)


class Bot:
    def __init__(self, risk: RiskConfig, hl_client: HyperliquidClient, store: PositionStore):
        self.risk = risk
        self.hl = hl_client
        self.store = store

    async def on_telegram_message(self, message_id: int, text: str) -> None:
        if self.store.has_seen_message(message_id):
            return
        self.store.mark_message_seen(message_id)

        signal = parse_signal(text)
        if signal is None:
            return

        logger.info("Parsed signal: %s", signal)
        try:
            await self._handle_signal(signal, message_id)
        except Exception:
            logger.exception("Failed to handle signal for message_id=%s", message_id)

    async def _handle_signal(self, signal: Signal, message_id: int) -> None:
        coin = signal.ticker

        if not self.risk.is_coin_allowed(coin):
            logger.info("Coin %s rejected by whitelist/blacklist, skipping", coin)
            return

        if not self.hl.coin_exists(coin):
            logger.warning("Coin %s not found on Hyperliquid, skipping", coin)
            return

        open_count = self.store.count_open_unprotected()
        if open_count >= self.risk.max_concurrent_positions:
            logger.info(
                "Max concurrent positions reached (%s/%s), skipping signal for %s",
                open_count,
                self.risk.max_concurrent_positions,
                coin,
            )
            return

        equity = self.hl.get_equity_usd()
        price = signal.price or self.hl.get_mid_price(coin)
        sz_decimals = self.hl.get_sz_decimals(coin)

        position = compute_position_size(equity, price, self.risk, sz_decimals)
        duration_minutes = clamp_duration_minutes(signal.duration_hours, self.risk)
        is_buy = signal.direction == "buy"

        logger.info(
            "Sizing for %s: equity=%.2f price=%.4f size=%.6f notional=%.2f duration_min=%s dry_run=%s",
            coin,
            equity,
            price,
            position.size_coin,
            position.notional_usd,
            duration_minutes,
            self.risk.dry_run,
        )

        if self.risk.dry_run:
            logger.info("[DRY RUN] Would place TWAP %s %s size=%s over %s min", coin, signal.direction, position.size_coin, duration_minutes)
            return

        is_cross = self.risk.margin_mode == "cross"
        self.hl.set_leverage(coin, self.risk.leverage, is_cross)

        response = self.hl.place_twap_order(
            coin=coin,
            is_buy=is_buy,
            size=position.size_coin,
            duration_minutes=duration_minutes,
            randomize=self.risk.randomize_twap,
        )
        logger.info("TWAP order response: %s", response)

        self.store.add_open_twap(
            coin=coin,
            is_buy=is_buy,
            size=position.size_coin,
            entry_price=price,
            duration_min=duration_minutes,
            stop_loss_pct=self.risk.stop_loss_pct,
            take_profit_pct=self.risk.take_profit_pct,
            source_message_id=message_id,
        )

    async def watch_pending_twaps(self) -> None:
        while True:
            try:
                self._protect_due_twaps()
            except Exception:
                logger.exception("Error while checking pending TWAPs")
            await asyncio.sleep(self.risk.watch_interval_seconds)

    def _protect_due_twaps(self) -> None:
        for twap in self.store.get_due_unprotected():
            if self.risk.dry_run:
                self.store.mark_protected(twap.id)
                continue

            actual_size = self.hl.get_position_size(twap.coin)
            if actual_size == 0:
                logger.warning("TWAP for %s finished but position is flat, skipping SL/TP", twap.coin)
                self.store.mark_protected(twap.id)
                continue

            is_long = actual_size > 0
            size = abs(actual_size)
            closing_is_buy = not is_long

            sl_px = twap.entry_price * (1 - twap.stop_loss_pct) if is_long else twap.entry_price * (1 + twap.stop_loss_pct)
            tp_px = twap.entry_price * (1 + twap.take_profit_pct) if is_long else twap.entry_price * (1 - twap.take_profit_pct)

            self.hl.place_reduce_only_trigger(twap.coin, closing_is_buy, size, sl_px, "sl")
            self.hl.place_reduce_only_trigger(twap.coin, closing_is_buy, size, tp_px, "tp")
            logger.info("Attached SL=%.4f TP=%.4f for %s", sl_px, tp_px, twap.coin)

            self.store.mark_protected(twap.id)
