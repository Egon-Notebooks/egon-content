"""
Synthetic Apple Health exports for demo personas.

The persona's own journal drives the data: the 1–5 mood rating in each entry's
frontmatter becomes a smoothed daily *wellbeing* score, and every health signal
moves with it the way research says it tends to — on better days people sleep
a little longer and more regularly, walk and exercise more, and show a lower
resting heart rate and higher HRV.  On top of that come realistic day-to-day
noise, weekend effects and missing data (the watch isn't worn every day).

The output is a standard ``export.xml`` that egon-journal reads like any real
export.  Generation is deterministic: the same journal and persona always give
the same file.

    from egon_content.demo.health import write_export
    write_export(persona, journal_dir, out_path, start, end)
"""

import random
import re
import zlib
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from statistics import mean
from xml.sax.saxutils import quoteattr

from egon_content.demo.personas import Persona

_MOOD_RE = re.compile(r'^mood:\s*"?\s*([1-5])', re.MULTILINE)
_DATE_RE = re.compile(r"^date:\s*(\d{4}-\d{2}-\d{2})", re.MULTILINE)

SOURCE = "Egon Demo Watch"
SLEEP_STAGES = [
    "HKCategoryValueSleepAnalysisAsleepCore",
    "HKCategoryValueSleepAnalysisAsleepDeep",
    "HKCategoryValueSleepAnalysisAsleepCore",
    "HKCategoryValueSleepAnalysisAsleepREM",
]


@dataclass(frozen=True)
class Record:
    type: str
    unit: str
    start: datetime
    end: datetime
    value: str


# ---------------------------------------------------------------------------
# Journal → daily wellbeing
# ---------------------------------------------------------------------------


