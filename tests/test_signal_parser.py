import unittest

from src.signal_parser import parse_signal


class TestSignalParser(unittest.TestCase):
    def test_buy_signal(self):
        text = (
            "🟩 $185.70K покупка VVV в течении 16.5 часа\n\n"
            "Цена: $11.77\n"
            "Объем: $5.25M (3.54%)\n"
            "Субъект: 0x99b9801f356dd303de0549a40cc9291ab06a9578\n"
            "#1ab06a9578\n\n"
            "Создан в: 21:47:20 (UTC)"
        )
        signal = parse_signal(text)
        self.assertIsNotNone(signal)
        self.assertEqual(signal.direction, "buy")
        self.assertEqual(signal.ticker, "VVV")
        self.assertAlmostEqual(signal.duration_hours, 16.5)
        self.assertAlmostEqual(signal.price, 11.77)

    def test_sell_signal(self):
        text = "🟥 $2.10M продажа BTC в течении 3 часа\n\nЦена: $65000.5\n"
        signal = parse_signal(text)
        self.assertIsNotNone(signal)
        self.assertEqual(signal.direction, "sell")
        self.assertEqual(signal.ticker, "BTC")
        self.assertAlmostEqual(signal.duration_hours, 3.0)
        self.assertAlmostEqual(signal.price, 65000.5)

    def test_millions_volume_and_word_fallback_without_emoji(self):
        text = "$1.2M покупка ETH в течении 2 часа\n\nЦена: $3200"
        signal = parse_signal(text)
        self.assertIsNotNone(signal)
        self.assertEqual(signal.direction, "buy")
        self.assertEqual(signal.ticker, "ETH")
        self.assertAlmostEqual(signal.duration_hours, 2.0)

    def test_fractional_duration_comma_decimal(self):
        text = "🟩 $500K покупка SOL в течении 0,5 часа\n\nЦена: $150"
        signal = parse_signal(text)
        self.assertIsNotNone(signal)
        self.assertAlmostEqual(signal.duration_hours, 0.5)

    def test_no_price_field_is_optional(self):
        text = "🟩 $500K покупка SOL в течении 1 часа"
        signal = parse_signal(text)
        self.assertIsNotNone(signal)
        self.assertIsNone(signal.price)

    def test_unrelated_message_returns_none(self):
        text = "просто какое-то сообщение в чате, не сигнал"
        signal = parse_signal(text)
        self.assertIsNone(signal)

    def test_billions_suffix(self):
        text = "🟩 $1.5B покупка XYZ в течении 24 часа\n\nЦена: $0.5"
        signal = parse_signal(text)
        self.assertIsNotNone(signal)
        self.assertEqual(signal.ticker, "XYZ")


if __name__ == "__main__":
    unittest.main()
