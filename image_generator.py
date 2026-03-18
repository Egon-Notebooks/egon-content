"""AI image generation for article illustrations using DALL-E 3."""

import base64
import os
from pathlib import Path

from openai import OpenAI, OpenAIError

IMAGE_PROMPT_TEMPLATE = (
    "A minimalistic, warm abstract illustration evoking the feeling of \"{topic}\". "
    "Style: soft watercolour with warm earth tones — terracotta, sage green, amber, and cream. "
    "Abstract flowing shapes, no text, no human faces, no hands, no identifiable objects. "
    "Calm, gentle, and suitable for mental health educational content. "
    "The image should feel safe, open, and hopeful."
)


def build_image_prompt(topic: str) -> str:
    return IMAGE_PROMPT_TEMPLATE.format(topic=topic)


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

    image_bytes = base64.b64decode(response.data[0].b64_json)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(image_bytes)
