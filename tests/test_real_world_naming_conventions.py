"""Regression coverage for P3 (camelCase/snake_case/kebab-case tokenization)
grounded in naming patterns pulled from real codebases on disk (TypeScript/
Playwright, Python, shell, Swift) rather than invented strings — so a passing
suite means the fix generalizes across languages and naming conventions
actually in use, not just the one synthetic case it was built against.

The TypeScript cases below use a generic e-commerce/QA-automation scenario
(retailer names as illustrative test data, not tied to any specific
codebase) rather than identifiers copied from a client repo; the naming
*shape* (camelCase with an embedded acronym, near-identical sibling
functions) is what's under test, not the literal source.

Sources (as of 2026-07-02, not vendored — copied here as literal strings):
  - My-Investment-Port (Python)
  - ~/.claude/scripts (shell)
  - harness-terminal (Swift)
  - QA-Automation-Coding-Course (HTML ids + JS)
"""
import networkx as nx

from graphify.serve import _score_nodes, _find_node


# --- TypeScript camelCase, including an embedded acronym ---
# Generic Playwright-style QA-automation naming (illustrative, not tied to a
# specific codebase).

def test_typescript_camel_case_with_embedded_acronym():
    """"amazon api login" must resolve to amazonAPILogin, not a same-domain
    decoy.

    "API" is a three-letter acronym run sandwiched between two ordinary
    words (amazon + API + Login) — the case most likely to fragment into
    single letters if the acronym-boundary rule is wrong.
    """
    G = nx.Graph()
    G.add_node("n1", label="amazonAPILogin", source_file="auth.ts", community=0)
    G.add_node("n2", label="ensureLoggedIn", source_file="auth.ts", community=0)
    scored = _score_nodes(G, ["amazon", "api", "login"])
    assert scored[0][1] == "n1"


def test_typescript_camel_case_disambiguates_near_identical_siblings():
    """submitAmazonOrderFlow / submitKinokuniyaOrderFlow / submitEditFlow
    share two of three words — the query must pick the one whose *specific*
    word (amazon) it named, not just whichever "submit...OrderFlow"/"Flow"
    node sorts first.
    """
    G = nx.Graph()
    G.add_node("amazon", label="submitAmazonOrderFlow", source_file="checkout.ts", community=0)
    G.add_node("kinokuniya", label="submitKinokuniyaOrderFlow", source_file="checkout.ts", community=0)
    G.add_node("edit", label="submitEditFlow", source_file="checkout.ts", community=0)
    scored = _score_nodes(G, ["submit", "amazon", "order", "flow"])
    assert scored[0][1] == "amazon"
    assert scored[0][0] > scored[1][0]


# --- Python snake_case ---
# Real function names from My-Investment-Port/*.py.

def test_python_snake_case_disambiguates_near_identical_siblings():
    """replace_css_transition vs replace_inline_transition — "css" is the
    only distinguishing word; it must carry the full disambiguation weight.
    """
    G = nx.Graph()
    G.add_node("css", label="replace_css_transition", source_file="fix_styles.py", community=0)
    G.add_node("inline", label="replace_inline_transition", source_file="fix_styles.py", community=0)
    scored = _score_nodes(G, ["replace", "css", "transition"])
    assert scored[0][1] == "css"
    assert scored[0][0] > scored[1][0]


# --- Shell: kebab-case filenames + snake_case function names ---
# Real filenames/functions from ~/.claude/scripts/*.sh.

def test_shell_kebab_case_filename_disambiguates_near_identical_siblings():
    """update-graphify-all.sh vs update-tools.sh — both start with "update",
    only "graphify" tells them apart.
    """
    G = nx.Graph()
    G.add_node(
        "graphify", label="update-graphify-all.sh",
        source_file="scripts/update-graphify-all.sh", community=0,
    )
    G.add_node(
        "tools", label="update-tools.sh",
        source_file="scripts/update-tools.sh", community=0,
    )
    scored = _score_nodes(G, ["update", "graphify"])
    assert scored[0][1] == "graphify"
    assert scored[0][0] > scored[1][0]


