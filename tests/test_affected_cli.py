from __future__ import annotations

import json

import networkx as nx
from networkx.readwrite import json_graph

import graphify.__main__ as mainmod


def _write_graph(tmp_path):
    graph = nx.DiGraph()
    graph.add_node("target", label="Foo", source_file="pkg/foo.py", source_location="L1")
    graph.add_node("caller", label="X()", source_file="app.py", source_location="L4")
    graph.add_node("barrel", label="__init__.py", source_file="pkg/__init__.py", source_location=None)
    graph.add_node("consumer", label="app.py", source_file="app.py", source_location=None)
    graph.add_edge("caller", "target", relation="calls", context="call", confidence="EXTRACTED")
    graph.add_edge("barrel", "target", relation="re_exports", context="export", confidence="EXTRACTED")
    graph.add_edge("consumer", "target", relation="imports", context="import", confidence="EXTRACTED")
    graph_path = tmp_path / "graph.json"
    graph_path.write_text(json.dumps(json_graph.node_link_data(graph, edges="links")), encoding="utf-8")
    return graph_path


def test_affected_cli_reverse_traverses_impact_edges(monkeypatch, tmp_path, capsys):
    graph_path = _write_graph(tmp_path)
    monkeypatch.setattr(mainmod, "_check_skill_version", lambda _: None)
    monkeypatch.setattr(
        mainmod.sys,
        "argv",
        ["graphify", "affected", "Foo", "--graph", str(graph_path)],
    )

    mainmod.main()

    out = capsys.readouterr().out
    assert "Affected nodes for Foo" in out
    assert "X()" in out
    assert "calls" in out
    assert "__init__.py" in out
    assert "re_exports" in out
    assert "app.py" in out
    assert "imports" in out


def test_affected_cli_relation_filter_limits_reverse_traversal(monkeypatch, tmp_path, capsys):
    graph_path = _write_graph(tmp_path)
    monkeypatch.setattr(mainmod, "_check_skill_version", lambda _: None)
    monkeypatch.setattr(
        mainmod.sys,
        "argv",
        ["graphify", "affected", "Foo", "--relation", "calls", "--graph", str(graph_path)],
    )

    mainmod.main()

    out = capsys.readouterr().out
    assert "Relations: calls" in out
    assert "X()" in out
    assert "__init__.py" not in out


def test_affected_cli_relation_filter_prefix_matches_parameterized_relation(monkeypatch, tmp_path, capsys):
    """A bare --relation filter (no ':') must also match P15-style parameterized
    relation labels like 'shares_value:<value>', since the caller can't know the
    exact value in advance (#P17 item 4).
    """
    graph = nx.DiGraph()
    graph.add_node("target", label="Foo", source_file="pkg/foo.py", source_location="L1")
    graph.add_node("coupled", label="Bar", source_file="pkg/bar.py", source_location="L2")
    graph.add_node("caller", label="X()", source_file="app.py", source_location="L4")
    graph.add_edge("coupled", "target", relation="shares_value:input_boolean.home_mode", context="config", confidence="EXTRACTED")
    graph.add_edge("caller", "target", relation="calls", context="call", confidence="EXTRACTED")
    graph_path = tmp_path / "graph.json"
    graph_path.write_text(json.dumps(json_graph.node_link_data(graph, edges="links")), encoding="utf-8")

    monkeypatch.setattr(mainmod, "_check_skill_version", lambda _: None)
    monkeypatch.setattr(
        mainmod.sys,
        "argv",
        ["graphify", "affected", "Foo", "--relation", "shares_value", "--graph", str(graph_path)],
    )

    mainmod.main()

    out = capsys.readouterr().out
    assert "Bar" in out
    assert "X()" not in out


def test_affected_cli_forces_directed_on_undirected_graph(monkeypatch, tmp_path, capsys):
    """A graph persisted with directed=false must still recover caller->callee
    direction (#1174): affected on the callee returns the caller, not the callee
    or nothing. Without forcing directed=True, node_link_graph builds an
    undirected Graph, predecessors() collapses, and the reverse traversal breaks.
    """
    graph = nx.DiGraph()
    graph.add_node("A", label="caller_fn", source_file="a.py", source_location="L1")
    graph.add_node("B", label="callee_fn", source_file="b.py", source_location="L2")
    graph.add_edge("A", "B", relation="calls", context="call", confidence="EXTRACTED")

    data = json_graph.node_link_data(graph, edges="links")
    # Persist as undirected on disk to reproduce the bug condition.
    data["directed"] = False
    graph_path = tmp_path / "graph.json"
    graph_path.write_text(json.dumps(data), encoding="utf-8")

    monkeypatch.setattr(mainmod, "_check_skill_version", lambda _: None)
    monkeypatch.setattr(
        mainmod.sys,
        "argv",
        ["graphify", "affected", "B", "--relation", "calls", "--graph", str(graph_path)],
    )

    mainmod.main()

    out = capsys.readouterr().out
    # A (the caller) is affected by a change to B (the callee).
    assert "caller_fn" in out
    assert "calls" in out
    # B is the query node, not an affected node, and the result is not empty.
    assert "No affected nodes found." not in out


