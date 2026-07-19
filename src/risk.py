import math
from dataclasses import dataclass

from src.config import RiskConfig


@dataclass
class PositionSize:
    size_coin: float
    notional_usd: float


def round_down_to_decimals(value: float, decimals: int) -> float:
    factor = 10**decimals
    return math.floor(value * factor) / factor


def compute_position_size(
    equity_usd: float,
    price_usd: float,
    risk: RiskConfig,
    sz_decimals: int,
) -> PositionSize:
    if equity_usd <= 0:
        raise ValueError("equity_usd must be positive")
    if price_usd <= 0:
        raise ValueError("price_usd must be positive")

    notional_usd = equity_usd * risk.pct_of_equity * risk.leverage
    raw_size = notional_usd / price_usd
    size_coin = round_down_to_decimals(raw_size, sz_decimals)

    if size_coin <= 0:
        raise ValueError(
            f"Computed size rounds down to 0 with sz_decimals={sz_decimals} "
            f"(equity={equity_usd}, pct={risk.pct_of_equity}, leverage={risk.leverage}, price={price_usd})"
        )

    return PositionSize(size_coin=size_coin, notional_usd=notional_usd)


def clamp_duration_minutes(duration_hours: float, risk: RiskConfig) -> int:
    capped_hours = min(duration_hours, risk.max_twap_duration_hours)
    minutes = capped_hours * 60
    minutes = max(minutes, risk.min_twap_duration_minutes)
    return round(minutes)
