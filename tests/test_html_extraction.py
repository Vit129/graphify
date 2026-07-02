"""Tests for the HTML extractor. .html files previously had no extractor
at all. Scope deliberately narrow: only elements with an `id` attribute
become nodes — see graphify/extractors/html.py's module docstring for why.
"""
from graphify.extractors.html import extract_html


def test_extract_html_element_with_id_produces_node(tmp_path):
    f = tmp_path / "page.html"
    f.write_text('<html><body><div id="header">Hi</div></body></html>\n')
    result = extract_html(f)
    labels = [n["label"] for n in result["nodes"]]
    assert "#header" in labels


def test_extract_html_element_without_id_produces_no_node(tmp_path):
    """A class-only element (no id) is deliberately not extracted — every
    HTML document has hundreds of these; extracting them all would be noise
    with no searchability benefit."""
    f = tmp_path / "page.html"
    f.write_text('<html><body><div class="course-card">Hi</div></body></html>\n')
    result = extract_html(f)
    labels = [n["label"] for n in result["nodes"]]
    assert labels == ["page.html"]


def test_extract_html_multiple_ids_all_extracted(tmp_path):
    f = tmp_path / "page.html"
    f.write_text(
        "<html><body>\n"
        '  <button id="run-tests-btn">Run</button>\n'
        '  <button id="hint-btn">Hint</button>\n'
        "</body></html>\n"
    )
    result = extract_html(f)
    labels = [n["label"] for n in result["nodes"]]
    assert "#run-tests-btn" in labels
    assert "#hint-btn" in labels


def test_extract_html_file_contains_edge_to_element(tmp_path):
    f = tmp_path / "chain.html"
    f.write_text('<html><body><div id="foo">Hi</div></body></html>\n')
    result = extract_html(f)
    by_label = {n["label"]: n["id"] for n in result["nodes"]}
    file_id = by_label["chain.html"]
    elem_id = by_label["#foo"]
    relations = {(e["source"], e["target"]) for e in result["edges"]}
    assert (file_id, elem_id) in relations


def test_extract_html_dispatches_from_extract_module(tmp_path):
    from graphify.extract import extract

    f = tmp_path / "wired.html"
    f.write_text('<html><body><div id="wired-element">Hi</div></body></html>\n')
    result = extract([str(f)])
    labels = [n["label"] for n in result["nodes"]]
    assert "#wired-element" in labels
