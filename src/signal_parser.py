import re
from dataclasses import dataclass
from typing import Optional

_DIRECTION_EMOJI = {
    "🟩": "buy",
    "🟥": "sell",
}

_DIRECTION_WORD = {
    "покупка": "buy",
    "продажа": "sell",
}

_HEADER_RE = re.compile(
    r"(?P<emoji>[🟩🟥])?\s*\$[\d.,]+[KMB]?\s*"
    r"(?P<word>покупка|продажа)\s+"
    r"(?P<ticker>[A-Za-z0-9]+)\s+"
    r"в\s+течени\w*\s+(?P<duration>[\d.,]+)\s*час",
    re.IGNORECASE,
)

_PRICE_RE = re.compile(r"Цена:\s*\$(?P<price>[\d.,]+)")


@dataclass
class Signal:
    direction: str  # "buy" | "sell"
    ticker: str
    duration_hours: float
    price: Optional[float]
    raw_text: str


def parse_signal(text: str) -> Optional[Signal]:
    """Parse a whale-tracker TWAP alert message.

    Returns None if the message doesn't match the expected format
    (so unrelated messages in the same chat are silently ignored).
    """
    match = _HEADER_RE.search(text)
    if not match:
        return None

    direction = None
    if match.group("emoji"):
        direction = _DIRECTION_EMOJI.get(match.group("emoji"))
    if direction is None:
        direction = _DIRECTION_WORD.get(match.group("word").lower())
    if direction is None:
        return None

    ticker = match.group("ticker").upper()
    duration_hours = float(match.group("duration").replace(",", "."))

    price = None
    price_match = _PRICE_RE.search(text)
    if price_match:
        price = float(price_match.group("price").replace(",", "."))

    return Signal(
        direction=direction,
        ticker=ticker,
        duration_hours=duration_hours,
        price=price,
        raw_text=text,
    )
