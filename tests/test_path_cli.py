"""Regression tests for `graphify path` arrow direction (#849)."""
from __future__ import annotations
import json
import networkx as nx
from networkx.readwrite import json_graph
import graphify.__main__ as mainmod


def _write_graph(tmp_path):
    graph_data = {
        "directed": False, "multigraph": False, "graph": {},
        "nodes": [
            {"id": "create_patch", "label": "createPatchHandler()",
             "source_file": "server/create-patch-handler.ts", "community": 0},
            {"id": "validate", "label": "validateSanitySession()",
             "source_file": "server/sanity-validate-session.ts", "community": 0},
        ],
        "links": [
            {"source": "create_patch", "target": "validate",
             "relation": "calls", "confidence": "EXTRACTED"},
        ],
    }
    p = tmp_path / "graph.json"
    p.write_text(json.dumps(graph_data))
    return p


def _run(monkeypatch, graph_path, src, tgt, capsys):
    monkeypatch.setattr(mainmod, "_check_skill_version", lambda _: None)
    monkeypatch.setattr(mainmod.sys, "argv",
        ["graphify", "path", src, tgt, "--graph", str(graph_path)])
    mainmod.main()
    return capsys.readouterr().out


def test_forward_arrow(monkeypatch, tmp_path, capsys):
    p = _write_graph(tmp_path)
    out = _run(monkeypatch, p, "createPatchHandler", "validateSanitySession", capsys)
    assert "Shortest path (1 hops):" in out
    assert "createPatchHandler() --calls [EXTRACTED]--> validateSanitySession()" in out


def test_reverse_arrow(monkeypatch, tmp_path, capsys):
    p = _write_graph(tmp_path)
    out = _run(monkeypatch, p, "validateSanitySession", "createPatchHandler", capsys)
    assert "Shortest path (1 hops):" in out
    assert "validateSanitySession() <--calls [EXTRACTED]-- createPatchHandler()" in out
    assert "validateSanitySession() --calls [EXTRACTED]--> createPatchHandler()" not in out


def _write_duplicate_name_graph(tmp_path):
    """Three identically-labeled "Stats" nodes across different files (the
    real failure found dogfooding a bilingual content repo: parallel
    English/Japanese progress trackers both titled "Stats", plus a third
    unrelated one) - only stats_b is actually reachable from "Overview"."""
    graph_data = {
        "directed": False, "multigraph": False, "graph": {},
        "nodes": [
            {"id": "overview", "label": "Overview", "source_file": "root.md", "community": 0},
            {"id": "stats_a", "label": "Stats", "source_file": "english/progress.md", "community": 1},
            {"id": "stats_b", "label": "Stats", "source_file": "japanese/progress.md", "community": 0},
            {"id": "stats_c", "label": "Stats", "source_file": "other/progress.md", "community": 2},
        ],
        "links": [
            {"source": "overview", "target": "stats_b", "relation": "contains", "confidence": "EXTRACTED"},
        ],
    }
    p = tmp_path / "graph.json"
    p.write_text(json.dumps(graph_data))
    return p


def test_path_tries_all_tied_candidates_before_giving_up(monkeypatch, tmp_path, capsys):
    """When the target name resolves to several equally-scored nodes (a
    duplicate heading/symbol across files), path must try every tied
    candidate - not just whichever ties first - before reporting no path.
    Previously an arbitrary tied pick that happened to be disconnected would
    silently report "No path found" even though a different tied candidate
    (stats_b) was reachable."""
    p = _write_duplicate_name_graph(tmp_path)
    out = _run(monkeypatch, p, "Overview", "Stats", capsys)
    assert "Shortest path (1 hops):" in out
    assert "Overview --contains [EXTRACTED]--> Stats" in out


def test_path_ambiguous_warning_lists_all_tied_candidates(monkeypatch, tmp_path, capsys):
    p = _write_duplicate_name_graph(tmp_path)
    monkeypatch.setattr(mainmod, "_check_skill_version", lambda _: None)
    monkeypatch.setattr(mainmod.sys, "argv",
        ["graphify", "path", "Overview", "Stats", "--graph", str(p)])
    mainmod.main()
    err = capsys.readouterr().err
    assert "target match was ambiguous - 3 equally-plausible nodes" in err
    assert "stats_a" in err and "stats_b" in err and "stats_c" in err
