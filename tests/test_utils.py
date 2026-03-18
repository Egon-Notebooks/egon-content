"""Unit tests for utils.parse_topics_file."""

import pytest
from pathlib import Path

from utils import parse_topics_file


def write_file(tmp_path: Path, content: str) -> Path:
    p = tmp_path / "topics.txt"
    p.write_text(content, encoding="utf-8")
    return p


class TestParseTopicsFile:
    def test_returns_topics(self, tmp_path):
        f = write_file(tmp_path, "Joy\nSadness\nAnger\n")
        assert parse_topics_file(f) == ["Joy", "Sadness", "Anger"]

    def test_ignores_empty_lines(self, tmp_path):
        f = write_file(tmp_path, "Joy\n\nSadness\n\n")
        assert parse_topics_file(f) == ["Joy", "Sadness"]

    def test_ignores_comment_lines(self, tmp_path):
        f = write_file(tmp_path, "# A comment\nJoy\n# Another comment\nSadness\n")
        assert parse_topics_file(f) == ["Joy", "Sadness"]

    def test_strips_whitespace(self, tmp_path):
        f = write_file(tmp_path, "  Joy  \n  Sadness  \n")
        assert parse_topics_file(f) == ["Joy", "Sadness"]

    def test_inline_comment_is_not_a_comment(self, tmp_path):
        # Only lines that START with # are comments; inline # is part of the topic
        f = write_file(tmp_path, "Joy # the happy one\n")
        assert parse_topics_file(f) == ["Joy # the happy one"]

    def test_raises_file_not_found(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            parse_topics_file(tmp_path / "nonexistent.txt")

    def test_raises_value_error_on_empty_file(self, tmp_path):
        f = write_file(tmp_path, "")
        with pytest.raises(ValueError, match="No topics found"):
            parse_topics_file(f)

    def test_raises_value_error_on_comments_only(self, tmp_path):
        f = write_file(tmp_path, "# only comments\n# nothing else\n")
        with pytest.raises(ValueError, match="No topics found"):
            parse_topics_file(f)

    def test_parses_example_file(self):
        example = Path(__file__).parent.parent / "topics.example.txt"
        topics = parse_topics_file(example)
        assert len(topics) > 0
        assert all(not t.startswith("#") for t in topics)
        assert all(t.strip() == t for t in topics)
