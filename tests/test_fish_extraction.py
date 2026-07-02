"""Tests for the fish shell extractor. .fish files previously had no
extractor at all — an earlier audit found only 1-2 real local files
(mostly duplicated activate.fish venv boilerplate) and deprioritized it; a
wider filesystem search found real hand-written fish scripts with genuine
function definitions (harness.fish's OSC133 prompt hooks), reversing that
verdict. See agent-memory/plans/p10-toml-and-fish-extraction.md.
"""
from graphify.extractors.fish import extract_fish


def test_extract_fish_function_produces_node(tmp_path):
    f = tmp_path / "script.fish"
    f.write_text("function greet\n    echo hello\nend\n")
    result = extract_fish(f)
    labels = [n["label"] for n in result["nodes"]]
    assert "greet" in labels


def test_extract_fish_function_nested_in_if_block_is_still_found(tmp_path):
    """Real fish scripts commonly guard function definitions behind an
    `if`/`end` block (see harness.fish) — the regex scanner doesn't track
    block nesting, so this must still find the function regardless of
    indentation depth."""
    f = tmp_path / "script.fish"
    f.write_text(
        "if set -q HARNESS\n"
        "    function __harness_osc133_prompt --on-event fish_prompt\n"
        "        printf '\\033]133;A\\007'\n"
        "    end\n"
        "end\n"
    )
    result = extract_fish(f)
    labels = [n["label"] for n in result["nodes"]]
    assert "__harness_osc133_prompt" in labels


def test_extract_fish_comment_mentioning_function_is_not_a_node(tmp_path):
    f = tmp_path / "script.fish"
    f.write_text("# see function foo for details\nfunction real_one\n    echo hi\nend\n")
    result = extract_fish(f)
    labels = [n["label"] for n in result["nodes"]]
    assert "real_one" in labels
    assert "foo" not in labels


def test_extract_fish_file_contains_edge_to_function(tmp_path):
    f = tmp_path / "script.fish"
    f.write_text("function greet\n    echo hello\nend\n")
    result = extract_fish(f)
    by_label = {n["label"]: n["id"] for n in result["nodes"]}
    file_id = by_label["script.fish"]
    fn_id = by_label["greet"]
    relations = {(e["source"], e["target"]) for e in result["edges"]}
    assert (file_id, fn_id) in relations


def test_extract_fish_dispatches_from_extract_module(tmp_path):
    from graphify.extract import extract

    f = tmp_path / "wired.fish"
    f.write_text("function wired_fn\n    echo hi\nend\n")
    result = extract([str(f)])
    labels = [n["label"] for n in result["nodes"]]
    assert "wired_fn" in labels
