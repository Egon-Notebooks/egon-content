"""Logseq Markdown formatter.

Logseq uses property syntax (key:: value) for page metadata
and expects content in its outline (bullet-point) format.
"""

from datetime import date


def format(topic: str, body: str, disclaimer: str) -> tuple[str, str]:
    """Return (filename, markdown_content) for a Logseq page."""
    slug = _slugify(topic)
    today = date.today().isoformat()
    filename = f"{slug}.md"

    # Logseq properties block (no YAML fences — uses :: syntax)
    properties = (
        f"author:: Claude\n"
        f"date:: {today}\n"
        f"tags:: mental-health\n"
    )

    # Logseq body: each paragraph as a top-level bullet
    bullet_paragraphs = "\n".join(
        f"- {para.strip()}" for para in body.strip().split("\n\n") if para.strip()
    )
    disclaimer_bullet = f"- {disclaimer}"

    content = f"{properties}\n{bullet_paragraphs}\n\n{disclaimer_bullet}\n"
    return filename, content


def _slugify(text: str) -> str:
    import re
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)   # keep word chars, spaces, hyphens
    text = re.sub(r"[\s_]+", "-", text)    # spaces/underscores → hyphens
    text = re.sub(r"-+", "-", text)        # collapse consecutive hyphens
    return text.strip("-")
