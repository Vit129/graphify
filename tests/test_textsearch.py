"""graphify grep: exact-text / regex search over the files the graph knows, with each hit
mapped to the innermost enclosing graph node (symbol)."""
from __future__ import annotations

import json
from pathlib import Path

from graphify.build import build_from_json
from graphify.extract import extract
from graphify.textsearch import format_text_hits, search_text


def _project(tmp_path: Path) -> tuple[object, Path]:
    (tmp_path / "state.py").write_text(
        "QUOTA = 250\n\n"
        "def load_session():\n"
        "    return {'session_id': None}  # TODO tidy\n\n"
        "class Store:\n"
        "    def save(self):\n"
        "        return 'saved quota 250'\n",
        encoding="utf-8",
    )
    (tmp_path / "app.py").write_text(
        "import state\n\ndef run():\n    return state.load_session()\n", encoding="utf-8"
    )
    (tmp_path / "notes.md").write_text("# Notes\nquota 250 warns\n", encoding="utf-8")
    result = extract([tmp_path / "state.py", tmp_path / "app.py"], cache_root=tmp_path)
    return build_from_json(result, directed=True, root=tmp_path), tmp_path


def test_literal_match_maps_to_enclosing_function(tmp_path: Path):
    G, root = _project(tmp_path)
    res = search_text(G, "TODO tidy", root=root)
    assert len(res["hits"]) == 1
    hit = res["hits"][0]
    assert (hit["file"], hit["line"]) == ("state.py", 4)
    assert hit["node"] == "load_session()"


def test_hit_inside_method_maps_to_the_method_not_the_class(tmp_path: Path):
    G, root = _project(tmp_path)
    hit = search_text(G, "saved quota", root=root)["hits"][0]
    assert hit["node"] == ".save()"


def test_top_level_line_maps_to_the_file_node(tmp_path: Path):
    G, root = _project(tmp_path)
    hit = search_text(G, "QUOTA = 250", root=root)["hits"][0]
    assert hit["node"] == "state.py"


def test_literal_is_not_a_regex(tmp_path: Path):
    G, root = _project(tmp_path)
    assert search_text(G, "load_.*", root=root)["hits"] == []
    assert search_text(G, "load_.*", root=root, regex=True)["hits"]


def test_ignore_case_and_limit(tmp_path: Path):
    G, root = _project(tmp_path)
    assert search_text(G, "todo", root=root)["hits"] == []
    assert len(search_text(G, "todo", root=root, ignore_case=True)["hits"]) == 1
    res = search_text(G, "250", root=root, limit=1)
    assert len(res["hits"]) == 1 and res["truncated"] is True


def test_path_filters(tmp_path: Path):
    G, root = _project(tmp_path)
    assert {h["file"] for h in search_text(G, "load_session", root=root)["hits"]} == {"state.py", "app.py"}
    only_app = search_text(G, "load_session", root=root, paths=["app.py"])
    assert {h["file"] for h in only_app["hits"]} == {"app.py"}
    no_app = search_text(G, "load_session", root=root, exclude_paths=["app.py"])
    assert {h["file"] for h in no_app["hits"]} == {"state.py"}


def test_only_files_the_graph_knows_are_searched(tmp_path: Path):
    G, root = _project(tmp_path)
    res = search_text(G, "warns", root=root)  # notes.md is on disk but not in the graph
    assert res["hits"] == []
    assert res["files_searched"] == 2


def test_context_lines(tmp_path: Path):
    G, root = _project(tmp_path)
    hit = search_text(G, "TODO tidy", root=root, context=1)["hits"][0]
    assert hit["before"] == ["def load_session():"]
    assert hit["after"] == [""]


def test_invalid_regex_raises_value_error(tmp_path: Path):
    G, root = _project(tmp_path)
    try:
        search_text(G, "(", root=root, regex=True)
    except ValueError as exc:
        assert "regex" in str(exc).lower()
    else:
        raise AssertionError("expected ValueError")


def test_paths_outside_root_are_never_read(tmp_path: Path):
    G, root = _project(tmp_path)
    outside = tmp_path.parent / "outside_secret.py"
    outside.write_text("SECRET = 1\n", encoding="utf-8")
    G.add_node("evil", label="evil.py", source_file=str(outside), source_location="L1")
    assert search_text(G, "SECRET", root=root)["hits"] == []


def test_format_and_json_roundtrip(tmp_path: Path):
    G, root = _project(tmp_path)
    res = search_text(G, "TODO tidy", root=root)
    text = format_text_hits(res)
    assert "state.py:4:" in text and "in load_session()" in text
    assert json.loads(json.dumps(res))["hits"][0]["line"] == 4
    assert "No matches" in format_text_hits(search_text(G, "zzzzzz", root=root))


def test_overlapping_context_is_not_printed_twice(tmp_path: Path):
    (tmp_path / "m.py").write_text("a = 1\nneedle one\nmiddle\nneedle two\nz = 2\n", encoding="utf-8")
    result = extract([tmp_path / "m.py"], cache_root=tmp_path)
    G = build_from_json(result, directed=True, root=tmp_path)
    text = format_text_hits(search_text(G, "needle", root=tmp_path, context=1))
    lines = [l for l in text.splitlines() if l.startswith("m.py")]
    assert len(lines) == len(set(lines)) == 5  # lines 1-5 once each, no duplicate context
    assert "--" not in text.splitlines()  # contiguous block: no separator
