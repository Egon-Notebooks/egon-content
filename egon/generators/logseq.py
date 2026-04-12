"""Logseq Markdown formatter.

Logseq uses property syntax (key:: value) for page metadata
and expects content in its outline (bullet-point) format.
"""

from datetime import date

from egon.generators import _to_filename


def format(
    topic: str,
    body: str,
    disclaimer: str,
    tags: list[str] | None = None,
    aliases: list[str] | None = None,
) -> tuple[str, str]:
    """Return (filename, markdown_content) for a Logseq page."""
    today = date.today().isoformat()
    filename = f"{_to_filename(topic)}.md"

    tags_value = ", ".join(tags) if tags else ""
    alias_line = f"alias:: {', '.join(aliases)}\n" if aliases else ""
    properties = f"author:: Claude\ndate:: {today}\ntags:: {tags_value}\n{alias_line}"

    bullet_paragraphs = "\n".join(
        f"- {para.strip()}" for para in body.strip().split("\n\n") if para.strip()
    )
    disclaimer_bullet = f"- {disclaimer}"

    content = f"{properties}\n{bullet_paragraphs}\n\n{disclaimer_bullet}\n"
    return filename, content
