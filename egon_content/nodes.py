"""
The node format that egon-content writes (see docs/NODE_SPEC.md).

egon-content writes egon_version "1" and reads nothing older: `upgrade-nodes`
brings nodes from before v0.3 up to "1".
"""

from __future__ import annotations

import re
from datetime import date

EGON_VERSION = "1"

_PIPED_LINK = re.compile(r"\[\[([^\]|]+)\|([^\]]+)\]\]")


def to_logseq_links(text: str) -> str:
    """Rewrite Obsidian-style [[page|text]] links into Logseq's [text]([[page]])."""
    return _PIPED_LINK.sub(r"[\2]([[\1]])", text)


def upgrade_node(text: str, app: str) -> str:
    """Add the type, egon_version and (for questionnaires) date fields a node lacks."""
    if app == "logseq":
        return _upgrade_logseq(text)
    return _upgrade_obsidian(text)


def _upgrade_obsidian(text: str) -> str:
    if not text.startswith("---\n"):
        return text
    end = text.index("\n---\n", 4)
    front, rest = text[4:end], text[end:]
    added = []
    if not re.search(r"^type:", front, re.M):
        added.append("type: article")
    if not re.search(r"^date:", front, re.M):
        added.append(f"date: {date.today().isoformat()}")
    if not re.search(r"^egon_version:", front, re.M):
        added.append(f'egon_version: "{EGON_VERSION}"')
    if not added:
        return text
    return "---\n" + front + "\n" + "\n".join(added) + rest


def _upgrade_logseq(text: str) -> str:
    lines = text.split("\n")
    props_end = next((i for i, line in enumerate(lines) if not re.match(r"^[a-z_-]+:: ", line)), 0)
    props = lines[:props_end]
    if not any(p.startswith("type:: ") for p in props):
        props.append("type:: article")
    if not any(p.startswith("egon_version:: ") for p in props):
        props.append(f"egon_version:: {EGON_VERSION}")
    return to_logseq_links("\n".join(props + lines[props_end:]))
