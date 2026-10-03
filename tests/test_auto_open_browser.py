"""`graphify update` / `cluster-only` must not pop a browser tab from agents, hooks or CI."""
from __future__ import annotations

import sys
import webbrowser
from pathlib import Path

from graphify.__main__ import _auto_open_browser


def _spy(monkeypatch):
    calls: list[str] = []
    monkeypatch.setattr(webbrowser, "open", lambda url, *a, **k: calls.append(url) or True)
    return calls


def test_no_browser_when_stdout_is_not_a_terminal(tmp_path: Path, monkeypatch):
    calls = _spy(monkeypatch)
    monkeypatch.delenv("GRAPHIFY_NO_OPEN", raising=False)
    monkeypatch.setattr(sys.stdout, "isatty", lambda: False, raising=False)
    _auto_open_browser(tmp_path / "graph.html")
    assert calls == []


def test_browser_opens_in_a_real_terminal(tmp_path: Path, monkeypatch):
    calls = _spy(monkeypatch)
    monkeypatch.delenv("GRAPHIFY_NO_OPEN", raising=False)
    monkeypatch.setattr(sys.stdout, "isatty", lambda: True, raising=False)
    _auto_open_browser(tmp_path / "graph.html")
    assert len(calls) == 1 and calls[0].endswith("graph.html")


def test_env_var_disables_it_even_in_a_terminal(tmp_path: Path, monkeypatch):
    calls = _spy(monkeypatch)
    monkeypatch.setenv("GRAPHIFY_NO_OPEN", "1")
    monkeypatch.setattr(sys.stdout, "isatty", lambda: True, raising=False)
    _auto_open_browser(tmp_path / "graph.html")
    assert calls == []
