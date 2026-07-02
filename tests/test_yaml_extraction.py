"""Tests for the YAML extractor (P2). YAML previously had no extractor at
all — .yaml/.yml files were invisible to the graph (0 nodes, confirmed on a
real Home-Assistant repo during P2's investigation). See
agent-memory/plans/p2-yaml-extraction.md.
"""
from graphify.extractors.yaml_ import extract_yaml


def test_extract_yaml_top_level_key_produces_node(tmp_path):
    f = tmp_path / "config.yaml"
    f.write_text("automation:\n  - alias: Turn on lights\n")
    result = extract_yaml(f)
    labels = [n["label"] for n in result["nodes"]]
    assert "automation" in labels


def test_extract_yaml_list_item_uses_alias_as_label(tmp_path):
    f = tmp_path / "automations.yaml"
    f.write_text(
        "automation:\n"
        "  - alias: Turn on lights\n"
        "    trigger:\n"
        "      platform: state\n"
        "  - alias: Living room AC timer\n"
        "    id: living_room_ac_timer\n"
    )
    result = extract_yaml(f)
    labels = [n["label"] for n in result["nodes"]]
    assert "Turn on lights" in labels
    assert "Living room AC timer" in labels


def test_extract_yaml_list_item_without_label_key_falls_back_to_position(tmp_path):
    f = tmp_path / "no_alias.yaml"
    f.write_text("items:\n  - foo: bar\n  - baz: qux\n")
    result = extract_yaml(f)
    labels = [n["label"] for n in result["nodes"]]
    assert "items[0]" in labels
    assert "items[1]" in labels


def test_extract_yaml_nested_mapping_key_uses_name_field(tmp_path):
    """Home Assistant's timer: entity_id: {name: ...} shape — a mapping
    (not a list) under a top-level key, each sub-key a named entity.
    """
    f = tmp_path / "timers.yaml"
    f.write_text(
        "timer:\n"
        "  living_room_ac_cleanup:\n"
        '    name: "Living Room AC Cleanup"\n'
        "    icon: mdi:fan-clock\n"
    )
    result = extract_yaml(f)
    labels = [n["label"] for n in result["nodes"]]
    assert "Living Room AC Cleanup" in labels


def test_extract_yaml_nested_mapping_key_without_name_falls_back_to_key(tmp_path):
    f = tmp_path / "scripts.yaml"
    f.write_text("script:\n  another_script:\n    sequence:\n      - delay: 5\n")
    result = extract_yaml(f)
    labels = [n["label"] for n in result["nodes"]]
    assert "another_script" in labels


def test_extract_yaml_edges_connect_file_to_top_level_to_items(tmp_path):
    f = tmp_path / "chain.yaml"
    f.write_text("automation:\n  - alias: Test automation\n")
    result = extract_yaml(f)
    by_label = {n["label"]: n["id"] for n in result["nodes"]}
    file_id = by_label["chain.yaml"]
    auto_id = by_label["automation"]
    item_id = by_label["Test automation"]
    relations = {(e["source"], e["target"]) for e in result["edges"]}
    assert (file_id, auto_id) in relations
    assert (auto_id, item_id) in relations


def test_extract_yaml_empty_file_produces_only_file_node(tmp_path):
    f = tmp_path / "empty.yaml"
    f.write_text("")
    result = extract_yaml(f)
    assert len(result["nodes"]) == 1
    assert result["nodes"][0]["label"] == "empty.yaml"
    assert result.get("error") is None


def test_extract_yaml_dispatches_from_extract_module(tmp_path):
    """.yaml/.yml must actually be wired into the main dispatch table, not
    just exist as a standalone function nobody calls."""
    from graphify.extract import extract

    f = tmp_path / "wired.yaml"
    f.write_text("key: value\n")
    result = extract([str(f)])
    labels = [n["label"] for n in result["nodes"]]
    assert "wired.yaml" in labels
