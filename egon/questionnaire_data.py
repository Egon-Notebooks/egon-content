"""Clinically validated self-assessment questionnaire definitions.

All instruments included here are open-licence and may be reproduced freely.
Exact question wording is preserved — paraphrasing invalidates psychometrics.

Sources
-------
PHQ-9 / GAD-7  Spitzer, Kroenke et al. — public domain (Pfizer release)
WHO-5          WHO Regional Office for Europe, 1998 — freely available
PSS-10         Cohen, Kamarck & Mermelstein, 1983 — free for use (per Cohen)
RSES           Rosenberg, 1965 — public domain
BRS            Smith et al., 2008 — free for use
"""

from dataclasses import dataclass, field


@dataclass
class Question:
    text: str
    reversed: bool = False  # True for reverse-scored items


@dataclass
class ScoringBand:
    range_str: str  # e.g. "0–4"
    label: str  # e.g. "Minimal depression"


@dataclass
class Questionnaire:
    key: str
    title: str  # Node filename / display title
    abbreviation: str  # "PHQ-9"
    full_name: str  # "Patient Health Questionnaire-9"
    measures: str  # "depression"
    frequency_note: str  # "Recommended frequency: monthly"
    timeframe: str  # "Over the last 2 weeks..."
    instructions: str  # Additional instructions shown above the table
    scale_labels: list[tuple[int, str]]  # [(0, "Not at all"), ...]
    questions: list[Question]
    scoring_formula: str  # Plain-text description of how to score
    interpretation: list[ScoringBand]
    safe_messaging_note: str | None  # Shown at the bottom if present
    licence: str
    citation: str
    tags: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Instrument definitions
# ---------------------------------------------------------------------------

PHQ9 = Questionnaire(
    key="phq9",
    title="PHQ-9 Monthly Depression Check-in",
    abbreviation="PHQ-9",
    full_name="Patient Health Questionnaire-9",
    measures="depression",
    frequency_note="Recommended frequency: monthly, or whenever your mood has been noticeably low.",
    timeframe=(
        "Over the last 2 weeks, how often have you been bothered by any of the following problems?"
    ),
    instructions=(
        "For each item, choose the option that best describes how often you have experienced it."
    ),
    scale_labels=[
        (0, "Not at all"),
        (1, "Several days"),
        (2, "More than half the days"),
        (3, "Nearly every day"),
    ],
    questions=[
        Question("Little interest or pleasure in doing things"),
        Question("Feeling down, depressed, or hopeless"),
        Question("Trouble falling or staying asleep, or sleeping too much"),
        Question("Feeling tired or having little energy"),
        Question("Poor appetite or overeating"),
        Question(
            "Feeling bad about yourself — or that you are a failure or have let yourself"
            " or your family down"
        ),
        Question(
            "Trouble concentrating on things, such as reading the newspaper or watching television"
        ),
        Question(
            "Moving or speaking so slowly that other people could have noticed?"
            " Or the opposite — being so fidgety or restless that you have been moving"
            " around a lot more than usual"
        ),
        Question("Thoughts that you would be better off dead, or of hurting yourself in some way"),
    ],
    scoring_formula="Add the scores for all 9 items. Total range: 0–27.",
    interpretation=[
        ScoringBand("0–4", "Minimal depression"),
        ScoringBand("5–9", "Mild depression"),
        ScoringBand("10–14", "Moderate depression"),
        ScoringBand("15–19", "Moderately severe depression"),
        ScoringBand("20–27", "Severe depression"),
    ],
    safe_messaging_note=(
        "If you scored 1 or more on question 9 (thoughts of self-harm), "
        "please reach out to a mental health professional or a crisis support service."
    ),
    licence="Public domain. No permission required for use or reproduction.",
    citation=(
        "Kroenke K, Spitzer RL, Williams JB. "
        "The PHQ-9: validity of a brief depression severity measure. "
        "J Gen Intern Med. 2001;16(9):606–613."
    ),
    tags=["questionnaire", "depression", "self-assessment"],
)

