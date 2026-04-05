"""Unit tests for graph analysis."""

from pathlib import Path
from egon.graph import build_graph, compute_report, format_report, save_report, save_graph_data, plot_graph, GraphReport


def _write_node(tmp_path: Path, name: str, body: str) -> Path:
    f = tmp_path / f"{name}.md"
    f.write_text(body, encoding="utf-8")
    return f


class TestBuildGraph:
    def test_empty_directory(self, tmp_path):
        graph = build_graph(tmp_path)
        assert graph == {}

    def test_single_node_no_links(self, tmp_path):
        _write_node(tmp_path, "Anger", "Anger is an emotion.")
        graph = build_graph(tmp_path)
        assert graph == {"Anger": set()}

    def test_link_between_two_nodes(self, tmp_path):
        _write_node(tmp_path, "Anger", "See also [[Fear]].")
        _write_node(tmp_path, "Fear", "No links here.")
        graph = build_graph(tmp_path)
        assert "Fear" in graph["Anger"]
        assert graph["Fear"] == set()

    def test_link_to_nonexistent_node_ignored(self, tmp_path):
        _write_node(tmp_path, "Anger", "See [[NonExistent]].")
        graph = build_graph(tmp_path)
        assert graph["Anger"] == set()

    def test_self_link_ignored(self, tmp_path):
        _write_node(tmp_path, "Anger", "[[Anger]] is tricky.")
        graph = build_graph(tmp_path)
        assert graph["Anger"] == set()

    def test_piped_link_resolves_to_target(self, tmp_path):
        _write_node(tmp_path, "Anger", "Feeling [[Fear|fearful]] is normal.")
        _write_node(tmp_path, "Fear", "No links.")
        graph = build_graph(tmp_path)
        assert "Fear" in graph["Anger"]

    def test_frontmatter_links_not_counted(self, tmp_path):
        content = "---\naliases:\n  - [[Fear]]\n---\nBody text."
        _write_node(tmp_path, "Anger", content)
        _write_node(tmp_path, "Fear", "No links.")
        graph = build_graph(tmp_path)
        assert "Fear" not in graph["Anger"]


class TestComputeReport:
    def test_empty_graph(self):
        report = compute_report({})
        assert report.total_nodes == 0
        assert report.total_edges == 0
        assert report.orphan_nodes == []
        assert report.clustering == 0.0
        assert report.connected_components == 0
        assert report.betweenness_top == []

    def test_orphan_detected(self):
        graph = {"Anger": set(), "Fear": {"Anger"}}
        report = compute_report(graph)
        assert "Anger" not in report.orphan_nodes  # Anger has degree 1 (Fear links to it)
        assert report.total_edges == 1

    def test_isolated_node_is_orphan(self):
        graph = {"Anger": set(), "Fear": set()}
        report = compute_report(graph)
        assert "Anger" in report.orphan_nodes
        assert "Fear" in report.orphan_nodes

    def test_density_complete_graph(self):
        # 3 nodes fully connected = 3 edges, density = 1.0
        graph = {"A": {"B", "C"}, "B": {"A", "C"}, "C": {"A", "B"}}
        report = compute_report(graph)
        assert report.total_edges == 3
        assert abs(report.density - 1.0) < 1e-9

    def test_avg_degree(self):
        graph = {"A": {"B"}, "B": {"A"}, "C": set()}
        report = compute_report(graph)
        # A and B have degree 1, C has degree 0 → avg = 2/3
        assert abs(report.avg_degree - (2 / 3)) < 1e-9

    def test_connected_components_single(self):
        graph = {"A": {"B"}, "B": {"C"}, "C": set()}
        report = compute_report(graph)
        assert report.connected_components == 1

    def test_connected_components_two(self):
        # A-B and C-D are disconnected
        graph = {"A": {"B"}, "B": set(), "C": {"D"}, "D": set()}
        report = compute_report(graph)
        assert report.connected_components == 2

    def test_clustering_complete_triangle(self):
        graph = {"A": {"B", "C"}, "B": {"A", "C"}, "C": {"A", "B"}}
        report = compute_report(graph)
        assert abs(report.clustering - 1.0) < 1e-9

    def test_betweenness_top_populated(self):
        # B bridges A and C
        graph = {"A": {"B"}, "B": {"C"}, "C": set()}
        report = compute_report(graph)
        assert len(report.betweenness_top) > 0
        top_node = report.betweenness_top[0][0]
        assert top_node == "B"


