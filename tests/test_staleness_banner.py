from __future__ import annotations

import os
import time
from pathlib import Path
import networkx as nx
from networkx.readwrite import json_graph

from graphify.staleness import find_stale_files, format_staleness_banner
import graphify.serve as servemod


def test_find_stale_files_identifies_modified_files(tmp_path):
    project_root = tmp_path / "my_project"
    project_root.mkdir()
    graph_dir = project_root / "graphify-out"
    graph_dir.mkdir()
    graph_path = graph_dir / "graph.json"

    # Create source files
    f1 = project_root / "src" / "app.py"
    f1.parent.mkdir(parents=True)
    f1.write_text("def main(): pass\n", encoding="utf-8")

    f2 = project_root / "src" / "utils.py"
    f2.write_text("def helper(): pass\n", encoding="utf-8")

    # Set file timestamps older than graph
    past = time.time() - 100
    os.utime(f1, (past, past))
    os.utime(f2, (past, past))

    # Create graph.json with current timestamp
    graph_path.write_text("{}", encoding="utf-8")
    graph_time = time.time() - 50
    os.utime(graph_path, (graph_time, graph_time))

    # Before modifying f1, no files are stale
    assert find_stale_files(graph_path, ["src/app.py", "src/utils.py"], project_root) == []
    assert format_staleness_banner(graph_path, ["src/app.py", "src/utils.py"], project_root) == ""

    # Modify f1 (newer timestamp than graph)
    future = time.time()
    os.utime(f1, (future, future))

    stale = find_stale_files(graph_path, ["src/app.py", "src/utils.py"], project_root)
    assert stale == ["src/app.py"]

    banner = format_staleness_banner(graph_path, ["src/app.py", "src/utils.py"], project_root)
    assert "1 file(s) modified since graph was built" in banner
    assert "src/app.py" in banner


def test_find_stale_files_handles_missing_files_gracefully(tmp_path):
    graph_path = tmp_path / "graphify-out" / "graph.json"
    graph_path.parent.mkdir()
    graph_path.write_text("{}", encoding="utf-8")

    assert find_stale_files(graph_path, ["non_existent.py", ""]) == []
    assert format_staleness_banner(graph_path, ["non_existent.py"]) == ""


def test_staleness_banner_in_mcp_get_node(tmp_path):
    project_root = tmp_path / "repo"
    project_root.mkdir()
    graph_dir = project_root / "graphify-out"
    graph_dir.mkdir()
    graph_path = graph_dir / "graph.json"

    src_file = project_root / "handler.py"
    src_file.write_text("def handle(): pass\n", encoding="utf-8")

    # Set old timestamp on src_file
    past = time.time() - 100
    os.utime(src_file, (past, past))

    G = nx.DiGraph()
    G.add_node("n1", label="handle()", source_file="handler.py", source_location="L1", file_type="function")
    graph_path.write_text("{}", encoding="utf-8")
    graph_time = time.time() - 50
    os.utime(graph_path, (graph_time, graph_time))

    # Fresh: no banner
    out = servemod._tool_get_node_text(G, {"label": "handle()"}, graph_path=graph_path)
    assert "staleness notice" not in out
    assert "Node: handle()" in out

    # Make handler.py stale
    os.utime(src_file, (time.time(), time.time()))

    out_stale = servemod._tool_get_node_text(G, {"label": "handle()"}, graph_path=graph_path)
    assert "staleness notice" in out_stale
    assert "handler.py" in out_stale
    assert "Node: handle()" in out_stale


def test_parse_and_execute_pattern_return_matched_nodes():
    from graphify.pattern_query import parse_and_execute_pattern
    G = nx.DiGraph()
    G.add_node("n1", label="login()", source_file="auth.py", file_type="function")
    G.add_node("n2", label="logout()", source_file="auth.py", file_type="function")
    G.add_node("n3", label="pay()", source_file="billing.py", file_type="function")
    G.add_edge("n1", "n2", relation="calls")

    res, matched = parse_and_execute_pattern(
        G, "MATCH (a)-[:calls]->(b) RETURN a.label, b.label", as_dict=True, return_matched_nodes=True
    )
    assert len(res) == 1
    assert matched == {"n1", "n2"}

    text, matched_text = parse_and_execute_pattern(
        G, "MATCH (a:function) WHERE a.label CONTAINS 'pay' RETURN a.label", as_dict=False, return_matched_nodes=True
    )
    assert "pay()" in text
    assert matched_text == {"n3"}

    # No match returns empty set
    empty_res, empty_matched = parse_and_execute_pattern(
        G, "MATCH (a:nonexistent) RETURN a.label", as_dict=False, return_matched_nodes=True
    )
    assert empty_matched == set()
    assert "No matching patterns" in empty_res


