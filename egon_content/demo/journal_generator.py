"""Batch journal entry generation via the Claude API.

Generates realistic demo journal entries for a persona, one calendar month per API call.
Each entry includes a date, mood rating, energy level, tags, and prose body.
"""

import calendar
import json
import random
import zlib
from datetime import date
from typing import NamedTuple

import anthropic
from json_repair import repair_json

from egon_content.demo.personas import Persona


class EntryData(NamedTuple):
    date: date
    mood: str
    energy: str
    tags: list[str]
    body: str


_SYSTEM = """\
You are a realistic journaling assistant generating demo journal entries for a fictional persona.
Write in first person, as if you ARE the persona journaling about their actual day.
Do not mention that entries are fictional or generated.
Be specific, personal, and emotionally honest. Vary the tone, length, and mood across entries.
Use the persona's background to write consistent, believable entries.

Respond ONLY with a valid JSON array — no markdown fences, no extra text, just the JSON.
Each element must have exactly these fields:
  "date"   — ISO date string matching the dates provided (e.g. "2025-01-06")
  "mood"   — a short mood descriptor like "3/5 - tired but hopeful", "4/5 - calm", "2/5 - anxious"
  "energy" — one of: "very low", "low", "medium", "high", "very high"
  "tags"   — an array of 1-4 lowercase tag strings relevant to the entry
  "body"   — the journal entry prose (150-350 words, paragraphs separated by \\n\\n, all newlines escaped as \\n within the JSON string)

CRITICAL: The "body" value must be a valid JSON string. Escape all newlines as \\n — never include literal line breaks inside a JSON string value.
"""


def _month_seed(slug: str, year: int, month: int) -> int:
    """Stable seed per persona-month (Python's hash() of a str changes every run)."""
    return zlib.crc32(f"{slug}:{year}-{month:02d}".encode())


def _select_entry_dates(year: int, month: int, persona: Persona, seed: int) -> list[date]:
    """Deterministically select journaling days within the given month."""
    rng = random.Random(seed)
    _, last_day = calendar.monthrange(year, month)
    all_days = list(range(1, last_day + 1))
    n = round(persona.entry_days_per_week * last_day / 7)
    chosen = sorted(rng.sample(all_days, min(n, len(all_days))))
    return [date(year, month, d) for d in chosen]


def _build_user_prompt(persona: Persona, year: int, month: int, dates: list[date]) -> str:
    month_name = date(year, month, 1).strftime("%B %Y")
    date_list = "\n".join(f"  - {d.isoformat()}" for d in dates)
    return (
        f"Persona background:\n{persona.background}\n\n"
        f"Write journal entries for {month_name}.\n"
        f"Write one entry for each of these dates:\n{date_list}\n\n"
        f"Typical tags for this persona: {', '.join(persona.tags)}\n"
        f"Make the entries feel emotionally consistent with where this persona is in their story "
        f"during {month_name}. Let the emotional arc progress naturally.\n\n"
        f"Return a JSON array with one object per date, in the order listed."
    )


def _parse_response(raw: str, expected_dates: list[date]) -> list[EntryData]:
    """Parse the Claude JSON response into EntryData objects."""
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]

    try:
        items = json.loads(raw)
    except json.JSONDecodeError:
        items = json.loads(repair_json(raw))
    results: list[EntryData] = []
    date_set = {d.isoformat() for d in expected_dates}

    for item in items:
        date_str = item.get("date", "")
        if date_str not in date_set:
            continue
        try:
            entry_date = date.fromisoformat(date_str)
        except ValueError:
            continue
        results.append(
            EntryData(
                date=entry_date,
                mood=str(item.get("mood", "3/5")),
                energy=str(item.get("energy", "medium")),
                tags=[str(t) for t in item.get("tags", [])],
                body=str(item.get("body", "")),
            )
        )

    return sorted(results, key=lambda e: e.date)


def generate_month(
    client: anthropic.Anthropic,
    persona: Persona,
    year: int,
    month: int,
    model: str = "claude-sonnet-4-6",
) -> list[EntryData]:
    """Generate all journal entries for one calendar month of one persona."""
    dates = _select_entry_dates(year, month, persona, _month_seed(persona.slug, year, month))
    if not dates:
        return []

    prompt = _build_user_prompt(persona, year, month, dates)
    with client.messages.stream(
        model=model,
        max_tokens=32768,
        system=_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        message = stream.get_final_message()
    return _parse_response(message.content[0].text, dates)


def generate_persona_entries(
    client: anthropic.Anthropic,
    persona: Persona,
    start: date,
    end: date,
    model: str = "claude-sonnet-4-6",
) -> list[EntryData]:
    """Generate all journal entries for a persona across a date range."""
    entries: list[EntryData] = []

    year, month = start.year, start.month
    while (year, month) <= (end.year, end.month):
        month_entries = generate_month(client, persona, year, month, model)
        entries.extend(month_entries)

        month += 1
        if month > 12:
            month = 1
            year += 1

    return entries


def plan_persona_entries(persona: Persona, start: date, end: date) -> list[date]:
    """Return the list of dates that would be generated, without making API calls."""
    dates: list[date] = []
    year, month = start.year, start.month
    while (year, month) <= (end.year, end.month):
        dates.extend(
            _select_entry_dates(year, month, persona, _month_seed(persona.slug, year, month))
        )
        month += 1
        if month > 12:
            month = 1
            year += 1
    return dates
