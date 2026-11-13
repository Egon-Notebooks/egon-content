"""Unit tests for image_generator."""

import base64
import io
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image as PILImage

from egon_content.image_generator import build_image_prompt, generate_image


def _make_png_b64(width: int = 4, height: int = 4) -> str:
    """Return a base64-encoded minimal PNG for use as a fake API response."""
    buf = io.BytesIO()
    PILImage.new("RGB", (width, height), color=(128, 128, 128)).save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


class TestBuildImagePrompt:
    def test_topic_included(self):
        prompt = build_image_prompt("managing anxiety")
        assert "managing anxiety" in prompt

    def test_mentions_style(self):
        prompt = build_image_prompt("grief")
        assert "watercolor" in prompt.lower()

    def test_no_faces_instruction(self):
        prompt = build_image_prompt("grief")
        assert "no human faces" in prompt.lower()


class TestGenerateImage:
    def test_raises_if_no_api_key(self, tmp_path, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        with pytest.raises(EnvironmentError, match="OPENAI_API_KEY"):
            generate_image("Joy", tmp_path / "joy.webp")

    def test_saves_image_to_disk(self, tmp_path, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        mock_response = MagicMock()
        mock_response.data = [MagicMock(b64_json=_make_png_b64())]

        with patch("egon_content.image_generator.OpenAI") as mock_openai_cls:
            mock_client = MagicMock()
            mock_client.images.generate.return_value = mock_response
            mock_openai_cls.return_value = mock_client

            output = tmp_path / "joy.webp"
            generate_image("Joy", output)

        assert output.exists()
        assert len(output.read_bytes()) > 0

    def test_saves_correct_size(self, tmp_path, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        mock_response = MagicMock()
        mock_response.data = [MagicMock(b64_json=_make_png_b64())]

        with patch("egon_content.image_generator.OpenAI") as mock_openai_cls:
            mock_client = MagicMock()
            mock_client.images.generate.return_value = mock_response
            mock_openai_cls.return_value = mock_client

            output = tmp_path / "joy.webp"
            generate_image("Joy", output)

        img = PILImage.open(output)
        assert img.size == (1200, 675)

    def test_creates_parent_directories(self, tmp_path, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        mock_response = MagicMock()
        mock_response.data = [MagicMock(b64_json=_make_png_b64())]

        with patch("egon_content.image_generator.OpenAI") as mock_openai_cls:
            mock_client = MagicMock()
            mock_client.images.generate.return_value = mock_response
            mock_openai_cls.return_value = mock_client

            output = tmp_path / "nested" / "dir" / "image.webp"
            generate_image("Joy", output)

        assert output.exists()


class TestPersonaPortraits:
    def test_every_persona_has_an_appearance_in_the_prompt(self):
        from egon_content.demo.personas import PERSONAS
        from egon_content.image_generator import build_portrait_prompt

        for persona in PERSONAS:
            assert persona.appearance
            prompt = build_portrait_prompt(persona.appearance)
            assert persona.appearance in prompt
            assert "does not exist" in prompt

    def test_demo_portraits_writes_one_webp_per_persona(self, tmp_path, monkeypatch):
        from typer.testing import CliRunner

        from egon_content import cli
        from egon_content.demo.personas import PERSONAS

        monkeypatch.setattr(cli, "OUTPUT_ROOT", tmp_path)
        monkeypatch.setenv("OPENAI_API_KEY", "test")
        mock_response = MagicMock()
        mock_response.data[0].b64_json = _make_png_b64(64, 64)
        with patch("egon_content.image_generator.OpenAI") as mock_openai_cls:
            mock_openai_cls.return_value.images.generate.return_value = mock_response
            result = CliRunner().invoke(cli.app, ["demo-portraits"])
        assert result.exit_code == 0, result.output
        for persona in PERSONAS:
            assert (tmp_path / "demo" / persona.slug / "portrait.webp").exists()
