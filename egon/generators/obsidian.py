"""Obsidian Markdown formatter.

Obsidian uses YAML frontmatter for metadata and prose paragraphs for content.
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
        f"author: Claude\n"
        f"date: {today}\n"
        f"{tags_yaml}"
        f"{aliases_yaml}"
        f"generated: true\n"
        "---\n"
    )

    content = f"{frontmatter}\n# {topic}\n\n{body.strip()}\n\n---\n\n{disclaimer}\n"
    return filename, content
