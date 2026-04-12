"""AI image generation for article illustrations using DALL-E 3.

Edit prompts/image_style.txt to update the image style prompt.
"""

import base64
import io
import os
from pathlib import Path

from openai import OpenAI
from PIL import Image

_PROMPTS_DIR = Path(__file__).parent.parent / "prompts"
_IMAGE_PROMPT_TEMPLATE: str = (_PROMPTS_DIR / "image_style.txt").read_text(encoding="utf-8").strip()

_TARGET_SIZE = (1200, 675)


def build_image_prompt(topic: str) -> str:
    return _IMAGE_PROMPT_TEMPLATE.format(topic=topic)


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
        model="dall-e-3",
        prompt=prompt,
        size="1024x1024",
        quality="standard",
        response_format="b64_json",
        n=1,
    )

    raw_bytes = base64.b64decode(response.data[0].b64_json)
    image = Image.open(io.BytesIO(raw_bytes))
    image = image.resize(_TARGET_SIZE, Image.LANCZOS)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path, format="WEBP")
