"""egon: Mental health Markdown node generator.

Usage examples:
    uv run egon generate --app obsidian --topic "managing social anxiety"
    uv run egon generate --app logseq --topic "Joy"
    uv run egon generate --app obsidian --topic "Joy" --no-image
    uv run egon pack --app obsidian --pack anxiety-and-worry
    uv run egon generate-all --app obsidian
    uv run egon list-packs
    uv run egon illustrate --description "a lighthouse in a storm"
    uv run egon illustrate --description "brain with interconnected nodes" --size square --quality hd
    uv run egon illustrate --description "calm ocean at dawn" --output my_image.webp
"""

import os
import re
from datetime import datetime
from enum import Enum
from pathlib import Path

import anthropic
import typer
from dotenv import load_dotenv
from openai import OpenAIError

from egon.demo.journal_generator import generate_persona_entries, plan_persona_entries
from egon.demo.personas import PERSONAS, PERSONAS_BY_SLUG
from egon.generators import logseq, obsidian
from egon.generators.journal_entry import format_logseq, format_obsidian
from egon.graph import (
    build_graph,
    compute_report,
    format_report,
    plot_graph,
    save_graph_data,
    save_report,
)
from egon.image_generator import generate_illustration, generate_image
from egon.linker import apply_wikilinks, get_aliases
from egon.packs import BASE_PACKS, PACKS
from egon.prompts import DISCLAIMER, SYSTEM_PROMPT, build_user_prompt, parse_response
from egon.questionnaire_data import ALL_QUESTIONNAIRES
from egon.questionnaire_formatter import format_questionnaire

load_dotenv()

app = typer.Typer(help="Generate mental health Markdown articles for Logseq or Obsidian.")

OUTPUT_ROOT = Path(__file__).parent.parent / "generated_content"

MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 1024

# Image output subdirectory per app — these must match the relative paths
# embedded in the Markdown by each formatter.
IMAGE_SUBDIR = {
    "obsidian": "images",  # referenced as images/<slug>.webp in the note
    "logseq": "assets",  # referenced as ../assets/<slug>.webp from pages/
}


class App(str, Enum):
    logseq = "logseq"
    obsidian = "obsidian"


def _get_client() -> anthropic.Anthropic:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        typer.echo("Error: ANTHROPIC_API_KEY is not set. Add it to your .env file.", err=True)
        raise typer.Exit(code=1)
    return anthropic.Anthropic(api_key=api_key)


def _generate_body(client: anthropic.Anthropic, topic: str) -> tuple[str, list[str]]:
    try:
        message = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": build_user_prompt(topic)}],
        )
    except anthropic.RateLimitError:
        typer.echo("Error: API rate limit reached. Wait a moment and try again.", err=True)
        raise typer.Exit(code=1)
    except anthropic.AuthenticationError:
        typer.echo("Error: Invalid API key. Check ANTHROPIC_API_KEY in your .env file.", err=True)
        raise typer.Exit(code=1)
    except anthropic.APIConnectionError:
        typer.echo(
            "Error: Could not reach the Anthropic API. Check your internet connection.",
            err=True,
        )
        raise typer.Exit(code=1)
    except anthropic.APIError as e:
        typer.echo(f"Error: API request failed — {e}", err=True)
        raise typer.Exit(code=1)
    return parse_response(message.content[0].text)


def _generate_and_save(
    client: anthropic.Anthropic,
    app_name: App,
    topic: str,
    with_image: bool = True,
    dry_run: bool = False,
) -> Path | None:
    formatter = logseq if app_name == App.logseq else obsidian
    filename, _ = formatter.format(topic, "", "")
    slug = filename.removesuffix(".md")
    output_path = OUTPUT_ROOT / app_name.value / "nodes" / filename

    if dry_run:
        status = "(exists)" if output_path.exists() else "(new)"
        typer.echo(f"  [dry-run] {filename} {status}")
        return None

    if output_path.exists():
        overwrite = typer.confirm(f"'{filename}' already exists. Overwrite?", default=True)
        if not overwrite:
            typer.echo("  Skipped.")
            return None

    all_topics = [t for topics in PACKS.values() for t in topics]
    typer.echo(f"Generating article: {topic!r} ...")
    body, tags = _generate_body(client, topic)
    body = apply_wikilinks(body, all_topics, topic)

    image_filename: str | None = None
    if with_image:
        typer.echo("  Generating image ...")
        image_filename = f"{slug}.webp"
        image_path = OUTPUT_ROOT / app_name.value / IMAGE_SUBDIR[app_name.value] / image_filename
        try:
            generate_image(topic, image_path)
            typer.echo(f"  Image saved -> {image_path}")
        except EnvironmentError as e:
            typer.echo(f"  Warning: {e} Skipping image.", err=True)
            image_filename = None
        except OpenAIError as e:
            typer.echo(f"  Warning: Image generation failed — {e}. Skipping image.", err=True)
            image_filename = None

    _, content = formatter.format(topic, body, DISCLAIMER, tags, get_aliases(topic))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")
    typer.echo(f"  Article saved -> {output_path}")
    return output_path


