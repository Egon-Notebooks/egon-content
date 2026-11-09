def _to_filename(text: str) -> str:
    """Strip characters that are invalid in filenames; preserve spaces and case."""
    invalid = set(r'\/:*?"<>|' + "\x00")
    return "".join(c for c in text if c not in invalid).strip()
