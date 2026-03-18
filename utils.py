"""Shared utilities."""

from pathlib import Path


def parse_topics_file(path: Path) -> list[str]:
    """Parse a topics file and return a list of topic strings.

    File format:
    - One topic per line
    - Empty lines are ignored
    - Lines starting with '#' are treated as comments
    """
    if not path.exists():
        raise FileNotFoundError(f"Topics file not found: {path}")

    topics = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            topics.append(stripped)

    if not topics:
        raise ValueError(f"No topics found in '{path}'. Add one topic per line.")

    return topics
