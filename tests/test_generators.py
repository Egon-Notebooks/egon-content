"""Unit tests for Logseq and Obsidian formatters."""

from egon.generators import logseq, obsidian
from egon.linker import apply_wikilinks, get_aliases
from egon.prompts import build_user_prompt, parse_response


SAMPLE_TOPIC = "Managing social anxiety"
SAMPLE_BODY = "Paragraph one about anxiety.\n\nParagraph two with strategies.\n\nParagraph three with hope."
SAMPLE_DISCLAIMER = "_This is a disclaimer._"


# ---------------------------------------------------------------------------
# Filename generation (tested via each formatter)
# ---------------------------------------------------------------------------

class TestFilename:
    def test_preserves_case(self):
        filename, _ = logseq.format("Joy", "", "")
        assert filename == "Joy.md"

    def test_preserves_spaces(self):
        filename, _ = logseq.format("Social Anxiety", "", "")
        assert filename == "Social Anxiety.md"

    def test_strips_invalid_chars(self):
        filename, _ = logseq.format("What is grief?", "", "")
        assert "?" not in filename

    def test_strips_slash(self):
        filename, _ = logseq.format("../../etc/passwd", "", "")
        assert "/" not in filename

    def test_null_bytes_stripped(self):
        filename, _ = logseq.format("topic\x00name", "", "")
        assert "\x00" not in filename

    def test_both_formatters_produce_same_filename(self):
        logseq_filename, _ = logseq.format(SAMPLE_TOPIC, "", "")
        obsidian_filename, _ = obsidian.format(SAMPLE_TOPIC, "", "")
        assert logseq_filename == obsidian_filename

    def test_wikilink_resolves_to_filename(self):
        # The filename stem must equal the topic title so [[Topic]] resolves correctly
        topic = "Building resilience"
        filename, _ = obsidian.format(topic, "", "")
        assert filename == f"{topic}.md"


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

    def test_aliases_rendered(self):
        _, content = logseq.format(SAMPLE_TOPIC, SAMPLE_BODY, SAMPLE_DISCLAIMER, [], ["anxious", "worried"])
        assert "alias:: anxious, worried" in content

    def test_no_alias_line_when_empty(self):
        _, content = logseq.format(SAMPLE_TOPIC, SAMPLE_BODY, SAMPLE_DISCLAIMER, [], [])
        assert "alias::" not in content

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
            line for line in content.splitlines()
            if line.startswith("- ") and SAMPLE_DISCLAIMER not in line
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

    def test_aliases_rendered(self):
        _, content = obsidian.format(SAMPLE_TOPIC, SAMPLE_BODY, SAMPLE_DISCLAIMER, [], ["anxious", "worried"])
        assert "aliases:" in content
        assert "  - anxious" in content
        assert "  - worried" in content

    def test_no_aliases_key_when_empty(self):
        _, content = obsidian.format(SAMPLE_TOPIC, SAMPLE_BODY, SAMPLE_DISCLAIMER, [], [])
        assert "aliases:" not in content

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
        frontmatter_line = next(line for line in content.splitlines() if line.startswith("title:"))
        inner = frontmatter_line[len('title: "'):-1]
        assert '\\"' in inner

    def test_yaml_title_escapes_backslash(self):
        _, content = obsidian.format("path\\topic", "", "")
        frontmatter_line = next(line for line in content.splitlines() if line.startswith("title:"))
        assert "\\\\" in frontmatter_line


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

class TestBuildUserPrompt:
    def test_topic_included(self):
        prompt = build_user_prompt("grief and loss")
        assert "grief and loss" in prompt

    def test_contains_guidelines_reminder(self):
        prompt = build_user_prompt("any topic")
        assert "safe messaging" in prompt.lower() or "guidelines" in prompt.lower()


class TestParseResponse:
    def test_extracts_tags(self):
        body, tags = parse_response("Article body.\nTAGS: emotions, anger")
        assert body == "Article body."
        assert tags == ["emotions", "anger"]

    def test_empty_tags_line(self):
        body, tags = parse_response("Article body.\nTAGS:")
        assert body == "Article body."
        assert tags == []

    def test_no_tags_line(self):
        body, tags = parse_response("Article body.")
        assert body == "Article body."
        assert tags == []

    def test_case_insensitive(self):
        _, tags = parse_response("Body.\ntags: anxiety")
        assert tags == ["anxiety"]


# ---------------------------------------------------------------------------
# Wikilinks
# ---------------------------------------------------------------------------

class TestApplyWikilinks:
    ALL_TOPICS = ["Anger", "Social anxiety", "Understanding anxiety", "Self-compassion", "Fear"]

    def test_exact_match_wrapped(self):
        result = apply_wikilinks("Anger is a natural emotion.", self.ALL_TOPICS, "Fear")
        assert "[[Anger]]" in result

    def test_case_insensitive_match_uses_pipe(self):
        result = apply_wikilinks("Feelings of anger can be overwhelming.", self.ALL_TOPICS, "Fear")
        assert "[[Anger|anger]]" in result

    def test_longer_phrase_takes_priority(self):
        result = apply_wikilinks("Social anxiety affects many people.", self.ALL_TOPICS, "Fear")
        assert "[[Social anxiety]]" in result
        assert "[[anxiety]]" not in result

    def test_self_topic_not_linked(self):
        result = apply_wikilinks("Fear is a common response.", self.ALL_TOPICS, "Fear")
        assert "[[Fear]]" not in result
        assert result == "Fear is a common response."

    def test_first_mention_only(self):
        # "Anger" appears twice — only the first should be linked
        result = apply_wikilinks("Anger and anger again.", self.ALL_TOPICS, "Fear")
        assert result.count("[[") == 1
        assert "[[Anger]]" in result

    def test_no_match_returns_unchanged(self):
        body = "This text mentions nothing relevant."
        assert apply_wikilinks(body, self.ALL_TOPICS, "Fear") == body

    def test_alias_resolves_to_canonical(self):
        topics = ["Fear", "Anger"]
        result = apply_wikilinks("Feeling fearful is normal.", topics, "Anger")
        assert "[[Fear|fearful]]" in result

    def test_self_alias_not_linked(self):
        result = apply_wikilinks("Feeling fearful is common.", ["Fear", "Anger"], "Fear")
        assert "[[" not in result


class TestGetAliases:
    def test_known_topic_returns_aliases(self):
        assert "angry" in get_aliases("Anger")

    def test_unknown_topic_returns_empty(self):
        assert get_aliases("Nonexistent topic") == []

    def test_topic_with_no_aliases_returns_empty(self):
        assert get_aliases("Catastrophizing") == []

    def test_case_insensitive_lookup(self):
        assert get_aliases("anger") == get_aliases("Anger")
