"""Tests for P4 (Playwright/Jest test()/describe() block extraction).

Before this, a *.spec.ts file's individual test() blocks were invisible to
the graph — only the file node and any top-level helper functions were
extracted. A natural-language query for a specific test case had nothing to
find. See agent-memory/plans/p4-spec-test-block-extraction.md.
"""
from graphify.extract import extract_js


def test_extract_ts_flat_test_call_produces_node(tmp_path):
    f = tmp_path / "flat.spec.ts"
    f.write_text(
        "test('[TS-169476-01] Territory Level 2 -> code=22, name=WholeSales', "
        "async ({ request }) => {\n"
        "  expect(true).toBe(true);\n"
        "});\n"
    )
    result = extract_js(f)
    labels = [n["label"] for n in result["nodes"]]
    assert "[TS-169476-01] Territory Level 2 -> code=22, name=WholeSales" in labels


def test_extract_ts_nested_it_inside_describe_produces_node(tmp_path):
    """The core regression risk of this feature: the new call_expression
    branch must return False, not True, or default recursion never reaches
    this nested it() and it silently disappears.
    """
    f = tmp_path / "nested.spec.ts"
    f.write_text(
        "describe('Territory suite', () => {\n"
        "  it('does the thing', async () => {\n"
        "    expect(1).toBe(1);\n"
        "  });\n"
        "});\n"
    )
    result = extract_js(f)
    labels = [n["label"] for n in result["nodes"]]
    assert "Territory suite" in labels
    assert "does the thing" in labels


def test_extract_ts_dynamic_test_name_produces_no_node(tmp_path):
    """A non-string-literal first argument (a variable, template literal,
    etc.) is out of scope — must not produce a node, and must not crash.
    """
    f = tmp_path / "dynamic.spec.ts"
    f.write_text(
        "const name = 'dyn';\n"
        "test(name, async () => {\n"
        "  expect(1).toBe(1);\n"
        "});\n"
    )
    result = extract_js(f)
    labels = [n["label"] for n in result["nodes"]]
    assert "dyn" not in labels
    assert not any(lbl == "name" for lbl in labels)


def test_extract_ts_duplicate_description_different_lines_both_extracted(tmp_path):
    """Two test() calls with identical description text must not collide to
    the same node id and silently drop the second (the id includes the line
    number specifically to prevent this).
    """
    f = tmp_path / "dupes.spec.ts"
    f.write_text(
        "test('setup', async () => { expect(1).toBe(1); });\n"
        "test('setup', async () => { expect(2).toBe(2); });\n"
    )
    result = extract_js(f)
    setup_nodes = [n for n in result["nodes"] if n["label"] == "setup"]
    assert len(setup_nodes) == 2
    assert setup_nodes[0]["id"] != setup_nodes[1]["id"]


def test_extract_ts_file_contains_edge_to_test_node(tmp_path):
    f = tmp_path / "edge.spec.ts"
    f.write_text("test('a test', async () => { expect(1).toBe(1); });\n")
    result = extract_js(f)
    file_nid = next(n["id"] for n in result["nodes"] if n["label"] == "edge.spec.ts")
    test_nid = next(n["id"] for n in result["nodes"] if n["label"] == "a test")
    assert any(
        e["source"] == file_nid and e["target"] == test_nid and e["relation"] == "contains"
        for e in result["edges"]
    )


def test_extract_js_test_call_also_supported(tmp_path):
    """The feature isn't TS-only — plain .js Jest/Playwright specs get it too."""
    f = tmp_path / "plain.spec.js"
    f.write_text("test('js works too', () => { expect(1).toBe(1); });\n")
    result = extract_js(f)
    labels = [n["label"] for n in result["nodes"]]
    assert "js works too" in labels


def test_extract_ts_unrelated_call_produces_no_test_node(tmp_path):
    """A call to some other function named similarly (e.g. a custom
    `describe`-named helper) shouldn't be excluded from normal call
    extraction — but this only asserts the common non-test-framework case:
    an ordinary function call must not spuriously produce a description-text
    node.
    """
    f = tmp_path / "unrelated.spec.ts"
    f.write_text("console.log('not a test description');\n")
    result = extract_js(f)
    labels = [n["label"] for n in result["nodes"]]
    assert "not a test description" not in labels


def test_extract_ts_arrow_function_still_extracted_alongside_test_blocks(tmp_path):
    """Regression: existing extraction (top-level helper functions) must be
    unaffected by a file that also contains test() blocks.
    """
    f = tmp_path / "mixed.spec.ts"
    f.write_text(
        "async function createMaster() { return null; }\n\n"
        "test('uses helper', async () => { await createMaster(); });\n"
    )
    result = extract_js(f)
    labels = [n["label"] for n in result["nodes"]]
    assert "createMaster()" in labels
    assert "uses helper" in labels
