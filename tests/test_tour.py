from __future__ import annotations

import json

import networkx as nx
from networkx.readwrite import json_graph

import graphify.__main__ as mainmod
from graphify.tour import build_tour, format_tour


def _graph() -> nx.DiGraph:
    G = nx.DiGraph()
    # api (community 0) -> service (1) -> db (2); sizes make db smallest
    for i in range(4):
        G.add_node(f"api{i}", label=f"handler{i}()", source_file="api.py", community=0, community_name="API")
    for i in range(3):
        G.add_node(f"svc{i}", label=f"Service{i}", source_file="svc.py", community=1, community_name="Services")
    for i in range(2):
        G.add_node(f"db{i}", label=f"Model{i}", source_file="db.py", community=2, community_name="Data")
    G.add_edge("api0", "svc0", relation="calls")
    G.add_edge("svc0", "db0", relation="calls")
    return G


def test_tour_orders_callers_before_dependencies():
    stops = build_tour(_graph())
    assert [s["title"] for s in stops] == ["API", "Services", "Data"]
    assert stops[0]["leads_to"] == ["Services"]
    assert stops[0]["files"] == ["api.py"]


def test_tour_respects_max_steps_keeps_largest():
    stops = build_tour(_graph(), max_steps=2)
    assert [s["title"] for s in stops] == ["API", "Services"]


def test_tour_empty_graph_message():
    assert build_tour(nx.DiGraph()) == []
    assert "No communities" in format_tour([])


def test_tour_cli(monkeypatch, tmp_path, capsys):
    gp = tmp_path / "graph.json"
    gp.write_text(json.dumps(json_graph.node_link_data(_graph(), edges="links")), encoding="utf-8")
    monkeypatch.setattr(mainmod, "_check_skill_version", lambda _: None)
    monkeypatch.setattr(mainmod.sys, "argv", ["graphify", "tour", "--graph", str(gp)])
    mainmod.main()
    out = capsys.readouterr().out
    assert out.index("API") < out.index("Services") < out.index("Data")
