"""Unit tests for image_generator."""

import os
import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path

from image_generator import build_image_prompt, generate_image


class TestBuildImagePrompt:
    def test_topic_included(self):
        prompt = build_image_prompt("managing anxiety")
        assert "managing anxiety" in prompt

    def test_mentions_style(self):
        prompt = build_image_prompt("grief")
        assert "watercolour" in prompt.lower() or "watercolor" in prompt.lower()

    def test_no_faces_instruction(self):
        prompt = build_image_prompt("grief")
        assert "no human faces" in prompt.lower()


class TestGenerateImage:
    def test_raises_if_no_api_key(self, tmp_path, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        with pytest.raises(EnvironmentError, match="OPENAI_API_KEY"):
            generate_image("Joy", tmp_path / "joy.png")

    def test_saves_image_to_disk(self, tmp_path, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        fake_image_bytes = b"PNG_FAKE_DATA"

        import base64
        fake_b64 = base64.b64encode(fake_image_bytes).decode()

        mock_response = MagicMock()
        mock_response.data = [MagicMock(b64_json=fake_b64)]

        with patch("image_generator.OpenAI") as mock_openai_cls:
            mock_client = MagicMock()
            mock_client.images.generate.return_value = mock_response
            mock_openai_cls.return_value = mock_client

            output = tmp_path / "joy.png"
            generate_image("Joy", output)

        assert output.exists()
        assert output.read_bytes() == fake_image_bytes

    def test_creates_parent_directories(self, tmp_path, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")

        import base64
        fake_b64 = base64.b64encode(b"data").decode()
        mock_response = MagicMock()
        mock_response.data = [MagicMock(b64_json=fake_b64)]

        with patch("image_generator.OpenAI") as mock_openai_cls:
            mock_client = MagicMock()
            mock_client.images.generate.return_value = mock_response
            mock_openai_cls.return_value = mock_client

            output = tmp_path / "nested" / "dir" / "image.png"
            generate_image("Joy", output)

        assert output.exists()
