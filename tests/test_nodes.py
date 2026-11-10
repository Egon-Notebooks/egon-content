"""The node format egon-content writes (docs/NODE_SPEC.md)."""

import re

import pytest
from typer.testing import CliRunner

from egon_content.cli import app
from egon_content.generators import logseq, obsidian
from egon_content.nodes import EGON_VERSION, to_logseq_links, upgrade_node
from egon_content.questionnaire_data import ALL_QUESTIONNAIRES
from egon_content.questionnaire_formatter import format_questionnaire

BODY = "Worry is linked to [[Understanding anxiety|anxiety]] and [[Sleep and mental health]]."


def _frontmatter(content: str) -> dict:
    """Top-level keys of a YAML frontmatter block, with quotes removed."""
    block = content.split("---\n")[1]
    return {k: v.strip().strip('"') for k, v in re.findall(r"^(\w+):(.*)$", block, re.M)}


def test_obsidian_article_has_type_and_version():
    fm = _frontmatter(obsidian.format("Worry", BODY, "_D._")[1])
    assert fm["type"] == "article"
    assert fm["egon_version"] == EGON_VERSION


def test_logseq_article_has_type_version_and_logseq_links():
    content = logseq.format("Worry", BODY, "_D._")[1]
    assert "type:: article\n" in content
    assert f"egon_version:: {EGON_VERSION}\n" in content
    assert "[anxiety]([[Understanding anxiety]])" in content
    assert "[[Sleep and mental health]]" in content
    assert "|" not in content


@pytest.mark.parametrize("q", ALL_QUESTIONNAIRES, ids=lambda q: q.key)
def test_obsidian_questionnaire_has_universal_fields(q):
    fm = _frontmatter(format_questionnaire(q, "obsidian")[1])
    assert {"title", "date", "type", "tags", "egon_version"} <= fm.keys()
    assert fm["type"] == "questionnaire"


@pytest.mark.parametrize("q", ALL_QUESTIONNAIRES, ids=lambda q: q.key)
def test_logseq_questionnaire_has_version(q):
    assert f"egon_version:: {EGON_VERSION}\n" in format_questionnaire(q, "logseq")[1]


def test_to_logseq_links_leaves_plain_links_alone():
    assert to_logseq_links("[[A]] and [[B|b]]") == "[[A]] and [b]([[B]])"


OLD_OBSIDIAN = '---\ntitle: "Worry"\nauthor: Claude\ndate: 2026-04-01\ntags: []\n---\n\n# Worry\n'
OLD_LOGSEQ = "author:: Claude\ndate:: 2026-04-01\ntags:: \n- " + BODY + "\n"


def test_upgrade_obsidian_node_adds_missing_fields_once():
    once = upgrade_node(OLD_OBSIDIAN, "obsidian")
    fm = _frontmatter(once)
    assert fm["type"] == "article" and fm["egon_version"] == EGON_VERSION
    assert upgrade_node(once, "obsidian") == once


def test_upgrade_obsidian_questionnaire_keeps_its_type_and_gains_a_date():
    old = '---\ntitle: "PHQ-9"\ntype: questionnaire\ntags: []\n---\n'
    fm = _frontmatter(upgrade_node(old, "obsidian"))
    assert fm["type"] == "questionnaire" and "date" in fm


def test_upgrade_logseq_node_adds_properties_and_fixes_links_once():
    once = upgrade_node(OLD_LOGSEQ, "logseq")
    assert once.startswith(
        "author:: Claude\ndate:: 2026-04-01\ntags:: \ntype:: article\negon_version:: 1\n- "
    )
    assert "[anxiety]([[Understanding anxiety]])" in once
    assert upgrade_node(once, "logseq") == once


def test_upgrade_nodes_command(tmp_path):
    (tmp_path / "Worry.md").write_text(OLD_OBSIDIAN)
    result = CliRunner().invoke(
        app, ["upgrade-nodes", "--nodes-dir", str(tmp_path), "--app", "obsidian"]
    )
    assert result.exit_code == 0 and "Updated 1 nodes" in result.output
    assert "egon_version" in (tmp_path / "Worry.md").read_text()
