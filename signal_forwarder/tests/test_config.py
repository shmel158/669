import os
import tempfile
import unittest

from src.config import load_config


class TestLoadConfig(unittest.TestCase):
    def _write(self, content: str) -> str:
        fd, path = tempfile.mkstemp(suffix=".yaml")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        self.addCleanup(os.remove, path)
        return path

    def test_target_default_sources_is_all(self):
        path = self._write(
            """
            sources:
              - name: a
                chat_id: -1
              - name: b
                chat_id: -2
            targets:
              - name: x
                chat_id: -3
                prefix: ""
                suffix: ""
                replacements: []
            """
        )
        config = load_config(path)
        self.assertEqual(sorted(config.targets[0].source_names), ["a", "b"])

    def test_target_explicit_sources(self):
        path = self._write(
            """
            sources:
              - name: a
                chat_id: -1
              - name: b
                chat_id: -2
            targets:
              - name: x
                chat_id: -3
                sources: [a]
            """
        )
        config = load_config(path)
        self.assertEqual(config.targets[0].source_names, ["a"])

    def test_target_unknown_source_raises(self):
        path = self._write(
            """
            sources:
              - name: a
                chat_id: -1
            targets:
              - name: x
                chat_id: -3
                sources: [does_not_exist]
            """
        )
        with self.assertRaises(ValueError):
            load_config(path)

    def test_dry_run_defaults_true(self):
        path = self._write(
            """
            sources:
              - name: a
                chat_id: -1
            targets:
              - name: x
                chat_id: -3
            """
        )
        config = load_config(path)
        self.assertTrue(config.dry_run)

    def test_replacements_parsed(self):
        path = self._write(
            """
            sources:
              - name: a
                chat_id: -1
            targets:
              - name: x
                chat_id: -3
                replacements:
                  - from: foo
                    to: bar
                  - from: "\\\\d+"
                    to: "#"
                    regex: true
            """
        )
        config = load_config(path)
        reps = config.targets[0].replacements
        self.assertEqual(len(reps), 2)
        self.assertEqual((reps[0].from_text, reps[0].to_text, reps[0].regex), ("foo", "bar", False))
        self.assertEqual((reps[1].from_text, reps[1].to_text, reps[1].regex), ("\\d+", "#", True))


if __name__ == "__main__":
    unittest.main()
