"""Tests for lightweight query expansion (P8 semantic-search alternative).
Chosen over full embedding search: a small curated synonym map riding the
existing BM25 pipeline, no new dependency/network/API key. See
agent-memory/knowledge/architecture/feature-provenance.md and
agent-memory/plans/p9-query-synonym-expansion.md.
"""
import networkx as nx

from graphify.serve import _query_terms, _score_nodes


def test_synonym_group_expands_single_term():
    terms = _query_terms("delete the record")
    assert "remove" in terms
    assert "erase" in terms


def test_phrase_synonym_expands_login_across_stopword():
    """'log in' spans a filtered stopword ('in'), so this can only work via
    phrase-level detection against the raw question, not single-token
    expansion (the literal token 'log' is never added — 'log' alone is
    ambiguous with logging and isn't in any synonym group)."""
    terms = _query_terms("log the user in")
    assert "authenticate" in terms
    assert "login" in terms


def test_unrelated_query_is_not_expanded():
    terms = _query_terms("what calls extract?")
    assert terms == ["calls", "extract"]


def test_synonym_expansion_finds_node_with_zero_literal_term_overlap():
    """End-to-end: a node labeled purely with the target concept word must
    be found by a query that only uses its synonym, with no literal term
    in common between query and label."""
    G = nx.DiGraph()
    G.add_node("n1", label="authenticateUser", file_type="code", source_file="auth.py")
    G.add_node("n2", label="renderDashboard", file_type="code", source_file="dash.py")
    terms = _query_terms("log the user in")
    scored = _score_nodes(G, terms)
    assert scored[0][1] == "n1"
