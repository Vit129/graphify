"""Regression tests for scoped call resolution in the Pascal/Delphi extractor.

Before this fix, both `extract_pascal` (tree-sitter path) and
`_extract_pascal_regex` (fallback path) resolved every call by a single
file-wide ``{method_name_lower: node_id}`` dict with no class scoping. Two
unrelated classes declaring a same-named method (a common Pascal/Delphi
pattern -- property accessors, generated wrapper classes such as TLB import
units) silently collapsed onto whichever declaration was inserted last,
producing wrong cross-class `calls` edges. See `sample_scoped_calls.pas`.
"""
from __future__ import annotations

import pytest
from pathlib import Path

FIXTURES = Path(__file__).parent / "fixtures"
FIXTURE_PATH = FIXTURES / "sample_scoped_calls.pas"


def _extractors():
    from graphify.extract import extract_pascal, _extract_pascal_regex
    return [extract_pascal, _extract_pascal_regex]


def _class_node_id(r, class_label):
    matches = [n["id"] for n in r["nodes"] if n["label"] == class_label]
    assert len(matches) == 1, f"expected exactly one node labeled {class_label!r}, got {matches}"
    return matches[0]


def _method_node_id(r, class_label, method_label):
    class_id = _class_node_id(r, class_label)
    node_by_id = {n["id"]: n for n in r["nodes"]}
    for e in r["edges"]:
        if e["relation"] == "method" and e["source"] == class_id:
            node = node_by_id.get(e["target"])
            if node and node["label"] == method_label:
                return node["id"]
    raise AssertionError(f"no method edge {class_label}.{method_label} found")


def _has_call(r, src_id, tgt_id):
    return any(
        e["relation"] == "calls" and e["source"] == src_id and e["target"] == tgt_id
        for e in r["edges"]
    )


@pytest.mark.parametrize("extract", [
    pytest.param(0, id="tree-sitter"),
    pytest.param(1, id="regex-fallback"),
])
def test_calls_scoped_to_own_class(extract):
    r = _extractors()[extract](FIXTURE_PATH)
    first_configure = _method_node_id(r, "TFirstWidget", "Configure()")
    first_reset = _method_node_id(r, "TFirstWidget", "Reset()")
    assert _has_call(r, first_configure, first_reset)


@pytest.mark.parametrize("extract", [
    pytest.param(0, id="tree-sitter"),
    pytest.param(1, id="regex-fallback"),
])
def test_calls_do_not_cross_unrelated_classes(extract):
    r = _extractors()[extract](FIXTURE_PATH)
    first_configure = _method_node_id(r, "TFirstWidget", "Configure()")
    second_reset = _method_node_id(r, "TSecondWidget", "Reset()")
    assert not _has_call(r, first_configure, second_reset), (
        "TFirstWidget.Configure must not resolve Reset() to the unrelated "
        "TSecondWidget.Reset -- same-named methods on unrelated classes must "
        "not collapse into a cross-class edge"
    )


@pytest.mark.parametrize("extract", [
    pytest.param(0, id="tree-sitter"),
    pytest.param(1, id="regex-fallback"),
])
def test_calls_scoped_other_direction(extract):
    r = _extractors()[extract](FIXTURE_PATH)
    second_configure = _method_node_id(r, "TSecondWidget", "Configure()")
    second_reset = _method_node_id(r, "TSecondWidget", "Reset()")
    first_reset = _method_node_id(r, "TFirstWidget", "Reset()")
    assert _has_call(r, second_configure, second_reset)
    assert not _has_call(r, second_configure, first_reset), (
        "TSecondWidget.Configure must not resolve Reset() to the unrelated "
        "TFirstWidget.Reset"
    )


@pytest.mark.parametrize("extract", [
    pytest.param(0, id="tree-sitter"),
    pytest.param(1, id="regex-fallback"),
])
def test_calls_resolve_via_ancestor_chain(extract):
    r = _extractors()[extract](FIXTURE_PATH)
    derived_run = _method_node_id(r, "TDerivedWidget", "Run()")
    base_prepare = _method_node_id(r, "TBaseWidget", "Prepare()")
    assert _has_call(r, derived_run, base_prepare), (
        "TDerivedWidget.Run should resolve the inherited Prepare() to "
        "TBaseWidget.Prepare via the inherits chain"
    )


@pytest.mark.parametrize("extract", [
    pytest.param(0, id="tree-sitter"),
    pytest.param(1, id="regex-fallback"),
])
def test_calls_resolve_declaration_only_abstract_method(extract, tmp_path):
    src = tmp_path / "AbstractWidget.pas"
    src.write_text(
        "unit AbstractWidget;\n\n"
        "interface\n\n"
        "type\n"
        "  TAbstractWidget = class(TObject)\n"
        "  public\n"
        "    procedure Init; virtual; abstract;\n"
        "    procedure Run;\n"
        "  end;\n\n"
        "implementation\n\n"
        "procedure TAbstractWidget.Run;\n"
        "begin\n"
        "  Init;\n"
        "end;\n\n"
        "end.\n",
        encoding="utf-8",
    )
    r = _extractors()[extract](src)
    run_nid = _method_node_id(r, "TAbstractWidget", "Run()")
    init_nid = _method_node_id(r, "TAbstractWidget", "Init()")
    assert _has_call(r, run_nid, init_nid), (
        "TAbstractWidget.Run should resolve calls to declaration-only Init() "
        "even when Init has no implementation body in this file"
    )