def test_affected_cli_direction_recovered_from_src_tgt_markers(monkeypatch, tmp_path, capsys):
    """#2309: affected must recover caller/callee direction from _src/_tgt markers
    even if the persisted link order is flipped (target -> caller)."""
    data = {
        "directed": False,
        "multigraph": False,
        "graph": {},
        "nodes": [
            {"id": "callee", "label": "CalleeFn", "source_file": "callee.py", "source_location": "L1"},
            {"id": "caller", "label": "CallerFn", "source_file": "caller.py", "source_location": "L2"},
        ],
        "links": [
            # Flipped persisted order: source is callee, target is caller,
            # but _src is caller, _tgt is callee (caller calls callee).
            {
                "source": "callee",
                "target": "caller",
                "_src": "caller",
                "_tgt": "callee",
                "relation": "calls",
                "confidence": "EXTRACTED",
            }
        ],
    }
    graph_path = tmp_path / "graph.json"
    graph_path.write_text(json.dumps(data), encoding="utf-8")

    monkeypatch.setattr(mainmod, "_check_skill_version", lambda _: None)
    monkeypatch.setattr(
        mainmod.sys,
        "argv",
        ["graphify", "affected", "CalleeFn", "--relation", "calls", "--graph", str(graph_path)],
    )

    mainmod.main()

    out = capsys.readouterr().out
    assert "Affected nodes for CalleeFn" in out
    assert "CallerFn" in out
    assert "calls" in out


def test_affected_cli_loads_edges_keyed_graph(monkeypatch, tmp_path, capsys):
    """graphify's `extract` writes graph.json with an "edges" key (not networkx's
    default "links"). affected.load_graph must handle it; before the edges/links
    normalization it raised an uncaught KeyError: 'links' (same class as #1198)."""
    graph = nx.DiGraph()
    graph.add_node("target", label="Foo", source_file="pkg/foo.py", source_location="L1")
    graph.add_node("caller", label="X()", source_file="app.py", source_location="L4")
    graph.add_edge("caller", "target", relation="calls", context="call", confidence="EXTRACTED")

    # Emulate graphify extract output: top-level "edges" key instead of "links".
    data = json_graph.node_link_data(graph, edges="links")
    data["edges"] = data.pop("links")
    graph_path = tmp_path / "graph.json"
    graph_path.write_text(json.dumps(data), encoding="utf-8")

    monkeypatch.setattr(mainmod, "_check_skill_version", lambda _: None)
    monkeypatch.setattr(
        mainmod.sys,
        "argv",
        ["graphify", "affected", "Foo", "--graph", str(graph_path)],
    )

    mainmod.main()

    out = capsys.readouterr().out
    assert "Affected nodes for Foo" in out
    assert "X()" in out
    assert "calls" in out


def test_resolve_seed_bare_name_matches_callable_label():
    from graphify.affected import resolve_seed

    graph = nx.DiGraph()
    graph.add_node("a", label="classifyProperty()", source_file="pkg/entity.py")
    graph.add_node("b", label="classifyPropertySafe()", source_file="app/context.py")

    assert resolve_seed(graph, "classifyProperty") == "a"
    assert resolve_seed(graph, "classifyPropertySafe") == "b"


def test_resolve_seed_decorated_query_matches_bare_label():
    from graphify.affected import resolve_seed

    graph = nx.DiGraph()
    graph.add_node("a", label="Foo", source_file="pkg/foo.py")
    graph.add_node("b", label="FooBar", source_file="pkg/foobar.py")

    assert resolve_seed(graph, "Foo()") == "a"


def test_resolve_seed_matches_unicode_normalized_label():
    import unicodedata

    from graphify.affected import resolve_seed

    graph = nx.DiGraph()
    graph.add_node("a", label="Auditoría", source_file="pkg/auditoria.py")

    assert resolve_seed(graph, unicodedata.normalize("NFD", "Auditoría")) == "a"


