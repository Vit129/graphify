import json
import re
import tempfile
from datetime import date, timedelta
from pathlib import Path
from graphify.build import build_from_json
from graphify.cluster import cluster
from graphify.export import (
    to_json, to_cypher, to_graphml, to_html,
    _prune_old_backups,
)

FIXTURES = Path(__file__).parent / "fixtures"

def make_graph():
    return build_from_json(json.loads((FIXTURES / "extraction.json").read_text()))

def test_to_json_creates_file():
    G = make_graph()
    communities = cluster(G)
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "graph.json"
        to_json(G, communities, str(out))
        assert out.exists()

def test_to_json_valid_json():
    G = make_graph()
    communities = cluster(G)
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "graph.json"
        to_json(G, communities, str(out))
        data = json.loads(out.read_text())
        assert "nodes" in data
        assert "links" in data

def test_to_json_nodes_have_community():
    G = make_graph()
    communities = cluster(G)
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "graph.json"
        to_json(G, communities, str(out))
        data = json.loads(out.read_text())
        for node in data["nodes"]:
            assert "community" in node

def test_to_cypher_creates_file():
    G = make_graph()
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "cypher.txt"
        to_cypher(G, str(out))
        assert out.exists()

def test_to_cypher_contains_merge_statements():
    G = make_graph()
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "cypher.txt"
        to_cypher(G, str(out))
        content = out.read_text()
        assert "MERGE" in content

def test_to_graphml_creates_file():
    G = make_graph()
    communities = cluster(G)
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "graph.graphml"
        to_graphml(G, communities, str(out))
        assert out.exists()

def test_to_graphml_valid_xml():
    G = make_graph()
    communities = cluster(G)
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "graph.graphml"
        to_graphml(G, communities, str(out))
        content = out.read_text()
        assert "<graphml" in content
        assert "<node" in content

def test_to_graphml_has_community_attribute():
    G = make_graph()
    communities = cluster(G)
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "graph.graphml"
        to_graphml(G, communities, str(out))
        content = out.read_text()
        assert "community" in content

def test_to_graphml_tolerates_none_attribute_values():
    """nx.write_graphml raises ValueError on a None attribute value; to_graphml
    must coerce None -> "" so a node/edge with a null field still exports (#1502)."""
    G = make_graph()
    communities = cluster(G)
    # Inject a None-valued attribute on one node and one edge.
    a_node = next(iter(G.nodes()))
    G.nodes[a_node]["nullable_field"] = None
    if G.number_of_edges():
        u, v = next(iter(G.edges()))
        G.edges[u, v]["nullable_field"] = None
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "graph.graphml"
        to_graphml(G, communities, str(out))  # must not raise
        content = out.read_text()
        assert "<graphml" in content

def test_to_html_creates_file():
    G = make_graph()
    communities = cluster(G)
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "graph.html"
        to_html(G, communities, str(out))
        assert out.exists()

def test_to_html_contains_visjs():
    G = make_graph()
    communities = cluster(G)
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "graph.html"
        to_html(G, communities, str(out))
        content = out.read_text()
        assert "vis-network" in content


def test_to_html_pins_visjs_version_with_sri():
    """vis-network script tag must use a pinned versioned URL with a sha384
    Subresource Integrity hash and crossorigin=anonymous. Without this,
    a compromised CDN could ship arbitrary JavaScript into every rendered
    graph viewer. The hash was verified against the upstream file at
    https://unpkg.com/vis-network@9.1.6/standalone/umd/vis-network.min.js
    (sha384-Ux6phic9PEHJ38YtrijhkzyJ8yQlH8i/+buBR8s3mAZOJrP1gwyvAcIYl3GWtpX1).
    Bumping the vis-network version MUST update both the URL and the hash.
    """
    G = make_graph()
    communities = cluster(G)
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "graph.html"
        to_html(G, communities, str(out))
        content = out.read_text()

    # Versioned URL — unversioned `vis-network/standalone/...` is rejected.
    assert "vis-network@9.1.6/standalone/umd/vis-network.min.js" in content
    assert "https://unpkg.com/vis-network/standalone" not in content

    # SRI integrity attribute pinning the known-good hash.
    assert 'integrity="sha384-Ux6phic9PEHJ38YtrijhkzyJ8yQlH8i/+buBR8s3mAZOJrP1gwyvAcIYl3GWtpX1"' in content

    # crossorigin="anonymous" is required for SRI on cross-origin scripts.
    assert 'crossorigin="anonymous"' in content

