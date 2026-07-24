"""Tests for Google Apps Script doGet/doPost action-dispatch arm parsing
(Feature 2 Task 6, iac-http-linking). No edges are emitted at this stage -
just the resolved {action: callee_node_id} mapping per handler, consumed
later by the http_calls resolver (Task 8).
"""
from graphify.extract import extract_js


def test_extract_js_doget_action_arms_resolve_to_callee_nodes(tmp_path):
    f = tmp_path / "sync.gs"
    f.write_text(
        "function doGet(e) {\n"
        "  var action = e.parameter.action;\n"
        "  if (action === 'holdings') {\n"
        "    data = getHoldings();\n"
        "  } else if (action === 'dividends') {\n"
        "    data = getDividends();\n"
        "  } else {\n"
        "    data = fallback();\n"
        "  }\n"
        "}\n"
        "function getHoldings() { return 1; }\n"
        "function getDividends() { return 2; }\n"
    )
    result = extract_js(f)
    handlers = result.get("gas_action_handlers") or []
    assert len(handlers) == 1
    actions = handlers[0]["actions"]
    node_by_label = {n["label"]: n["id"] for n in result["nodes"]}
    assert actions["holdings"] == node_by_label["getHoldings()"]
    assert actions["dividends"] == node_by_label["getDividends()"]
    # the final plain `else` (no action literal) must not appear
    assert "fallback" not in actions
    assert len(actions) == 2


def test_extract_js_non_gas_function_produces_no_action_handlers(tmp_path):
    """A plain if/else-if chain in a function NOT named doGet/doPost must not
    be mistaken for an action dispatcher."""
    f = tmp_path / "plain.js"
    f.write_text(
        "function route(action) {\n"
        "  if (action === 'holdings') { getHoldings(); }\n"
        "}\n"
        "function getHoldings() {}\n"
    )
    result = extract_js(f)
    assert result.get("gas_action_handlers") is None


def test_extract_js_dopost_with_unresolvable_callee_is_skipped(tmp_path):
    """An arm whose callee isn't defined anywhere in this file (e.g. it's a
    cross-file/global helper) must be skipped, not produce a None/dangling
    entry - same-file resolution only, matching the design's stated scope."""
    f = tmp_path / "sync.gs"
    f.write_text(
        "function doPost(e) {\n"
        "  var action = e.parameter.action;\n"
        "  if (action === 'save') {\n"
        "    saveEverything();\n"
        "  }\n"
        "}\n"
    )
    result = extract_js(f)
    handlers = result.get("gas_action_handlers") or []
    assert handlers == []