def test_resolve_seed_preserves_distinct_accents():
    from graphify.affected import resolve_seed

    graph = nx.DiGraph()
    graph.add_node("a", label="resume", source_file="pkg/resume.py")
    graph.add_node("b", label="résumé", source_file="pkg/resume_accented.py")

    assert resolve_seed(graph, "resume") == "a"


def test_resolve_seed_bare_name_tie_still_returns_none():
    from graphify.affected import resolve_seed

    graph = nx.DiGraph()
    graph.add_node("a", label="dup()", source_file="pkg/one.py")
    graph.add_node("b", label="dup()", source_file="pkg/two.py")

    assert resolve_seed(graph, "dup") is None


def test_resolve_seed_source_file_path_prefers_file_level_node():
    from graphify.affected import resolve_seed

    graph = nx.DiGraph()
    source_file = "app/api/example/route.ts"
    graph.add_node(
        "example_route_get",
        label="GET()",
        source_file=source_file,
        source_location="L42",
    )
    graph.add_node(
        "example_route",
        label="route.ts",
        source_file=source_file,
        source_location="L1",
    )

    assert resolve_seed(graph, source_file) == "example_route"


def test_resolve_seed_source_file_trailing_slash_parity():
    """A trailing path separator must not change the match (parity with explain's
    _find_node, which tokenizes the path and drops the slash)."""
    from graphify.affected import resolve_seed

    graph = nx.DiGraph()
    source_file = "app/api/example/route.ts"
    graph.add_node("get", label="GET()", source_file=source_file, source_location="L42")
    graph.add_node("file", label="route.ts", source_file=source_file, source_location="L1")

    assert resolve_seed(graph, source_file + "/") == "file"


def test_resolve_seed_source_file_ambiguous_no_file_node_returns_none():
    """Several nodes share a source_file but none is the L1 file node and none's
    basename matches the path — must not guess; return None."""
    from graphify.affected import resolve_seed

    graph = nx.DiGraph()
    source_file = "pkg/handlers.py"
    graph.add_node("a", label="handle_a()", source_file=source_file, source_location="L10")
    graph.add_node("b", label="handle_b()", source_file=source_file, source_location="L20")

    assert resolve_seed(graph, source_file) is None


def test_affected_cli_source_file_path_uses_file_level_node(monkeypatch, tmp_path, capsys):
    graph = nx.DiGraph()
    source_file = "app/api/example/route.ts"
    graph.add_node(
        "example_route_get",
        label="GET()",
        source_file=source_file,
        source_location="L42",
    )
    graph.add_node(
        "example_route",
        label="route.ts",
        source_file=source_file,
        source_location="L1",
    )
    graph.add_node(
        "consumer",
        label="consumer.ts",
        source_file="app/consumer.ts",
        source_location="L1",
    )
    graph.add_edge(
        "consumer",
        "example_route",
        relation="imports_from",
        context="import",
        confidence="EXTRACTED",
    )
    graph_path = tmp_path / "graph.json"
    graph_path.write_text(json.dumps(json_graph.node_link_data(graph, edges="links")), encoding="utf-8")

    monkeypatch.setattr(mainmod, "_check_skill_version", lambda _: None)
    monkeypatch.setattr(
        mainmod.sys,
        "argv",
        ["graphify", "affected", source_file, "--graph", str(graph_path)],
    )

    mainmod.main()

    out = capsys.readouterr().out
    assert "Affected nodes for route.ts" in out
    assert "consumer.ts" in out
    assert "imports_from" in out
    assert "No unique node matched" not in out


def _init_git_repo(root):
    import subprocess

    subprocess.run(["git", "init", "-q"], cwd=str(root), check=True)
    subprocess.run(["git", "config", "user.email", "t@t.com"], cwd=str(root), check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=str(root), check=True)


def test_parse_git_diff_hunks_maps_added_line_to_range():
    from graphify.affected import _parse_git_diff_hunks

    diff = (
        "diff --git a/pkg/foo.py b/pkg/foo.py\n"
        "index 111..222 100644\n"
        "--- a/pkg/foo.py\n"
        "+++ b/pkg/foo.py\n"
        "@@ -10,0 +11 @@ def bar():\n"
        "+    new_line\n"
    )
    result = _parse_git_diff_hunks(diff)
    assert result == {"pkg/foo.py": [(11, 11)]}


def test_parse_git_diff_hunks_multi_line_range():
    from graphify.affected import _parse_git_diff_hunks

    diff = (
        "diff --git a/pkg/foo.py b/pkg/foo.py\n"
        "--- a/pkg/foo.py\n"
        "+++ b/pkg/foo.py\n"
        "@@ -5,2 +5,4 @@ def bar():\n"
        "+a\n+b\n+c\n+d\n"
    )
    result = _parse_git_diff_hunks(diff)
    assert result == {"pkg/foo.py": [(5, 8)]}


