"""Unit tests for Logseq and Obsidian formatters."""

import pytest
from generators import logseq, obsidian


SAMPLE_TOPIC = "Managing social anxiety"
SAMPLE_BODY = "Paragraph one about anxiety.\n\nParagraph two with strategies.\n\nParagraph three with hope."
SAMPLE_DISCLAIMER = "_This is a disclaimer._"


# ---------------------------------------------------------------------------
# Shared slugify behavior (tested via each formatter)
# ---------------------------------------------------------------------------

class TestSlugify:
    def test_lowercases(self):
        filename, _ = logseq.format("Joy", "", "")
        assert filename == "joy.md"

    def test_spaces_become_hyphens(self):
        filename, _ = logseq.format("Social Anxiety", "", "")
        assert filename == "social-anxiety.md"

    def test_strips_special_characters(self):
        filename, _ = logseq.format("What is grief?", "", "")
        assert "?" not in filename

    def test_collapses_multiple_hyphens(self):
        filename, _ = logseq.format("a  b", "", "")
        assert filename == "a-b.md"

    def test_path_traversal_attempt(self):
        filename, _ = logseq.format("../../etc/passwd", "", "")
        assert ".." not in filename
        assert "/" not in filename

    def test_null_bytes_stripped(self):
        filename, _ = logseq.format("topic\x00name", "", "")
        assert "\x00" not in filename

    def test_obsidian_slugify_matches_logseq(self):
        logseq_filename, _ = logseq.format(SAMPLE_TOPIC, "", "")
        obsidian_filename, _ = obsidian.format(SAMPLE_TOPIC, "", "")
        assert logseq_filename == obsidian_filename


# ---------------------------------------------------------------------------
# Logseq formatter
# ---------------------------------------------------------------------------

class TestLogseqFormatter:
    def setup_method(self):
        self.filename, self.content = logseq.format(SAMPLE_TOPIC, SAMPLE_BODY, SAMPLE_DISCLAIMER)

    def test_filename_is_md(self):
        assert self.filename.endswith(".md")

    def test_has_author_property(self):
        assert "author:: Claude" in self.content

    def test_has_date_property(self):
        assert "date::" in self.content

    def test_has_tags_property(self):
        assert "tags::" in self.content

    def test_tags_with_values(self):
        _, content = logseq.format(SAMPLE_TOPIC, SAMPLE_BODY, SAMPLE_DISCLAIMER, ["anxiety", "stress"])
        assert "tags:: anxiety, stress" in content

    def test_tags_empty(self):
        _, content = logseq.format(SAMPLE_TOPIC, SAMPLE_BODY, SAMPLE_DISCLAIMER, [])
        assert "tags:: \n" in content

    def test_no_title_property(self):
        assert "title::" not in self.content

    def test_body_paragraphs_are_bullets(self):
        assert "- Paragraph one about anxiety." in self.content
        assert "- Paragraph two with strategies." in self.content
        assert "- Paragraph three with hope." in self.content

    def test_disclaimer_is_last_bullet(self):
        lines = self.content.strip().splitlines()
        assert lines[-1].startswith("- ")
        assert SAMPLE_DISCLAIMER in lines[-1]

    def test_empty_body_produces_no_bullets(self):
        _, content = logseq.format(SAMPLE_TOPIC, "", SAMPLE_DISCLAIMER)
        non_disclaimer_bullets = [
            l for l in content.splitlines()
            if l.startswith("- ") and SAMPLE_DISCLAIMER not in l
        ]
        assert non_disclaimer_bullets == []

    def test_no_image_in_content(self):
        _, content = logseq.format(SAMPLE_TOPIC, SAMPLE_BODY, SAMPLE_DISCLAIMER)
        assert "![" not in content


# ---------------------------------------------------------------------------
# Obsidian formatter
# ---------------------------------------------------------------------------

class TestObsidianFormatter:
    def setup_method(self):
        self.filename, self.content = obsidian.format(SAMPLE_TOPIC, SAMPLE_BODY, SAMPLE_DISCLAIMER)

    def test_filename_is_md(self):
        assert self.filename.endswith(".md")

    def test_has_yaml_frontmatter(self):
        assert self.content.startswith("---\n")
        assert "---\n" in self.content[4:]  # closing fence

    def test_frontmatter_has_title(self):
        assert 'title: "Managing social anxiety"' in self.content

    def test_frontmatter_has_author(self):
        assert "author: Claude" in self.content

    def test_frontmatter_has_date(self):
        assert "date:" in self.content

    def test_frontmatter_has_tags_key(self):
        assert "tags:" in self.content

    def test_frontmatter_tags_with_values(self):
        _, content = obsidian.format(SAMPLE_TOPIC, SAMPLE_BODY, SAMPLE_DISCLAIMER, ["emotions", "anxiety"])
        assert "  - emotions" in content
        assert "  - anxiety" in content

    def test_frontmatter_tags_empty(self):
        _, content = obsidian.format(SAMPLE_TOPIC, SAMPLE_BODY, SAMPLE_DISCLAIMER, [])
        assert "tags: []" in content

    def test_h1_title_present(self):
        assert f"# {SAMPLE_TOPIC}" in self.content

    def test_body_is_prose(self):
        assert "Paragraph one about anxiety." in self.content
        assert "Paragraph two with strategies." in self.content

    def test_disclaimer_at_end(self):
        assert self.content.strip().endswith(SAMPLE_DISCLAIMER)

    def test_no_image_in_content(self):
        _, content = obsidian.format(SAMPLE_TOPIC, SAMPLE_BODY, SAMPLE_DISCLAIMER)
        assert "![" not in content

    def test_yaml_title_escapes_double_quotes(self):
        topic_with_quotes = 'He said "hello"'
        _, content = obsidian.format(topic_with_quotes, "", "")
        # Must not produce unescaped double quote inside the YAML value
        frontmatter_line = next(l for l in content.splitlines() if l.startswith("title:"))
        # Count unescaped quotes: after `title: "` there should be no bare `"`
        # until the closing quote — i.e. the inner quotes must be escaped
        inner = frontmatter_line[len('title: "'):-1]
        assert '\\"' in inner

    def test_yaml_title_escapes_backslash(self):
        _, content = obsidian.format("path\\topic", "", "")
        frontmatter_line = next(l for l in content.splitlines() if l.startswith("title:"))
        assert "\\\\" in frontmatter_line


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

class TestBuildUserPrompt:
    def test_topic_included(self):
        from prompts import build_user_prompt
        prompt = build_user_prompt("grief and loss")
        assert "grief and loss" in prompt

    def test_contains_guidelines_reminder(self):
        from prompts import build_user_prompt
        prompt = build_user_prompt("any topic")
        assert "safe messaging" in prompt.lower() or "guidelines" in prompt.lower()


class TestParseBodyAndTags:
    def test_extracts_tags(self):
        from prompts import parse_body_and_tags
        body, tags = parse_body_and_tags("Some article text.\nTAGS: emotions, anger")
        assert body == "Some article text."
        assert tags == ["emotions", "anger"]

    def test_empty_tags_line(self):
        from prompts import parse_body_and_tags
        body, tags = parse_body_and_tags("Some article text.\nTAGS:")
        assert body == "Some article text."
        assert tags == []

    def test_no_tags_line(self):
        from prompts import parse_body_and_tags
        body, tags = parse_body_and_tags("Some article text.")
        assert body == "Some article text."
        assert tags == []

    def test_case_insensitive(self):
        from prompts import parse_body_and_tags
        _, tags = parse_body_and_tags("Body.\ntags: anxiety")
        assert tags == ["anxiety"]
