"""Logseq Markdown formatter.

Logseq uses property syntax (key:: value) for page metadata
and expects content in its outline (bullet-point) format.
"""

from datetime import date

from egon_content.generators import _to_filename
from egon_content.nodes import EGON_VERSION, to_logseq_links


def format(
    topic: str,
    body: str,
    disclaimer: str,
    tags: list[str] | None = None,
    aliases: list[str] | None = None,
    crisis_note: str | None = None,
) -> tuple[str, str]:
    """Return (filename, markdown_content) for a Logseq page."""
    today = date.today().isoformat()
    filename = f"{_to_filename(topic)}.md"

    tags_value = ", ".join(tags) if tags else ""
    alias_line = f"alias:: {', '.join(aliases)}\n" if aliases else ""
    properties = (
        f"type:: article\nauthor:: Claude\ndate:: {today}\ntags:: {tags_value}\n{alias_line}"
        f"egon_version:: {EGON_VERSION}\n"
    )

    bullet_paragraphs = "\n".join(
        f"- {para.strip()}" for para in to_logseq_links(body).strip().split("\n\n") if para.strip()
    )
    if crisis_note:
        bullet_paragraphs = f"- {crisis_note}\n{bullet_paragraphs}"
    disclaimer_bullet = f"- {disclaimer}"

    content = f"{properties}\n{bullet_paragraphs}\n\n{disclaimer_bullet}\n"
    return filename, content
