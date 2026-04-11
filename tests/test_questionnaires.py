"""Tests for questionnaire data and formatters."""

import pytest
from egon.questionnaire_data import ALL_QUESTIONNAIRES, PHQ9, GAD7, WHO5, PSS10, RSES, BRS
from egon.questionnaire_formatter import format_questionnaire


class TestQuestionnaireData:
    def test_all_questionnaires_present(self):
        keys = {q.key for q in ALL_QUESTIONNAIRES}
        assert keys == {"phq9", "gad7", "who5", "pss10", "rses", "brs"}

    def test_phq9_has_nine_questions(self):
        assert len(PHQ9.questions) == 9

    def test_gad7_has_seven_questions(self):
        assert len(GAD7.questions) == 7

    def test_who5_has_five_questions(self):
        assert len(WHO5.questions) == 5

    def test_pss10_has_ten_questions(self):
        assert len(PSS10.questions) == 10

    def test_rses_has_ten_questions(self):
        assert len(RSES.questions) == 10

    def test_brs_has_six_questions(self):
        assert len(BRS.questions) == 6

    def test_pss10_reverse_scored_items(self):
        reversed_idx = [i for i, q in enumerate(PSS10.questions, 1) if q.reversed]
        assert reversed_idx == [4, 5, 7, 8]

    def test_rses_reverse_scored_items(self):
        reversed_idx = [i for i, q in enumerate(RSES.questions, 1) if q.reversed]
        assert reversed_idx == [2, 5, 6, 8, 9]

    def test_brs_reverse_scored_items(self):
        reversed_idx = [i for i, q in enumerate(BRS.questions, 1) if q.reversed]
        assert reversed_idx == [2, 4, 6]

    def test_phq9_has_safe_messaging_note(self):
        assert PHQ9.safe_messaging_note is not None
        assert "question 9" in PHQ9.safe_messaging_note

    def test_all_have_licence_and_citation(self):
        for q in ALL_QUESTIONNAIRES:
            assert q.licence
            assert q.citation

    def test_all_have_tags(self):
        for q in ALL_QUESTIONNAIRES:
            assert "questionnaire" in q.tags
            assert "self-assessment" in q.tags


class TestObsidianFormatter:
    @pytest.fixture(params=ALL_QUESTIONNAIRES, ids=lambda q: q.key)
    def rendered(self, request):
        _, content = format_questionnaire(request.param, "obsidian")
        return content

    def test_has_yaml_frontmatter(self, rendered):
        assert rendered.startswith("---")
        assert "type: questionnaire" in rendered

    def test_contains_question_text(self):
        _, content = format_questionnaire(PHQ9, "obsidian")
        assert "Little interest or pleasure in doing things" in content

    def test_reverse_items_marked(self):
        _, content = format_questionnaire(PSS10, "obsidian")
        assert "*(R)*" in content

    def test_safe_messaging_callout(self):
        _, content = format_questionnaire(PHQ9, "obsidian")
        assert "[!warning]" in content

    def test_no_safe_messaging_when_absent(self):
        _, content = format_questionnaire(GAD7, "obsidian")
        assert "[!warning]" not in content

    def test_interpretation_table_present(self, rendered):
        assert "| Score | Interpretation |" in rendered

    def test_scale_labels_in_header(self):
        _, content = format_questionnaire(PHQ9, "obsidian")
        assert "Not at all" in content
        assert "Nearly every day" in content


class TestLogseqFormatter:
    @pytest.fixture(params=ALL_QUESTIONNAIRES, ids=lambda q: q.key)
    def rendered(self, request):
        _, content = format_questionnaire(request.param, "logseq")
        return content

    def test_has_type_property(self, rendered):
        assert "type:: questionnaire" in rendered

    def test_score_properties_present(self):
        _, content = format_questionnaire(PHQ9, "logseq")
        assert "score-1::" in content
        assert "score-9::" in content

    def test_contains_question_text(self):
        _, content = format_questionnaire(GAD7, "logseq")
        assert "Feeling nervous, anxious, or on edge" in content

    def test_reverse_items_marked(self):
        _, content = format_questionnaire(RSES, "logseq")
        assert "*(R)*" in content

    def test_total_score_property(self, rendered):
        assert "Total score::" in rendered


class TestFilename:
    def test_phq9_filename(self):
        filename, _ = format_questionnaire(PHQ9, "obsidian")
        assert filename == "PHQ-9 Monthly Depression Check-in.md"

    def test_brs_filename(self):
        filename, _ = format_questionnaire(BRS, "logseq")
        assert filename == "Brief Resilience Scale Check-in.md"
