"""Tests for fetch() literal-action call-site extraction (Feature 2 Task 7,
iac-http-linking). Produces `gas_fetch_calls` raw facts + a node per literal
call-site; cross-file correlation against gas_action_handlers is Task 8.
"""
from graphify.extract import extract_js


def test_extract_js_fetch_template_literal_action_is_captured(tmp_path):
    f = tmp_path / "api.js"
    f.write_text(
        "async function backupAll() {\n"
        "  const r = await fetch(`${GAS_URL}?action=all&token=${encodeURIComponent(GAS_TOKEN)}`);\n"
        "  return r.json();\n"
        "}\n"
    )
    result = extract_js(f)
    calls = result.get("gas_fetch_calls") or []
    assert len(calls) == 1
    assert calls[0]["action"] == "all"
    call_nid = calls[0]["call_nid"]
    assert any(n["id"] == call_nid for n in result["nodes"])


def test_extract_js_fetch_plain_string_literal_action_is_captured(tmp_path):
    f = tmp_path / "api.js"
    f.write_text(
        "function getHoldings() {\n"
        "  return fetch('?action=holdings');\n"
        "}\n"
    )
    result = extract_js(f)
    calls = result.get("gas_fetch_calls") or []
    assert len(calls) == 1
    assert calls[0]["action"] == "holdings"


def test_extract_js_fetch_interpolated_action_is_skipped(tmp_path):
    """Real My-Investment-Port pattern: `GAS_URL + '?action=' + action + ...`
    where `action` is a variable, not a literal - must be skipped, not
    guessed at."""
    f = tmp_path / "api.js"
    f.write_text(
        "function callGas(action) {\n"
        "  return fetch(GAS_URL + '?action=' + action + '&token=x');\n"
        "}\n"
    )
    result = extract_js(f)
    assert result.get("gas_fetch_calls") is None


def test_extract_js_fetch_template_interpolated_action_is_skipped(tmp_path):
    f = tmp_path / "api.js"
    f.write_text(
        "function callGas(action) {\n"
        "  return fetch(`${GAS_URL}?action=${action}`);\n"
        "}\n"
    )
    result = extract_js(f)
    assert result.get("gas_fetch_calls") is None


def test_extract_js_non_fetch_call_produces_no_facts(tmp_path):
    f = tmp_path / "plain.js"
    f.write_text("function f() { return axios.get('?action=holdings'); }\n")
    result = extract_js(f)
    assert result.get("gas_fetch_calls") is None
