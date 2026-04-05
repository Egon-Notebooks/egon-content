"""Node graph analysis.

Builds an undirected graph from generated Markdown nodes by scanning for
[[wikilinks]] in their bodies, then computes key structural metrics.
"""

import re
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import networkx as nx
import numpy as np


# Matches [[Target]] and [[Target|display]] wikilinks.
_WIKILINK_RE = re.compile(r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]')


@dataclass
class GraphReport:
    total_nodes: int
    total_edges: int
    orphan_nodes: list[str]
    most_linked: list[tuple[str, int]]        # (node, undirected degree), descending
    avg_degree: float
    density: float
    clustering: float                         # global average clustering coefficient
    connected_components: int                 # number of disconnected sub-graphs
    betweenness_top: list[tuple[str, float]]  # (node, betweenness score), top 5


def _parse_wikilinks(path: Path) -> set[str]:
    """Return the set of unique link targets found in a node file."""
    text = path.read_text(encoding="utf-8")
    # Skip YAML frontmatter so alias lines don't produce false links.
    if text.startswith("---"):
        end = text.find("---", 3)
        if end != -1:
            text = text[end + 3:]
    return {m.group(1).strip() for m in _WIKILINK_RE.finditer(text)}


def build_graph(nodes_dir: Path) -> dict[str, set[str]]:
    """Return an adjacency dict {node_title: {linked_titles}} from a nodes directory.

    Node titles are derived from filenames (stem, preserving case).
    Only links that point to another node in the same directory are kept.
    """
    md_files = list(nodes_dir.glob("*.md"))
    titles = {f.stem for f in md_files}
    graph: dict[str, set[str]] = {t: set() for t in titles}

    for f in md_files:
        source = f.stem
        for target in _parse_wikilinks(f):
            if target in titles and target != source:
                graph[source].add(target)

    return graph


def _build_nx_undirected(graph: dict[str, set[str]]) -> nx.Graph:
    G: nx.Graph = nx.Graph()
    for node, targets in graph.items():
        G.add_node(node)
        for target in targets:
            G.add_edge(node, target)
    return G


def compute_report(graph: dict[str, set[str]]) -> GraphReport:
    """Compute structural metrics for an adjacency dict."""
    n = len(graph)
    if n == 0:
        return GraphReport(0, 0, [], [], 0.0, 0.0, 0.0, 0, [])

    G = _build_nx_undirected(graph)
    degree = dict(G.degree())
    edges = G.number_of_edges()

    orphans = sorted(node for node, deg in degree.items() if deg == 0)
    most_linked = sorted(degree.items(), key=lambda x: x[1], reverse=True)[:10]
    avg_degree = sum(degree.values()) / n
    max_edges = n * (n - 1) / 2
    density = edges / max_edges if max_edges > 0 else 0.0

    clustering = nx.average_clustering(G)
    connected_components = nx.number_connected_components(G)

    betweenness = nx.betweenness_centrality(G)
    betweenness_top = sorted(betweenness.items(), key=lambda x: x[1], reverse=True)[:5]

    return GraphReport(
        total_nodes=n,
        total_edges=edges,
        orphan_nodes=orphans,
        most_linked=most_linked,
        avg_degree=avg_degree,
        density=density,
        clustering=clustering,
        connected_components=connected_components,
        betweenness_top=betweenness_top,
    )


def format_report(report: GraphReport) -> str:
    lines: list[str] = [
        "Graph report",
        "============",
        f"Nodes:               {report.total_nodes}",
        f"Edges:               {report.total_edges}",
        f"Avg degree:          {report.avg_degree:.2f}",
        f"Density:             {report.density:.4f}",
        f"Clustering coeff:    {report.clustering:.4f}",
        f"Connected components:{report.connected_components:>2}",
        f"Orphan nodes:        {len(report.orphan_nodes)}",
    ]

    if report.orphan_nodes:
        lines.append("")
        lines.append("Orphans:")
        for node in report.orphan_nodes:
            lines.append(f"  - {node}")

    if report.most_linked:
        lines.append("")
        lines.append("Most linked (top 10):")
        for node, deg in report.most_linked:
            if deg > 0:
                lines.append(f"  {deg:3d}  {node}")

    if report.betweenness_top:
        lines.append("")
        lines.append("Top bridge concepts (betweenness centrality):")
        for node, score in report.betweenness_top:
            lines.append(f"  {score:.4f}  {node}")

    return "\n".join(lines)


