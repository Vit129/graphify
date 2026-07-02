"""Tests for the SCSS extractor. .scss uses a different grammar from plain
CSS (tree-sitter-css produces ERROR nodes on SCSS variables/nesting/`&`) —
`extract_scss` shares `_extract_stylesheet` with `extract_css` but parses
with `tree-sitter-scss`. See agent-memory/plans/p8-scss-cross-file-and-gherkin.md.
"""
from graphify.extractors.css import extract_scss


def test_extract_scss_class_selector_produces_node(tmp_path):
    f = tmp_path / "style.scss"
    f.write_text(".btn-primary {\n  color: blue;\n}\n")
    result = extract_scss(f)
    labels = [n["label"] for n in result["nodes"]]
    assert ".btn-primary" in labels


def test_extract_scss_nested_selector_produces_distinct_child_node(tmp_path):
    """SCSS nesting (`.card { .title { ... } }`) is real SCSS syntax that
    plain CSS's grammar can't parse at all — the plain-CSS extractor never
    needed to handle it since CSS rule_sets don't nest."""
    f = tmp_path / "card.scss"
    f.write_text(
        ".card {\n"
        "  color: black;\n"
        "  .title {\n"
        "    font-weight: bold;\n"
        "  }\n"
        "}\n"
    )
    result = extract_scss(f)
    labels = [n["label"] for n in result["nodes"]]
    assert ".card" in labels
    assert ".title" in labels


def test_extract_scss_variable_declaration_does_not_error(tmp_path):
    f = tmp_path / "vars.scss"
    f.write_text("$primary: #333;\n.card {\n  color: $primary;\n}\n")
    result = extract_scss(f)
    assert result.get("error") is None


def test_extract_scss_mixin_produces_container_node(tmp_path):
    f = tmp_path / "mixins.scss"
    f.write_text("@mixin flex-center {\n  display: flex;\n}\n")
    result = extract_scss(f)
    labels = [n["label"] for n in result["nodes"]]
    assert any("@mixin" in lbl and "flex-center" in lbl for lbl in labels)


def test_extract_scss_dispatches_from_extract_module(tmp_path):
    from graphify.extract import extract

    f = tmp_path / "wired.scss"
    f.write_text(".wired-class {\n  color: green;\n}\n")
    result = extract([str(f)])
    labels = [n["label"] for n in result["nodes"]]
    assert ".wired-class" in labels
