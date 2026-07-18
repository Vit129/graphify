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


def test_extract_html_inline_script_function_produces_node(tmp_path):
    """A function defined inside an inline <script> block was previously
    invisible to the graph entirely (no id attribute involved, so the DOM-id
    pass never saw it, and nothing ran a JS pass over the script body) -
    `graphify explain`/`query` could never find it. extract_html_with_scripts
    fixes this by running a JS extraction pass over the masked script body."""
    from graphify.extract import extract_html_with_scripts

    f = tmp_path / "dashboard.html"
    f.write_text(
        "<html><body>\n"
        '  <div id="chart"></div>\n'
        "  <script>\n"
        "    function renderChart(data) {\n"
        "      return data.length;\n"
        "    }\n"
        "  </script>\n"
        "</body></html>\n"
    )
    result = extract_html_with_scripts(f)
    labels = [n["label"] for n in result["nodes"]]
    assert "#chart" in labels  # DOM-id pass still runs
    assert "renderChart()" in labels  # new: inline script pass


def test_extract_html_without_script_unaffected(tmp_path):
    """No <script> body at all -> extract_html_with_scripts must not add or
    change anything relative to plain extract_html (regression guard against
    the new wrapper adding noise to ordinary HTML)."""
    from graphify.extract import extract_html_with_scripts
    from graphify.extractors.html import extract_html

    f = tmp_path / "plain.html"
    f.write_text('<html><body><div id="foo">Hi</div></body></html>\n')
    assert extract_html_with_scripts(f) == extract_html(f)
