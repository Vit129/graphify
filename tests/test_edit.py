"""Graph-guided symbol edits: replace body, insert after, rename, safe delete.

Safety contract under test: dry-run by default (diff, no write); the graph's line range must
still match the file; ambiguous nodes are refused; Python files must still parse; paths outside
the project root are never touched; rename only edits lines the graph confirms and reports the rest.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from networkx.readwrite import json_graph

import graphify.__main__ as mainmod
from graphify import serve as servemod
from graphify.build import build_from_json
from graphify.edit import EditError, delete_symbol, insert_after_symbol, rename_symbol, replace_symbol_body
from graphify.extract import extract

STATE = (
    "def load_session():\n"
    "    return {'session_id': None}\n"
    "\n"
    "\n"
    "def save_session(session):\n"
    "    # mirrors load_session()\n"
    "    return session\n"
)
APP = (
    "import state\n"
    "from state import save_session\n"
    "\n"
    "\n"
    "def run():\n"
    "    data = state.load_session()\n"
    "    return save_session(data)\n"
)


def _project(tmp_path: Path, state: str = STATE, app: str = APP):
    (tmp_path / "state.py").write_text(state, encoding="utf-8", newline="")
    (tmp_path / "app.py").write_text(app, encoding="utf-8", newline="")
    result = extract([tmp_path / "state.py", tmp_path / "app.py"], cache_root=tmp_path)
    G = build_from_json(result, directed=True, root=tmp_path)
    out = tmp_path / "graphify-out"
    out.mkdir(exist_ok=True)
    gp = out / "graph.json"
    gp.write_text(json.dumps(json_graph.node_link_data(G, edges="links")), encoding="utf-8")
    return G, gp


def _read(tmp_path: Path, name: str) -> str:
    return (tmp_path / name).read_bytes().decode("utf-8")


# ---- replace_symbol_body -------------------------------------------------------------
def test_replace_is_a_dry_run_by_default(tmp_path: Path):
    G, _ = _project(tmp_path)
    r = replace_symbol_body(G, "load_session()", "def load_session():\n    return {}\n", tmp_path)
    assert r["applied"] is False and "-    return {'session_id': None}" in r["diff"]
    assert _read(tmp_path, "state.py") == STATE


def test_replace_apply_changes_only_the_symbol(tmp_path: Path):
    G, _ = _project(tmp_path)
    replace_symbol_body(G, "load_session()", "def load_session():\n    return {}", tmp_path, apply=True)
    after = _read(tmp_path, "state.py")
    assert after.startswith("def load_session():\n    return {}\n\n\ndef save_session")
    assert after.endswith("    return session\n")


def test_replace_refuses_when_graph_is_stale_for_the_file(tmp_path: Path):
    G, _ = _project(tmp_path)
    (tmp_path / "state.py").write_text("# new first line\n" + STATE, encoding="utf-8")
    with pytest.raises(EditError, match="stale"):
        replace_symbol_body(G, "load_session()", "def load_session():\n    return 1\n", tmp_path, apply=True)


def test_replace_refuses_python_that_no_longer_parses(tmp_path: Path):
    G, _ = _project(tmp_path)
    with pytest.raises(EditError, match="syntax"):
        replace_symbol_body(G, "load_session()", "def load_session(:\n", tmp_path, apply=True)
    assert _read(tmp_path, "state.py") == STATE


def test_replace_refuses_ambiguous_label(tmp_path: Path):
    G, _ = _project(tmp_path)
    G.add_node("dup", label="load_session()", source_file="app.py", source_location="L5", end_line=7)
    with pytest.raises(EditError, match="ambiguous"):
        replace_symbol_body(G, "load_session()", "def load_session():\n    pass\n", tmp_path)


def test_replace_preserves_crlf(tmp_path: Path):
    G, _ = _project(tmp_path, state=STATE.replace("\n", "\r\n"))
    replace_symbol_body(G, "load_session()", "def load_session():\n    return {}\n", tmp_path, apply=True)
    raw = (tmp_path / "state.py").read_bytes()
    assert b"\r\n" in raw and b"\n" not in raw.replace(b"\r\n", b"")


def test_nothing_outside_the_project_root_is_edited(tmp_path: Path):
    G, _ = _project(tmp_path)
    outside = tmp_path.parent / "outside_edit.py"
    outside.write_text("def evil():\n    pass\n", encoding="utf-8")
    G.add_node("evil", label="evil()", source_file=str(outside), source_location="L1", end_line=2)
    with pytest.raises(EditError, match="outside"):
        replace_symbol_body(G, "evil()", "def evil():\n    return 1\n", tmp_path, apply=True)
    assert outside.read_text(encoding="utf-8") == "def evil():\n    pass\n"


# ---- insert_after_symbol --------------------------------------------------------------
def test_insert_after_symbol(tmp_path: Path):
    G, _ = _project(tmp_path)
    insert_after_symbol(G, "load_session()", "\n\ndef clear_session():\n    return None", tmp_path, apply=True)
    after = _read(tmp_path, "state.py")
    assert "    return {'session_id': None}\n\n\ndef clear_session():\n    return None\n\n\ndef save_session" in after


# ---- rename_symbol --------------------------------------------------------------------
def test_rename_updates_definition_call_sites_and_reports_the_unverified(tmp_path: Path):
    G, _ = _project(tmp_path)
    r = rename_symbol(G, "load_session()", "read_session", tmp_path, apply=True)
    assert "def read_session():" in _read(tmp_path, "state.py")
    assert "state.read_session()" in _read(tmp_path, "app.py")
    # the comment on state.py line 6 is not backed by any graph edge: untouched but reported
    assert "# mirrors load_session()" in _read(tmp_path, "state.py")
    assert any(u["file"] == "state.py" and u["line"] == 6 for u in r["unverified"])
    assert r["applied"] is True


def test_rename_dry_run_writes_nothing(tmp_path: Path):
    G, _ = _project(tmp_path)
    r = rename_symbol(G, "load_session()", "read_session", tmp_path)
    assert r["applied"] is False and "+def read_session():" in r["diff"]
    assert _read(tmp_path, "state.py") == STATE and _read(tmp_path, "app.py") == APP


def test_rename_all_occurrences_also_renames_the_unverified(tmp_path: Path):
    G, _ = _project(tmp_path)
    rename_symbol(G, "load_session()", "read_session", tmp_path, apply=True, all_occurrences=True)
    assert "# mirrors read_session()" in _read(tmp_path, "state.py")


def test_rename_follows_a_from_import(tmp_path: Path):
    G, _ = _project(tmp_path)
    rename_symbol(G, "save_session()", "store_session", tmp_path, apply=True)
    app = _read(tmp_path, "app.py")
    assert "from state import store_session" in app and "return store_session(data)" in app


def test_rename_rejects_bad_or_colliding_names(tmp_path: Path):
    G, _ = _project(tmp_path)
    with pytest.raises(EditError, match="identifier"):
        rename_symbol(G, "load_session()", "not an identifier", tmp_path)
    with pytest.raises(EditError, match="already"):
        rename_symbol(G, "load_session()", "save_session", tmp_path)


def test_rename_result_must_still_parse(tmp_path: Path):
    G, _ = _project(tmp_path)
    with pytest.raises(EditError, match="syntax"):
        rename_symbol(G, "load_session()", "class", tmp_path, apply=True)  # keyword: breaks the file
    assert _read(tmp_path, "state.py") == STATE


# ---- delete_symbol --------------------------------------------------------------------
def test_delete_is_refused_while_something_depends_on_it(tmp_path: Path):
    G, _ = _project(tmp_path)
    with pytest.raises(EditError, match="dependen"):
        delete_symbol(G, "load_session()", tmp_path, apply=True)
    assert _read(tmp_path, "state.py") == STATE


def test_delete_unreferenced_symbol_removes_exactly_its_lines(tmp_path: Path):
    G, _ = _project(tmp_path, app="import state\n\n\ndef run():\n    return 1\n")
    delete_symbol(G, "load_session()", tmp_path, apply=True)
    assert _read(tmp_path, "state.py") == "def save_session(session):\n    # mirrors load_session()\n    return session\n"


# ---- CLI / MCP wiring -----------------------------------------------------------------
def test_cli_rename_dry_run_then_apply(tmp_path: Path, monkeypatch, capsys):
    _, gp = _project(tmp_path)
    monkeypatch.setattr(sys, "argv", ["graphify", "edit", "rename", "load_session()", "read_session", "--graph", str(gp)])
    mainmod.main()
    out = capsys.readouterr().out
    assert "+def read_session():" in out and "dry run" in out.lower()
    assert _read(tmp_path, "state.py") == STATE
    monkeypatch.setattr(sys, "argv", ["graphify", "edit", "rename", "load_session()", "read_session", "--apply", "--graph", str(gp)])
    mainmod.main()
    assert "def read_session():" in _read(tmp_path, "state.py")


def test_cli_edit_error_exits_nonzero(tmp_path: Path, monkeypatch, capsys):
    _, gp = _project(tmp_path)
    monkeypatch.setattr(sys, "argv", ["graphify", "edit", "rename", "load_session()", "bad name", "--graph", str(gp)])
    with pytest.raises(SystemExit) as exc:
        mainmod.main()
    assert exc.value.code == 1 and "identifier" in capsys.readouterr().err


def test_mcp_edit_tools_default_to_dry_run(tmp_path: Path):
    G, gp = _project(tmp_path)
    out = servemod._tool_rename_symbol_text(G, {"node": "load_session()", "new_name": "read_session"}, gp)
    assert "dry run" in out.lower() and _read(tmp_path, "state.py") == STATE
    assert servemod._tool_rename_symbol_text(G, {"node": "load_session()", "new_name": "x y"}, gp).startswith("Error:")
    src = Path(servemod.__file__).read_text(encoding="utf-8")
    for name in ("replace_symbol_body", "insert_after_symbol", "rename_symbol", "safe_delete_symbol"):
        assert f'name="{name}"' in src