GAD7 = Questionnaire(
    key="gad7",
    title="GAD-7 Monthly Anxiety Check-in",
    abbreviation="GAD-7",
    full_name="Generalized Anxiety Disorder-7",
    measures="generalized anxiety",
    frequency_note=(
        "Recommended frequency: monthly, or whenever anxiety has been noticeably elevated."
    ),
    timeframe="Over the last 2 weeks, how often have you been bothered by the following problems?",
    instructions=(
        "For each item, choose the option that best describes how often you have experienced it."
    ),
    scale_labels=[
        (0, "Not at all"),
        (1, "Several days"),
        (2, "More than half the days"),
        (3, "Nearly every day"),
    ],
    questions=[
        Question("Feeling nervous, anxious, or on edge"),
        Question("Not being able to stop or control worrying"),
        Question("Worrying too much about different things"),
        Question("Trouble relaxing"),
        Question("Being so restless that it is hard to sit still"),
        Question("Becoming easily annoyed or irritable"),
        Question("Feeling afraid, as if something awful might happen"),
    ],
    scoring_formula="Add the scores for all 7 items. Total range: 0–21.",
    interpretation=[
        ScoringBand("0–4", "Minimal anxiety"),
        ScoringBand("5–9", "Mild anxiety"),
        ScoringBand("10–14", "Moderate anxiety"),
        ScoringBand("15–21", "Severe anxiety"),
    ],
    safe_messaging_note=None,
    licence="Public domain. No permission required for use or reproduction.",
    citation=(
        "Spitzer RL, Kroenke K, Williams JB, Löwe B. "
        "A brief measure for assessing generalized anxiety disorder. "
        "Arch Intern Med. 2006;166(10):1092–1097."
    ),
    tags=["questionnaire", "anxiety", "self-assessment"],
)

WHO5 = Questionnaire(
    key="who5",
    title="WHO-5 Wellbeing Check-in",
    abbreviation="WHO-5",
    full_name="World Health Organization Five Well-Being Index",
    measures="subjective wellbeing",
    frequency_note="Recommended frequency: monthly.",
    timeframe="Over the last two weeks:",
    instructions=(
        "For each of the five statements, choose the response that best describes "
        "how you have been feeling."
    ),
    scale_labels=[
        (5, "All of the time"),
        (4, "Most of the time"),
        (3, "More than half of the time"),
        (2, "Less than half of the time"),
        (1, "Some of the time"),
        (0, "At no time"),
    ],
    questions=[
        Question("I have felt cheerful and in good spirits"),
        Question("I have felt calm and relaxed"),
        Question("I have felt active and vigorous"),
        Question("I woke up feeling fresh and rested"),
        Question("My daily life has been filled with things that interest me"),
    ],
    scoring_formula=(
        "Add the scores for all 5 items (raw score 0–25). "
        "Multiply by 4 to convert to a percentage score (0–100). "
        "A percentage score ≤ 50, or a raw score ≤ 12 on any item, suggests low wellbeing "
        "and possible depression — consider discussing with a professional."
    ),
    interpretation=[
        ScoringBand("0–50 %", "Low wellbeing — consider seeking support"),
        ScoringBand("51–67 %", "Below-average wellbeing"),
        ScoringBand("68–84 %", "Average wellbeing"),
        ScoringBand("85–100 %", "High wellbeing"),
    ],
    safe_messaging_note=None,
    licence=(
        "Freely available for use. Reproduced with permission from the "
        "WHO Regional Office for Europe."
    ),
    citation=(
        "World Health Organization. "
        "Wellbeing measures in primary health care: the DepCare project. "
        "WHO Regional Office for Europe, Copenhagen, 1998."
    ),
    tags=["questionnaire", "wellbeing", "self-assessment"],
)

PSS10 = Questionnaire(
    key="pss10",
    title="PSS-10 Monthly Stress Check-in",
    abbreviation="PSS-10",
    full_name="Perceived Stress Scale (10-item)",
    measures="perceived stress",
    frequency_note="Recommended frequency: monthly.",
    timeframe=(
        "The questions in this scale ask about your feelings and thoughts during the last month."
    ),
    instructions=(
        "For each question, indicate how often you felt or thought a certain way. "
        "Items marked (R) are reverse-scored — see the scoring note below."
    ),
    scale_labels=[
        (0, "Never"),
        (1, "Almost never"),
        (2, "Sometimes"),
        (3, "Fairly often"),
        (4, "Very often"),
    ],
    questions=[
        Question(
            "In the last month, how often have you been upset because of something"
            " that happened unexpectedly?"
        ),
        Question(
            "In the last month, how often have you felt that you were unable to control"
            " the important things in your life?"
        ),
        Question("In the last month, how often have you felt nervous and stressed?"),
        Question(
            "In the last month, how often have you felt confident about your ability"
            " to handle your personal problems?",
            reversed=True,
        ),
        Question(
            "In the last month, how often have you felt that things were going your way?",
            reversed=True,
        ),
        Question(
            "In the last month, how often have you found that you could not cope with"
            " all the things that you had to do?"
        ),
        Question(
            "In the last month, how often have you been able to control irritations in your life?",
            reversed=True,
        ),
        Question(
            "In the last month, how often have you felt that you were on top of things?",
            reversed=True,
        ),
        Question(
            "In the last month, how often have you been angered because of things"
            " that were outside of your control?"
        ),
        Question(
            "In the last month, how often have you felt difficulties were piling up so high"
            " that you could not overcome them?"
        ),
    ],
    scoring_formula=(
        "Items 4, 5, 7, and 8 are reverse-scored: replace 0→4, 1→3, 2→2, 3→1, 4→0. "
        "Add all 10 scores. Total range: 0–40. Higher scores indicate greater perceived stress."
    ),
    interpretation=[
        ScoringBand("0–13", "Low stress"),
        ScoringBand("14–26", "Moderate stress"),
        ScoringBand("27–40", "High perceived stress"),
    ],
    safe_messaging_note=None,
    licence=(
        "Free to use for non-commercial purposes. "
        "Permission granted by Sheldon Cohen (Carnegie Mellon University)."
    ),
    citation=(
        "Cohen S, Kamarck T, Mermelstein R. "
        "A global measure of perceived stress. "
        "J Health Soc Behav. 1983;24(4):385–396."
    ),
    tags=["questionnaire", "stress", "self-assessment"],
)

