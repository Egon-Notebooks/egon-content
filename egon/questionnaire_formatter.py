"""Questionnaire template formatters for Obsidian and Logseq.

Generates app-native Markdown from structured Questionnaire objects.
The exact question wording from questionnaire_data.py is preserved verbatim.
"""

from egon.generators import _to_filename
from egon.questionnaire_data import Questionnaire


def _obsidian(q: Questionnaire) -> str:
    """Render a questionnaire as an Obsidian note with YAML frontmatter."""
    tags_yaml = "\n".join(f"  - {t}" for t in q.tags)
    reversed_nums = [str(i + 1) for i, question in enumerate(q.questions) if question.reversed]
    reversed_note = f"Reverse-scored items: {', '.join(reversed_nums)}. " if reversed_nums else ""

    # Scale header row
    scale_header = " | ".join(f"{score} — {label}" for score, label in q.scale_labels)
    scale_sep = " | ".join("---" for _ in q.scale_labels)

    # Question rows
    question_rows = []
    for i, question in enumerate(q.questions, start=1):
        marker = " *(R)*" if question.reversed else ""
        question_rows.append(f"| **{i}** | {question.text}{marker} | |")

    question_table = "\n".join(
        [
            f"| # | Question | {scale_header} | Score |",
            f"| --- | --- | {scale_sep} | --- |",
        ]
        + question_rows
    )

    # Interpretation table
    interp_rows = "\n".join(f"| {band.range_str} | {band.label} |" for band in q.interpretation)
    interp_table = f"| Score | Interpretation |\n| --- | --- |\n{interp_rows}"

    safe_note = f"\n> [!warning]\n> {q.safe_messaging_note}\n" if q.safe_messaging_note else ""

    return f"""---
title: "{q.title}"
type: questionnaire
questionnaire: {q.abbreviation}
measures: {q.measures}
tags:
{tags_yaml}
---

# {q.abbreviation} — {q.full_name}

*{q.frequency_note}*

---

**{q.timeframe}**

{q.instructions}

{question_table}

**Total score:**

---

## Scoring

{reversed_note}{q.scoring_formula}

## Interpretation

{interp_table}
{safe_note}
---

*{q.licence}*

*{q.citation}*
""".strip()


def _logseq(q: Questionnaire) -> str:
    """Render a questionnaire as a Logseq page with properties and bullet points."""
    tags_prop = ", ".join(q.tags)
    reversed_nums = [str(i + 1) for i, question in enumerate(q.questions) if question.reversed]
    reversed_note = f"Reverse-scored items: {', '.join(reversed_nums)}. " if reversed_nums else ""

    scale_inline = " | ".join(f"{score} = {label}" for score, label in q.scale_labels)

    question_bullets = []
    for i, question in enumerate(q.questions, start=1):
        marker = " *(R)*" if question.reversed else ""
        question_bullets.append(f"- **{i}.** {question.text}{marker}")
        question_bullets.append(f"\t- score-{i}:: ")

    interp_rows = "\n".join(f"\t- {band.range_str} — {band.label}" for band in q.interpretation)

    safe_note = f"- ⚠️ {q.safe_messaging_note}\n" if q.safe_messaging_note else ""

    questions_block = "\n".join(question_bullets)

    return f"""type:: questionnaire
questionnaire:: {q.abbreviation}
measures:: {q.measures}
tags:: {tags_prop}

- # {q.abbreviation} — {q.full_name}
- *{q.frequency_note}*
- ---
- **{q.timeframe}**
- *Scale: {scale_inline}*
- *{q.instructions}*
- ---
{questions_block}
- ---
- **Total score::**\u0020
- ---
- ## Scoring
- {reversed_note}{q.scoring_formula}
- ## Interpretation
{interp_rows}
{safe_note}- ---
- *{q.licence}*
- *{q.citation}*
""".strip()


def format_questionnaire(q: Questionnaire, app: str) -> tuple[str, str]:
    """Return (filename, content) for the given app ('obsidian' or 'logseq')."""
    filename = _to_filename(q.title) + ".md"
    if app == "obsidian":
        return filename, _obsidian(q)
    return filename, _logseq(q)
