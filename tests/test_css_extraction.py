"""Tests for the CSS extractor. .css files previously had no extractor at
all. See real-project audit findings referenced in
agent-memory/knowledge/architecture/feature-provenance.md.
"""
from graphify.extractors.css import extract_css


def test_extract_css_class_selector_produces_node(tmp_path):
    f = tmp_path / "style.css"
    f.write_text(".btn-primary {\n  color: blue;\n}\n")
    result = extract_css(f)
    labels = [n["label"] for n in result["nodes"]]
    assert ".btn-primary" in labels


def test_extract_css_id_and_descendant_selector_produces_node(tmp_path):
    f = tmp_path / "style.css"
    f.write_text("#header .nav-item {\n  display: flex;\n}\n")
    result = extract_css(f)
    labels = [n["label"] for n in result["nodes"]]
    assert "#header .nav-item" in labels


def test_extract_css_media_query_produces_container_node(tmp_path):
    f = tmp_path / "responsive.css"
    f.write_text(
        "@media (max-width: 600px) {\n"
        "  .btn-primary {\n"
        "    color: red;\n"
        "  }\n"
        "}\n"
    )
    result = extract_css(f)
    labels = [n["label"] for n in result["nodes"]]
    assert any("@media" in lbl for lbl in labels)


def test_extract_css_rule_nested_in_media_query_is_distinct_from_top_level_rule(tmp_path):
    """The same selector appearing both at top level and inside @media must
    produce two distinct nodes, not collide/overwrite each other."""
    f = tmp_path / "override.css"
    f.write_text(
        ".btn-primary {\n  color: blue;\n}\n"
        "@media (max-width: 600px) {\n"
        "  .btn-primary {\n"
        "    color: red;\n"
        "  }\n"
        "}\n"
    )
    result = extract_css(f)
    btn_nodes = [n for n in result["nodes"] if n["label"] == ".btn-primary"]
    assert len(btn_nodes) == 2
    assert btn_nodes[0]["id"] != btn_nodes[1]["id"]


def test_extract_css_file_contains_edge_to_rule(tmp_path):
    f = tmp_path / "chain.css"
    f.write_text(".foo {\n  color: blue;\n}\n")
    result = extract_css(f)
    by_label = {n["label"]: n["id"] for n in result["nodes"]}
    file_id = by_label["chain.css"]
    rule_id = by_label[".foo"]
    relations = {(e["source"], e["target"]) for e in result["edges"]}
    assert (file_id, rule_id) in relations


def test_extract_css_dispatches_from_extract_module(tmp_path):
    from graphify.extract import extract

    f = tmp_path / "wired.css"
    f.write_text(".wired-class {\n  color: green;\n}\n")
    result = extract([str(f)])
    labels = [n["label"] for n in result["nodes"]]
    assert ".wired-class" in labels
