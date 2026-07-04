"""Tests for `find_path_with_disambiguation` (graphify/query.py) - the shared
resolver CLI `path` and the MCP `shortest_path` tool both call. Extracted so
a fix to ambiguity handling or hub-avoidance lands in both callers at once;
these tests pin the behavior at the function level, independent of either
caller's formatting.
"""
from __future__ import annotations
import networkx as nx

from graphify.query import find_path_with_disambiguation


def _add(G, nid, label, source_file, **extra):
    G.add_node(nid, label=label, source_file=source_file, community=extra.pop("community", 0), **extra)


def test_no_match_on_source_returns_error():
    G = nx.Graph()
    _add(G, "a", "Alpha", "a.py")
    result = find_path_with_disambiguation(G, "totallyUnrelated", "Alpha")
    assert "error" in result
    assert "No node matching 'totallyUnrelated'" in result["error"]


def test_no_match_on_target_returns_error():
    G = nx.Graph()
    _add(G, "a", "Alpha", "a.py")
    result = find_path_with_disambiguation(G, "Alpha", "totallyUnrelated")
    assert "error" in result
    assert "No node matching 'totallyUnrelated'" in result["error"]


def test_same_node_both_sides_returns_same_node_error():
    G = nx.Graph()
    _add(G, "a", "Alpha", "a.py")
    result = find_path_with_disambiguation(G, "Alpha", "Alpha")
    assert "same_node_error" in result
    assert "both resolved to the same node" in result["same_node_error"]


def test_unambiguous_path_has_no_warnings():
    G = nx.Graph()
    _add(G, "a", "sourceFunction()", "a.py")
    _add(G, "b", "targetFunction()", "b.py")
    G.add_edge("a", "b", relation="calls", confidence="EXTRACTED")
    result = find_path_with_disambiguation(G, "sourceFunction", "targetFunction")
    assert result["warnings"] == []
    assert result["path_nodes"] == ["a", "b"]
    assert result["used_hub_fallback"] is False


def test_retries_disconnected_top_candidate_and_finds_connected_tie():
    """The exact false-negative class this fix closes: a duplicate-labeled
    target has one candidate genuinely disconnected from the source and one
    genuinely connected. Previously (MCP `shortest_path` before this fix)
    only the top-scored candidate was tried - if that happened to be the
    disconnected one, the tool reported "no path found" even though a real
    path existed via the other tied candidate."""
    G = nx.Graph()
    _add(G, "src", "sourceFunction()", "src.py")
    _add(G, "tgt_a", "Stats", "english/progress.md")
    _add(G, "tgt_b", "Stats", "japanese/progress.md")
    _add(G, "unrelated", "Unrelated", "z.py")
    # tgt_a is isolated (no edges at all); only tgt_b connects to src.
    G.add_edge("unrelated", "tgt_a", relation="contains", confidence="EXTRACTED")
    G.add_edge("src", "tgt_b", relation="contains", confidence="EXTRACTED")

    result = find_path_with_disambiguation(G, "sourceFunction", "Stats")
    assert any("target match was ambiguous" in w for w in result["warnings"])
    assert result["path_nodes"] == ["src", "tgt_b"]
    assert result["tgt_nid"] == "tgt_b"


def test_hub_avoidance_still_applies_through_shared_function():
    """Regression: the degree/label-based hub-avoidance (path's other fix)
    must survive being moved into the shared function unchanged."""
    G = nx.Graph()
    _add(G, "source_fn", "sourceFunction()", "a.swift")
    _add(G, "int_hub", "Int", "b.swift")
    _add(G, "target_fn", "targetFunction()", "c.swift")
    _add(G, "real1", "realHelperOne()", "a.swift")
    _add(G, "real2", "realHelperTwo()", "c.swift")
    G.add_edge("source_fn", "int_hub", relation="references", confidence="EXTRACTED")
    G.add_edge("int_hub", "target_fn", relation="references", confidence="EXTRACTED")
    G.add_edge("source_fn", "real1", relation="calls", confidence="EXTRACTED")
    G.add_edge("real1", "real2", relation="calls", confidence="EXTRACTED")
    G.add_edge("real2", "target_fn", relation="calls", confidence="EXTRACTED")

    result = find_path_with_disambiguation(G, "sourceFunction", "targetFunction")
    assert result["path_nodes"] == ["source_fn", "real1", "real2", "target_fn"]
    assert result["used_hub_fallback"] is False


def test_no_path_reports_tried_pairs_count():
    G = nx.Graph()
    _add(G, "a", "Alpha", "a.py")
    _add(G, "b", "Beta", "b.py")
    result = find_path_with_disambiguation(G, "Alpha", "Beta")
    assert result["path_nodes"] is None
    assert result["tried_pairs"] == 1