class TestFormatReport:
    def _make_report(self, **kwargs):
        defaults = dict(
            total_nodes=5, total_edges=3, orphan_nodes=["Anger"],
            most_linked=[("Fear", 4), ("Sadness", 2)], avg_degree=1.2,
            density=0.15, clustering=0.4, connected_components=1,
            betweenness_top=[("Fear", 0.5), ("Sadness", 0.2)],
        )
        return GraphReport(**{**defaults, **kwargs})

    def test_contains_key_fields(self):
        text = format_report(self._make_report())
        assert "5" in text
        assert "3" in text
        assert "Anger" in text
        assert "Fear" in text

    def test_contains_new_metrics(self):
        text = format_report(self._make_report())
        assert "Clustering" in text
        assert "Connected components" in text
        assert "betweenness" in text.lower()

    def test_no_orphans_section_when_none(self):
        text = format_report(self._make_report(orphan_nodes=[]))
        assert "Orphans:" not in text


def _simple_report(**kwargs) -> GraphReport:
    defaults = dict(
        total_nodes=2, total_edges=1, orphan_nodes=[], most_linked=[("Fear", 1)],
        avg_degree=0.5, density=0.5, clustering=0.0, connected_components=1,
        betweenness_top=[],
    )
    return GraphReport(**{**defaults, **kwargs})


class TestSaveReport:
    def test_file_created(self, tmp_path):
        out = tmp_path / "graph-report.txt"
        save_report(_simple_report(), out)
        assert out.exists()

    def test_file_content(self, tmp_path):
        out = tmp_path / "graph-report.txt"
        save_report(_simple_report(), out)
        text = out.read_text()
        assert "Nodes:" in text
        assert "Edges:" in text

    def test_creates_parent_dirs(self, tmp_path):
        out = tmp_path / "nested" / "dir" / "report.txt"
        save_report(_simple_report(total_nodes=1, total_edges=0, orphan_nodes=["Anger"]), out)
        assert out.exists()


class TestSaveGraphData:
    def test_file_created(self, tmp_path):
        graph = {"Anger": {"Fear"}, "Fear": set()}
        out = tmp_path / "graph-data.txt"
        save_graph_data(graph, out)
        assert out.exists()

    def test_contains_node_names(self, tmp_path):
        graph = {"Anger": {"Fear"}, "Fear": set()}
        out = tmp_path / "graph-data.txt"
        save_graph_data(graph, out)
        text = out.read_text()
        assert "Anger" in text
        assert "Fear" in text

    def test_sorted_by_degree(self, tmp_path):
        # Fear links to Anger and Sadness — highest degree hub.
        graph = {"Fear": {"Anger", "Sadness"}, "Anger": set(), "Sadness": set()}
        out = tmp_path / "graph-data.txt"
        save_graph_data(graph, out)
        text = out.read_text()
        # Fear should appear before Anger and Sadness.
        assert text.index("Fear") < text.index("Anger")

    def test_shows_degree(self, tmp_path):
        graph = {"Anger": {"Fear"}, "Fear": set()}
        out = tmp_path / "graph-data.txt"
        save_graph_data(graph, out)
        assert "degree" in out.read_text()


class TestPlotGraph:
    def test_pdf_created(self, tmp_path):
        graph = {"Anger": {"Fear"}, "Fear": set(), "Sadness": set()}
        out = tmp_path / "graph-plot.png"
        plot_graph(graph, out)
        assert out.exists() and out.stat().st_size > 0

    def test_empty_graph_does_not_crash(self, tmp_path):
        out = tmp_path / "graph-plot.png"
        plot_graph({}, out)
        assert out.exists()
