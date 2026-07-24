"""Tests for the cross-file http_calls resolver (Feature 2 Task 8,
iac-http-linking) - wires Task 6's doGet/doPost action arms to Task 7's
fetch() call-sites, purely by action-string match across files. Goes
through the real extract() pipeline (multi-file corpus), not extract_js()
alone, since resolution is cross-file.
"""
from graphify.extract import extract


def test_http_calls_links_fetch_call_site_to_action_handler_target(tmp_path):
    gas = tmp_path / "sync.gs"
    gas.write_text(
        "function doGet(e) {\n"
        "  var action = e.parameter.action;\n"
        "  if (action === 'holdings') {\n"
        "    data = getHoldings();\n"
        "  } else if (action === 'dividends') {\n"
        "    data = getDividends();\n"
        "  }\n"
        "}\n"
        "function getHoldings() { return 1; }\n"
        "function getDividends() { return 2; }\n"
    )
    api = tmp_path / "api.js"
    api.write_text(
        "async function fetchHoldings() {\n"
        "  return fetch(`${GAS_URL}?action=holdings&token=x`);\n"
        "}\n"
    )

    result = extract([str(gas), str(api)])
    getholdings_nid = next(n["id"] for n in result["nodes"] if n["label"] == "getHoldings()")
    dogGet_nid = next(n["id"] for n in result["nodes"] if n["label"] == "doGet()")
    call_nid = next(n["id"] for n in result["nodes"] if n["label"] == "fetch(action=holdings)")

    http_edges = {(e["source"], e["target"]) for e in result["edges"] if e["relation"] == "http_calls"}
    assert (call_nid, getholdings_nid) in http_edges
    assert (call_nid, dogGet_nid) not in http_edges  # links to the arm's target, not doGet itself

    edge = next(e for e in result["edges"] if e["relation"] == "http_calls")
    assert edge["confidence"] == "INFERRED"


def test_http_calls_interpolated_call_site_gets_no_edge(tmp_path):
    gas = tmp_path / "sync.gs"
    gas.write_text(
        "function doGet(e) {\n"
        "  var action = e.parameter.action;\n"
        "  if (action === 'holdings') { data = getHoldings(); }\n"
        "}\n"
        "function getHoldings() { return 1; }\n"
    )
    api = tmp_path / "api.js"
    api.write_text(
        "function fetchDynamic(action) {\n"
        "  return fetch(`${GAS_URL}?action=${action}`);\n"
        "}\n"
    )
    result = extract([str(gas), str(api)])
    http_edges = [e for e in result["edges"] if e["relation"] == "http_calls"]
    assert http_edges == []


def test_http_calls_no_gas_handlers_in_corpus_is_a_no_op(tmp_path):
    """A repo with no doGet/doPost anywhere must never even attempt
    resolution - cheap early exit, no accidental edges."""
    api = tmp_path / "api.js"
    api.write_text(
        "function fetchHoldings() {\n"
        "  return fetch(`${GAS_URL}?action=holdings`);\n"
        "}\n"
    )
    result = extract([str(api)])
    http_edges = [e for e in result["edges"] if e["relation"] == "http_calls"]
    assert http_edges == []
