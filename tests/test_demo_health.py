"""Tests for egon.demo.health — synthetic Apple Health exports for demo personas."""

import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import date, timedelta
from statistics import mean

import pytest

from egon_content.demo.health import (
    daily_wellbeing,
    generate_records,
    read_moods,
    to_export_xml,
    write_export,
)
from egon_content.demo.journal_generator import _month_seed
from egon_content.demo.personas import FLAGSHIP_SLUG, PERSONAS, PERSONAS_BY_SLUG

PERSONA = PERSONAS_BY_SLUG[FLAGSHIP_SLUG]
START, END = date(2025, 1, 1), date(2025, 3, 31)


def _journal(tmp_path, moods: dict[date, int]):
    d = tmp_path / "obsidian"
    d.mkdir()
    for day, m in moods.items():
        (d / f"Journal — {day}.md").write_text(
            f'---\ndate: {day}\ntype: journal\nmood: "{m}/5 - fine"\n---\n\nSome text.\n',
            encoding="utf-8",
        )
    return d


def _alternating_moods() -> dict[date, int]:
    # Two-week stretches of good (5) and bad (1) moods.
    moods = {}
    for i in range((END - START).days + 1):
        day = START + timedelta(days=i)
        if i % 2 == 0:
            moods[day] = 5 if (i // 14) % 2 == 0 else 1
    return moods


def test_every_persona_has_an_archetype_and_health_profile():
    archetypes = {p.archetype for p in PERSONAS}
    assert "Self-Directed Individual" in archetypes
    assert PERSONA.archetype == "Self-Directed Individual"
    assert all(p.health.resting_hr > 40 for p in PERSONAS)


def test_month_seed_is_stable():
    # Python's hash() of a str changes per process; the seed must not.
    assert _month_seed("david-osei", 2025, 1) == _month_seed("david-osei", 2025, 1)
    assert _month_seed("david-osei", 2025, 1) == 3510185138


def test_read_moods_and_interpolate(tmp_path):
    journal = _journal(tmp_path, {date(2025, 1, 1): 1, date(2025, 1, 11): 5})
    moods = read_moods(journal)
    assert moods == {date(2025, 1, 1): 1, date(2025, 1, 11): 5}
    wb = daily_wellbeing(moods, date(2025, 1, 1), date(2025, 1, 11))
    assert wb[date(2025, 1, 1)] < 0 < wb[date(2025, 1, 11)]
    assert all(-1 <= v <= 1 for v in wb.values())


def test_no_moods_raises():
    with pytest.raises(ValueError):
        daily_wellbeing({}, START, END)


def test_health_follows_wellbeing(tmp_path):
    wb = daily_wellbeing(read_moods(_journal(tmp_path, _alternating_moods())), START, END)
    records = generate_records(PERSONA, wb)
    steps: dict[date, float] = defaultdict(float)
    sleep: dict[date, float] = defaultdict(float)
    for r in records:
        if r.type.endswith("StepCount"):
            steps[r.start.date()] += float(r.value)
        elif r.type.endswith("SleepAnalysis"):
            sleep[r.end.date()] += (r.end - r.start).total_seconds() / 3600
    good = [d for d in wb if wb[d] > 0.5]
    bad = [d for d in wb if wb[d] < -0.5]
    assert mean(steps[d] for d in good) > mean(steps[d] for d in bad)
    assert mean(sleep[d] for d in good if d in sleep) > mean(sleep[d] for d in bad if d in sleep)


def test_export_is_deterministic_marked_and_well_formed(tmp_path):
    journal = _journal(tmp_path, _alternating_moods())
    a, b = tmp_path / "a.xml", tmp_path / "b.xml"
    n = write_export(PERSONA, journal, a, START, END)
    write_export(PERSONA, journal, b, START, END)
    assert a.read_bytes() == b.read_bytes()
    text = a.read_text(encoding="utf-8")
    assert "Synthetic demo data" in text[:500]  # egon-journal's demo-report requires this
    root = ET.fromstring(text.split("\n", 2)[2])  # skip XML declaration and comment
    types = {r.get("type") for r in root.iter("Record")}
    assert len(list(root.iter("Record"))) == n
    assert {
        "HKQuantityTypeIdentifierStepCount",
        "HKQuantityTypeIdentifierRestingHeartRate",
        "HKQuantityTypeIdentifierHeartRateVariabilitySDNN",
        "HKQuantityTypeIdentifierBodyMass",
        "HKCategoryTypeIdentifierSleepAnalysis",
    } <= types


def test_xml_escapes_values():
    from datetime import datetime

    from egon_content.demo.health import Record

    t = datetime(2025, 1, 1, 8)
    rec = Record("T", "u", t, t, 'a"<b>')
    assert "&lt;b&gt;" in to_export_xml(PERSONA, [rec])