@app.command()
def generate(
    app_name: App = typer.Option(..., "--app", help="Target app: logseq or obsidian"),
    topic: str = typer.Option(..., "--topic", help="The mental health topic to write about"),
    with_image: bool = typer.Option(True, "--image/--no-image", help="Generate an illustration"),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Preview what would be generated without making API calls"
    ),
) -> None:
    """Generate a single article for a given topic."""
    client = _get_client()
    _generate_and_save(client, app_name, topic, with_image, dry_run)


@app.command()
def pack(
    app_name: App = typer.Option(..., "--app", help="Target app: logseq or obsidian"),
    pack_name: str = typer.Option(..., "--pack", help="Name of the topic pack to generate"),
    with_image: bool = typer.Option(
        True, "--image/--no-image", help="Generate an illustration per article"
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Preview what would be generated without making API calls"
    ),
) -> None:
    """Generate all articles in a named topic pack."""
    if pack_name not in PACKS:
        available = ", ".join(PACKS.keys())
        typer.echo(f"Error: Unknown pack '{pack_name}'. Available packs: {available}", err=True)
        raise typer.Exit(code=1)

    topics = PACKS[pack_name]
    typer.echo(f"Generating pack '{pack_name}' ({len(topics)} topics) for {app_name.value} ...\n")
    client = _get_client()
    for topic in topics:
        _generate_and_save(client, app_name, topic, with_image, dry_run)
    typer.echo(f"\nDone. {len(topics)} articles written to {OUTPUT_ROOT / app_name.value}")


@app.command(name="generate-all")
def generate_all(
    app_name: App = typer.Option(..., "--app", help="Target app: logseq or obsidian"),
    with_image: bool = typer.Option(
        True, "--image/--no-image", help="Generate an illustration per article"
    ),
    all_packs: bool = typer.Option(
        False, "--all-packs", help="Include supplementary packs, not just the base graph"
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Preview what would be generated without making API calls"
    ),
) -> None:
    """Generate the base graph — or all packs with --all-packs."""
    packs_to_run = PACKS if all_packs else {k: v for k, v in PACKS.items() if k in BASE_PACKS}
    label = "all packs" if all_packs else "base graph"
    total_topics = sum(len(topics) for topics in packs_to_run.values())
    typer.echo(
        f"Generating {label} ({len(packs_to_run)} packs, {total_topics} topics)"
        f" for {app_name.value} ...\n"
    )
    client = _get_client()
    for pack_name, topics in packs_to_run.items():
        typer.echo(f"--- Pack: {pack_name} ---")
        for topic in topics:
            _generate_and_save(client, app_name, topic, with_image, dry_run)
        typer.echo()
    typer.echo(f"Done. {total_topics} articles written to {OUTPUT_ROOT / app_name.value}")


@app.command(name="graph-report")
def graph_report(
    app_name: App = typer.Option(..., "--app", help="Target app: logseq or obsidian"),
) -> None:
    """Analyze the generated node graph and print structural metrics."""
    nodes_dir = OUTPUT_ROOT / app_name.value / "nodes"
    if not nodes_dir.exists() or not any(nodes_dir.glob("*.md")):
        typer.echo(f"No nodes found in {nodes_dir}. Generate some content first.", err=True)
        raise typer.Exit(code=1)
    graph = build_graph(nodes_dir)
    report = compute_report(graph)
    text = format_report(report)
    typer.echo(text)

    out_dir = OUTPUT_ROOT / app_name.value
    report_path = out_dir / "graph-report.txt"
    data_path = out_dir / "graph-data.txt"
    plot_path = out_dir / "graph-plot.png"

    save_report(report, report_path)
    typer.echo(f"\nReport saved -> {report_path}")

    save_graph_data(graph, data_path)
    typer.echo(f"Data saved   -> {data_path}")

    plot_graph(graph, plot_path)
    typer.echo(f"Plot saved   -> {plot_path}")


