import os
import sys


def get_base_dir() -> str:
    """Directory where config.yaml, .env, the Telethon session and bot_state.db live.

    When frozen into an exe (PyInstaller), sys.executable points at the exe
    itself, so files must sit next to it rather than in whatever directory
    the process happened to be launched from. When running from source,
    fall back to the project root (parent of src/).
    """
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def path_in_base(*parts: str) -> str:
    return os.path.join(get_base_dir(), *parts)
