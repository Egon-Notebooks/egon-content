"""Demo personas for the journal generator."""

from dataclasses import dataclass, field


@dataclass
class Persona:
    slug: str
    name: str
    age: int
    occupation: str
    background: str
    entry_days_per_week: float = 4.5
    tags: list[str] = field(default_factory=list)


PERSONAS: list[Persona] = [
    Persona(
        slug="lena-fischer",
        name="Lena Fischer",
        age=29,
        occupation="UX Designer",
        entry_days_per_week=5.0,
        tags=["anxiety", "design", "social", "relocation", "mindfulness"],
        background="""You are writing the personal journal of Lena Fischer, a 29-year-old UX designer
who moved from Munich to Amsterdam six months ago for a new job at a mid-sized tech startup.

Personality and situation:
- Introverted but curious; enjoys solo cycling, visiting museums, and cooking
- Experiences mild-to-moderate social anxiety, especially in group settings and networking events
- Slowly building a social life in Amsterdam but still misses her close friends and family in Germany
- Works in a fast-paced startup where she has to collaborate closely with product managers and developers
- Started attending a weekly mindfulness class to manage anxiety
- Has a long-distance relationship with her partner Jonas, who is still in Munich
- Journaling is a way for her to process the day and check in with herself

Writing style:
- Thoughtful, introspective, sometimes self-critical
- Moves between German-influenced phrasing and English (she journals in English to practice)
- Honest about anxiety and loneliness without being dramatic
- Notes small wins and moments of beauty alongside hard days
- Mentions specific details: recipes she tried, books she's reading (currently Jan Gijsen, Ali Smith),
  coffee shops she discovered, video calls with Jonas, work challenges

Emotional arc across the year:
- January–March: adjustment blues, homesickness, some very anxious weeks at work
- April–May: starts feeling more settled, a few new friendships forming, relationship with Jonas strained by distance
- June–July: a visit from Jonas in June, summer energy, more social activity, anxiety more manageable
- August–September: Jonas and Lena agree to try couples therapy over video call; career is going well
- October–November: a difficult project deadline causes a stress spike; mindfulness practice deepens
- December: year-end reflection, genuine pride in how much she's grown, cautious optimism""",
    ),
    Persona(
        slug="marcus-webb",
        name="Marcus Webb",
        age=45,
        occupation="High School History Teacher",
        entry_days_per_week=4.0,
        tags=["depression", "divorce", "therapy", "teaching", "fatherhood", "recovery"],
        background="""You are writing the personal journal of Marcus Webb, a 45-year-old high school
history teacher in a mid-sized American city (Columbus, Ohio).

Personality and situation:
- Thoughtful, slightly old-fashioned, deeply committed to his students
- Going through a divorce from his wife Claire of 16 years; they separated last October
- Has two kids: Theo (14) and Mara (11), who live primarily with Claire; he has them every other weekend
- Was diagnosed with moderate depression following the separation and started seeing a therapist (Dr. Okonkwo) every two weeks
- Also began a low-dose antidepressant in February; cautiously adjusting to it
- Finds meaning in teaching but struggles with feeling like a failure at home
- Enjoys woodworking in his garage, listening to jazz, and running (training for a 10K)
- Journaling was recommended by Dr. Okonkwo as a way to track mood and process emotions

Writing style:
- Measured, sometimes dry humor; a reader's voice — references Steinbeck, Cormac McCarthy, historical events
- Honest but not self-pitying; sometimes more analytical than emotional
- Notes interactions with his kids with particular tenderness
- Mentions therapy sessions by reflection, not verbatim
- Writes on Sunday nights and some weekday mornings

Emotional arc across the year:
- January–February: at rock bottom; barely functional outside of work; starts therapy; medication begins
- March–April: very slowly stabilizing; first signs the antidepressant is working; a difficult conversation with Theo
- May–June: Mara's birthday weekend, a moment of genuine joy; finishes the 10K race
- July–August: summer is hard (less structure, less contact with kids); Theo comes to stay for 3 weeks
- September–October: back to school gives purpose; a breakthrough therapy session; starts woodworking again
- November–December: holidays are complicated; a tentative rapprochement with Claire; genuine gratitude by year end""",
    ),
    Persona(
        slug="priya-sharma",
        name="Priya Sharma",
        age=26,
        occupation="PhD Student (Neuroscience)",
        entry_days_per_week=5.0,
        tags=["anxiety", "perfectionism", "academia", "impostor-syndrome", "burnout", "meditation"],
        background="""You are writing the personal journal of Priya Sharma, a 26-year-old third-year
PhD student in computational neuroscience at University College London.

Personality and situation:
- Highly intelligent, driven, and deeply perfectionist; the first in her family to pursue a PhD
- Indian-British background; family in Leicester expects success and find it hard to understand PhD life
- Struggles significantly with impostor syndrome — despite strong results, constantly feels like a fraud
- Anxiety manifests as perfectionism, over-preparation, difficulty sleeping, and catastrophising
- Supervisor Prof. Hartmann is brilliant but demanding and sometimes dismissive
- Has a small but solid group of friends in her cohort, particularly her friend Sunita
- Started journaling after a panic attack in the lab in November of the previous year
- Attends a weekly 10-minute meditation app session; wants to do more
- Romantic life: recently ended a relationship with Dev, still processing the breakup

Writing style:
- Sharp, analytical, sometimes humorous; her journal is one of the few places she's not performing
- Can switch between nerdy technical excitement about her research and raw emotional honesty
- Lists things, uses parenthetical asides, mixes self-compassion attempts with self-criticism
- References scientific papers and podcasts she's consuming alongside personal reflections
- Sometimes writes at 11pm after a long day in the lab

Emotional arc across the year:
- January–February: crushing start to the year — a major model failure; Dev breakup; worst impostor syndrome
- March–April: a paper idea starts to click; small academic wins; begins seeing a university counsellor
- May–June: conference in Barcelona sparks excitement; reconnecting with why she loves neuroscience
- July–August: summer slump; isolation; difficult family visit; Sunita's support crucial
- September–October: paper submitted to a journal; high anxiety waiting for reviews; meditation practice grows
- November–December: paper accepted (with revisions); huge relief and pride; year-end with warmth and hope""",
    ),
    Persona(
        slug="david-osei",
        name="David Osei",
        age=58,
        occupation="Retired Hospital Administrator",
        entry_days_per_week=4.0,
        tags=["retirement", "loneliness", "grief", "purpose", "health", "family", "gardening"],
        background="""You are writing the personal journal of David Osei, a 58-year-old man who retired
six months ago after 30 years as a hospital administrator in Manchester, UK.

Personality and situation:
- Ghanaian-British; came to the UK at 22; enormously proud of the life he built
- Retired earlier than planned after a mild cardiac event last July — doctors said it was a warning
- Wife Abena (55) still works as a community nurse; children grown: Emmanuel (30) in London, Diana (27) in Ghana
- David is discovering that retirement is harder than expected: loss of identity, structure, and purpose
- Experiences loneliness during weekdays while Abena works; friends still mostly at work
- Has a lot of time to think — and sometimes ruminate — about mortality, legacy, and what comes next
- Newly interested in gardening (took over the back garden), and cooking West African food properly
- Started journaling at the suggestion of his cardiac rehabilitation nurse as part of recovery
- Attends a weekly cardiac rehab group where he's met a few interesting characters

Writing style:
- Warm, wise, occasionally wry; the voice of someone who has seen a lot in hospital settings
- Reflective and philosophical but also practical and grounded
- References his faith (Anglican Christian, but privately questioning)
- Notes things he's grateful for alongside honest accounts of hard days
- Sometimes wonders aloud about life's meaning; sometimes just writes about the garden or a good meal

Emotional arc across the year:
- January–February: the reality of retirement hits; more lonely than expected; heart health a source of worry
- March–April: spring energy; garden begins to bloom; connects with two other retired men from rehab
- May–June: Emmanuel visits from London for a long weekend; profound conversation about life and legacy
- July–August: anniversary of the cardiac event triggers anxiety and reflection; Abena and David go on holiday to Portugal
- September–October: finds a volunteering role mentoring young NHS administrators; sense of purpose starts returning
- November–December: first quiet Christmas since retirement; Diana calls from Ghana; genuine contentment""",
    ),
]

PERSONAS_BY_SLUG: dict[str, Persona] = {p.slug: p for p in PERSONAS}
