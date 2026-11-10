"""Obsidian Markdown formatter.

Obsidian uses YAML frontmatter for metadata and prose paragraphs for content.
"""

from datetime import date

from egon_content.generators import _to_filename
from egon_content.nodes import EGON_VERSION


def format(
    topic: str,
    body: str,
    disclaimer: str,
    tags: list[str] | None = None,
    aliases: list[str] | None = None,
    crisis_note: str | None = None,
) -> tuple[str, str]:
    """Return (filename, markdown_content) for an Obsidian note."""
    today = date.today().isoformat()
    filename = f"{_to_filename(topic)}.md"

    safe_title = topic.replace("\\", "\\\\").replace('"', '\\"')
    if tags:
        tags_yaml = "tags:\n" + "".join(f"  - {t}\n" for t in tags)
    else:
        tags_yaml = "tags: []\n"
    if aliases:
        aliases_yaml = "aliases:\n" + "".join(f"  - {a}\n" for a in aliases)
    else:
        aliases_yaml = ""
    frontmatter = (
        "---\n"
        f'title: "{safe_title}"\n'
        "type: article\n"
        f"author: Claude\n"
        f"date: {today}\n"
        f"{tags_yaml}"
        f"{aliases_yaml}"
        f"generated: true\n"
        f'egon_version: "{EGON_VERSION}"\n'
        "---\n"
    )

    crisis_block = f"{crisis_note}\n\n" if crisis_note else ""
    content = f"{frontmatter}\n# {topic}\n\n{crisis_block}{body.strip()}\n\n---\n\n{disclaimer}\n"
    return filename, content
