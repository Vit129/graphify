from __future__ import annotations

import json

import networkx as nx
from networkx.readwrite import json_graph

import graphify.__main__ as mainmod


def _write_graph(tmp_path):
    graph = nx.DiGraph()
    graph.add_node("entry", label="main", source_file="app.py", source_location="L1")
    graph.add_node("helper", label="helper", source_file="app.py", source_location="L5")
    graph.add_node("orphan", label="_orphan", source_file="util.py", source_location="L9")
    graph.add_edge("entry", "helper", relation="calls", context="call", confidence="EXTRACTED")
    graph_path = tmp_path / "graph.json"
    graph_path.write_text(json.dumps(json_graph.node_link_data(graph, edges="links")), encoding="utf-8")
    return graph_path


def test_dead_code_cli_flags_unreachable_private_function(monkeypatch, tmp_path, capsys):
    graph_path = _write_graph(tmp_path)
    monkeypatch.setattr(mainmod, "_check_skill_version", lambda _: None)
    monkeypatch.setattr(
        mainmod.sys,
        "argv",
        ["graphify", "dead-code", "--graph", str(graph_path)],
    )

    mainmod.main()

    out = capsys.readouterr().out
    assert "_orphan" in out
    assert "util.py" in out
    assert "helper" not in out
    assert "main" not in out


def test_dead_code_cli_top_n_limits_results(monkeypatch, tmp_path, capsys):
    graph = nx.DiGraph()
    graph.add_node("entry", label="main", source_file="app.py", source_location="L1")
    for i in range(3):
        graph.add_node(f"orphan{i}", label=f"_orphan{i}", source_file="util.py", source_location=f"L{i}")
    graph_path = tmp_path / "graph.json"
    graph_path.write_text(json.dumps(json_graph.node_link_data(graph, edges="links")), encoding="utf-8")

    monkeypatch.setattr(mainmod, "_check_skill_version", lambda _: None)
    monkeypatch.setattr(
        mainmod.sys,
        "argv",
        ["graphify", "dead-code", "--graph", str(graph_path), "--top-n", "1"],
    )

    mainmod.main()

    out = capsys.readouterr().out
    assert out.count("_orphan") == 1


def test_dead_code_cli_no_unreachable_functions(monkeypatch, tmp_path, capsys):
    graph = nx.DiGraph()
    graph.add_node("entry", label="main", source_file="app.py", source_location="L1")
    graph_path = tmp_path / "graph.json"
    graph_path.write_text(json.dumps(json_graph.node_link_data(graph, edges="links")), encoding="utf-8")

    monkeypatch.setattr(mainmod, "_check_skill_version", lambda _: None)
    monkeypatch.setattr(
        mainmod.sys,
        "argv",
        ["graphify", "dead-code", "--graph", str(graph_path)],
    )

    mainmod.main()

    out = capsys.readouterr().out
    assert "No unreachable functions found." in out