RSES = Questionnaire(
    key="rses",
    title="Rosenberg Self-Esteem Scale Check-in",
    abbreviation="RSES",
    full_name="Rosenberg Self-Esteem Scale",
    measures="global self-esteem",
    frequency_note="Recommended frequency: monthly or quarterly.",
    timeframe=(
        "Please read each statement and indicate how strongly you agree or disagree"
        " with it right now."
    ),
    instructions=("Items marked (R) are reverse-scored — see the scoring note below."),
    scale_labels=[
        (3, "Strongly agree"),
        (2, "Agree"),
        (1, "Disagree"),
        (0, "Strongly disagree"),
    ],
    questions=[
        Question("On the whole, I am satisfied with myself."),
        Question("At times, I think I am no good at all.", reversed=True),
        Question("I feel that I have a number of good qualities."),
        Question("I am able to do things as well as most other people."),
        Question("I feel I do not have much to be proud of.", reversed=True),
        Question("I certainly feel useless at times.", reversed=True),
        Question("I feel that I'm a person of worth, at least on an equal plane with others."),
        Question("I wish I could have more respect for myself.", reversed=True),
        Question("All in all, I am inclined to feel that I am a failure.", reversed=True),
        Question("I take a positive attitude toward myself."),
    ],
    scoring_formula=(
        "Items 2, 5, 6, 8, and 9 are reverse-scored: replace 0→3, 1→2, 2→1, 3→0. "
        "Add all 10 scores. Total range: 0–30."
    ),
    interpretation=[
        ScoringBand("0–14", "Low self-esteem"),
        ScoringBand("15–25", "Within the normal range"),
        ScoringBand("26–30", "High self-esteem"),
    ],
    safe_messaging_note=None,
    licence="Public domain.",
    citation=(
        "Rosenberg M. Society and the Adolescent Self-Image. Princeton University Press, 1965."
    ),
    tags=["questionnaire", "self-esteem", "self-assessment"],
)

BRS = Questionnaire(
    key="brs",
    title="Brief Resilience Scale Check-in",
    abbreviation="BRS",
    full_name="Brief Resilience Scale",
    measures="resilience — the ability to bounce back from stress",
    frequency_note="Recommended frequency: monthly or quarterly.",
    timeframe=(
        "Please indicate the extent to which you agree with each of the following statements."
    ),
    instructions=("Items marked (R) are reverse-scored — see the scoring note below."),
    scale_labels=[
        (1, "Strongly disagree"),
        (2, "Disagree"),
        (3, "Neutral"),
        (4, "Agree"),
        (5, "Strongly agree"),
    ],
    questions=[
        Question("I tend to bounce back quickly after hard times."),
        Question("I have a hard time making it through stressful events.", reversed=True),
        Question("It does not take me long to recover from a stressful event."),
        Question("It is hard for me to snap back when something bad happens.", reversed=True),
        Question("I usually come through difficult times with little trouble."),
        Question("I tend to take a long time to get over set-backs in my life.", reversed=True),
    ],
    scoring_formula=(
        "Items 2, 4, and 6 are reverse-scored: replace 1→5, 2→4, 3→3, 4→2, 5→1. "
        "Add all 6 scores and divide by 6 to get your average. Range: 1.00–5.00."
    ),
    interpretation=[
        ScoringBand("1.00–2.99", "Low resilience"),
        ScoringBand("3.00–4.30", "Normal resilience"),
        ScoringBand("4.31–5.00", "High resilience"),
    ],
    safe_messaging_note=None,
    licence="Free to use for non-commercial purposes.",
    citation=(
        "Smith BW, Dalen J, Wiggins K, Tooley E, Christopher P, Bernard J. "
        "The Brief Resilience Scale: assessing the ability to bounce back. "
        "Int J Behav Med. 2008;15(3):194–200."
    ),
    tags=["questionnaire", "resilience", "self-assessment"],
)

# Ordered list used by the CLI and formatter.
ALL_QUESTIONNAIRES: list[Questionnaire] = [PHQ9, GAD7, WHO5, PSS10, RSES, BRS]
