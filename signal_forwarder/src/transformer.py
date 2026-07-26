import re

from src.config import Target


def render(text: str, target: Target) -> str:
    result = text
    for repl in target.replacements:
        if repl.regex:
            result = re.sub(repl.from_text, repl.to_text, result)
        else:
            result = result.replace(repl.from_text, repl.to_text)
    return f"{target.prefix}{result}{target.suffix}"
