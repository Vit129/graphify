"""Tests for P17 item 6 (content-as-data indexing): a top-level
`const NAME = [ {...}, {...}, ... ]` array whose elements look like structured
content (lesson/course/quiz entries with a title/name/label/description/id key)
gets one lightweight node per element, instead of staying a single opaque
`NAME` node with its content invisible to the graph.

Gate is deliberately narrow (mirrors _is_config_json's shape-probe for data
JSON, #1224): 3+ sibling object elements, each with 3+ properties, each
carrying a recognized key. Anything less falls back to the pre-existing
single-node behavior — no regression for dispatch registries or plain data
blobs.
"""
from graphify.extract import extract_js


def test_extract_js_content_data_array_produces_per_item_nodes(tmp_path):
    f = tmp_path / "course.js"
    f.write_text(
        "const LESSONS = [\n"
        "  { id: 'intro', title: 'Intro to Playwright', template: `code1`, hint: 'h1' },\n"
        "  { id: 'locators', title: 'Locators', template: `code2`, hint: 'h2' },\n"
        "  { id: 'assertions', title: 'Assertions', template: `code3`, hint: 'h3' },\n"
        "];\n"
    )
    result = extract_js(f)
    labels = [n["label"] for n in result["nodes"]]
    assert "LESSONS" in labels
    assert "Intro to Playwright" in labels
    assert "Locators" in labels
    assert "Assertions" in labels

    item_nodes = [n for n in result["nodes"] if n.get("type") == "content_item"]
    assert len(item_nodes) == 3

    lessons_nid = next(n["id"] for n in result["nodes"] if n["label"] == "LESSONS")
    item_ids = {n["id"] for n in item_nodes}
    contains_edges = [e for e in result["edges"]
                       if e["source"] == lessons_nid and e["relation"] == "contains"
                       and e["target"] in item_ids]
    assert len(contains_edges) == 3


def test_extract_js_content_data_array_falls_back_below_size_gate(tmp_path):
    """Only 2 sibling objects — below the 3-object gate — must not be walked
    into items; the pre-existing single-node behavior stays unchanged."""
    f = tmp_path / "two.js"
    f.write_text(
        "const LESSONS = [\n"
        "  { id: 'a', title: 'A', template: `code`, hint: 'h' },\n"
        "  { id: 'b', title: 'B', template: `code`, hint: 'h' },\n"
        "];\n"
    )
    result = extract_js(f)
    labels = [n["label"] for n in result["nodes"]]
    assert "LESSONS" in labels
    assert "A" not in labels
    assert "B" not in labels
    assert not [n for n in result["nodes"] if n.get("type") == "content_item"]


def test_extract_js_content_data_array_requires_recognized_key(tmp_path):
    """3+ objects with 3+ properties each, but none carrying a title/name/
    label/description/id key — a plain data array, not content. Falls back
    to the single opaque node, same as any other array-valued const."""
    f = tmp_path / "data.js"
    f.write_text(
        "const ROWS = [\n"
        "  { x: 1, y: 2, z: 3 },\n"
        "  { x: 4, y: 5, z: 6 },\n"
        "  { x: 7, y: 8, z: 9 },\n"
        "];\n"
    )
    result = extract_js(f)
    assert not [n for n in result["nodes"] if n.get("type") == "content_item"]
    labels = [n["label"] for n in result["nodes"]]
    assert "ROWS" in labels


def test_extract_js_content_data_array_inside_top_level_iife(tmp_path):
    """A whole-file IIFE `(function(){...})()` is a common module-scoping
    idiom (the real-world motivating case: QA-Automation-Coding-Course's
    course.js files are all wrapped this way) — declarations directly inside
    it must be treated as module-level, not rejected by the #1077 scope
    guard the way an arbitrary nested callback is."""
    f = tmp_path / "iife.js"
    f.write_text(
        "(function() {\n"
        "  const LESSONS = [\n"
        "    { id: 'a', title: 'Lesson A', template: `code`, hint: 'h' },\n"
        "    { id: 'b', title: 'Lesson B', template: `code`, hint: 'h' },\n"
        "    { id: 'c', title: 'Lesson C', template: `code`, hint: 'h' },\n"
        "  ];\n"
        "})();\n"
    )
    result = extract_js(f)
    labels = [n["label"] for n in result["nodes"]]
    assert "LESSONS" in labels
    assert "Lesson A" in labels
    assert "Lesson B" in labels
    assert "Lesson C" in labels


def test_extract_js_nested_callback_inside_iife_still_rejected(tmp_path):
    """The IIFE recognition must stay narrow: a const declared inside a
    *nested* callback within the IIFE (not directly in its top-level body)
    must still be rejected by the #1077 scope guard — same as it would be
    at true module scope."""
    f = tmp_path / "nested_in_iife.js"
    f.write_text(
        "(function() {\n"
        "  describe('suite', () => {\n"
        "    const inner = new Set([1, 2, 3]);\n"
        "  });\n"
        "})();\n"
    )
    result = extract_js(f)
    labels = [n["label"] for n in result["nodes"]]
    assert "inner" not in labels


def test_extract_js_bare_identifier_array_registry_unaffected(tmp_path):
    """A dispatch-registry array of bare identifiers (existing indirect-dispatch
    case, tests/test_indirect_dispatch.py) has no `object` elements at all —
    the content-data gate must never fire for it."""
    f = tmp_path / "registry.js"
    f.write_text(
        "function handler() {}\n"
        "function cb() {}\n"
        "const HOOKS = [handler, cb];\n"
    )
    result = extract_js(f)
    assert not [n for n in result["nodes"] if n.get("type") == "content_item"]
    labels = [n["label"] for n in result["nodes"]]
    assert "HOOKS" in labels
