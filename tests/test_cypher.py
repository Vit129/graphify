"""graphify.cypher: the read-only Cypher SUBSET (parser, executor, safety rails, CLI, MCP tool)."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import networkx as nx
import pytest
from networkx.readwrite import json_graph

import graphify.__main__ as mainmod
import graphify.serve as servemod
from graphify import cypher
from graphify.affected import load_graph
from graphify.cypher import CypherError, format_table, parse_cypher, run_cypher


def _graph() -> nx.MultiDiGraph:
    G = nx.MultiDiGraph()
    nodes = [
        ("main", "main()", "app/main.py", "L1", 0, "code"),
        ("run", "run()", "app/main.py", "L5", 0, "code"),
        ("load", "load()", "app/state.py", "L2", 1, "code"),
        ("helper", "helper()", "lib/util.py", "L3", 1, "code"),
        ("util", "util()", "lib/util.py", "L9", 1, "code"),
        ("test_run", "test_run()", "tests/test_main.py", "L4", 2, "code"),
        ("appfile", "main.py", "app/main.py", "L1", 0, "code"),
        ("statefile", "state.py", "app/state.py", "L1", 1, "code"),
        ("readme", "README", "README.md", None, 3, "document"),
    ]
    for nid, label, sf, loc, comm, ft in nodes:
        G.add_node(nid, label=label, source_file=sf, source_location=loc, community=comm, file_type=ft)

    def calls(a, b, conf="EXTRACTED"):
        G.add_edge(a, b, relation="calls", confidence=conf, context="call", _src=a, _tgt=b)

    calls("main", "run")
    calls("run", "load")
    calls("run", "helper", "INFERRED")
    calls("load", "helper")
    calls("helper", "util")
    calls("test_run", "run")
    G.add_edge("appfile", "statefile", relation="imports", confidence="EXTRACTED", context="import",
               _src="appfile", _tgt="statefile")
    # stored in flipped endpoint order: _src/_tgt say util -> main
    G.add_edge("main", "util", relation="references", confidence="INFERRED", _src="util", _tgt="main")
    return G


@pytest.fixture(scope="module")
def G():
    return _graph()


def _rows(G, q, **kw):
    return run_cypher(G, q, **kw).rows


def _col(G, q, **kw):
    return [r[0] for r in _rows(G, q, **kw)]


# --------------------------------------------------------------------------- parser

def test_parse_valid_shapes():
    for q in [
        "MATCH (a) RETURN a",
        "match (a:code {label: 'x'})-[r:calls|imports]->(b) where a.degree >= 1 return a.label as l, count(*) "
        "order by l desc skip 1 limit 5",
        "MATCH (a)<-[:calls*1..3]-(b) RETURN DISTINCT b.label;",
        "MATCH (a)--(b) RETURN a.id",
        "MATCH (a)-->(b)<--(c) RETURN count(DISTINCT c)",
        "MATCH (a) WHERE NOT (a.label = 'x' OR a.label STARTS WITH 'y') AND a.layer IS NOT NULL RETURN a.id",
    ]:
        assert parse_cypher(q).items


@pytest.mark.parametrize("query,construct", [
    ("CREATE (a) RETURN a", "CREATE"),
    ("MERGE (a) RETURN a", "MERGE"),
    ("MATCH (a) DELETE a", "DELETE"),
    ("MATCH (a) DETACH DELETE a", "DETACH"),
    ("MATCH (a) SET a.label = 'x'", "SET"),
    ("MATCH (a) REMOVE a.label", "REMOVE"),
    ("CALL db.labels()", "CALL"),
    ("MATCH (a) WITH a RETURN a", "WITH"),
    ("MATCH (a) RETURN a.id UNION MATCH (b) RETURN b.id", "UNION"),
    ("OPTIONAL MATCH (a) RETURN a", "OPTIONAL MATCH"),
    ("MATCH (a) UNWIND [1] AS x RETURN a", "UNWIND"),
    ("MATCH (a) RETURN a.id LIMIT 1 DROP", "DROP"),
])
def test_rejects_unsupported_constructs_naming_them(query, construct):
    with pytest.raises(CypherError, match=construct):
        parse_cypher(query)


@pytest.mark.parametrize("query,fragment", [
    ("RETURN 1", "start with MATCH"),
    ("MATCH (a), (b) RETURN a", "comma-separated"),
    ("MATCH (a) MATCH (b) RETURN a", "multiple MATCH"),
    ("MATCH (a)", "RETURN"),
    ("MATCH (a) RETURN *", "RETURN *"),
    ("MATCH (a) RETURN collect(a.id)", "collect"),
    ("MATCH (a) RETURN sum(a.degree)", "sum"),
    ("MATCH (a) RETURN toLower(a.id)", "toLower"),
    ("MATCH p = (a)-->(b) RETURN p", "path variables"),
    ("MATCH (a)-[*0..2]->(b) RETURN b", "zero-length"),
    ("MATCH (a)-[*1..6]->(b) RETURN b", "capped at 5"),
    ("MATCH (a)-[*3..2]->(b) RETURN b", "invalid hop range"),
    ("MATCH (a)<-->(b) RETURN b", "both ways"),
    ("MATCH (a) WHERE a.foo = 1 RETURN a", "unknown node property"),
    ("MATCH (a)-[r]->(b) WHERE r.weight = 1 RETURN a", "unknown relationship property"),
    ("MATCH (a) RETURN b.id", "unknown variable"),
    ("MATCH (a) WHERE a.id != 'x' RETURN a", "<>"),
    ("MATCH (a) WHERE a.id = $x RETURN a", "parameters"),
    ("MATCH (a) WHERE a.degree + 1 > 2 RETURN a", "arithmetic"),
    ("MATCH (a) WHERE a.label = 'x RETURN a", "unterminated"),
    ("MATCH (a) WHERE count(*) > 1 RETURN a", "count()"),
    ("MATCH (a) RETURN a.id LIMIT -1", "LIMIT"),
    ("MATCH (a) RETURN a.id, a.id", "duplicate"),
    ("MATCH (a) RETURN count(*) ORDER BY a.id", "ORDER BY"),
    ("MATCH (a)-[r]->(b) RETURN type(a)", "type()"),
    ("MATCH (a) RETURN a.id garbage", "unexpected"),
])
def test_rejects_malformed_or_out_of_subset(query, fragment):
    with pytest.raises(CypherError) as exc:
        parse_cypher(query)
    assert fragment in str(exc.value)


def test_unsupported_keywords_only_matter_at_clause_boundaries(G):
    # `set` as a variable name is fine
    assert _rows(G, "MATCH (set {label: 'main()'}) RETURN set.id") == [["main"]]


# --------------------------------------------------------------------------- execution

def test_direction_out_in_any(G):
    assert sorted(_col(G, "MATCH (a)-[:calls]->(b {id: 'run'}) RETURN a.id")) == ["main", "test_run"]
    assert sorted(_col(G, "MATCH (a {id: 'run'})<-[:calls]-(b) RETURN b.id")) == ["main", "test_run"]
    assert sorted(_col(G, "MATCH (a {id: 'run'})-[:calls]-(b) RETURN b.id")) == ["helper", "load", "main", "test_run"]
    assert sorted(_col(G, "MATCH (a {id: 'run'})-[:calls]->(b) RETURN b.id")) == ["helper", "load"]


def test_direction_recovered_from_src_tgt_markers(G):
    # nx stores main->util but _src/_tgt say util references main
    assert _rows(G, "MATCH (a)-[:references]->(b) RETURN a.id, b.id") == [["util", "main"]]
    assert _rows(G, "MATCH (a)<-[:references]-(b) RETURN a.id, b.id") == [["main", "util"]]


def test_direction_survives_load_graph_roundtrip(tmp_path, G):
    p = tmp_path / "graph.json"
    p.write_text(json.dumps(json_graph.node_link_data(G, edges="links")), encoding="utf-8")
    assert _rows(load_graph(p), "MATCH (a)-[:references]->(b) RETURN a.id, b.id") == [["util", "main"]]


def test_relation_filter_and_alternatives(G):
    assert _rows(G, "MATCH (a)-[r:imports]->(b) RETURN a.label, b.label, type(r), r.relation") == [
        ["main.py", "state.py", "imports", "imports"]]
    rels = _col(G, "MATCH (a)-[r:imports|references]->(b) RETURN DISTINCT r.relation ORDER BY r.relation")
    assert rels == ["imports", "references"]
    assert _col(G, "MATCH (a)-[r:imports|:references]->(b) RETURN count(*)") == [2]


def test_relationship_properties_and_inline_maps(G):
    assert _col(G, "MATCH (a)-[r:calls {confidence: 'INFERRED'}]->(b) RETURN b.id") == ["helper"]
    assert _col(G, "MATCH (a)-[r]->(b) WHERE r.context = 'import' RETURN a.id") == ["appfile"]
    assert _col(G, "MATCH (a {label: 'main()'}) RETURN a.source_file") == ["app/main.py"]


def test_variable_length(G):
    assert sorted(_col(G, "MATCH (a {id: 'main'})-[:calls*1..1]->(b) RETURN b.id")) == ["run"]
    assert sorted(_col(G, "MATCH (a {id: 'main'})-[:calls*2]->(b) RETURN b.id")) == ["helper", "load"]
    assert _col(G, "MATCH (a {id: 'main'})-[:calls*1..5]->(b) RETURN DISTINCT b.id ORDER BY b.id") == [
        "helper", "load", "run", "util"]
    # open-ended `*` is capped at 5 hops, not unbounded
    assert parse_cypher("MATCH (a)-[*]->(b) RETURN b").rels[0].hi == cypher.MAX_HOPS
    # relationship variable over a variable-length hop is a list
    r = _rows(G, "MATCH (a {id: 'main'})-[r:calls*2]->(b {id: 'load'}) RETURN r.relation")
    assert r == [[["calls", "calls"]]]


def test_variable_length_does_not_reuse_an_edge(G):
    # undirected 2-hop from main must not walk the same edge back to main
    assert "main" not in _col(G, "MATCH (a {id: 'main'})-[:calls*2]-(b) RETURN b.id")


def test_multi_hop_chain_and_repeated_variable(G):
    assert _rows(G, "MATCH (a {id: 'main'})-[:calls]->(b)-[:calls]->(c) RETURN b.id, c.id ORDER BY c.id") == [
        ["run", "helper"], ["run", "load"]]
    assert _col(G, "MATCH (a)-[:calls]->(b)-[:calls]->(c)-[:calls]->(a) RETURN a.id") == []
    assert _rows(G, "MATCH (a)-->(b)-->(a) RETURN a.id") == []


def test_labels_match_file_type_and_unknown_label_notes(G):
    assert _col(G, "MATCH (d:document) RETURN d.label") == ["README"]
    res = run_cypher(G, "MATCH (d:Function) RETURN d.label")
    assert res.rows == [] and any("Function" in n for n in res.notes)
    res = run_cypher(G, "MATCH (a)-[:nope]->(b) RETURN a")
    assert any("nope" in n for n in res.notes)


def test_node_properties(G):
    row = _rows(G, "MATCH (n {id: 'helper'}) RETURN n.id, n.label, n.source_file, n.source_location, "
                   "n.community, n.file_type, n.layer, n.degree")[0]
    assert row == ["helper", "helper()", "lib/util.py", "L3", 1, "code", "Utility", 3]
    assert _col(G, "MATCH (n {id: 'test_run'}) RETURN n.layer") == ["Test"]
    assert _rows(G, "MATCH (n {id: 'run'}) RETURN n.community_name") == [[None]]
    res = run_cypher(G, "MATCH (n {id: 'run'}) RETURN n.community_name", community_names={0: "Core app"})
    assert res.rows == [["Core app"]]


def test_where_operators(G):
    q = "MATCH (n:code) WHERE %s RETURN n.id ORDER BY n.id"

    def f(cond):
        return _col(G, q % cond)

    assert f("n.label = 'run()'") == ["run"]
    assert f("n.label <> 'run()' AND n.degree > 4") == []
    assert f("n.degree >= 3 AND n.degree < 5") == ["helper", "run"]
    assert f("n.degree <= 1") == ["appfile", "statefile", "test_run"]
    assert f("n.source_file CONTAINS 'util'") == ["helper", "util"]
    assert f("n.source_file STARTS WITH 'tests/'") == ["test_run"]
    assert f("n.label ENDS WITH 'main()'") == ["main"]
    assert f("n.id =~ 'h.*'") == ["helper"]
    assert f("n.id =~ 'H.*'") == []
    assert f("n.id =~ '(?i)H.*'") == ["helper"]
    assert f("n.id =~ 'hel'") == []  # whole-string semantics, like Cypher
    assert f("n.id IN ['main', 'util', 'zzz']") == ["main", "util"]
    assert f("n.id IN []") == []
    assert f("NOT n.id IN ['main', 'util', 'zzz'] AND n.degree > 3") == ["run"]
    assert f("n.id = 'main' OR n.id = 'util'") == ["main", "util"]
    assert f("(n.id = 'main' OR n.id = 'util') AND n.layer = 'Core'") == ["main"]
    assert f("n.source_location IS NULL") == []
    assert f("n.source_location IS NOT NULL AND n.id = 'main'") == ["main"]
    assert _col(G, "MATCH (n:document) WHERE n.source_location IS NULL RETURN n.id") == ["readme"]


def test_null_semantics_and_type_mismatch(G):
    # null never equals anything, `<>` with null is null (row dropped), ordering across types is null
    assert _col(G, "MATCH (n:document) WHERE n.source_location = 'L1' RETURN n.id") == []
    assert _col(G, "MATCH (n:document) WHERE n.source_location <> 'L1' RETURN n.id") == []
    assert _col(G, "MATCH (n {id: 'main'}) WHERE n.label > 3 RETURN n.id") == []
    assert _col(G, "MATCH (n {id: 'main'}) WHERE n.community = '0' RETURN n.id") == []
    with pytest.raises(CypherError, match="boolean"):
        run_cypher(G, "MATCH (n) WHERE n.label RETURN n")


def test_aggregation_count(G):
    assert _rows(G, "MATCH (a)-[r]->(b) RETURN count(*)") == [[8]]
    assert _rows(G, "MATCH (a)-[:nope]->(b) RETURN count(*)") == [[0]]
    assert _rows(G, "MATCH (a)-[r:calls]->(b) RETURN type(r) AS t, count(*) AS n") == [["calls", 6]]
    rows = _rows(G, "MATCH (a)-[:calls]->(b) RETURN b.label AS callee, count(a) AS callers "
                    "ORDER BY callers DESC, callee")
    assert rows[0] == ["helper()", 2] and rows[1] == ["run()", 2]
    assert _rows(G, "MATCH (a)-[:calls]->(b) RETURN count(DISTINCT b)") == [[4]]
    assert _rows(G, "MATCH (a)-[:calls]->(b) RETURN count(b.id), count(*)") == [[6, 6]]
    # count(x) skips nulls, count(*) does not
    assert _rows(G, "MATCH (n) RETURN count(n.source_location), count(*)") == [[8, 9]]


def test_order_skip_limit_distinct(G):
    q = "MATCH (n:code) RETURN n.id ORDER BY n.degree DESC, n.id ASC"
    ids = _col(G, q)
    assert ids[:2] == ["run", "helper"] and ids[-1] == "test_run"
    assert _col(G, q + " SKIP 1 LIMIT 2") == ids[1:3]
    assert _col(G, "MATCH (n:code) RETURN n.id AS i ORDER BY i DESC LIMIT 1") == ["util"]
    assert _col(G, "MATCH (n:code) RETURN n.id ORDER BY n.id LIMIT 2") == ["appfile", "helper"]
    assert run_cypher(G, "MATCH (n:code) RETURN n.id ORDER BY n.id LIMIT 2").truncated is True
    assert run_cypher(G, "MATCH (n:code) RETURN n.id LIMIT 50").truncated is False
    assert sorted(_col(G, "MATCH (a)-[:calls]->(b) RETURN DISTINCT b.id")) == ["helper", "load", "run", "util"]
    assert len(_col(G, "MATCH (a)-[:calls]->(b) RETURN b.id")) == 6
    # null sorts last ascending, first descending
    nulls = _col(G, "MATCH (n) RETURN n.source_location ORDER BY n.source_location")
    assert nulls[-1] is None
    assert _col(G, "MATCH (n) RETURN n.source_location ORDER BY n.source_location DESC")[0] is None


def test_returning_whole_nodes_and_relationships(G):
    node = _rows(G, "MATCH (n {id: 'util'}) RETURN n")[0][0]
    assert node == {"id": "util", "label": "util()", "source_file": "lib/util.py", "source_location": "L9"}
    rel = _rows(G, "MATCH (a)-[r:references]->(b) RETURN r")[0][0]
    assert rel["relation"] == "references" and (rel["source"], rel["target"]) == ("util", "main")
    assert len(_rows(G, "MATCH (a {id: 'main'})-[:calls]->(b) RETURN DISTINCT a")) == 1
    json.dumps(run_cypher(G, "MATCH (a)-[r*1..2]->(b) RETURN a, r, b LIMIT 5").to_dict())


def test_works_on_plain_digraph_without_markers():
    D = nx.DiGraph()
    D.add_node("a", label="a", file_type="code")
    D.add_node("b", label="b", file_type="code")
    D.add_edge("a", "b", relation="calls")
    assert _rows(D, "MATCH (x)-[:calls]->(y) RETURN x.id, y.id") == [["a", "b"]]
    assert _rows(D, "MATCH (x)<-[:calls]-(y) RETURN x.id, y.id") == [["b", "a"]]
    U = nx.Graph(D)
    assert _rows(U, "MATCH (x)-[:calls]-(y) RETURN count(*)") == [[2]]


# --------------------------------------------------------------------------- safety

def _big_graph(n=400) -> nx.DiGraph:
    D = nx.DiGraph()
    for i in range(n):
        D.add_node(i, label=f"n{i}", file_type="code", source_file="x.py")
    for i in range(n):
        for j in (1, 7, 13):
            D.add_edge(i, (i + j) % n, relation="calls")
    return D


def test_row_cap_and_default_limit():
    D = _big_graph(1500)
    res = run_cypher(D, "MATCH (n) RETURN n.id")
    assert len(res.rows) == cypher.DEFAULT_LIMIT and res.truncated
    assert len(run_cypher(D, "MATCH (n) RETURN n.id", limit=300).rows) == 300
    res = run_cypher(D, "MATCH (n) RETURN n.id LIMIT 5000")
    assert len(res.rows) == cypher.MAX_ROWS and res.truncated
    assert any("clamped" in n for n in res.notes)
    res = run_cypher(D, "MATCH (n) RETURN n.id ORDER BY n.id LIMIT 5000")
    assert len(res.rows) == cypher.MAX_ROWS
    with pytest.raises(CypherError, match="positive"):
        run_cypher(D, "MATCH (n) RETURN n.id", limit=0)


def test_step_budget_stops_runaway_queries():
    D = _big_graph()
    with pytest.raises(CypherError, match="step budget"):
        run_cypher(D, "MATCH (a)-[*1..5]-(b) RETURN count(*)", max_steps=50_000)
    with pytest.raises(CypherError, match="step budget"):
        run_cypher(D, "MATCH (a)-[*1..3]->(b) RETURN count(*) ", max_steps=1000)


def test_time_budget():
    D = _big_graph()
    with pytest.raises(CypherError, match="time budget"):
        run_cypher(D, "MATCH (a)-[*1..5]-(b) RETURN count(*)", max_seconds=-1.0)


def test_early_exit_keeps_simple_limited_queries_cheap():
    D = _big_graph(2000)
    # 20 rows must not require scanning every edge of a 2000-node graph
    ex = cypher._Exec(D, parse_cypher("MATCH (a)-[:calls]->(b) RETURN a.id LIMIT 20"), {}, 10_000, 5)
    assert len(ex.run(100).rows) == 20


@pytest.mark.parametrize("pattern,fragment", [
    ("(a+)+", "nested repetition"),
    ("(.*)*", "nested repetition"),
    ("(a|b+)*c", "nested repetition"),
    ("(\\w+\\s?)+", "nested repetition"),
    ("(a)\\1", "backreferences"),
    ("." * 201, "too long"),
    ("a{1,9999}", "too large"),
    (".*a.*b.*c.*d.*", "too many"),
    ("(unclosed", "invalid regex"),
    ("[z-a]", "invalid regex"),
])
def test_bad_or_dangerous_regex_rejected(G, pattern, fragment):
    q = 'MATCH (n) WHERE n.label =~ "%s" RETURN n.id' % pattern.replace("\\", "\\\\")
    with pytest.raises(CypherError) as exc:
        run_cypher(G, q)
    assert fragment in str(exc.value)


def test_regex_error_surfaces_even_when_no_rows_match():
    with pytest.raises(CypherError, match="invalid regex"):
        parse_cypher("MATCH (n {id: 'nonexistent'}) WHERE n.label =~ '(' RETURN n")


def test_dynamic_regex_pattern_is_guarded_too():
    H = nx.DiGraph()
    H.add_node("n", label="(a+)+", file_type="code")
    with pytest.raises(CypherError, match="nested repetition"):
        run_cypher(H, "MATCH (n) WHERE 'aaaa' =~ n.label RETURN n")


def test_regex_does_not_hang_on_classic_catastrophic_input():
    H = nx.DiGraph()
    H.add_node("n", label="a" * 40 + "!", file_type="code")
    with pytest.raises(CypherError):
        run_cypher(H, "MATCH (n) WHERE n.label =~ '(a+)+$' RETURN n")
    # a safe pattern on the same data returns promptly
    assert run_cypher(H, "MATCH (n) WHERE n.label =~ 'a+!' RETURN n.id").rows == [["n"]]


def test_query_is_never_evaluated_as_python(G):
    with pytest.raises(CypherError):
        run_cypher(G, "MATCH (n) WHERE __import__('os').system('true') RETURN n")
    with pytest.raises(CypherError, match="too long"):
        parse_cypher("MATCH (n) RETURN n.id " + " " * cypher.MAX_QUERY_CHARS)


def test_graph_is_not_mutated(G):
    before = (G.number_of_nodes(), G.number_of_edges(), dict(G.nodes["main"]))
    run_cypher(G, "MATCH (a)-[r]->(b) RETURN a, r, b")
    assert (G.number_of_nodes(), G.number_of_edges(), dict(G.nodes["main"])) == before


# --------------------------------------------------------------------------- formatting

def test_format_table(G):
    out = format_table(run_cypher(G, "MATCH (a)-[:calls]->(b {id: 'util'}) RETURN a.label AS caller, a.degree AS d"))
    lines = out.splitlines()
    assert lines[0].split() == ["caller", "d"]
    assert lines[2].split() == ["helper()", "3"]
    assert lines[-1] == "(1 row)"
    empty = format_table(run_cypher(G, "MATCH (a:nothing) RETURN a.id"))
    assert "(0 rows)" in empty and "note: label :nothing matches no node" in empty
    assert "more available" in format_table(run_cypher(G, "MATCH (n) RETURN n.id LIMIT 2"))


# --------------------------------------------------------------------------- CLI

def _write(tmp_path: Path, G) -> Path:
    gp = tmp_path / "graph.json"
    gp.write_text(json.dumps(json_graph.node_link_data(G, edges="links")), encoding="utf-8")
    return gp


def _cli(monkeypatch, capsys, *args):
    monkeypatch.setattr(mainmod, "_check_skill_version", lambda _: None)
    monkeypatch.setattr(mainmod.sys, "argv", ["graphify", "cypher", *args])
    code = 0
    try:
        mainmod.main()
    except SystemExit as exc:
        code = exc.code or 0
    cap = capsys.readouterr()
    return code, cap.out, cap.err


def test_cli_table(monkeypatch, tmp_path, capsys, G):
    gp = _write(tmp_path, G)
    code, out, err = _cli(monkeypatch, capsys, "MATCH (a)-[:calls]->(b {id: 'run'}) RETURN a.label ORDER BY a.label",
                          "--graph", str(gp))
    assert code == 0, err
    assert out.splitlines()[0] == "a.label"
    assert "main()" in out and "test_run()" in out and "(2 rows)" in out


def test_cli_json_and_limit(monkeypatch, tmp_path, capsys, G):
    gp = _write(tmp_path, G)
    code, out, err = _cli(monkeypatch, capsys, "MATCH (n:code) RETURN n.id ORDER BY n.id", "--json", "--limit", "3",
                          f"--graph={gp}")
    assert code == 0, err
    data = json.loads(out)
    assert data["columns"] == ["n.id"] and data["row_count"] == 3 and data["truncated"] is True
    assert data["rows"] == [["appfile"], ["helper"], ["load"]]
    # a query's own LIMIT wins over --limit
    _, out, _ = _cli(monkeypatch, capsys, "MATCH (n:code) RETURN n.id LIMIT 1", "--limit", "5",
                     "--graph", str(gp), "--json")
    assert json.loads(out)["row_count"] == 1


def test_cli_errors(monkeypatch, tmp_path, capsys, G):
    gp = _write(tmp_path, G)
    code, out, err = _cli(monkeypatch, capsys, "MATCH (a) DELETE a", "--graph", str(gp))
    assert code == 1 and "DELETE" in err and out == ""
    code, _, err = _cli(monkeypatch, capsys, "MATCH (a) RETURN a", "--graph", str(tmp_path / "missing.json"))
    assert code == 1 and "not found" in err
    code, _, err = _cli(monkeypatch, capsys)
    assert code == 1 and "Usage: graphify cypher" in err
    code, _, err = _cli(monkeypatch, capsys, "MATCH (a) RETURN a", "--limit", "x", "--graph", str(gp))
    assert code == 1 and "--limit" in err
    code, _, err = _cli(monkeypatch, capsys, "MATCH (a) RETURN a", "--bogus")
    assert code == 1 and "unknown" in err


def test_cli_help_lists_cypher(monkeypatch, capsys):
    monkeypatch.setattr(mainmod.sys, "argv", ["graphify", "--help"])
    monkeypatch.setattr(mainmod, "_check_skill_version", lambda _: None)
    mainmod.main()
    assert "cypher" in capsys.readouterr().out


# --------------------------------------------------------------------------- MCP

def test_mcp_tool_text_handler(tmp_path, G):
    out = servemod._tool_cypher_query_text(G, {"query": "MATCH (a)-[:calls]->(b {id: 'util'}) RETURN a.id"})
    assert "helper" in out and "(1 row)" in out
    out = servemod._tool_cypher_query_text(G, {"query": "MATCH (a) SET a.x = 1"})
    assert out.startswith("Cypher error:") and "SET" in out
    out = servemod._tool_cypher_query_text(G, {"query": "MATCH (n) RETURN n.id", "limit": 2})
    assert "(2 rows, more available" in out
    (tmp_path / ".graphify_labels.json").write_text(json.dumps({"0": "Entry"}), encoding="utf-8")
    out = servemod._tool_cypher_query_text(
        G, {"query": "MATCH (n {id: 'main'}) RETURN n.community_name"}, tmp_path / "graph.json")
    assert "Entry" in out


def test_mcp_tool_is_declared_with_valid_schema_over_stdio(tmp_path, G):
    """tools/list must still build (a Python-source JSON `false` once crashed it) and cypher_query be callable."""
    pytest.importorskip("mcp", reason="the MCP server needs the optional `mcp` extra")
    gp = _write(tmp_path, G)
    p = subprocess.Popen(
        [sys.executable, "-m", "graphify.serve", "--graph", str(gp)],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=tmp_path,
    )
    ids = iter(range(1, 100))

    def send(method, params=None, notify=False):
        msg = {"jsonrpc": "2.0", "method": method, "params": params or {}}
        if not notify:
            msg["id"] = next(ids)
        p.stdin.write(json.dumps(msg) + "\n")
        p.stdin.flush()
        while not notify:
            line = p.stdout.readline()
            assert line, f"server exited: {p.stderr.read()[:500]}"
            got = json.loads(line)
            if got.get("id") == msg["id"]:
                return got

    try:
        send("initialize", {"protocolVersion": "2024-11-05", "capabilities": {},
                            "clientInfo": {"name": "t", "version": "0"}})
        send("notifications/initialized", notify=True)
        listed = send("tools/list")
        assert "error" not in listed, listed
        tools = {t["name"]: t for t in listed["result"]["tools"]}
        assert {"query_graph", "match_pattern", "cypher_query"} <= set(tools)
        schema = tools["cypher_query"]["inputSchema"]
        assert schema["type"] == "object" and schema["required"] == ["query"]
        assert schema["properties"]["limit"]["type"] == "integer" and "project_path" in schema["properties"]
        called = send("tools/call", {"name": "cypher_query", "arguments": {
            "query": "MATCH (a)-[:calls]->(b {id: 'run'}) RETURN a.id ORDER BY a.id"}})
        text = called["result"]["content"][0]["text"]
        assert "main" in text and "test_run" in text and "(2 rows)" in text
        bad = send("tools/call", {"name": "cypher_query", "arguments": {"query": "CREATE (n)"}})
        assert "Cypher error" in bad["result"]["content"][0]["text"]
    finally:
        p.terminate()
        p.wait(timeout=10)
