"""MCP search_text tool: registered, dispatched, and returns hits with their enclosing symbol."""
from __future__ import annotations

import json
from pathlib import Path

from graphify import serve as servemod
from graphify.build import build_from_json
from graphify.extract import extract


def _graph(tmp_path: Path):
    (tmp_path / "state.py").write_text(
        "def load_session():\n    return 'needle here'\n", encoding="utf-8"
    )
    result = extract([tmp_path / "state.py"], cache_root=tmp_path)
    G = build_from_json(result, directed=True, root=tmp_path)
    out = tmp_path / "graphify-out"
    out.mkdir(exist_ok=True)
    gp = out / "graph.json"
    gp.write_text(json.dumps({"nodes": [], "links": []}), encoding="utf-8")
    return G, gp


def test_search_text_text_returns_hit_with_enclosing_symbol(tmp_path: Path):
    G, gp = _graph(tmp_path)
    out = servemod._tool_search_text_text(G, {"pattern": "needle"}, gp)
    assert "state.py:2:" in out and "[in load_session()]" in out


def test_search_text_text_reports_invalid_regex_instead_of_raising(tmp_path: Path):
    G, gp = _graph(tmp_path)
    assert servemod._tool_search_text_text(G, {"pattern": "(", "regex": True}, gp).startswith("Error:")


def test_search_text_is_registered_as_an_mcp_tool():
    src = Path(servemod.__file__).read_text(encoding="utf-8")
    assert 'name="search_text"' in src and '"search_text": _tool_search_text' in src
