"""Inline wikilink injection and alias definitions.

TOPIC_ALIASES is the single source of truth for node aliases.
It is used both to:
  - Inject [[...]] wikilinks into article bodies (apply_wikilinks)
  - Populate alias metadata in generated node files (get_aliases)
"""

import re


# Maps canonical topic title → list of aliases.
# Keep entries conservative: only add aliases that are a natural, unambiguous
# way to refer to that specific node. Omit entries with no clear aliases.
TOPIC_ALIASES: dict[str, list[str]] = {
    "Anger": ["angry"],
    "Fear": ["fearful"],
    "Sadness": ["sad"],
    "Shame and guilt": ["shame", "guilt"],
    "Joy and positive emotions": ["joy"],
    "Understanding anxiety": ["anxiety"],
    "Panic and panic attacks": ["panic attack"],
    "Social anxiety": ["social phobia"],
    "Understanding low mood": ["low mood"],
    "Understanding stress": ["stress"],
    "The stress response": ["stress response"],
    "Understanding grief": ["grief"],
    "Understanding trauma": ["trauma"],
    "Rumination and how to interrupt it": ["rumination"],
    "Attachment styles": ["attachment style"],
    "Loneliness and connection": ["loneliness"],
    "Setting healthy boundaries": ["boundaries"],
    "Building resilience": ["resilience"],
    "The inner critic": ["inner critic"],
    "Imposter syndrome": ["impostor syndrome"],
    "Perfectionism": ["perfectionist"],
    "Self-esteem and where it comes from": ["self-esteem"],
    "Body image and self-acceptance": ["body image"],
    "Sleep hygiene and mood": ["sleep hygiene"],
    "Post-traumatic growth": ["PTG"],
    "The Big Five personality traits": ["Big Five", "OCEAN"],
    "Extraversion and introversion": ["introversion", "extraversion", "introvert", "extrovert"],
    "Neuroticism and emotional stability": ["neuroticism"],
}


def get_aliases(topic: str) -> list[str]:
    """Return the alias list for a given topic title, or [] if none defined."""
    topic_lower = topic.lower()
    for key, aliases in TOPIC_ALIASES.items():
        if key.lower() == topic_lower:
            return aliases
    return []


def apply_wikilinks(body: str, all_topics: list[str], current_topic: str) -> str:
    """Return body with topic titles (and aliases) wrapped in [[...]].

    Matching is case-insensitive and whole-word. When the matched text differs
    in case from the canonical title, a piped link [[canonical|matched]] is used
    so the page resolves correctly while preserving the original display text.
    The current topic and its aliases are excluded to avoid self-links.
    """
    current_lower = current_topic.lower()
    current_aliases_lower = {a.lower() for a in get_aliases(current_topic)}

    # Build (phrase, canonical) pairs from aliases and topic titles.
    # Longer phrases first to prevent partial matches.
    candidates: list[tuple[str, str]] = []
    for canonical, aliases in TOPIC_ALIASES.items():
        if canonical.lower() == current_lower:
            continue
        for alias in aliases:
            if alias.lower() not in current_aliases_lower:
                candidates.append((alias, canonical))
    for topic in all_topics:
        if topic.lower() != current_lower:
            candidates.append((topic, topic))
    candidates.sort(key=lambda x: len(x[0]), reverse=True)

    # Collect all non-overlapping match spans.
    spans: list[tuple[int, int, str]] = []  # (start, end, replacement)

    for phrase, canonical in candidates:
        pattern = re.compile(r'\b' + re.escape(phrase) + r'\b', re.IGNORECASE)
        for m in pattern.finditer(body):
            start, end = m.start(), m.end()
            if any(s <= start < e or s < end <= e for s, e, _ in spans):
                continue
            matched = m.group(0)
            if matched == canonical:
                replacement = f'[[{matched}]]'
            else:
                replacement = f'[[{canonical}|{matched}]]'
            spans.append((start, end, replacement))

    if not spans:
        return body

    spans.sort(key=lambda x: x[0])
    parts: list[str] = []
    pos = 0
    for start, end, replacement in spans:
        parts.append(body[pos:start])
        parts.append(replacement)
        pos = end
    parts.append(body[pos:])
    return ''.join(parts)
