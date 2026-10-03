"""The CLI's "graph may be stale" hint must follow CONTENT, not commit identity.

A graph committed to git is always at least one commit behind HEAD (committing it creates a new
commit), so comparing hashes alone warned on every read. It should warn only when files the graph
knows (or new code files) changed between the build commit and HEAD."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from graphify.__main__ import _warn_if_graph_stale


def _git(cwd: Path, *args: str) -> str:
    r = subprocess.run(
        ["git", "-c", "user.email=t@t", "-c", "user.name=t", *args],
        cwd=cwd, check=True, capture_output=True, text=True,
    )
    return r.stdout.strip()


def _repo(tmp_path: Path) -> str:
    _git(tmp_path, "init", "-q")
    (tmp_path / "a.py").write_text("def f():\n    pass\n", encoding="utf-8")
    _git(tmp_path, "add", "a.py")
    _git(tmp_path, "commit", "-q", "-m", "init")
    return _git(tmp_path, "rev-parse", "HEAD")


def _graph(tmp_path: Path, commit: str) -> Path:
    out = tmp_path / "graphify-out"
    out.mkdir(exist_ok=True)
    gp = out / "graph.json"
    gp.write_text(json.dumps({
        "built_at_commit": commit,
        "nodes": [{"id": "a", "label": "f()", "source_file": "a.py"}],
        "links": [],
    }), encoding="utf-8")
    return gp


def _commit_file(tmp_path: Path, rel: str, text: str) -> None:
    p = tmp_path / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    _git(tmp_path, "add", rel)
    _git(tmp_path, "commit", "-q", "-m", f"touch {rel}")


def test_no_hint_when_graph_is_at_head(tmp_path: Path, capsys):
    gp = _graph(tmp_path, _repo(tmp_path))
    _warn_if_graph_stale(gp)
    assert capsys.readouterr().err == ""


def test_no_hint_when_only_graphify_out_changed_since_the_build(tmp_path: Path, capsys):
    built = _repo(tmp_path)
    gp = _graph(tmp_path, built)
    _commit_file(tmp_path, "graphify-out/graph.json", gp.read_text(encoding="utf-8"))
    _warn_if_graph_stale(gp)
    assert capsys.readouterr().err == ""


def test_no_hint_when_only_non_code_files_changed(tmp_path: Path, capsys):
    built = _repo(tmp_path)
    gp = _graph(tmp_path, built)
    _commit_file(tmp_path, "notes.txt.bak", "x")
    _warn_if_graph_stale(gp)
    assert capsys.readouterr().err == ""


def test_hint_when_a_graph_file_changed(tmp_path: Path, capsys):
    built = _repo(tmp_path)
    gp = _graph(tmp_path, built)
    _commit_file(tmp_path, "a.py", "def f():\n    return 1\n")
    _warn_if_graph_stale(gp)
    err = capsys.readouterr().err
    assert "may be stale" in err and "a.py" in err


def test_hint_when_a_new_code_file_appeared(tmp_path: Path, capsys):
    built = _repo(tmp_path)
    gp = _graph(tmp_path, built)
    _commit_file(tmp_path, "pkg/b.py", "def g():\n    pass\n")
    _warn_if_graph_stale(gp)
    assert "pkg/b.py" in capsys.readouterr().err


def test_hint_falls_back_to_hash_comparison_when_the_commit_is_unknown(tmp_path: Path, capsys):
    _repo(tmp_path)
    gp = _graph(tmp_path, "deadbeefdeadbeefdeadbeefdeadbeefdeadbeef")
    _warn_if_graph_stale(gp)
    assert "may be stale" in capsys.readouterr().err
