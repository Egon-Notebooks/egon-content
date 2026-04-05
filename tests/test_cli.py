"""Integration tests for the CLI using mocked API clients."""

import base64
import io
from unittest.mock import MagicMock, patch

from PIL import Image as PILImage
from typer.testing import CliRunner

from egon.cli import app


runner = CliRunner()


def _make_png_b64() -> str:
    buf = io.BytesIO()
    PILImage.new("RGB", (4, 4), color=(128, 128, 128)).save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def _mock_anthropic(body: str = "Article body.\nTAGS: emotions"):
    mock_client = MagicMock()
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text=body)]
    mock_client.messages.create.return_value = mock_message
    return mock_client


def _mock_openai():
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.data = [MagicMock(b64_json=_make_png_b64())]
    mock_client.images.generate.return_value = mock_response
    return mock_client


class TestGenerateCommand:
    def test_generate_dry_run(self, tmp_path, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        with patch("egon.cli.OUTPUT_ROOT", tmp_path):
            result = runner.invoke(app, [
                "generate", "--app", "obsidian", "--topic", "Anger", "--dry-run",
            ])
        assert result.exit_code == 0
        assert "[dry-run]" in result.output
        # No files should be written
        assert not any(tmp_path.rglob("*.md"))

    def test_generate_creates_node_file(self, tmp_path, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        mock_client = _mock_anthropic()
        with (
            patch("egon.cli.OUTPUT_ROOT", tmp_path),
            patch("egon.cli._get_client", return_value=mock_client),
            patch("egon.cli.generate_image"),
        ):
            result = runner.invoke(app, [
                "generate", "--app", "obsidian", "--topic", "Anger", "--no-image",
            ])
        assert result.exit_code == 0
        assert (tmp_path / "obsidian" / "nodes" / "Anger.md").exists()

    def test_generate_missing_api_key(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        result = runner.invoke(app, [
            "generate", "--app", "obsidian", "--topic", "Anger",
        ])
        assert result.exit_code == 1

    def test_generate_with_image(self, tmp_path, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        mock_client = _mock_anthropic()
        mock_openai = _mock_openai()
        with (
            patch("egon.cli.OUTPUT_ROOT", tmp_path),
            patch("egon.cli._get_client", return_value=mock_client),
            patch("egon.image_generator.OpenAI", return_value=mock_openai),
        ):
            result = runner.invoke(app, [
                "generate", "--app", "obsidian", "--topic", "Anger",
            ])
        assert result.exit_code == 0
        assert (tmp_path / "obsidian" / "nodes" / "Anger.md").exists()
        assert any((tmp_path / "obsidian" / "images").glob("*.webp"))


class TestPackCommand:
    def test_pack_dry_run(self, tmp_path, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        mock_client = _mock_anthropic()
        with (
            patch("egon.cli.OUTPUT_ROOT", tmp_path),
            patch("egon.cli._get_client", return_value=mock_client),
        ):
            result = runner.invoke(app, [
                "pack", "--app", "obsidian", "--pack", "understanding-emotions", "--dry-run",
            ])
        assert result.exit_code == 0
        assert "[dry-run]" in result.output
        assert not any(tmp_path.rglob("*.md"))

    def test_pack_unknown_pack_exits(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        result = runner.invoke(app, [
            "pack", "--app", "obsidian", "--pack", "nonexistent-pack",
        ])
        assert result.exit_code == 1


class TestGenerateAllCommand:
    def test_generate_all_dry_run_base_only(self, tmp_path, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        mock_client = _mock_anthropic()
        with (
            patch("egon.cli.OUTPUT_ROOT", tmp_path),
            patch("egon.cli._get_client", return_value=mock_client),
        ):
            result = runner.invoke(app, [
                "generate-all", "--app", "obsidian", "--dry-run",
            ])
        assert result.exit_code == 0
        assert "[dry-run]" in result.output
        assert "base graph" in result.output
        assert not any(tmp_path.rglob("*.md"))

    def test_generate_all_dry_run_all_packs(self, tmp_path, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        mock_client = _mock_anthropic()
        with (
            patch("egon.cli.OUTPUT_ROOT", tmp_path),
            patch("egon.cli._get_client", return_value=mock_client),
        ):
            result = runner.invoke(app, [
                "generate-all", "--app", "obsidian", "--all-packs", "--dry-run",
            ])
        assert result.exit_code == 0
        assert "all packs" in result.output


class TestGraphReportCommand:
    def test_no_nodes_exits(self, tmp_path, monkeypatch):
        with patch("egon.cli.OUTPUT_ROOT", tmp_path):
            result = runner.invoke(app, ["graph-report", "--app", "obsidian"])
        assert result.exit_code == 1

    def test_report_printed(self, tmp_path):
        nodes_dir = tmp_path / "obsidian" / "nodes"
        nodes_dir.mkdir(parents=True)
        (nodes_dir / "Anger.md").write_text("[[Fear]] is related.", encoding="utf-8")
        (nodes_dir / "Fear.md").write_text("No links.", encoding="utf-8")
        with patch("egon.cli.OUTPUT_ROOT", tmp_path):
            result = runner.invoke(app, ["graph-report", "--app", "obsidian"])
        assert result.exit_code == 0
        assert "Nodes:" in result.output
        assert "Edges:" in result.output
        assert (tmp_path / "obsidian" / "graph-report.txt").exists()
        assert (tmp_path / "obsidian" / "graph-data.txt").exists()
        assert (tmp_path / "obsidian" / "graph-plot.png").exists()


class TestListPacksCommand:
    def test_lists_base_and_supplementary(self):
        result = runner.invoke(app, ["list-packs"])
        assert result.exit_code == 0
        assert "Base graph packs:" in result.output
        assert "Supplementary packs:" in result.output
        assert "bullying" in result.output