def test_to_html_contains_search():
    G = make_graph()
    communities = cluster(G)
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "graph.html"
        to_html(G, communities, str(out))
        content = out.read_text()
        assert "search" in content.lower()

def test_to_html_contains_legend_with_labels():
    G = make_graph()
    communities = cluster(G)
    labels = {cid: f"Group {cid}" for cid in communities}
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "graph.html"
        to_html(G, communities, str(out), community_labels=labels)
        content = out.read_text()
        assert "Group 0" in content

def test_to_html_contains_nodes_and_edges():
    G = make_graph()
    communities = cluster(G)
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "graph.html"
        to_html(G, communities, str(out))
        content = out.read_text()
        assert "RAW_NODES" in content
        assert "RAW_EDGES" in content

def test_to_html_contains_calls_lens():
    # 'calls' lens: code-symbol-only, non-collapsed view (file_type != 'code'
    # hidden, edges restricted to REL_WHITELIST) — distinct from the existing
    # community/file/deps lenses.
    G = make_graph()
    communities = cluster(G)
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "graph.html"
        to_html(G, communities, str(out))
        content = out.read_text()
        assert "lens-btn-calls" in content
        assert "switchLens('calls')" in content
        assert "REL_WHITELIST" in content
        assert content.count("REL_WHITELIST = new Set(") == 1

def test_to_html_search_respects_lens_and_has_type_filter():
    # Search gaps closed together: (1) results must respect the active lens
    # (isNodeHidden) so a hidden concept/rationale node in the Calls lens can't
    # surface and then fail to focus, (2) label matching is tokenized
    # (camelCase/snake_case split, same rule as the CLI's query.py _tokenize),
    # (3) source_file is also searchable, (4) a file_type dropdown filter.
    G = make_graph()
    communities = cluster(G)
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "graph.html"
        to_html(G, communities, str(out))
        content = out.read_text()
        assert "search-type-filter" in content
        assert "function tokenize(text)" in content
        assert "function runSearch()" in content
        assert "if (isNodeHidden(n)) return;" in content
        assert "typeFilter !== 'all' && n.file_type !== typeFilter" in content
        assert "file.includes(q)" in content

def test_to_html_calls_lens_legend_counts_code_only():
    # Legend/select-all counts for the Calls lens must come from code-type
    # nodes only (fileScopedNodes), or the displayed count wouldn't match what
    # the lens actually shows (a file with only concept/rationale nodes has
    # nothing visible in Calls, so it shouldn't inflate the file count/legend).
    G = make_graph()
    communities = cluster(G)
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "graph.html"
        to_html(G, communities, str(out))
        content = out.read_text()
        assert "function fileScopedNodes()" in content
        assert "fileScopedNodes().map(n => n.source_file" in content
        assert "fileScopedNodes().forEach(n => { const f = n.source_file" in content


def test_to_html_member_counts_accepted():
    """to_html accepts member_counts without raising."""
    G = make_graph()
    communities = cluster(G)
    member_counts = {cid: len(members) for cid, members in communities.items()}
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "graph.html"
        to_html(G, communities, str(out), member_counts=member_counts)
        assert out.exists()


def _vis_nodes_from_html(content: str) -> list:
    """Extract the RAW_NODES JSON array embedded in the generated HTML."""
    m = re.search(r"const RAW_NODES = (\[.*?\]);", content, re.DOTALL)
    assert m, "RAW_NODES not found in HTML"
    return json.loads(m.group(1).replace("<\\/", "</"))