def test_parse_git_diff_hunks_skips_deleted_file():
    from graphify.affected import _parse_git_diff_hunks

    diff = "diff --git a/gone.py b/gone.py\n--- a/gone.py\n+++ /dev/null\n@@ -1,3 +0,0 @@\n-x\n-y\n-z\n"
    assert _parse_git_diff_hunks(diff) == {}


def test_changed_seeds_maps_real_git_diff_to_nearest_node(tmp_path):
    """End-to-end against a real git repo (real subprocess git diff, not mocked) --
    the whole point of this feature is that it must work against real git output,
    not an idealized mock of it."""
    from graphify.affected import changed_seeds

    _init_git_repo(tmp_path)
    src = tmp_path / "mod.py"
    src.write_text("def foo():\n    return 1\n\n\ndef bar():\n    return 2\n", encoding="utf-8")
    import subprocess
    subprocess.run(["git", "add", "."], cwd=str(tmp_path), check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=str(tmp_path), check=True)

    # Modify bar() only.
    src.write_text("def foo():\n    return 1\n\n\ndef bar():\n    return 999\n", encoding="utf-8")

    graph = nx.DiGraph()
    graph.add_node("file", label="mod.py", source_file="mod.py", source_location="L1")
    graph.add_node("foo", label="foo()", source_file="mod.py", source_location="L1")
    graph.add_node("bar", label="bar()", source_file="mod.py", source_location="L5")

    result = changed_seeds(graph, tmp_path)
    assert result == {"mod.py": ["bar"]}


def test_format_git_diff_affected_reports_dependents(tmp_path):
    from graphify.affected import format_git_diff_affected

    _init_git_repo(tmp_path)
    src = tmp_path / "mod.py"
    src.write_text("def target():\n    return 1\n", encoding="utf-8")
    import subprocess
    subprocess.run(["git", "add", "."], cwd=str(tmp_path), check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=str(tmp_path), check=True)
    src.write_text("def target():\n    return 999\n", encoding="utf-8")

    graph = nx.DiGraph()
    graph.add_node("target", label="target()", source_file="mod.py", source_location="L1")
    graph.add_node("caller", label="caller()", source_file="app.py", source_location="L1")
    graph.add_edge("caller", "target", relation="calls", context="call", confidence="EXTRACTED")

    out = format_git_diff_affected(graph, tmp_path)
    assert "target()" in out
    assert "caller()" in out
    assert "contained (1 dependent)" in out
    assert "Total: 1 changed symbol(s), 1 dependent edge(s) found." in out


def test_format_git_diff_affected_clean_tree_reports_none(tmp_path):
    from graphify.affected import format_git_diff_affected

    _init_git_repo(tmp_path)
    (tmp_path / "mod.py").write_text("def target():\n    return 1\n", encoding="utf-8")
    import subprocess
    subprocess.run(["git", "add", "."], cwd=str(tmp_path), check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=str(tmp_path), check=True)

    graph = nx.DiGraph()
    graph.add_node("target", label="target()", source_file="mod.py", source_location="L1")

    out = format_git_diff_affected(graph, tmp_path)
    assert "No changed symbols found" in out


def test_affected_cli_git_diff_flag_reports_impact(monkeypatch, tmp_path, capsys):
    """CLI wiring: `graphify affected --git-diff` runs without a positional query."""
    import subprocess

    _init_git_repo(tmp_path)
    src = tmp_path / "mod.py"
    src.write_text("def target():\n    return 1\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=str(tmp_path), check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=str(tmp_path), check=True)
    src.write_text("def target():\n    return 999\n", encoding="utf-8")

    graphify_out = tmp_path / "graphify-out"
    graphify_out.mkdir()
    graph = nx.DiGraph()
    graph.add_node("target", label="target()", source_file="mod.py", source_location="L1")
    graph_path = graphify_out / "graph.json"
    graph_path.write_text(json.dumps(json_graph.node_link_data(graph, edges="links")), encoding="utf-8")

    monkeypatch.setattr(mainmod, "_check_skill_version", lambda _: None)
    monkeypatch.setattr(
        mainmod.sys, "argv", ["graphify", "affected", "--git-diff", "--graph", str(graph_path)]
    )

    mainmod.main()

    out = capsys.readouterr().out
    assert "Git-diff impact" in out
    assert "target()" in out
