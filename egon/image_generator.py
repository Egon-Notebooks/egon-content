"""AI image generation for article illustrations using gpt-image-1.

Edit prompts/image_style.txt to update the article image style prompt.
Edit prompts/pencil_style.txt to update the ad-hoc illustration style prompt.
"""

import base64
import io
import os
from pathlib import Path

from openai import OpenAI
from PIL import Image

_PROMPTS_DIR = Path(__file__).parent.parent / "prompts"
_IMAGE_PROMPT_TEMPLATE: str = (_PROMPTS_DIR / "image_style.txt").read_text(encoding="utf-8").strip()
_PENCIL_PROMPT_TEMPLATE: str = (
    (_PROMPTS_DIR / "pencil_style.txt").read_text(encoding="utf-8").strip()
)

_TARGET_SIZE = (1200, 675)

# gpt-image-1 supported sizes
_ILLUSTRATION_SIZES = {
    "square": "1024x1024",
    "landscape": "1536x1024",
    "portrait": "1024x1536",
}

# gpt-image-1 quality values
_QUALITY_VALUES = {"low", "medium", "high", "auto"}


def build_image_prompt(topic: str) -> str:
    return _IMAGE_PROMPT_TEMPLATE.format(topic=topic)


def build_illustration_prompt(description: str) -> str:
    return _PENCIL_PROMPT_TEMPLATE.format(description=description)


def _decode_response(response) -> bytes:
    return base64.b64decode(response.data[0].b64_json)


def generate_image(topic: str, output_path: Path) -> None:
    """Generate an image for the given topic and save it to output_path.

    Raises:
        EnvironmentError: if OPENAI_API_KEY is not set.
        OpenAIError: if the API request fails.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError("OPENAI_API_KEY is not set. Add it to your .env file.")

    client = OpenAI(api_key=api_key)
    prompt = build_image_prompt(topic)

    response = client.images.generate(
        model="gpt-image-1",
        prompt=prompt,
        size="1024x1024",
        quality="medium",
        n=1,
    )

    image = Image.open(io.BytesIO(_decode_response(response)))
    image = image.resize(_TARGET_SIZE, Image.LANCZOS)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path, format="WEBP")


def generate_illustration(
    description: str,
    output_path: Path,
    size: str = "landscape",
    quality: str = "medium",
) -> None:
    """Generate a pencil-sketch illustration for the given description.

    Args:
        description: Short description of what to illustrate.
        output_path: Where to save the resulting image (PNG or WEBP based on suffix).
        size: One of 'square', 'landscape', or 'portrait'.
        quality: 'low', 'medium', 'high', or 'auto'.

    Raises:
        EnvironmentError: if OPENAI_API_KEY is not set.
        ValueError: if size or quality is not recognised.
        OpenAIError: if the API request fails.
    """
    if size not in _ILLUSTRATION_SIZES:
        raise ValueError(f"size must be one of {list(_ILLUSTRATION_SIZES)}; got {size!r}")
    if quality not in _QUALITY_VALUES:
        raise ValueError(f"quality must be one of {sorted(_QUALITY_VALUES)}; got {quality!r}")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError("OPENAI_API_KEY is not set. Add it to your .env file.")

    client = OpenAI(api_key=api_key)
    prompt = build_illustration_prompt(description)

    response = client.images.generate(
        model="gpt-image-1",
        prompt=prompt,
        size=_ILLUSTRATION_SIZES[size],
        quality=quality,
        n=1,
    )

    image = Image.open(io.BytesIO(_decode_response(response)))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fmt = "PNG" if output_path.suffix.lower() == ".png" else "WEBP"
    image.save(output_path, format=fmt)
