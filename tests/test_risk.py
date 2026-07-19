import unittest

from src.config import RiskConfig
from src.risk import clamp_duration_minutes, compute_position_size, round_down_to_decimals


def make_risk(**overrides) -> RiskConfig:
    base = dict(
        pct_of_equity=0.02,
        leverage=3,
        margin_mode="cross",
        max_concurrent_positions=3,
        stop_loss_pct=0.05,
        take_profit_pct=0.1,
        max_twap_duration_hours=24,
        min_twap_duration_minutes=5,
    )
    base.update(overrides)
    return RiskConfig(**base)


class TestRoundDown(unittest.TestCase):
    def test_round_down_basic(self):
        self.assertAlmostEqual(round_down_to_decimals(1.23456, 2), 1.23)
        self.assertAlmostEqual(round_down_to_decimals(1.999, 0), 1.0)


class TestComputePositionSize(unittest.TestCase):
    def test_basic_sizing(self):
        risk = make_risk(pct_of_equity=0.02, leverage=3)
        result = compute_position_size(equity_usd=10_000, price_usd=100, risk=risk, sz_decimals=2)
        # notional = 10000 * 0.02 * 3 = 600; size = 600/100 = 6.0
        self.assertAlmostEqual(result.notional_usd, 600)
        self.assertAlmostEqual(result.size_coin, 6.0)

    def test_rounding_down_to_sz_decimals(self):
        risk = make_risk(pct_of_equity=0.01, leverage=1)
        result = compute_position_size(equity_usd=1000, price_usd=3, risk=risk, sz_decimals=0)
        # notional = 10, size = 3.33 -> floor to 0 decimals = 3
        self.assertEqual(result.size_coin, 3)

    def test_zero_size_raises(self):
        risk = make_risk(pct_of_equity=0.0001, leverage=1)
        with self.assertRaises(ValueError):
            compute_position_size(equity_usd=10, price_usd=100000, risk=risk, sz_decimals=0)

    def test_invalid_inputs_raise(self):
        risk = make_risk()
        with self.assertRaises(ValueError):
            compute_position_size(equity_usd=0, price_usd=100, risk=risk, sz_decimals=2)
        with self.assertRaises(ValueError):
            compute_position_size(equity_usd=100, price_usd=0, risk=risk, sz_decimals=2)


class TestClampDuration(unittest.TestCase):
    def test_within_bounds(self):
        risk = make_risk(max_twap_duration_hours=24, min_twap_duration_minutes=5)
        self.assertEqual(clamp_duration_minutes(2, risk), 120)

    def test_caps_at_max_hours(self):
        risk = make_risk(max_twap_duration_hours=10, min_twap_duration_minutes=5)
        self.assertEqual(clamp_duration_minutes(100, risk), 600)

    def test_floors_at_min_minutes(self):
        risk = make_risk(max_twap_duration_hours=24, min_twap_duration_minutes=15)
        self.assertEqual(clamp_duration_minutes(0.1, risk), 15)


if __name__ == "__main__":
    unittest.main()