def read_moods(journal_dir: Path) -> dict[date, int]:
    """The 1–5 mood rating per entry date, from journal frontmatter."""
    moods: dict[date, int] = {}
    for path in sorted(journal_dir.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        head = text.split("---", 2)[1] if text.startswith("---") else ""
        d, m = _DATE_RE.search(head), _MOOD_RE.search(head)
        if d and m:
            moods[date.fromisoformat(d.group(1))] = int(m.group(1))
    return moods


def daily_wellbeing(moods: dict[date, int], start: date, end: date) -> dict[date, float]:
    """A smooth daily score in [-1, 1] (0 = a 3/5 day), interpolated between entries."""
    if not moods:
        raise ValueError("No mood ratings found in the journal frontmatter.")
    known = sorted(moods.items())
    days = [start + timedelta(days=i) for i in range((end - start).days + 1)]

    raw: dict[date, float] = {}
    for d in days:
        before = [(k, v) for k, v in known if k <= d]
        after = [(k, v) for k, v in known if k >= d]
        if before and after:
            (d0, v0), (d1, v1) = before[-1], after[0]
            span = (d1 - d0).days
            v = v0 if span == 0 else v0 + (v1 - v0) * (d - d0).days / span
        else:
            v = (before or after)[-1 if before else 0][1]
        raw[d] = (v - 3) / 2

    # 7-day centered moving average: physiology follows weeks, not single entries.
    smooth = {}
    for i, d in enumerate(days):
        window = [raw[days[j]] for j in range(max(0, i - 3), min(len(days), i + 4))]
        smooth[d] = max(-1.0, min(1.0, mean(window)))
    return smooth


# ---------------------------------------------------------------------------
# Wellbeing → health records
# ---------------------------------------------------------------------------


def _at(d: date, hours: float) -> datetime:
    return datetime(d.year, d.month, d.day) + timedelta(hours=hours)


def generate_records(persona: Persona, wellbeing: dict[date, float]) -> list[Record]:
    h = persona.health
    rng = random.Random(zlib.crc32(persona.slug.encode()))
    records: list[Record] = []
    weight = h.weight_kg
    days = sorted(wellbeing)
    month_z = {d: mean(wellbeing[x] for x in days if abs((x - d).days) <= 15) for d in days}

    for d in days:
        z = wellbeing[d]
        weekend = d.weekday() >= 5
        wears_watch = rng.random() > 0.05

        # Sleep for the night ending on the morning of d.
        if wears_watch:
            asleep = h.sleep_h + 0.55 * z + (0.45 if weekend else 0) + rng.gauss(0, 0.45)
            asleep = max(4.0, min(10.0, asleep))
            onset = h.bedtime - 0.3 * z + (0.6 if weekend else 0)
            onset += rng.gauss(0, 0.3 + 0.45 * max(0.0, -z))  # irregular on low days
            t = _at(d - timedelta(days=1), 18 + onset)
            remaining = asleep
            for i, stage in enumerate(SLEEP_STAGES):
                part = remaining if i == len(SLEEP_STAGES) - 1 else asleep / len(SLEEP_STAGES)
                part_end = t + timedelta(hours=part)
                records.append(
                    Record("HKCategoryTypeIdentifierSleepAnalysis", "", t, part_end, stage)
                )
                remaining -= part
                t = part_end + timedelta(minutes=rng.randint(3, 15))  # brief awakenings

        # Heart: resting HR once a day, HRV a few times a day.
        if wears_watch:
            rhr = h.resting_hr - 2.5 * z + rng.gauss(0, 1.3)
            records.append(
                Record(
                    "HKQuantityTypeIdentifierRestingHeartRate",
                    "count/min",
                    _at(d, 7),
                    _at(d, 7.1),
                    f"{rhr:.0f}",
                )
            )
            for hour in (3, 9, 14, 20):
                hrv = h.hrv_ms * (1 + 0.18 * z) + rng.gauss(0, 0.15 * h.hrv_ms)
                records.append(
                    Record(
                        "HKQuantityTypeIdentifierHeartRateVariabilitySDNN",
                        "ms",
                        _at(d, hour),
                        _at(d, hour + 0.02),
                        f"{max(8.0, hrv):.1f}",
                    )
                )

        # Movement: steps from the phone even without the watch.
        weekday_factor = 0.85 if weekend else 1.05
        steps = h.steps * (1 + 0.3 * z) * weekday_factor * rng.lognormvariate(0, 0.25)
        chunks = [0.1, 0.2, 0.15, 0.2, 0.2, 0.15]
        for hour, share in zip((8, 10, 12, 14, 17, 19), chunks, strict=True):
            records.append(
                Record(
                    "HKQuantityTypeIdentifierStepCount",
                    "count",
                    _at(d, hour),
                    _at(d, hour + 1),
                    f"{max(0, round(steps * share))}",
                )
            )
        if wears_watch:
            exercise = h.exercise_min * (1 + 0.5 * z) + rng.gauss(0, 0.45 * h.exercise_min)
            if exercise > 1:
                records.append(
                    Record(
                        "HKQuantityTypeIdentifierAppleExerciseTime",
                        "min",
                        _at(d, 17.5),
                        _at(d, 17.5 + exercise / 60),
                        f"{exercise:.0f}",
                    )
                )

        # Body: slow weight drift (a little up in low stretches), occasional weigh-ins.
        weight += rng.gauss(0, 0.04) - 0.012 * z
        if rng.random() < h.weigh_ins_per_week / 7:
            measured = weight + rng.gauss(0, 0.25)
            records.append(
                Record(
                    "HKQuantityTypeIdentifierBodyMass",
                    "kg",
                    _at(d, 7.25),
                    _at(d, 7.25),
                    f"{measured:.1f}",
                )
            )
            if h.lean_mass_kg is not None:
                lean = h.lean_mass_kg + 0.25 * (weight - h.weight_kg) + rng.gauss(0, 0.2)
                records.append(
                    Record(
                        "HKQuantityTypeIdentifierLeanBodyMass",
                        "kg",
                        _at(d, 7.25),
                        _at(d, 7.25),
                        f"{lean:.1f}",
                    )
                )

        # Fitness: an occasional VO₂ max estimate after an outdoor walk.
        if wears_watch and rng.random() < 0.18:
            vo2 = h.vo2max + 0.8 * month_z[d] + rng.gauss(0, 0.35)
            records.append(
                Record(
                    "HKQuantityTypeIdentifierVO2Max",
                    "mL/min·kg",
                    _at(d, 18.5),
                    _at(d, 18.5),
                    f"{vo2:.1f}",
                )
            )
    return records


# ---------------------------------------------------------------------------
# XML
# ---------------------------------------------------------------------------


def _fmt(dt: datetime, tz: str) -> str:
    return f"{dt:%Y-%m-%d %H:%M:%S} {tz}"


def to_export_xml(persona: Persona, records: list[Record], tz: str = "+0000") -> str:
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f"<!-- Synthetic demo data for the fictional persona {persona.name} "
        f"({persona.archetype}), generated by egon-content. Not a real person. -->",
        '<HealthData locale="en_GB">',
    ]
    for r in records:
        unit = f" unit={quoteattr(r.unit)}" if r.unit else ""
        lines.append(
            f"  <Record type={quoteattr(r.type)} sourceName={quoteattr(SOURCE)}{unit} "
            f'creationDate="{_fmt(r.end, tz)}" startDate="{_fmt(r.start, tz)}" '
            f'endDate="{_fmt(r.end, tz)}" value={quoteattr(r.value)}/>'
        )
    lines.append("</HealthData>")
    return "\n".join(lines) + "\n"


def write_export(
    persona: Persona, journal_dir: Path, out_path: Path, start: date, end: date
) -> int:
    """Generate the persona's export.xml for [start, end]; returns the number of records."""
    wellbeing = daily_wellbeing(read_moods(journal_dir), start, end)
    records = generate_records(persona, wellbeing)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(to_export_xml(persona, records), encoding="utf-8")
    return len(records)
