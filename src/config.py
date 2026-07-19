import os
from dataclasses import dataclass, field
from typing import List

import yaml
from dotenv import load_dotenv


@dataclass
class RiskConfig:
    pct_of_equity: float
    leverage: int
    margin_mode: str
    max_concurrent_positions: int
    stop_loss_pct: float
    take_profit_pct: float
    coin_whitelist: List[str] = field(default_factory=list)
    coin_blacklist: List[str] = field(default_factory=list)
    max_twap_duration_hours: float = 24
    min_twap_duration_minutes: float = 5
    randomize_twap: bool = True
    dry_run: bool = True
    use_testnet: bool = True
    watch_interval_seconds: int = 60

    def is_coin_allowed(self, coin: str) -> bool:
        if self.coin_whitelist and coin not in self.coin_whitelist:
            return False
        if coin in self.coin_blacklist:
            return False
        return True


@dataclass
class Secrets:
    hl_agent_private_key: str
    hl_account_address: str
    tg_api_id: int
    tg_api_hash: str
    tg_session_name: str
    tg_source_chat_id: int


def load_risk_config(path: str = "config.yaml") -> RiskConfig:
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    margin_mode = raw["margin_mode"]
    if margin_mode not in ("cross", "isolated"):
        raise ValueError(f"margin_mode must be 'cross' or 'isolated', got {margin_mode!r}")

    if not (0 < raw["pct_of_equity"] <= 1):
        raise ValueError("pct_of_equity must be in (0, 1]")

    return RiskConfig(
        pct_of_equity=float(raw["pct_of_equity"]),
        leverage=int(raw["leverage"]),
        margin_mode=margin_mode,
        max_concurrent_positions=int(raw["max_concurrent_positions"]),
        stop_loss_pct=float(raw["stop_loss_pct"]),
        take_profit_pct=float(raw["take_profit_pct"]),
        coin_whitelist=list(raw.get("coin_whitelist") or []),
        coin_blacklist=list(raw.get("coin_blacklist") or []),
        max_twap_duration_hours=float(raw.get("max_twap_duration_hours", 24)),
        min_twap_duration_minutes=float(raw.get("min_twap_duration_minutes", 5)),
        randomize_twap=bool(raw.get("randomize_twap", True)),
        dry_run=bool(raw.get("dry_run", True)),
        use_testnet=bool(raw.get("use_testnet", True)),
        watch_interval_seconds=int(raw.get("watch_interval_seconds", 60)),
    )


def load_secrets(env_path: str = ".env") -> Secrets:
    load_dotenv(env_path)

    def require(name: str) -> str:
        value = os.environ.get(name)
        if not value:
            raise ValueError(f"Missing required environment variable: {name}")
        return value

    return Secrets(
        hl_agent_private_key=require("HL_AGENT_PRIVATE_KEY"),
        hl_account_address=require("HL_ACCOUNT_ADDRESS"),
        tg_api_id=int(require("TG_API_ID")),
        tg_api_hash=require("TG_API_HASH"),
        tg_session_name=require("TG_SESSION_NAME"),
        tg_source_chat_id=int(require("TG_SOURCE_CHAT_ID")),
    )
