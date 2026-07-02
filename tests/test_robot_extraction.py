"""Tests for the Robot Framework extractor (P6). .robot files previously
had no extractor at all — entire QA test suites were invisible to the graph
(confirmed: 12 real .robot files in harness-terminal's actual test suite,
0 nodes before this). See agent-memory/plans/p6-robot-framework-extraction.md.
"""
from graphify.extractors.robot import extract_robot


def test_extract_robot_test_case_produces_node(tmp_path):
    f = tmp_path / "login.robot"
    f.write_text(
        "*** Test Cases ***\n"
        "Login With Valid Credentials\n"
        "    Open Browser    ${URL}    chrome\n"
    )
    result = extract_robot(f)
    labels = [n["label"] for n in result["nodes"]]
    assert "Login With Valid Credentials" in labels


def test_extract_robot_keyword_definition_produces_node(tmp_path):
    f = tmp_path / "keywords.robot"
    f.write_text(
        "*** Keywords ***\n"
        "Login As Admin\n"
        "    Open Browser    ${URL}    chrome\n"
    )
    result = extract_robot(f)
    labels = [n["label"] for n in result["nodes"]]
    assert "Login As Admin" in labels


def test_extract_robot_test_case_calls_locally_defined_keyword(tmp_path):
    f = tmp_path / "flow.robot"
    f.write_text(
        "*** Test Cases ***\n"
        "Login With Valid Credentials\n"
        "    Login As Admin\n"
        "    Should Be On Dashboard\n"
        "\n"
        "*** Keywords ***\n"
        "Login As Admin\n"
        "    Open Browser    ${URL}    chrome\n"
        "\n"
        "Should Be On Dashboard\n"
        "    Wait Until Page Contains    Dashboard\n"
    )
    result = extract_robot(f)
    by_label = {n["label"]: n["id"] for n in result["nodes"]}
    test_nid = by_label["Login With Valid Credentials"]
    admin_nid = by_label["Login As Admin"]
    dashboard_nid = by_label["Should Be On Dashboard"]
    calls = {(e["source"], e["target"]) for e in result["edges"] if e["relation"] == "calls"}
    assert (test_nid, admin_nid) in calls
    assert (test_nid, dashboard_nid) in calls


def test_extract_robot_call_to_builtin_keyword_produces_no_calls_edge(tmp_path):
    """Open Browser/Should Contain/etc. are library keywords, not locally
    defined — must not fabricate a phantom node/edge for them."""
    f = tmp_path / "builtin_only.robot"
    f.write_text(
        "*** Test Cases ***\n"
        "Login With Invalid Credentials\n"
        "    Open Browser    ${URL}    chrome\n"
    )
    result = extract_robot(f)
    calls = [e for e in result["edges"] if e["relation"] == "calls"]
    assert calls == []


def test_extract_robot_file_contains_edges_to_test_cases_and_keywords(tmp_path):
    f = tmp_path / "chain.robot"
    f.write_text(
        "*** Test Cases ***\n"
        "A Test\n"
        "    No Operation\n"
        "\n"
        "*** Keywords ***\n"
        "A Keyword\n"
        "    No Operation\n"
    )
    result = extract_robot(f)
    by_label = {n["label"]: n["id"] for n in result["nodes"]}
    file_id = by_label["chain.robot"]
    test_id = by_label["A Test"]
    keyword_id = by_label["A Keyword"]
    contains = {(e["source"], e["target"]) for e in result["edges"] if e["relation"] == "contains"}
    assert (file_id, test_id) in contains
    assert (file_id, keyword_id) in contains


def test_extract_robot_settings_and_variables_sections_do_not_crash(tmp_path):
    """*** Settings *** / *** Variables *** sections have no test-case/
    keyword definitions — must not error, must not spuriously produce
    nodes for setting names or variable names."""
    f = tmp_path / "settings.robot"
    f.write_text(
        "*** Settings ***\n"
        "Library    OperatingSystem\n"
        "\n"
        "*** Variables ***\n"
        "${URL}    https://example.com\n"
    )
    result = extract_robot(f)
    assert result.get("error") is None
    labels = [n["label"] for n in result["nodes"]]
    assert labels == ["settings.robot"]


def test_extract_robot_dispatches_from_extract_module(tmp_path):
    """.robot must actually be wired into the main dispatch table."""
    from graphify.extract import extract

    f = tmp_path / "wired.robot"
    f.write_text("*** Test Cases ***\nA Test\n    No Operation\n")
    result = extract([str(f)])
    labels = [n["label"] for n in result["nodes"]]
    assert "A Test" in labels


def test_extract_resource_file_shares_the_robot_extractor(tmp_path):
    """.resource files (shared/importable keyword libraries) use the exact
    same Robot Framework syntax as .robot test suites — same grammar,
    same extractor, just no test_case_definition (only keywords)."""
    from graphify.extract import extract

    f = tmp_path / "common.resource"
    f.write_text(
        "*** Keywords ***\n"
        "Split Right\n"
        "    Press Shortcut    cmd+d\n"
    )
    result = extract([str(f)])
    labels = [n["label"] for n in result["nodes"]]
    assert "Split Right" in labels
