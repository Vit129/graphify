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
