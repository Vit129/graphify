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


def test_staleness_banner_in_mcp_match_pattern(tmp_path):
    import json
    import pytest
    pytest.importorskip("mcp")
    pytest.importorskip("starlette")
    from starlette.testclient import TestClient

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

    app = servemod._build_http_app(str(graph_path), json_response=True)
    with TestClient(app, base_url="http://127.0.0.1") as client:
        init = client.post("/mcp", headers={"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}, json={
            "jsonrpc": "2.0", "id": 1, "method": "initialize",
            "params": {"protocolVersion": "2025-03-26", "capabilities": {}, "clientInfo": {"name": "test", "version": "0"}},
        })
        headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream", "mcp-session-id": init.headers.get("mcp-session-id")}
        client.post("/mcp", headers=headers, json={"jsonrpc": "2.0", "method": "notifications/initialized"})

        # 1. Query for matched_func -> unrelated.py is stale, but matched_func.py is NOT. No banner should appear.
        resp = client.post("/mcp", headers=headers, json={
            "jsonrpc": "2.0", "id": 2, "method": "tools/call",
            "params": {"name": "match_pattern", "arguments": {"pattern": "MATCH (a) WHERE a.label CONTAINS 'matched' RETURN a.label"}},
        })
        out = resp.json()["result"]["content"][0]["text"]
        assert "matched_func" in out
        assert "staleness notice" not in out
        assert "unrelated.py" not in out

        # 2. Now touch matched.py -> query should now include staleness banner for matched.py
        os.utime(f_matched, (time.time() + 20, time.time() + 20))
        resp2 = client.post("/mcp", headers=headers, json={
            "jsonrpc": "2.0", "id": 3, "method": "tools/call",
            "params": {"name": "match_pattern", "arguments": {"pattern": "MATCH (a) WHERE a.label CONTAINS 'matched' RETURN a.label"}},
        })
        out2 = resp2.json()["result"]["content"][0]["text"]
        assert "staleness notice" in out2
        assert "matched.py" in out2


def test_staleness_banner_coverage_for_other_tools(tmp_path):
    import json
    import pytest
    pytest.importorskip("mcp")
    pytest.importorskip("starlette")
    from starlette.testclient import TestClient

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

    app = servemod._build_http_app(str(graph_path), json_response=True)
    with TestClient(app, base_url="http://127.0.0.1") as client:
        init = client.post("/mcp", headers={"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}, json={
            "jsonrpc": "2.0", "id": 1, "method": "initialize",
            "params": {"protocolVersion": "2025-03-26", "capabilities": {}, "clientInfo": {"name": "test", "version": "0"}},
        })
        headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream", "mcp-session-id": init.headers.get("mcp-session-id")}
        client.post("/mcp", headers=headers, json={"jsonrpc": "2.0", "method": "notifications/initialized"})

        # get_community
        resp = client.post("/mcp", headers=headers, json={
            "jsonrpc": "2.0", "id": 2, "method": "tools/call",
            "params": {"name": "get_community", "arguments": {"community_id": 0}},
        })
        out = resp.json()["result"]["content"][0]["text"]
        assert "staleness notice" in out
        assert "app.py" in out

        # god_nodes
        resp = client.post("/mcp", headers=headers, json={
            "jsonrpc": "2.0", "id": 3, "method": "tools/call",
            "params": {"name": "god_nodes", "arguments": {}},
        })
        out = resp.json()["result"]["content"][0]["text"]
        assert "staleness notice" in out
        assert "app.py" in out

        # dead_code
        resp = client.post("/mcp", headers=headers, json={
            "jsonrpc": "2.0", "id": 4, "method": "tools/call",
            "params": {"name": "dead_code", "arguments": {}},
        })
        out = resp.json()["result"]["content"][0]["text"]
        assert "staleness notice" in out
        assert "app.py" in out

        # shortest_path
        resp = client.post("/mcp", headers=headers, json={
            "jsonrpc": "2.0", "id": 5, "method": "tools/call",
            "params": {"name": "shortest_path", "arguments": {"source": "app()", "target": "_internal()"}},
        })
        out = resp.json()["result"]["content"][0]["text"]
        assert "staleness notice" in out
        assert "app.py" in out

        # query_graph
        resp = client.post("/mcp", headers=headers, json={
            "jsonrpc": "2.0", "id": 6, "method": "tools/call",
            "params": {"name": "query_graph", "arguments": {"question": "app"}},
        })
        out = resp.json()["result"]["content"][0]["text"]
        assert "staleness notice" in out
        assert "app.py" in out

