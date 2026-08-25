from __future__ import annotations

import networkx as nx
import pytest
from graphify.pattern_query import parse_and_execute_pattern, PatternQueryError


def _sample_graph():
    G = nx.DiGraph()
    G.add_node("n1", label="main()", file_type="function", source_file="src/main.py")
    G.add_node("n2", label="init_app()", file_type="function", source_file="src/app.py")
    G.add_node("n3", label="UserAuth", file_type="class", source_file="src/auth.py")
    G.add_node("n4", label="GET /users", file_type="route", source_file="src/routes.py")

    G.add_edge("n1", "n2", relation="calls", confidence="EXTRACTED", _src="n1", _tgt="n2")
    G.add_edge("n2", "n3", relation="imports", confidence="EXTRACTED", _src="n2", _tgt="n3")
    G.add_edge("n4", "n2", relation="handles", confidence="EXTRACTED", _src="n4", _tgt="n2")
    return G


def test_pattern_query_basic_match():
    G = _sample_graph()
    q = "MATCH (a:function)-[:calls]->(b:function) RETURN a.label, b.label"
    results = parse_and_execute_pattern(G, q, as_dict=True)
    assert len(results) == 1
    assert results[0]["a"] == "main()"
    assert results[0]["b"] == "init_app()"


def test_pattern_query_with_where_clause():
    G = _sample_graph()
    q = "MATCH (a)-[:imports]->(b) WHERE b.source_file CONTAINS 'auth' RETURN a.label, b.label, b.source_file"
    results = parse_and_execute_pattern(G, q, as_dict=True)
    assert len(results) == 1
    assert results[0]["a"] == "init_app()"
    assert results[0]["b"] == "UserAuth"
    assert results[0]["b.source_file"] == "src/auth.py"


def test_pattern_query_with_route_handles():
    G = _sample_graph()
    q = "MATCH (r:route)-[:handles]->(f) RETURN r.label, f.label"
    results = parse_and_execute_pattern(G, q, as_dict=True)
    assert len(results) == 1
    assert results[0]["r"] == "GET /users"
    assert results[0]["f"] == "init_app()"


def test_pattern_query_text_table_formatting():
    G = _sample_graph()
    q = "MATCH (a:function)-[:calls]->(b:function) RETURN a.label, b.label"
    text = parse_and_execute_pattern(G, q, as_dict=False)
    assert "main()" in text
    assert "init_app()" in text
    assert "result(s) returned" in text


def test_pattern_query_syntax_error():
    G = _sample_graph()
    with pytest.raises(PatternQueryError):
        parse_and_execute_pattern(G, "SELECT * FROM nodes")
