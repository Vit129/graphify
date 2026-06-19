from __future__ import annotations

from pathlib import Path

import pytest

from graphify.extract import (
    extract,
    _api_normalize_path,
    _api_verbs_compatible,
    _api_path_is_specific,
)


# ── path normalization (unit) ───────────────────────────────────────────────

def test_param_styles_normalize_equal():
    # Flask, FastAPI/Spring, Express/React, and a JS template literal must all
    # canonicalize to the same path so a client matches its route.
    forms = [
        "/api/users/<int:id>",   # Flask
        "/api/users/{id}",       # FastAPI / Spring
        "/api/users/:id",        # Express / React
        "/api/users/${id}",      # JS template
        "/api/users/42",         # concrete numeric id
        "https://host/api/users/7?x=1#f",  # scheme/host/query/fragment stripped
    ]
    norms = {_api_normalize_path(f) for f in forms}
    assert norms == {"/api/users/{}"}


def test_specificity_guard():
    assert not _api_path_is_specific("/")
    assert not _api_path_is_specific("/{}")
    assert _api_path_is_specific("/api/users/{}")


def test_verb_compatibility():
    assert _api_verbs_compatible("GET", "GET")
    assert _api_verbs_compatible("ANY", "POST")   # fetch/route default
    assert not _api_verbs_compatible("GET", "POST")


# ── end-to-end resolution ───────────────────────────────────────────────────

def _write(p: Path, text: str) -> Path:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    return p


def _api_edges(result: dict) -> set[tuple[str, str]]:
    by_id = {n["id"]: n.get("label", "") for n in result["nodes"]}
    return {
        (by_id.get(e["source"], ""), by_id.get(e["target"], ""))
        for e in result["edges"]
        if e.get("resolution") == "api_contract"
    }


def _two_service_fixture(base: Path):
    _write(base / "frontend/src/api.ts",
           "export async function loadUser(id: number) {\n"
           "    const res = await fetch(`/api/users/${id}`);\n"
           "    return res.json();\n"
           "}\n\n"
           "export async function createUser(data: any) {\n"
           "    return axios.post('/api/users', data);\n"
           "}\n")
    _write(base / "backend/app.py",
           "from flask import Flask\napp = Flask(__name__)\n\n"
           "@app.get('/api/users/<int:id>')\n"
           "def get_user(id):\n    return {'id': id}\n\n"
           "@app.post('/api/users')\n"
           "def create_user():\n    return {'created': True}\n")
    return sorted([p for p in base.rglob("*") if p.suffix in (".ts", ".py")])


def test_cross_language_api_edges_resolve(tmp_path, monkeypatch):
    monkeypatch.setenv("GRAPHIFY_API_CONTRACT_EDGES", "1")
    files = _two_service_fixture(tmp_path / "src")
    result = extract(files, cache_root=tmp_path / "src")
    edges = _api_edges(result)
    assert ("loadUser()", "get_user()") in edges       # GET /api/users/{}
    assert ("createUser()", "create_user()") in edges  # POST /api/users


def test_api_edges_off_by_default(tmp_path, monkeypatch):
    monkeypatch.delenv("GRAPHIFY_API_CONTRACT_EDGES", raising=False)
    files = _two_service_fixture(tmp_path / "src")
    result = extract(files, cache_root=tmp_path / "src")
    assert _api_edges(result) == set()


def test_same_file_call_and_route_not_linked(tmp_path, monkeypatch):
    # A fetch and a route in the SAME file are not an API contract across services.
    monkeypatch.setenv("GRAPHIFY_API_CONTRACT_EDGES", "1")
    _write(tmp_path / "src/app.py",
           "from flask import Flask\napp = Flask(__name__)\n\n"
           "@app.get('/api/ping')\n"
           "def ping():\n    return 'ok'\n\n"
           "def caller():\n    return requests.get('/api/ping')\n")
    files = sorted((tmp_path / "src").rglob("*.py"))
    result = extract(files, cache_root=tmp_path / "src")
    assert _api_edges(result) == set()


def test_ambiguous_route_path_not_linked(tmp_path, monkeypatch):
    # Same path served by two different backend files -> ambiguous -> skip.
    monkeypatch.setenv("GRAPHIFY_API_CONTRACT_EDGES", "1")
    _write(tmp_path / "src/frontend/c.ts",
           "function go() { return fetch('/api/data'); }\n")
    _write(tmp_path / "src/svcA/a.py",
           "@app.get('/api/data')\ndef a():\n    return 1\n")
    _write(tmp_path / "src/svcB/b.py",
           "@app.get('/api/data')\ndef b():\n    return 2\n")
    files = sorted([p for p in (tmp_path / "src").rglob("*") if p.suffix in (".ts", ".py")])
    result = extract(files, cache_root=tmp_path / "src")
    assert _api_edges(result) == set()