@app.command(name="install-questionnaires")
def install_questionnaires(
    app_name: App = typer.Option(..., "--app", help="Target app: logseq or obsidian"),
) -> None:
    """Write clinically validated questionnaire templates to the nodes directory.

    These are static templates — no API call is made. Each questionnaire is
    written verbatim from its validated source; question wording is never altered.
    """
    nodes_dir = OUTPUT_ROOT / app_name.value / "nodes"
    nodes_dir.mkdir(parents=True, exist_ok=True)

    for q in ALL_QUESTIONNAIRES:
        filename, content = format_questionnaire(q, app_name.value)
        dest = nodes_dir / filename
        if dest.exists():
            typer.echo(f"  [exists]  {filename}")
        else:
            dest.write_text(content, encoding="utf-8")
            typer.echo(f"  [written] {filename}")

    typer.echo(f"\n{len(ALL_QUESTIONNAIRES)} questionnaire templates written to {nodes_dir}")


@app.command()
def illustrate(
    description: str = typer.Option(
        ..., "--description", "-d", help="Short description of the image to generate"
    ),
    size: str = typer.Option(
        "landscape",
        "--size",
        help="Image dimensions: 'landscape' (1792x1024), 'square' (1024x1024), or 'portrait' (1024x1792)",
    ),
    quality: str = typer.Option(
        "medium", "--quality", help="Image quality: 'low', 'medium', 'high', or 'auto'"
    ),
    output: Path = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file path (default: generated_content/illustrations/<slug>_<timestamp>.webp)",
    ),
) -> None:
    """Generate a pencil-sketch illustration from a short description.

    The style is fixed as a hand-drawn pencil sketch. Edit prompts/pencil_style.txt
    to tweak the style without touching code.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        typer.echo("Error: OPENAI_API_KEY is not set. Add it to your .env file.", err=True)
        raise typer.Exit(code=1)

    if output is None:
        slug = re.sub(r"[^a-z0-9]+", "-", description.lower()).strip("-")[:50]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output = OUTPUT_ROOT / "illustrations" / f"{slug}_{timestamp}.webp"

    typer.echo(f"Generating pencil illustration: {description!r} ...")
    try:
        generate_illustration(description, output, size=size, quality=quality)
    except ValueError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)
    except EnvironmentError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)
    except OpenAIError as e:
        typer.echo(f"Error: Image generation failed — {e}", err=True)
        raise typer.Exit(code=1)

    typer.echo(f"Illustration saved -> {output}")


@app.command(name="demo-journals")
def demo_journals(
    app_name: App = typer.Option(..., "--app", help="Target app: logseq or obsidian"),
    persona_slug: str = typer.Option(
        None, "--persona", help="Generate only one persona by slug (default: all personas)"
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Preview filenames without making API calls"
    ),
) -> None:
    """Generate a year of demo journal entries for fictional personas.

    Writes one vault per persona under generated_content/demo/<persona-slug>/<app>/.
    Each persona has ~200 entries across 2025, written by Claude in a consistent voice.

    Available persona slugs: lena-fischer, marcus-webb, priya-sharma, david-osei
    """
    from datetime import date

    start = date(2025, 1, 1)
    end = date(2025, 12, 31)

    personas = PERSONAS
    if persona_slug:
        if persona_slug not in PERSONAS_BY_SLUG:
            available = ", ".join(p.slug for p in PERSONAS)
            typer.echo(f"Error: Unknown persona '{persona_slug}'. Available: {available}", err=True)
            raise typer.Exit(code=1)
        personas = [PERSONAS_BY_SLUG[persona_slug]]

    if dry_run:
        for persona in personas:
            dates = plan_persona_entries(persona, start, end)
            typer.echo(f"\nPersona: {persona.name} ({persona.slug}) — {len(dates)} entries")
            for d in dates:
                if app_name == App.obsidian:
                    filename = f"Journal — {d.strftime('%Y-%m-%d')}.md"
                    path = OUTPUT_ROOT / "demo" / persona.slug / "obsidian" / filename
                else:
                    filename = d.strftime("%Y_%m_%d") + ".md"
                    path = OUTPUT_ROOT / "demo" / persona.slug / "logseq" / "journals" / filename
                status = "(exists)" if path.exists() else "(new)"
                typer.echo(f"  [dry-run] {path.relative_to(OUTPUT_ROOT)} {status}")
        return

    client = _get_client()
    formatter = format_obsidian if app_name == App.obsidian else format_logseq

    for persona in personas:
        typer.echo(f"\nGenerating journal for {persona.name} ({persona.slug}) ...")

        if app_name == App.obsidian:
            out_dir = OUTPUT_ROOT / "demo" / persona.slug / "obsidian"
        else:
            out_dir = OUTPUT_ROOT / "demo" / persona.slug / "logseq" / "journals"
        out_dir.mkdir(parents=True, exist_ok=True)

        try:
            entries = generate_persona_entries(client, persona, start, end)
        except anthropic.RateLimitError:
            typer.echo("Error: API rate limit reached. Wait a moment and try again.", err=True)
            raise typer.Exit(code=1)
        except anthropic.AuthenticationError:
            typer.echo(
                "Error: Invalid API key. Check ANTHROPIC_API_KEY in your .env file.", err=True
            )
            raise typer.Exit(code=1)
        except anthropic.APIError as e:
            typer.echo(f"Error: API request failed — {e}", err=True)
            raise typer.Exit(code=1)

        written = 0
        skipped = 0
        for entry in entries:
            filename, content = formatter(
                entry.date, entry.body, entry.mood, entry.energy, entry.tags
            )
            dest = out_dir / filename
            if dest.exists():
                skipped += 1
                continue
            dest.write_text(content, encoding="utf-8")
            written += 1

        typer.echo(f"  {written} entries written, {skipped} skipped (already exist) -> {out_dir}")

    typer.echo(f"\nDone. Demo journals saved to {OUTPUT_ROOT / 'demo'}")


@app.command(name="demo-health")
def demo_health(
    persona_slug: str = typer.Option(
        None, "--persona", help="Generate only one persona by slug (default: all personas)"
    ),
    year: int = typer.Option(2025, "--year", help="Calendar year to generate"),
) -> None:
    """Generate a synthetic Apple Health export for demo personas.

    Daily health data follows the mood in each persona's journal (run demo-journals first),
    so sleep, heart rate and activity move plausibly with how they feel. Deterministic: the
    same journal always gives the same export.xml, written to
    generated_content/demo/<persona-slug>/apple_health_export/export.xml.
    """
    from datetime import date

    from egon.demo.health import write_export

    personas = PERSONAS
    if persona_slug:
        if persona_slug not in PERSONAS_BY_SLUG:
            available = ", ".join(p.slug for p in PERSONAS)
            typer.echo(f"Error: Unknown persona '{persona_slug}'. Available: {available}", err=True)
            raise typer.Exit(code=1)
        personas = [PERSONAS_BY_SLUG[persona_slug]]

    for persona in personas:
        journal_dir = OUTPUT_ROOT / "demo" / persona.slug / "obsidian"
        if not any(journal_dir.glob("*.md")):
            typer.echo(
                f"  – {persona.slug}: no journal entries in {journal_dir} (run demo-journals)"
            )
            continue
        out = OUTPUT_ROOT / "demo" / persona.slug / "apple_health_export" / "export.xml"
        n = write_export(persona, journal_dir, out, date(year, 1, 1), date(year, 12, 31))
        typer.echo(f"  ✓ {persona.slug:<14} {n:,} records -> {out.relative_to(OUTPUT_ROOT)}")


@app.command(name="list-packs")
def list_packs() -> None:
    """List all available topic packs and their topics."""
    typer.echo("Base graph packs:\n")
    for pack_name, topics in PACKS.items():
        if pack_name not in BASE_PACKS:
            continue
        typer.echo(f"  {pack_name}")
        for topic in topics:
            typer.echo(f"    - {topic}")
        typer.echo()
    typer.echo("Supplementary packs:\n")
    for pack_name, topics in PACKS.items():
        if pack_name in BASE_PACKS:
            continue
        typer.echo(f"  {pack_name}")
        for topic in topics:
            typer.echo(f"    - {topic}")
        typer.echo()
