"""Code snippets for graph results: node_snippet / format_snippet / query-result snippets,
plus the CLI flags (`explain --snippet`, `query --snippet`) and the MCP get_snippet tool."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from networkx.readwrite import json_graph

import graphify.__main__ as mainmod
from graphify import serve as servemod
from graphify.build import build_from_json
from graphify.extract import extract
from graphify.snippet import format_snippet, node_snippet, snippets_for_query_result

SOURCE = (
    "import os\n"
    "\n"
    "def load_session():\n"
    "    a = 1\n"
    "    b = 2\n"
    "    return a + b\n"
    "\n"
    "class Store:\n"
    "    def save(self):\n"
    "        return 'x'\n"
)


def _project(tmp_path: Path):
    (tmp_path / "state.py").write_text(SOURCE, encoding="utf-8")
    result = extract([tmp_path / "state.py"], cache_root=tmp_path)
    G = build_from_json(result, directed=True, root=tmp_path)
    out = tmp_path / "graphify-out"
    out.mkdir(exist_ok=True)
    gp = out / "graph.json"
    gp.write_text(json.dumps(json_graph.node_link_data(G, edges="links")), encoding="utf-8")
    return G, gp


def _nid(G, label):
    return next(n for n, d in G.nodes(data=True) if d.get("label") == label)


def test_function_snippet_is_exactly_its_body(tmp_path: Path):
    G, _ = _project(tmp_path)
    s = node_snippet(G, _nid(G, "load_session()"), tmp_path)
    assert (s["file"], s["start"], s["end"], s["truncated"]) == ("state.py", 3, 6, False)
    assert s["lines"] == ["def load_session():", "    a = 1", "    b = 2", "    return a + b"]


def test_method_snippet_does_not_include_the_rest_of_the_class(tmp_path: Path):
    G, _ = _project(tmp_path)
    s = node_snippet(G, _nid(G, ".save()"), tmp_path)
    assert s["lines"] == ["    def save(self):", "        return 'x'"]


def test_long_body_is_truncated_with_the_real_extent_reported(tmp_path: Path):
    G, _ = _project(tmp_path)
    s = node_snippet(G, _nid(G, "load_session()"), tmp_path, max_lines=2)
    assert len(s["lines"]) == 2 and s["truncated"] is True and s["node_end"] == 6


def test_node_without_a_line_range_has_no_snippet(tmp_path: Path):
    G, _ = _project(tmp_path)
    G.add_node("doc", label="Idea", source_file="state.py", source_location="L1")
    assert node_snippet(G, "doc", tmp_path) is None


def test_file_outside_root_is_never_read(tmp_path: Path):
    G, _ = _project(tmp_path)
    outside = tmp_path.parent / "outside_snip.py"
    outside.write_text("SECRET = 1\n", encoding="utf-8")
    G.add_node("evil", label="evil()", source_file=str(outside), source_location="L1", end_line=1)
    assert node_snippet(G, "evil", tmp_path) is None


def test_format_snippet_numbers_lines_and_marks_truncation(tmp_path: Path):
    G, _ = _project(tmp_path)
    text = format_snippet("load_session()", node_snippet(G, _nid(G, "load_session()"), tmp_path, max_lines=2))
    assert "state.py:3-6" in text and "    3| def load_session():" in text
    assert "2 more line(s)" in text


def test_snippets_for_query_result_picks_code_nodes_and_skips_file_nodes(tmp_path: Path):
    G, _ = _project(tmp_path)
    result = (
        "Traversal: BFS depth=2 | Start: ['state.py'] | 3 nodes found\n\n"
        "NODE state.py [src=state.py loc=L1 community=0]\n"
        "NODE load_session() [src=state.py loc=L3 community=0]\n"
        "NODE .save() [src=state.py loc=L9 community=0]\n"
    )
    text = snippets_for_query_result(G, result, tmp_path, limit=5, max_lines=10)
    assert "load_session()" in text and ".save()" in text
    assert "import os" not in text  # the file node was skipped
    only_one = snippets_for_query_result(G, result, tmp_path, limit=1, max_lines=10)
    assert "load_session()" in only_one and ".save()" not in only_one


def test_cli_explain_snippet(tmp_path: Path, monkeypatch, capsys):
    _, gp = _project(tmp_path)
    monkeypatch.setattr(sys, "argv", ["graphify", "explain", "load_session()", "--snippet", "--graph", str(gp)])
    mainmod.main()
    out = capsys.readouterr().out
    assert "def load_session():" in out and "return a + b" in out


def test_cli_explain_without_flag_prints_no_code(tmp_path: Path, monkeypatch, capsys):
    _, gp = _project(tmp_path)
    monkeypatch.setattr(sys, "argv", ["graphify", "explain", "load_session()", "--graph", str(gp)])
    mainmod.main()
    assert "return a + b" not in capsys.readouterr().out


def test_cli_query_snippet(tmp_path: Path, monkeypatch, capsys):
    _, gp = _project(tmp_path)
    monkeypatch.setattr(sys, "argv", ["graphify", "query", "load_session", "--snippet", "--graph", str(gp)])
    mainmod.main()
    out = capsys.readouterr().out
    assert "return a + b" in out


def test_mcp_get_snippet(tmp_path: Path):
    G, gp = _project(tmp_path)
    out = servemod._tool_get_snippet_text(G, {"node": "load_session()"}, gp)
    assert "return a + b" in out
    assert "No node matching" in servemod._tool_get_snippet_text(G, {"node": "nope_nothing"}, gp)