def test_staleness_banner_in_match_pattern(tmp_path):
    """Drives _tool_match_pattern_text directly -- a plain module-level
    function over G/arguments/graph_path, same as _shortest_path_text and
    _tool_get_node_text -- rather than through the mcp/starlette HTTP
    transport, so this test actually runs under the documented
    `uv run pytest tests/ -q` (neither mcp nor starlette is a dev dependency;
    a version of this test gated behind pytest.importorskip("mcp") silently
    skips under that command and never actually verifies the fix)."""
    import json

    project_root = tmp_path / "repo"
    project_root.mkdir()
    graph_dir = project_root / "graphify-out"
    graph_dir.mkdir()
    graph_path = graph_dir / "graph.json"

    f_matched = project_root / "matched.py"
    f_matched.write_text("def matched_func(): pass\n", encoding="utf-8")
    f_unrelated = project_root / "unrelated.py"
    f_unrelated.write_text("def unrelated_func(): pass\n", encoding="utf-8")

    past = time.time() - 100
    os.utime(f_matched, (past, past))
    future = time.time() + 10
    os.utime(f_unrelated, (future, future))

    graph_data = {
        "directed": True,
        "nodes": [
            {"id": "n1", "label": "matched_func()", "source_file": "matched.py", "file_type": "function", "community": 0},
            {"id": "n2", "label": "unrelated_func()", "source_file": "unrelated.py", "file_type": "function", "community": 0},
        ],
        "edges": [],
    }
    graph_path.write_text(json.dumps(graph_data), encoding="utf-8")
    graph_time = time.time() - 50
    os.utime(graph_path, (graph_time, graph_time))

    G = servemod._load_graph(str(graph_path))

    # 1. Query for matched_func -> unrelated.py is stale, but matched.py is NOT. No banner should appear.
    out = servemod._tool_match_pattern_text(
        G, {"pattern": "MATCH (a) WHERE a.label CONTAINS 'matched' RETURN a.label"}, str(graph_path)
    )
    assert "matched_func" in out
    assert "staleness notice" not in out
    assert "unrelated.py" not in out

    # 2. Now touch matched.py -> query should now include a staleness banner for matched.py
    os.utime(f_matched, (time.time() + 20, time.time() + 20))
    out2 = servemod._tool_match_pattern_text(
        G, {"pattern": "MATCH (a) WHERE a.label CONTAINS 'matched' RETURN a.label"}, str(graph_path)
    )
    assert "staleness notice" in out2
    assert "matched.py" in out2


def test_staleness_banner_coverage_for_other_tools(tmp_path):
    """Same rationale as test_staleness_banner_in_match_pattern -- drives
    _tool_get_community_text/_tool_god_nodes_text/_tool_dead_code_text
    directly rather than through the mcp/starlette HTTP transport."""
    import json

    project_root = tmp_path / "repo"
    project_root.mkdir()
    graph_dir = project_root / "graphify-out"
    graph_dir.mkdir()
    graph_path = graph_dir / "graph.json"

    f1 = project_root / "app.py"
    f1.write_text("def app(): pass\n", encoding="utf-8")
    future = time.time() + 10
    os.utime(f1, (future, future))

    graph_data = {
        "directed": True,
        "nodes": [
            {"id": "n1", "label": "app()", "source_file": "app.py", "file_type": "function", "community": 0, "community_name": "Core"},
            {"id": "n2", "label": "_internal()", "source_file": "app.py", "file_type": "function", "community": 0},
            {"id": "n3", "label": "_internal2()", "source_file": "app.py", "file_type": "function", "community": 0},
            {"id": "n4", "label": "_orphan_dead()", "source_file": "app.py", "file_type": "function", "community": 0},
        ],
        "edges": [
            {"source": "n1", "target": "n2", "relation": "calls", "confidence": "EXTRACTED", "_src": "n1", "_tgt": "n2"},
            {"source": "n1", "target": "n3", "relation": "calls", "confidence": "EXTRACTED", "_src": "n1", "_tgt": "n3"},
            {"source": "n4", "target": "n2", "relation": "calls", "confidence": "EXTRACTED", "_src": "n4", "_tgt": "n2"},
            {"source": "n4", "target": "n3", "relation": "calls", "confidence": "EXTRACTED", "_src": "n4", "_tgt": "n3"},
        ],
    }
    graph_path.write_text(json.dumps(graph_data), encoding="utf-8")
    graph_time = time.time() - 50
    os.utime(graph_path, (graph_time, graph_time))

    G = servemod._load_graph(str(graph_path))
    communities = servemod._communities_from_graph(G)

    out = servemod._tool_get_community_text(G, communities, {"community_id": 0}, str(graph_path))
    assert "staleness notice" in out
    assert "app.py" in out

    out = servemod._tool_god_nodes_text(G, {}, str(graph_path))
    assert "staleness notice" in out
    assert "app.py" in out

    out = servemod._tool_dead_code_text(G, {}, str(graph_path))
    assert "staleness notice" in out
    assert "app.py" in out

    # shortest_path: already a module-level _shortest_path_text, unchanged
    # by this branch -- confirms it still gets a banner alongside the tools
    # actually touched here.
    out = servemod._shortest_path_text(
        G, {"source": "app()", "target": "_internal()"}, str(graph_path)
    )
    assert "staleness notice" in out
    assert "app.py" in out

    # query_graph: exercises the _query_graph_text(..., return_nodes=True) +
    # format_staleness_banner wiring _tool_query_graph's closure uses --
    # replicated directly here rather than via the closure itself, since the
    # closure only exists inside _build_server (which imports mcp at the top
    # regardless of which tool is actually being tested).
    from graphify.query import _query_graph_text
    from graphify.staleness import format_staleness_banner
    result, cited_files = _query_graph_text(G, "app", return_nodes=True)
    banner = format_staleness_banner(str(graph_path), cited_files)
    out = banner + result
    assert "staleness notice" in out
    assert "app.py" in out

