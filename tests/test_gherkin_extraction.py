"""Tests for the Gherkin (.feature) extractor. .feature files previously
had no extractor at all — no tree-sitter grammar exists for Gherkin on PyPI
(checked), so this is a hand-rolled line scanner instead of the tree-sitter
template every other extractor in this session used. See
agent-memory/plans/p8-scss-cross-file-and-gherkin.md.
"""
from graphify.extractors.gherkin import extract_gherkin


def test_extract_gherkin_feature_produces_node(tmp_path):
    f = tmp_path / "login.feature"
    f.write_text("Feature: User login\n  As a user\n  I want to log in\n")
    result = extract_gherkin(f)
    labels = [n["label"] for n in result["nodes"]]
    assert "User login" in labels


def test_extract_gherkin_scenario_produces_child_node(tmp_path):
    f = tmp_path / "login.feature"
    f.write_text(
        "Feature: User login\n"
        "\n"
        "  Scenario: Successful login\n"
        "    Given a registered user\n"
        "    When they enter valid credentials\n"
        "    Then they should see the dashboard\n"
    )
    result = extract_gherkin(f)
    labels = [n["label"] for n in result["nodes"]]
    assert "Successful login" in labels
    # Given/When/Then step lines must not become their own nodes.
    assert not any("registered user" in lbl for lbl in labels)


def test_extract_gherkin_scenario_outline_produces_child_node(tmp_path):
    f = tmp_path / "login.feature"
    f.write_text(
        "Feature: User login\n"
        "\n"
        "  Scenario Outline: Failed login with bad password\n"
        "    Given a registered user\n"
        "    When they enter an invalid password \"<password>\"\n"
        "    Then they should see an error\n"
        "\n"
        "    Examples:\n"
        "      | password |\n"
        "      | wrong123 |\n"
    )
    result = extract_gherkin(f)
    labels = [n["label"] for n in result["nodes"]]
    assert "Failed login with bad password" in labels


def test_extract_gherkin_scenario_nests_under_its_feature(tmp_path):
    f = tmp_path / "login.feature"
    f.write_text(
        "Feature: User login\n"
        "\n"
        "  Scenario: Successful login\n"
        "    Given a registered user\n"
    )
    result = extract_gherkin(f)
    by_label = {n["label"]: n["id"] for n in result["nodes"]}
    feature_id = by_label["User login"]
    scenario_id = by_label["Successful login"]
    relations = {(e["source"], e["target"]) for e in result["edges"]}
    assert (feature_id, scenario_id) in relations


def test_extract_gherkin_tags_and_comments_are_skipped(tmp_path):
    f = tmp_path / "login.feature"
    f.write_text(
        "# a top-level comment\n"
        "@smoke @login\n"
        "Feature: User login\n"
        "\n"
        "  @slow\n"
        "  Scenario: Successful login\n"
        "    Given a registered user\n"
    )
    result = extract_gherkin(f)
    assert result.get("error") is None
    labels = [n["label"] for n in result["nodes"]]
    assert "User login" in labels
    assert "Successful login" in labels


def test_extract_gherkin_dispatches_from_extract_module(tmp_path):
    from graphify.extract import extract

    f = tmp_path / "wired.feature"
    f.write_text("Feature: Wired feature\n\n  Scenario: A test\n    Given something\n")
    result = extract([str(f)])
    labels = [n["label"] for n in result["nodes"]]
    assert "Wired feature" in labels
    assert "A test" in labels
