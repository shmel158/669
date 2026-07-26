import os
from dataclasses import dataclass, field
from typing import List, Optional

import yaml
from dotenv import load_dotenv


@dataclass
class Replacement:
    from_text: str
    to_text: str
    regex: bool = False


@dataclass
class Source:
    name: str
    chat_id: int


@dataclass
class Target:
    name: str
    chat_id: int
    source_names: List[str]
    prefix: str = ""
    suffix: str = ""
    replacements: List[Replacement] = field(default_factory=list)


@dataclass
class ForwardConfig:
    dry_run: bool
    sources: List[Source]
    targets: List[Target]

    def sources_by_chat_id(self):
        return {s.chat_id: s for s in self.sources}

    def targets_for_source(self, source_name: str) -> List[Target]:
        return [t for t in self.targets if source_name in t.source_names]


@dataclass
class Secrets:
    tg_api_id: int
    tg_api_hash: str
    tg_session_name: str


def load_config(path: str = "config.yaml") -> ForwardConfig:
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    raw_sources = raw.get("sources") or []
    if not raw_sources:
        raise ValueError("config.yaml must define at least one entry under 'sources'")

    sources = []
    seen_source_names = set()
    for entry in raw_sources:
        name = entry["name"]
        if name in seen_source_names:
            raise ValueError(f"Duplicate source name: {name!r}")
        seen_source_names.add(name)
        sources.append(Source(name=name, chat_id=int(entry["chat_id"])))

    raw_targets = raw.get("targets") or []
    if not raw_targets:
        raise ValueError("config.yaml must define at least one entry under 'targets'")

    targets = []
    seen_target_names = set()
    for entry in raw_targets:
        name = entry["name"]
        if name in seen_target_names:
            raise ValueError(f"Duplicate target name: {name!r}")
        seen_target_names.add(name)

        source_names = entry.get("sources")
        if not source_names:
            source_names = [s.name for s in sources]  # default: forward from every source
        for sn in source_names:
            if sn not in seen_source_names:
                raise ValueError(
                    f"Target {name!r} references unknown source {sn!r}"
                )

        replacements = [
            Replacement(
                from_text=r["from"],
                to_text=r["to"],
                regex=bool(r.get("regex", False)),
            )
            for r in (entry.get("replacements") or [])
        ]

        targets.append(
            Target(
                name=name,
                chat_id=int(entry["chat_id"]),
                source_names=source_names,
                prefix=entry.get("prefix") or "",
                suffix=entry.get("suffix") or "",
                replacements=replacements,
            )
        )

    return ForwardConfig(
        dry_run=bool(raw.get("dry_run", True)),
        sources=sources,
        targets=targets,
    )


def load_secrets(env_path: str = ".env") -> Secrets:
    load_dotenv(env_path)

    def require(name: str) -> str:
        value = os.environ.get(name)
        if not value:
            raise ValueError(f"Missing required environment variable: {name}")
        return value

    return Secrets(
        tg_api_id=int(require("TG_API_ID")),
        tg_api_hash=require("TG_API_HASH"),
        tg_session_name=require("TG_SESSION_NAME"),
    )
