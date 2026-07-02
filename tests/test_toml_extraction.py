"""Tests for the TOML extractor. .toml files previously had no extractor
at all — an earlier audit found only ~1 real local file and deprioritized
it; a wider filesystem search found real config files everywhere
(starship.toml, multiple cliff.toml, tool command configs), reversing that
verdict. See agent-memory/plans/p10-toml-and-fish-extraction.md.
"""
from graphify.extractors.toml_ import extract_toml


def test_extract_toml_table_produces_node(tmp_path):
    f = tmp_path / "config.toml"
    f.write_text("[server]\nport = 8080\n")
    result = extract_toml(f)
    labels = [n["label"] for n in result["nodes"]]
    assert "server" in labels


def test_extract_toml_dotted_table_key_produces_node(tmp_path):
    f = tmp_path / "pyproject.toml"
    f.write_text("[project.optional-dependencies]\ndev = [\"pytest\"]\n")
    result = extract_toml(f)
    labels = [n["label"] for n in result["nodes"]]
    assert "project.optional-dependencies" in labels


def test_extract_toml_root_level_pair_produces_node(tmp_path):
    f = tmp_path / "config.toml"
    f.write_text("title = \"my app\"\n\n[server]\nport = 8080\n")
    result = extract_toml(f)
    labels = [n["label"] for n in result["nodes"]]
    assert "title" in labels


def test_extract_toml_repeated_array_of_tables_produces_distinct_nodes(tmp_path):
    f = tmp_path / "plugins.toml"
    f.write_text("[[tool.plugin]]\nname = \"a\"\n\n[[tool.plugin]]\nname = \"b\"\n")
    result = extract_toml(f)
    plugin_nodes = [n for n in result["nodes"] if n["label"] == "tool.plugin"]
    assert len(plugin_nodes) == 2
    assert plugin_nodes[0]["id"] != plugin_nodes[1]["id"]


def test_extract_toml_file_contains_edge_to_table(tmp_path):
    f = tmp_path / "config.toml"
    f.write_text("[server]\nport = 8080\n")
    result = extract_toml(f)
    by_label = {n["label"]: n["id"] for n in result["nodes"]}
    file_id = by_label["config.toml"]
    table_id = by_label["server"]
    relations = {(e["source"], e["target"]) for e in result["edges"]}
    assert (file_id, table_id) in relations


def test_extract_toml_dispatches_from_extract_module(tmp_path):
    from graphify.extract import extract

    f = tmp_path / "wired.toml"
    f.write_text("[wired_section]\nkey = 1\n")
    result = extract([str(f)])
    labels = [n["label"] for n in result["nodes"]]
    assert "wired_section" in labels
