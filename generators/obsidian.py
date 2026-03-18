"""Obsidian Markdown formatter.

Obsidian uses YAML frontmatter for metadata and prose paragraphs for content.
"""

from datetime import date


def format(
    topic: str,
    body: str,
    disclaimer: str,
    image_filename: str | None = None,
) -> tuple[str, str]:
    """Return (filename, markdown_content) for an Obsidian note."""
    slug = _slugify(topic)
    today = date.today().isoformat()
    filename = f"{slug}.md"

    safe_title = topic.replace("\\", "\\\\").replace('"', '\\"')
    frontmatter = (
        "---\n"
        f"title: \"{safe_title}\"\n"
        f"author: Claude\n"
        f"date: {today}\n"
        f"tags:\n"
        f"  - mental-health\n"
        f"generated: true\n"
        "---\n"
    )

    image_block = f"![{topic}](images/{image_filename})\n\n" if image_filename else ""

    content = (
        f"{frontmatter}\n"
        f"# {topic}\n\n"
        f"{image_block}"
        f"{body.strip()}\n\n"
        f"---\n\n"
        f"{disclaimer}\n"
    )
    return filename, content


def _slugify(text: str) -> str:
    import re
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)   # keep word chars, spaces, hyphens
    text = re.sub(r"[\s_]+", "-", text)    # spaces/underscores → hyphens
    text = re.sub(r"-+", "-", text)        # collapse consecutive hyphens
    return text.strip("-")