def test_to_html_annotated_node_gets_learning_status_and_ring():
    """A node with an overlay entry gets learning_status + learning_stale fields,
    a status-colored ring (border), and a Lesson line in its hover title."""
    G = make_graph()
    communities = cluster(G)
    overlay = {
        "n_transformer": {"status": "preferred", "uses": 3, "score": 2.4,
                          "stale": False, "neg": 0},
    }
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "graph.html"
        to_html(G, communities, str(out), learning_overlay=overlay)
        content = out.read_text()
    nodes = {n["id"]: n for n in _vis_nodes_from_html(content)}
    ann = nodes["n_transformer"]
    assert ann["learning_status"] == "preferred"
    assert ann["learning_stale"] is False
    assert ann["color"]["border"] == "#22c55e"  # green ring for preferred
    assert ann.get("borderWidth") == 3
    assert "Lesson: preferred source" in ann["title"]
    # An un-annotated node carries no learning fields.
    other = next(n for nid, n in nodes.items() if nid != "n_transformer")
    assert "learning_status" not in other
    assert "learning_stale" not in other


def test_to_html_contested_stale_node_gets_dashed_desaturated_ring():
    G = make_graph()
    communities = cluster(G)
    overlay = {
        "n_transformer": {"status": "contested", "uses": 2, "neg": 1,
                          "verdict": "dead end", "stale": True},
    }
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "graph.html"
        to_html(G, communities, str(out), learning_overlay=overlay)
        content = out.read_text()
    ann = {n["id"]: n for n in _vis_nodes_from_html(content)}["n_transformer"]
    assert ann["learning_status"] == "contested"
    assert ann["learning_stale"] is True
    assert ann["color"]["border"] == "#9ca3af"  # desaturated when stale
    assert ann["shapeProperties"]["borderDashes"] == [4, 4]
    assert "code changed" in ann["title"]


def test_to_html_unannotated_identical_to_pre_feature():
    """With no overlay, the HTML is byte-identical whether learning_overlay is
    omitted or passed empty — no learning fields leak into the un-annotated render."""
    G = make_graph()
    communities = cluster(G)
    with tempfile.TemporaryDirectory() as tmp:
        a = Path(tmp) / "a.html"
        b = Path(tmp) / "b.html"
        to_html(G, communities, str(a))
        to_html(G, communities, str(b), learning_overlay={})
        # Output path appears in the title, so compare with paths normalized out.
        ca = a.read_text().replace("a.html", "X.html")
        cb = b.read_text().replace("b.html", "X.html")
    assert ca == cb
    assert "learning_status" not in ca



def test_backup_no_graph_json(tmp_path):
    """No graph.json → no backup."""
    from graphify.export import backup_if_protected
    assert backup_if_protected(tmp_path) is None


def test_backup_no_markers(tmp_path):
    """graph.json present but no sentinel and no curated labels → no backup."""
    from graphify.export import backup_if_protected
    (tmp_path / "graph.json").write_text('{"nodes":[],"links":[]}')
    assert backup_if_protected(tmp_path) is None


def test_backup_semantic_marker(tmp_path):
    """graph.json + .graphify_semantic_marker → backup taken."""
    from graphify.export import backup_if_protected
    (tmp_path / "graph.json").write_text('{"nodes":[],"links":[]}')
    (tmp_path / "GRAPH_REPORT.md").write_text("# Report")
    (tmp_path / ".graphify_semantic_marker").write_text('{"output_tokens": 1234}')
    result = backup_if_protected(tmp_path)
    assert result is not None
    assert result.is_dir()
    assert (result / "graph.json").exists()
    assert (result / "GRAPH_REPORT.md").exists()
    assert (result / ".graphify_semantic_marker").exists()


def test_backup_curated_labels(tmp_path):
    """graph.json + non-default label in .graphify_labels.json → backup taken."""
    import json
    from graphify.export import backup_if_protected
    (tmp_path / "graph.json").write_text('{"nodes":[],"links":[]}')
    (tmp_path / ".graphify_labels.json").write_text(json.dumps({"0": "Auth Pipeline", "1": "Community 1"}))
    result = backup_if_protected(tmp_path)
    assert result is not None


