"""P15 — opt-in cross-file value-coupling edges (`shares_value`).

Validated at ~96% precision on Home-Assistant's real YAML corpus (Phase 0,
2026-07-04) after adding the service-verb + UI-file filters the plan's
original 3-filter set lacked (which measured only ~27%).
"""
from __future__ import annotations
from pathlib import Path

from graphify.extract import (
    _resolve_value_coupling,
    _is_value_coupling_service_verb,
    _is_value_coupling_ui_file,
)
from graphify.extractors.yaml_ import extract_yaml, _is_identifier_leaf


def _pf(*files):
    """Build per_file dicts: each arg is (source_file, [values])."""
    out = []
    for src, values in files:
        out.append({
            "nodes": [], "edges": [],
            "values": [
                {"value": v, "node_id": f"nid::{src}", "source_file": src, "line": 1}
                for v in values
            ],
        })
    return out


def test_shared_value_across_two_files_makes_one_edge():
    per_file = _pf(
        ("a/bedroom_ac.yaml", ["climate.living_room_ac", "input_boolean.home_mode"]),
        ("b/home_mode.yaml", ["input_boolean.home_mode"]),
    )
    edges = _resolve_value_coupling(per_file)
    assert len(edges) == 1
    e = edges[0]
    assert e["relation"] == "shares_value:input_boolean.home_mode"
    assert e["confidence"] == "INFERRED"
    assert e["weight"] == 0.3
    assert {e["source"], e["target"]} == {"nid::a/bedroom_ac.yaml", "nid::b/home_mode.yaml"}


def test_endpoints_resolved_against_final_nodes_after_id_remap():
    """Regression: later extract() passes remap file-node ids (an absolute-path
    stem `/x/a.yaml` → `a`), so the node_id captured at YAML-extraction time
    dangles. Passing all_nodes lets the coupling pass resolve the CURRENT file
    node id by source_file, so the edge points at real nodes instead of being
    silently dropped by graph assembly (the bug that made `graphify update`
    emit zero coupling edges)."""
    per_file = [
        {"nodes": [], "edges": [], "values": [
            {"value": "climate.x", "node_id": "STALE_LONG_ID_A",
             "source_file": "/abs/a.yaml", "line": 1}]},
        {"nodes": [], "edges": [], "values": [
            {"value": "climate.x", "node_id": "STALE_LONG_ID_B",
             "source_file": "/abs/b.yaml", "line": 1}]},
    ]
    # Final nodes carry the REMAPPED short ids + relative source_file.
    all_nodes = [
        {"id": "a", "source_file": "a.yaml", "source_location": "L1"},
        {"id": "b", "source_file": "b.yaml", "source_location": "L1"},
    ]
    edges = _resolve_value_coupling(per_file, all_nodes)
    assert len(edges) == 1
    assert {edges[0]["source"], edges[0]["target"]} == {"a", "b"}
    # NOT the stale captured ids.
    assert "STALE_LONG_ID_A" not in {edges[0]["source"], edges[0]["target"]}


def test_value_in_more_than_hub_cap_files_makes_no_edge():
    # Same value in 6 files (> cap 5) => it's a constant, not a reference.
    per_file = _pf(*[(f"f{i}.yaml", ["sensor.shared_thing"]) for i in range(6)])
    assert _resolve_value_coupling(per_file) == []


def test_value_in_exactly_hub_cap_files_still_couples():
    per_file = _pf(*[(f"f{i}.yaml", ["sensor.shared_thing"]) for i in range(5)])
    edges = _resolve_value_coupling(per_file)
    # 5 files => C(5,2) = 10 pairwise edges.
    assert len(edges) == 10


def test_non_dotted_value_is_excluded_even_if_identifier_shaped():
    """Only dotted entity-reference shapes (`domain.entity`) couple - the
    non-dotted long-snake branch (`power_outage_scheduler`, HA schema keywords
    like `automation`/`binary_sensor`) is collected by the leaf scanner but
    NOT coupled, because it exploded edge count +106% and tanked precision on
    the real corpus. Dotted-only is the filter the Phase 0 gate passed at 96%."""
    per_file = _pf(
        ("a.yaml", ["power_outage_scheduler", "automation"]),
        ("b.yaml", ["power_outage_scheduler", "automation"]),
    )
    assert _resolve_value_coupling(per_file) == []


def test_service_verb_value_is_excluded():
    per_file = _pf(
        ("a.yaml", ["fan.turn_on"]),
        ("b.yaml", ["fan.turn_on"]),
    )
    assert _resolve_value_coupling(per_file) == []


def test_ui_dashboard_file_side_is_excluded():
    per_file = _pf(
        ("ha/automations/climate/bedroom.yaml", ["light.living_room"]),
        ("ha/lovelace/floorplan.yaml", ["light.living_room"]),
    )
    # The only other file sharing the value is a UI file => dropped => no pair.
    assert _resolve_value_coupling(per_file) == []


def test_same_file_repeated_value_makes_no_self_edge():
    per_file = [{
        "nodes": [], "edges": [],
        "values": [
            {"value": "climate.x", "node_id": "nid::solo", "source_file": "solo.yaml", "line": 1},
        ],
    }]
    assert _resolve_value_coupling(per_file) == []


def test_missing_values_field_is_tolerated():
    # Cached-stale extraction from before the `values` field existed.
    per_file = [{"nodes": [], "edges": []}, None]
    assert _resolve_value_coupling(per_file) == []


def test_service_verb_predicate():
    assert _is_value_coupling_service_verb("fan.turn_on")
    assert _is_value_coupling_service_verb("climate.set_temperature")
    assert not _is_value_coupling_service_verb("climate.living_room_ac")
    assert not _is_value_coupling_service_verb("input_boolean.home_mode")


def test_ui_file_predicate():
    assert _is_value_coupling_ui_file("ha/lovelace/floorplan.yaml")
    assert _is_value_coupling_ui_file("config/dashboards/home.yaml")
    assert not _is_value_coupling_ui_file("ha/automations/climate/bedroom.yaml")


def test_identifier_leaf_shape():
    assert _is_identifier_leaf("climate.living_room_ac")
    assert _is_identifier_leaf("binary_sensor.front_door")
    assert _is_identifier_leaf("power_outage_scheduler")  # long snake
    assert not _is_identifier_leaf("on")       # too short / boolean-ish
    assert not _is_identifier_leaf("off")
    assert not _is_identifier_leaf("123")
    assert not _is_identifier_leaf("Hello World")


def test_yaml_extractor_collects_identifier_leaves(tmp_path):
    p = tmp_path / "automation.yaml"
    p.write_text(
        "automation:\n"
        "  - alias: AC on arrival\n"
        "    trigger:\n"
        "      platform: state\n"
        "      entity_id: device_tracker.vit_iphone\n"
        "    action:\n"
        "      service: climate.turn_on\n"
        "      target:\n"
        "        entity_id: climate.living_room_ac\n",
        encoding="utf-8",
    )
    result = extract_yaml(p)
    got = {v["value"] for v in result.get("values", [])}
    assert "device_tracker.vit_iphone" in got
    assert "climate.living_room_ac" in got
    # every collected leaf carries the file's source_file (for the UI filter)
    assert all(v["source_file"] == str(p) for v in result["values"])
