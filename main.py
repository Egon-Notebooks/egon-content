"""egon-content: Mental health Markdown page generator.

Usage examples:
    uv run main.py generate --app obsidian --topic "managing social anxiety"
    uv run main.py generate --app logseq --topic "Joy"
    uv run main.py generate --app obsidian --topic "Joy" --no-image
    uv run main.py pack --app obsidian --pack basic-emotions
    uv run main.py from-file --app obsidian --file my-topics.txt
    uv run main.py list-packs
"""

import os
from pathlib import Path
from enum import Enum

import anthropic
import typer
from dotenv import load_dotenv
from openai import OpenAIError

from generators import logseq, obsidian
from image_generator import generate_image
from packs import PACKS
from prompts import DISCLAIMER, SYSTEM_PROMPT, build_user_prompt
from utils import parse_topics_file

load_dotenv()

app = typer.Typer(help="Generate mental health Markdown articles for Logseq or Obsidian.")

OUTPUT_ROOT = Path(__file__).parent / "generated_content"

MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 1024

# Image output subdirectory per app — these must match the relative paths
# embedded in the Markdown by each formatter.
IMAGE_SUBDIR = {
    "obsidian": "images",   # referenced as images/<slug>.png in the note
    "logseq": "assets",     # referenced as ../assets/<slug>.png from pages/
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


def _generate_body(client: anthropic.Anthropic, topic: str) -> str:
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
        typer.echo("Error: Could not reach the Anthropic API. Check your internet connection.", err=True)
        raise typer.Exit(code=1)
    except anthropic.APIError as e:
        typer.echo(f"Error: API request failed — {e}", err=True)
        raise typer.Exit(code=1)
    return message.content[0].text


def _generate_and_save(
    client: anthropic.Anthropic,
    app_name: App,
    topic: str,
    with_image: bool = True,
) -> Path | None:
    formatter = logseq if app_name == App.logseq else obsidian
    filename, _ = formatter.format(topic, "", "")
    slug = filename.removesuffix(".md")
    output_path = OUTPUT_ROOT / app_name.value / filename

    if output_path.exists():
        overwrite = typer.confirm(f"'{filename}' already exists. Overwrite?", default=True)
        if not overwrite:
            typer.echo("  Skipped.")
            return None

    typer.echo(f"Generating article: {topic!r} ...")
    body = _generate_body(client, topic)

    image_filename: str | None = None
    if with_image:
        typer.echo(f"  Generating image ...")
        image_filename = f"{slug}.png"
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

    _, content = formatter.format(topic, body, DISCLAIMER, image_filename)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")
    typer.echo(f"  Article saved -> {output_path}")
    return output_path


@app.command()
def generate(
    app_name: App = typer.Option(..., "--app", help="Target app: logseq or obsidian"),
    topic: str = typer.Option(..., "--topic", help="The mental health topic to write about"),
    with_image: bool = typer.Option(True, "--image/--no-image", help="Generate an illustration"),
) -> None:
    """Generate a single article for a given topic."""
    client = _get_client()
    _generate_and_save(client, app_name, topic, with_image)


@app.command()
def pack(
    app_name: App = typer.Option(..., "--app", help="Target app: logseq or obsidian"),
    pack_name: str = typer.Option(..., "--pack", help="Name of the topic pack to generate"),
    with_image: bool = typer.Option(True, "--image/--no-image", help="Generate an illustration per article"),
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
        _generate_and_save(client, app_name, topic, with_image)
    typer.echo(f"\nDone. {len(topics)} articles written to {OUTPUT_ROOT / app_name.value}")


@app.command(name="from-file")
def from_file(
    app_name: App = typer.Option(..., "--app", help="Target app: logseq or obsidian"),
    file: Path = typer.Option(..., "--file", help="Path to a topics file (one topic per line)"),
    with_image: bool = typer.Option(True, "--image/--no-image", help="Generate an illustration per article"),
) -> None:
    """Generate articles for all topics listed in a file."""
    try:
        topics = parse_topics_file(file)
    except FileNotFoundError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)
    except ValueError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)

    typer.echo(f"Found {len(topics)} topics in '{file}'. Generating for {app_name.value} ...\n")
    client = _get_client()
    for topic in topics:
        _generate_and_save(client, app_name, topic, with_image)
    typer.echo(f"\nDone. {len(topics)} articles written to {OUTPUT_ROOT / app_name.value}")


@app.command(name="list-packs")
def list_packs() -> None:
    """List all available topic packs and their topics."""
    typer.echo("Available packs:\n")
    for pack_name, topics in PACKS.items():
        typer.echo(f"  {pack_name}")
        for topic in topics:
            typer.echo(f"    - {topic}")
        typer.echo()


if __name__ == "__main__":
    app()
