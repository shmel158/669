import unittest

from src.config import Replacement, Target
from src.transformer import render


def make_target(prefix="", suffix="", replacements=None, source_names=None):
    return Target(
        name="t",
        chat_id=-1,
        source_names=source_names or ["s"],
        prefix=prefix,
        suffix=suffix,
        replacements=replacements or [],
    )


class TestRender(unittest.TestCase):
    def test_no_changes(self):
        target = make_target()
        self.assertEqual(render("hello world", target), "hello world")

    def test_prefix_and_suffix(self):
        target = make_target(prefix="HEAD\n", suffix="\nFOOT")
        self.assertEqual(render("body", target), "HEAD\nbody\nFOOT")

    def test_literal_replacement(self):
        target = make_target(replacements=[Replacement(from_text="foo", to_text="bar")])
        self.assertEqual(render("foo baz foo", target), "bar baz bar")

    def test_regex_replacement(self):
        target = make_target(
            replacements=[Replacement(from_text=r"\d+", to_text="#", regex=True)]
        )
        self.assertEqual(render("price 123 usd 456", target), "price # usd #")

    def test_replacements_applied_in_order(self):
        target = make_target(
            replacements=[
                Replacement(from_text="a", to_text="b"),
                Replacement(from_text="b", to_text="c"),
            ]
        )
        self.assertEqual(render("a", target), "c")

    def test_replacements_then_wrap(self):
        target = make_target(
            prefix=">> ",
            suffix=" <<",
            replacements=[Replacement(from_text="X", to_text="Y")],
        )
        self.assertEqual(render("X signal", target), ">> Y signal <<")


if __name__ == "__main__":
    unittest.main()
