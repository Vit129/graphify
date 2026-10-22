from __future__ import annotations

import networkx as nx

import graphify.__main__ as mainmod
from graphify.layers import detect_layers, layer_of_path
from graphify.onboard import build_onboarding
from graphify.tour import find_entry_points


def _graph() -> nx.DiGraph:
    G = nx.DiGraph()
    spec = [
        ("main", "main.py", "File main.py", 0),
        ("route", "app/routes/users.py", "get_users()", 0),
        ("svc", "app/services/user_service.py", "UserService", 1),
        ("model", "app/models/user.py", "User", 2),
    ]
    for nid, path, label, cid in spec:
        G.add_node(nid, label=label, source_file=path, community=cid)
    G.nodes["main"]["label"] = "main.py"
    G.add_edge("main", "route", relation="imports")
    G.add_edge("route", "svc", relation="calls")
    G.add_edge("svc", "model", relation="calls")
    return G


def test_layer_of_path_matches_singular_and_plural_dirs():
    assert layer_of_path("app/routes/users.py") == "API"
    assert layer_of_path("app/service/x.py") == "Service"
    assert layer_of_path("src/models/user.py") == "Data"
    assert layer_of_path("tests/test_x.py") == "Test"
    assert layer_of_path("main.py") == "Core"


def test_layer_match_ignores_filename_segment():
    assert layer_of_path("app/user_service.py") == "Core"


def test_detect_layers_counts_nodes():
    names = {l["name"]: l["node_count"] for l in detect_layers(_graph())}
    assert names == {"Core": 1, "API": 1, "Service": 1, "Data": 1}


def test_find_entry_points_prefers_entry_named_root_file():
    G = _graph()
    G.nodes["main"]["label"] = "main.py"
    entries = find_entry_points(G)
    assert entries and entries[0]["source_file"] == "main.py"


def test_build_onboarding_has_sections():
    doc = build_onboarding(_graph(), project_name="demo")
    for heading in ("# Onboarding: demo", "## Overview", "## Architecture layers", "## Guided tour"):
        assert heading in doc


def test_onboard_cli_writes_file(monkeypatch, tmp_path, capsys):
    import json

    from networkx.readwrite import json_graph

    gp = tmp_path / "graph.json"
    gp.write_text(json.dumps(json_graph.node_link_data(_graph(), edges="links")), encoding="utf-8")
    out = tmp_path / "docs" / "ONBOARDING.md"
    monkeypatch.setattr(mainmod, "_check_skill_version", lambda _: None)
    monkeypatch.setattr(mainmod.sys, "argv", ["graphify", "onboard", "--graph", str(gp), "--out", str(out)])
    mainmod.main()
    assert out.exists() and "## Guided tour" in out.read_text(encoding="utf-8")


def test_entry_points_unique_and_skip_tests():
    G = _graph()
    G.add_node("main2", label="main.py", source_file="main.py", community=0)
    G.add_node("t", label="main.py", source_file="tests/fixtures/main.py", community=0)
    paths = [e["source_file"] for e in find_entry_points(G)]
    assert paths.count("main.py") == 1
    assert not any("tests" in p for p in paths)