def save_report(report: GraphReport, output_path: Path) -> None:
    """Write the formatted report to a text file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(format_report(report), encoding="utf-8")


def save_graph_data(graph: dict[str, set[str]], output_path: Path) -> None:
    """Write a human-readable adjacency list sorted by degree (most connected first).

    Format:
        Anger  (degree 7)
          → Fear
          → Sadness
          ...
    """
    undirected: dict[str, set[str]] = {}
    for node, targets in graph.items():
        undirected.setdefault(node, set())
        for t in targets:
            undirected[node].add(t)
            undirected.setdefault(t, set()).add(node)

    # Undirected degree = union of both directions.
    degrees = {n: len(neighbours) for n, neighbours in undirected.items()}
    sorted_nodes = sorted(degrees, key=lambda n: degrees[n], reverse=True)

    lines: list[str] = ["Graph adjacency list", "====================", ""]
    for node in sorted_nodes:
        neighbours = sorted(undirected[node])
        lines.append(f"{node}  (degree {degrees[node]})")
        for nb in neighbours:
            lines.append(f"  → {nb}")
        lines.append("")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")


def _draw_background_gradient(ax: plt.Axes, bg_dark: str, bg_mid: str) -> None:
    """Fill the axes with a radial gradient from bg_mid at the center to bg_dark at the edges."""
    size = 512
    y_idx, x_idx = np.ogrid[:size, :size]
    cx, cy = size / 2, size / 2
    r = np.sqrt((x_idx - cx) ** 2 + (y_idx - cy) ** 2)
    r = r / r.max()

    dark = np.array(mcolors.to_rgb(bg_dark))
    mid = np.array(mcolors.to_rgb(bg_mid))
    gradient = dark[np.newaxis, np.newaxis, :] + r[:, :, np.newaxis] * (dark - mid)[np.newaxis, np.newaxis, :]
    gradient = np.clip(gradient, 0, 1)

    ax.imshow(gradient, extent=ax.get_xlim() + ax.get_ylim(), aspect="auto", zorder=0, origin="upper")


def plot_graph(graph: dict[str, set[str]], output_path: Path) -> None:
    """Render a beautiful network visualization and save it as a PNG.



    Style: deep-space gradient background, nodes on a purple→teal gradient sized
    by degree, multi-layer glow, soft semi-transparent edges, clean labels.
    """
    BG_DARK = "#05050f"   # near-black with a hint of blue
    BG_MID  = "#0f0a2a"   # deep indigo at the centre
    EDGE_COLOR = "#c4b5fd"  # soft lavender edges

    G = nx.DiGraph()
    for node, targets in graph.items():
        G.add_node(node)
        for target in targets:
            G.add_edge(node, target)

    undirected = G.to_undirected()
    degrees = dict(undirected.degree())
    max_deg = max(degrees.values(), default=1) or 1

    # Spring layout — larger k spreads nodes out more for readability.
    n = len(undirected)
    k_val = 3.2 / (n ** 0.45 + 1e-6)
    pos = nx.spring_layout(undirected, seed=42, k=k_val, iterations=80)

    fig, ax = plt.subplots(figsize=(22, 15))
    fig.patch.set_facecolor(BG_DARK)
    ax.set_facecolor(BG_DARK)
    ax.set_aspect("equal")
    ax.axis("off")

    # Expand axes limits slightly so the gradient fills edge-to-edge.
    if pos:
        xs = [x for x, _ in pos.values()]
        ys = [y for _, y in pos.values()]
        pad = 0.25
        ax.set_xlim(min(xs) - pad, max(xs) + pad)
        ax.set_ylim(min(ys) - pad, max(ys) + pad)
    else:
        ax.set_xlim(-1, 1)
        ax.set_ylim(-1, 1)

    _draw_background_gradient(ax, BG_DARK, BG_MID)

    # --- Edges: three layers for a soft glow effect ---
    edge_params = [
        dict(width=4.0, alpha=0.03),   # outermost halo
        dict(width=1.8, alpha=0.08),   # mid glow
        dict(width=0.7, alpha=0.22),   # crisp core
    ]
    for params in edge_params:
        nx.draw_networkx_edges(
            undirected, pos, ax=ax,
            edge_color=EDGE_COLOR,
            arrows=False,
            **params,
        )

    # --- Node colors: #7c3aed (violet) → #06b6d4 (cyan) by degree ---
    color_low  = np.array(mcolors.to_rgb("#7c3aed"))
    color_high = np.array(mcolors.to_rgb("#06b6d4"))
    node_list = list(undirected.nodes())
    norms = [degrees[n] / max_deg for n in node_list]
    node_colors = [tuple(color_low + t * (color_high - color_low)) for t in norms]

    # Node sizes: 80 (isolated) → 700 (hub).
    node_sizes = [80 + 620 * (degrees[n] / max_deg) for n in node_list]

    # Three glow layers per node.
    for scale, alpha in [(9, 0.04), (4, 0.10), (1.8, 0.18), (1, 0.92)]:
        nx.draw_networkx_nodes(
            undirected, pos, nodelist=node_list, ax=ax,
            node_color=node_colors,
            node_size=[s * scale for s in node_sizes],
            alpha=alpha,
            linewidths=0,
        )

    # Thin bright ring on each node for definition.
    nx.draw_networkx_nodes(
        undirected, pos, nodelist=node_list, ax=ax,
        node_color="none",
        node_size=node_sizes,
        linewidths=0.6,
        edgecolors="#e2e8f0",
    )

    # --- Labels: offset above each node, size proportional to degree ---
    label_offset = 0.055
    label_pos = {n: (x, y + label_offset) for n, (x, y) in pos.items()}
    font_sizes = {n: 5.5 + 3.5 * (degrees[n] / max_deg) for n in node_list}
    for node, (lx, ly) in label_pos.items():
        ax.text(
            lx, ly, node,
            ha="center", va="bottom",
            fontsize=font_sizes[node],
            color="#e2e8f0",
            fontfamily="sans-serif",
            fontweight="semibold" if degrees[node] / max_deg > 0.5 else "normal",
            zorder=10,
        )

    # Subtle legend strip: degree → color.
    cmap = mcolors.LinearSegmentedColormap.from_list("deg", [color_low, color_high])
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(0, max_deg))
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=ax, orientation="vertical", fraction=0.018, pad=0.01, shrink=0.35)
    cbar.set_label("Degree", color="#94a3b8", fontsize=9, labelpad=8)
    cbar.ax.yaxis.set_tick_params(color="#94a3b8", labelcolor="#94a3b8", labelsize=7)
    cbar.outline.set_edgecolor("#334155")

    plt.tight_layout(pad=0.3)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=180, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
