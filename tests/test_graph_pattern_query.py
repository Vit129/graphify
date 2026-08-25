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


# --- Regressions from the #p20-review WHERE/parse-silence findings (4 & 5) ---

def test_where_unquoted_value_raises_instead_of_matching_everything():
    """Regression: an unquoted WHERE value ('a.label = main' instead of
    "a.label = 'main'") used to fail to parse and be silently ignored,
    returning every node as if the clause never existed."""
    G = _sample_graph()
    with pytest.raises(PatternQueryError):
        parse_and_execute_pattern(G, "MATCH (a) WHERE a.label = main RETURN a.label")


def test_where_or_is_unsupported_and_raises():
    """Regression: an OR clause silently dropped everything after AND-split,
    so only the first sub-clause was ever enforced with no indication the
    rest of the WHERE expression was ignored."""
    G = _sample_graph()
    with pytest.raises(PatternQueryError):
        parse_and_execute_pattern(
            G,
            "MATCH (a) WHERE a.label CONTAINS 'main' OR a.label CONTAINS 'init' RETURN a.label",
        )


def test_where_unknown_variable_raises():
    """Regression: a WHERE clause referencing a variable not present anywhere
    in the MATCH pattern (a typo) was silently never enforced, since env.get
    always returned None for it."""
    G = _sample_graph()
    with pytest.raises(PatternQueryError):
        parse_and_execute_pattern(G, "MATCH (a) WHERE z.label = 'main()' RETURN a.label")


def test_malformed_edge_syntax_raises_instead_of_truncating():
    """Regression: `(a)-[]-(b)` failed to match the edge-arrow group, so the
    tokenizer silently stopped after the first node and executed a 1-node
    pattern instead of erroring on the malformed rest of the string."""
    G = _sample_graph()
    with pytest.raises(PatternQueryError):
        parse_and_execute_pattern(G, "MATCH (a)-[]-(b) RETURN a.label, b.label")


def test_type_filter_does_not_substring_match_label():
    """Regression: (a:route) matched _node_type_matches via `req_type in lbl`,
    so any node whose *label* happened to contain "route" (e.g. reroute())
    matched a route-type filter regardless of its real file_type."""
    G = _sample_graph()
    G.add_node("n5", label="reroute()", file_type="function", source_file="src/util.py")
    results = parse_and_execute_pattern(G, "MATCH (a:route) RETURN a.label", as_dict=True)
    labels = {r["a"] for r in results}
    assert "reroute()" not in labels
    assert labels == {"GET /users"}


def test_limit_is_clamped_to_max():
    """Regression: LIMIT was passed straight to int() with no upper bound."""
    G = _sample_graph()
    results = parse_and_execute_pattern(
        G, "MATCH (a) RETURN a.label LIMIT 999999999", as_dict=True
    )
    assert len(results) == G.number_of_nodes()  # graph is tiny; clamp just must not error


def test_oversized_pattern_raises_before_recursing():
    """Regression: recursion depth equals step count with no cap, so a long
    enough pattern crashed the whole process with an uncaught RecursionError
    instead of a clean query error."""
    G = _sample_graph()
    long_pattern = "MATCH " + "".join(f"(n{i})-[:calls]->" for i in range(30)) + "(n30) RETURN n0.label"
    with pytest.raises(PatternQueryError):
        parse_and_execute_pattern(G, long_pattern)


def test_cycle_guard_prevents_revisiting_a_bound_node():
    """Regression: no cycle prevention meant a path could reuse the same node
    for two different pattern variables (e.g. walking a->b->a back to the
    start), which is not a valid match under standard MATCH semantics and
    also fed unbounded revisits on any cyclic graph."""
    G = nx.DiGraph()
    G.add_node("a", label="a()", file_type="function")
    G.add_node("b", label="b()", file_type="function")
    G.add_edge("a", "b", relation="calls", confidence="EXTRACTED", _src="a", _tgt="b")
    G.add_edge("b", "a", relation="calls", confidence="EXTRACTED", _src="b", _tgt="a")

    results = parse_and_execute_pattern(
        G, "MATCH (x)-[:calls]->(y)-[:calls]->(z) RETURN x.label, y.label, z.label", as_dict=True
    )
    assert results == []  # the only 2-hop walk on a 2-cycle returns to the start


def test_where_prunes_search_instead_of_exhaustive_traversal():
    """Regression: WHERE was only checked at the leaf (after a full path was
    assembled), so a query with zero matches still explored the whole
    traversal space -- measured at 45.8s for a 4-hop no-match query on this
    project's own 10k-node graph. On a graph of a few thousand nodes/edges,
    an unpruned exhaustive search is slow enough to be a clear regression
    signal even without reproducing the exact prior timing."""
    import time

    G = nx.DiGraph()
    n = 2000
    for i in range(n):
        G.add_node(f"n{i}", label=f"node{i}", file_type="function")
    for i in range(n - 1):
        G.add_edge(f"n{i}", f"n{i + 1}", relation="calls", confidence="EXTRACTED", _src=f"n{i}", _tgt=f"n{i+1}")

    start = time.perf_counter()
    result = parse_and_execute_pattern(
        G,
        "MATCH (a)-[:calls]->(b)-[:calls]->(c)-[:calls]->(d) "
        "WHERE a.label = 'ZZZ_NOPE_ZZZ' RETURN a.label LIMIT 5",
    )
    elapsed = time.perf_counter() - start
    assert result == "No matching patterns found in graph."
    assert elapsed < 2.0, f"WHERE should prune at step 0, took {elapsed:.2f}s"