def test_backup_default_labels_only(tmp_path):
    """All-default labels → no backup (not curated)."""
    import json
    from graphify.export import backup_if_protected
    (tmp_path / "graph.json").write_text('{"nodes":[],"links":[]}')
    (tmp_path / ".graphify_labels.json").write_text(json.dumps({"0": "Community 0", "1": "Community 1"}))
    assert backup_if_protected(tmp_path) is None


def test_backup_same_day_no_accumulation(tmp_path):
    """Same content on same day returns existing backup dir without re-copying."""
    from graphify.export import backup_if_protected
    from datetime import date
    (tmp_path / "graph.json").write_text('{"nodes":[],"links":[]}')
    (tmp_path / ".graphify_semantic_marker").write_text("{}")
    b1 = backup_if_protected(tmp_path)
    b2 = backup_if_protected(tmp_path)
    assert b1 is not None and b2 is not None
    assert b1 == b2  # same dir, no _2 accumulation
    assert b1.name == date.today().isoformat()


def test_backup_same_day_changed_content(tmp_path):
    """Changed graph.json on same day overwrites the existing backup in place."""
    from graphify.export import backup_if_protected
    from datetime import date
    (tmp_path / "graph.json").write_text('{"nodes":[],"links":[]}')
    (tmp_path / ".graphify_semantic_marker").write_text("{}")
    b1 = backup_if_protected(tmp_path)
    (tmp_path / "graph.json").write_text('{"nodes":[{"id":"x"}],"links":[]}')
    b2 = backup_if_protected(tmp_path)
    assert b1 == b2  # still one folder per day
    assert (b2 / "graph.json").read_text() == '{"nodes":[{"id":"x"}],"links":[]}'


def test_backup_env_disable(tmp_path, monkeypatch):
    """GRAPHIFY_NO_BACKUP=1 disables backup entirely."""
    from graphify.export import backup_if_protected
    monkeypatch.setenv("GRAPHIFY_NO_BACKUP", "1")
    (tmp_path / "graph.json").write_text('{"nodes":[],"links":[]}')
    (tmp_path / ".graphify_semantic_marker").write_text("{}")
    assert backup_if_protected(tmp_path) is None


def test_prune_old_backups_removes_stale_dirs(tmp_path):
    """Dated dirs older than keep_days are deleted; recent ones survive."""
    old_dir = tmp_path / (date.today() - timedelta(days=30)).isoformat()
    old_dir_suffixed = tmp_path / f"{(date.today() - timedelta(days=20)).isoformat()}_2"
    recent_dir = tmp_path / (date.today() - timedelta(days=1)).isoformat()
    for d in (old_dir, old_dir_suffixed, recent_dir):
        d.mkdir()
        (d / "graph.json").write_text("{}")

    _prune_old_backups(tmp_path, keep_days=14)

    assert not old_dir.exists()
    assert not old_dir_suffixed.exists()
    assert recent_dir.exists()


def test_prune_old_backups_env_override(tmp_path, monkeypatch):
    """GRAPHIFY_BACKUP_KEEP_DAYS overrides the default retention window."""
    monkeypatch.setenv("GRAPHIFY_BACKUP_KEEP_DAYS", "1")
    two_days_old = tmp_path / (date.today() - timedelta(days=2)).isoformat()
    two_days_old.mkdir()

    _prune_old_backups(tmp_path)

    assert not two_days_old.exists()


def test_backup_if_protected_prunes_stale_dirs(tmp_path):
    """backup_if_protected() itself triggers pruning, not just the helper."""
    from graphify.export import backup_if_protected
    stale = tmp_path / (date.today() - timedelta(days=30)).isoformat()
    stale.mkdir()
    (tmp_path / "graph.json").write_text('{"nodes":[],"links":[]}')
    (tmp_path / ".graphify_semantic_marker").write_text("{}")

    backup_if_protected(tmp_path)

    assert not stale.exists()
