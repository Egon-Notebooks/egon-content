"""Journal entry formatters for Obsidian and Logseq."""

from datetime import date as date_type


def format_obsidian(
    entry_date: date_type,
    body: str,
    mood: str,
    energy: str,
    tags: list[str],
) -> tuple[str, str]:
    """Return (filename, content) for an Obsidian journal entry.

    Matches the egon-journal frontmatter schema (type=journal, egon_version=1).
    """
    date_str = entry_date.strftime("%Y-%m-%d")
    filename = f"Journal — {date_str}.md"

    if tags:
        tags_yaml = "tags:\n" + "".join(f"  - {t}\n" for t in tags)
    else:
        tags_yaml = "tags: []\n"

    frontmatter = (
        "---\n"
        f'title: "Journal — {date_str}"\n'
        f"date: {date_str}\n"
        f"type: journal\n"
        f"{tags_yaml}"
        f'mood: "{mood}"\n'
        f'energy: "{energy}"\n'
        f'egon_version: "1"\n'
        "---\n"
    )

    content = f"{frontmatter}\n{body.strip()}\n"
    return filename, content


def format_logseq(
    entry_date: date_type,
    body: str,
    mood: str,
    energy: str,
    tags: list[str],
) -> tuple[str, str]:
    """Return (filename, content) for a Logseq journal entry.

    Logseq journal files use underscored dates and property:: value syntax.
    """
    date_str = entry_date.strftime("%Y-%m-%d")
    filename = entry_date.strftime("%Y_%m_%d") + ".md"

    tags_value = ", ".join(f"[[{t}]]" for t in tags) if tags else ""
    properties = f"date:: {date_str}\nmood:: {mood}\nenergy:: {energy}\n"
    if tags_value:
        properties += f"tags:: {tags_value}\n"

    bullet_paragraphs = "\n".join(
        f"- {para.strip()}" for para in body.strip().split("\n\n") if para.strip()
    )

    content = f"{properties}\n{bullet_paragraphs}\n"
    return filename, content
