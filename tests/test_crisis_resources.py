"""Crisis resources in content nodes and questionnaire templates (docs/SAFETY.md)."""

import pytest
from typer.testing import CliRunner

from egon.cli import app
from egon.generators import logseq, obsidian
from egon.prompts import CRISIS_NOTE, needs_crisis_note
from egon.questionnaire_data import ALL_QUESTIONNAIRES
from egon.questionnaire_formatter import format_questionnaire

runner = CliRunner()


@pytest.mark.parametrize(
    "topic",
    ["Understanding low mood", "Energy conservation when depressed", "Sadness", "Self-harm"],
)
def test_topics_that_need_the_note(topic):
    assert needs_crisis_note(topic)


@pytest.mark.parametrize("topic", ["Movement and mood", "Disgust", "What is mindfulness"])
def test_topics_that_do_not(topic):
    assert not needs_crisis_note(topic)


def test_obsidian_note_sits_under_the_title():
    _, content = obsidian.format("Sadness", "Body.", "_D._", crisis_note=CRISIS_NOTE)
    assert f"# Sadness\n\n{CRISIS_NOTE}\n\nBody." in content


def test_logseq_note_is_the_first_bullet():
    _, content = logseq.format("Sadness", "Body.", "_D._", crisis_note=CRISIS_NOTE)
    assert f"- {CRISIS_NOTE}\n- Body." in content


def test_no_note_by_default():
    _, content = obsidian.format("Disgust", "Body.", "_D._")
    assert "findahelpline.com" not in content


@pytest.mark.parametrize("app_name", ["obsidian", "logseq"])
@pytest.mark.parametrize("q", ALL_QUESTIONNAIRES, ids=lambda q: q.key)
def test_every_questionnaire_has_the_note_before_its_questions(q, app_name):
    _, content = format_questionnaire(q, app_name)
    assert CRISIS_NOTE in content
    assert content.index(CRISIS_NOTE) < content.index(q.questions[0].text)


def test_add_crisis_notes_updates_only_matching_nodes_once(tmp_path):
    _, sad = obsidian.format("Sadness", "Body.", "_D._")
    _, sad_logseq = logseq.format("Low mood", "Body.", "_D._")
    _, other = obsidian.format("Disgust", "Body.", "_D._")
    (tmp_path / "Sadness.md").write_text(sad)
    (tmp_path / "Low mood.md").write_text(sad_logseq)
    (tmp_path / "Disgust.md").write_text(other)

    for _ in range(2):
        assert runner.invoke(app, ["add-crisis-notes", "--nodes-dir", str(tmp_path)]).exit_code == 0

    assert f"# Sadness\n\n{CRISIS_NOTE}\n" in (tmp_path / "Sadness.md").read_text()
    assert f"- {CRISIS_NOTE}\n- Body." in (tmp_path / "Low mood.md").read_text()
    assert (tmp_path / "Sadness.md").read_text().count(CRISIS_NOTE) == 1
    assert "findahelpline.com" not in (tmp_path / "Disgust.md").read_text()