def test_shell_snake_case_function_name_hits_prefix_tier():
    G = nx.Graph()
    G.add_node(
        "n1", label="generate_instruction_file",
        source_file="scripts/session-start.sh", community=0,
    )
    G.add_node(
        "n2", label="merge_skills_dir",
        source_file="scripts/sync-all.sh", community=0,
    )
    scored = _score_nodes(G, ["generate", "instruction", "file"])
    assert scored[0][1] == "n1"


# --- Swift PascalCase/camelCase method, multi-word natural-language query ---
# Real method from harness-terminal (also the P3 plan's manual real-graph
# validation case — encoded here as a hermetic regression so it doesn't
# depend on an external checkout being present).

def test_swift_camel_case_method_found_by_paraphrased_query():
    G = nx.Graph()
    G.add_node(
        "n1", label=".reconcileSessionPersistenceWithMode()",
        source_file="AppDelegate.swift", community=0,
    )
    G.add_node("n2", label="Persistence", source_file="docs/keybindings.md", community=1)
    G.add_node("n3", label="session", source_file="SessionCoordinator.swift", community=2)
    scored = _score_nodes(G, ["reconcile", "session", "persistence"])
    assert scored[0][1] == "n1"


# --- HTML kebab-case ids + JS camelCase ---
# Real element ids and function names from QA-Automation-Coding-Course
# (an interactive coding-lesson site: HTML ids for editor/dialog/progress
# UI, JS handlers for lesson state).

def test_html_kebab_case_id_disambiguates_near_identical_siblings():
    """run-tests-btn / hint-btn / next-lesson-btn all end in "-btn" — only
    "run" + "tests" together identify the right element id.
    """
    G = nx.Graph()
    G.add_node("run", label="run-tests-btn", source_file="index.html", community=0)
    G.add_node("hint", label="hint-btn", source_file="index.html", community=0)
    G.add_node("next", label="next-lesson-btn", source_file="index.html", community=0)
    scored = _score_nodes(G, ["run", "tests", "btn"])
    assert scored[0][1] == "run"
    assert scored[0][0] > scored[1][0]


def test_html_kebab_case_compound_id_disambiguates_shared_prefix():
    """progress-bar-fill vs progress-label share "progress" — "bar" and
    "fill" must carry the disambiguation.
    """
    G = nx.Graph()
    G.add_node("fill", label="progress-bar-fill", source_file="index.html", community=0)
    G.add_node("label", label="progress-label", source_file="index.html", community=0)
    scored = _score_nodes(G, ["progress", "bar", "fill"])
    assert scored[0][1] == "fill"
    assert scored[0][0] > scored[1][0]


def test_js_camel_case_multiword_function_found_by_natural_query():
    """A developer describing the bug in plain words ("input salary and
    save") must resolve to inputSalaryAndSave, not a same-file decoy.
    """
    G = nx.Graph()
    G.add_node("n1", label="inputSalaryAndSave", source_file="course.js", community=0)
    G.add_node("n2", label="getHoldingsFromStorage", source_file="course.js", community=0)
    G.add_node("n3", label="setLessonCompleted", source_file="course.js", community=1)
    scored = _score_nodes(G, ["input", "salary", "and", "save"])
    assert scored[0][1] == "n1"


# --- _find_node: same fix, resolved through the exact-symbol-lookup path ---

def test_find_node_resolves_paraphrased_query_across_conventions():
    G = nx.Graph()
    G.add_node("n1", label="amazonAPILogin")
    G.add_node("n2", label="replace_css_transition")
    G.add_node("n3", label="update-graphify-all.sh")
    assert _find_node(G, "amazon api login") == ["n1"]
    assert _find_node(G, "replace css transition") == ["n2"]
    assert _find_node(G, "update graphify all") == ["n3"]
