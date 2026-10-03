"""`module.func()` calls resolve to the module's top-level function (gap found in line-bot:
`import state` + `state.load_session()` produced no `calls` edge, so `affected` missed callers)."""
from __future__ import annotations

from pathlib import Path

from graphify.extract import extract


def _write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _nid(result: dict, label: str, source_file: str) -> str:
    matches = [
        n["id"] for n in result["nodes"]
        if n.get("label") == label and n.get("source_file") == source_file
    ]
    assert len(matches) == 1, (label, source_file, matches)
    return matches[0]


def _calls(result: dict, source: str, target: str) -> bool:
    return any(
        e["source"] == source and e["target"] == target and e["relation"] == "calls"
        for e in result["edges"]
    )


def _run(tmp_path: Path, files: dict[str, str]) -> dict:
    paths = [_write(tmp_path / name, text) for name, text in files.items()]
    return extract(paths, cache_root=tmp_path)


def test_plain_import_module_call_from_function(tmp_path: Path):
    r = _run(tmp_path, {
        "state.py": "def load():\n    return 1\n",
        "app.py": "import state\n\ndef f():\n    return state.load()\n",
    })
    assert _calls(r, _nid(r, "f()", "app.py"), _nid(r, "load()", "state.py"))


def test_plain_import_module_call_from_method(tmp_path: Path):
    r = _run(tmp_path, {
        "state.py": "def load():\n    return 1\n",
        "app.py": "import state\n\nclass H:\n    def m(self):\n        return state.load()\n",
    })
    assert _calls(r, _nid(r, ".m()", "app.py"), _nid(r, "load()", "state.py"))


def test_aliased_import(tmp_path: Path):
    r = _run(tmp_path, {
        "state.py": "def load():\n    return 1\n",
        "app.py": "import state as st\n\ndef f():\n    return st.load()\n",
    })
    assert _calls(r, _nid(r, "f()", "app.py"), _nid(r, "load()", "state.py"))


def test_from_package_import_submodule(tmp_path: Path):
    r = _run(tmp_path, {
        "pkg/__init__.py": "",
        "pkg/state.py": "def load():\n    return 1\n",
        "app.py": "from pkg import state\n\ndef f():\n    return state.load()\n",
    })
    assert _calls(r, _nid(r, "f()", "app.py"), _nid(r, "load()", "pkg/state.py"))


def test_relative_import_submodule(tmp_path: Path):
    r = _run(tmp_path, {
        "pkg/__init__.py": "",
        "pkg/state.py": "def load():\n    return 1\n",
        "pkg/app.py": "from . import state\n\ndef f():\n    return state.load()\n",
    })
    assert _calls(r, _nid(r, "f()", "pkg/app.py"), _nid(r, "load()", "pkg/state.py"))


def test_dotted_import_with_alias(tmp_path: Path):
    r = _run(tmp_path, {
        "pkg/__init__.py": "",
        "pkg/state.py": "def load():\n    return 1\n",
        "app.py": "import pkg.state as s\n\ndef f():\n    return s.load()\n",
    })
    assert _calls(r, _nid(r, "f()", "app.py"), _nid(r, "load()", "pkg/state.py"))


def test_missing_function_creates_no_edge_and_no_node(tmp_path: Path):
    r = _run(tmp_path, {
        "state.py": "def load():\n    return 1\n",
        "app.py": "import state\n\ndef f():\n    return state.nothing()\n",
    })
    f = _nid(r, "f()", "app.py")
    assert not any(e["source"] == f and e["relation"] == "calls" for e in r["edges"])
    assert not any(n.get("label") == "nothing()" for n in r["nodes"])


def test_external_module_creates_no_edge(tmp_path: Path):
    r = _run(tmp_path, {
        "state.py": "def load():\n    return 1\n",
        "app.py": "import os\n\ndef f():\n    return os.load()\n",
    })
    f = _nid(r, "f()", "app.py")
    assert not any(e["source"] == f and e["relation"] == "calls" for e in r["edges"])


def test_instance_receiver_is_not_treated_as_a_module(tmp_path: Path):
    r = _run(tmp_path, {
        "state.py": "def load():\n    return 1\n",
        "app.py": "import state\n\ndef f(obj):\n    return obj.load()\n",
    })
    f = _nid(r, "f()", "app.py")
    assert not _calls(r, f, _nid(r, "load()", "state.py"))


def test_ambiguous_module_name_creates_no_edge(tmp_path: Path):
    r = _run(tmp_path, {
        "a/state.py": "def load():\n    return 1\n",
        "b/state.py": "def load():\n    return 2\n",
        "app.py": "import state\n\ndef f():\n    return state.load()\n",
    })
    f = _nid(r, "f()", "app.py")
    assert not any(e["source"] == f and e["relation"] == "calls" for e in r["edges"])
