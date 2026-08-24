"""#2072: Python import resolution must not depend on the scan root.

A src-layout project (code under `src/`) used to lose most of its `imports` /
`imports_from` edges when scanned from the repo root, because absolute imports
were resolved only against the scan root while file-node ids are scan-root
relative. The same project scanned from `src/` resolved fine — so the chosen
scan root silently changed the graph.
"""
from __future__ import annotations

from pathlib import Path

from graphify.extract import extract, _resolve_python_module_path
from graphify.build import build_from_json


_FILES = {
    "mypkg/__init__.py": "from mypkg.core import Engine\n",
    "mypkg/core.py": "class Engine:\n    pass\n",
    "mypkg/helpers.py": "def helper():\n    return 1\n",
    "mypkg/app.py": (
        "from mypkg.core import Engine\n"
        "import mypkg.helpers\n\n"
        "def run():\n    return mypkg.helpers.helper()\n"
    ),
}


def _write(base: Path, prefix: str = "") -> list[Path]:
    written = []
    for rel, body in _FILES.items():
        p = base / prefix / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body, encoding="utf-8")
        written.append(p)
    return written


def _import_edges(G):
    """(relation, source, target) for import edges, present-endpoints only."""
    return {
        (d.get("relation"), u, v)
        for u, v, d in G.edges(data=True)
        if d.get("relation") in ("imports", "imports_from")
    }


def test_resolve_python_module_path_walks_up_to_src_package_root(tmp_path):
    (tmp_path / "src" / "mypkg").mkdir(parents=True)
    core = tmp_path / "src" / "mypkg" / "core.py"
    core.write_text("class Engine: pass\n")
    app = tmp_path / "src" / "mypkg" / "app.py"
    app.write_text("from mypkg.core import Engine\n")
    # scan root is the repo, code is under src/: must still resolve.
    resolved = _resolve_python_module_path("mypkg.core", app, tmp_path, level=0)
    assert resolved == core
    # flat layout (package at root) is unchanged.
    (tmp_path / "flat").mkdir()
    (tmp_path / "flat" / "mod.py").write_text("x = 1\n")
    assert _resolve_python_module_path("flat.mod", tmp_path / "flat" / "a.py", tmp_path, 0) == (
        tmp_path / "flat" / "mod.py"
    )


def test_import_edges_identical_from_root_or_src(tmp_path):
    """Headline (#2072): the same project yields the same import edges whether
    scanned from the repo root or from src/ (modulo the `src_` id prefix)."""
    direct = tmp_path / "direct"
    nested = tmp_path / "nested"
    _write(direct)                 # direct/mypkg/...
    _write(nested, prefix="src")   # nested/src/mypkg/...  (byte-identical)

    dpaths = [direct / r for r in _FILES]
    npaths = [nested / "src" / r for r in _FILES]
    dG = build_from_json(extract(dpaths, cache_root=tmp_path / "cd", root=direct, parallel=False), root=str(direct))
    nG = build_from_json(extract(npaths, cache_root=tmp_path / "cn", root=nested, parallel=False), root=str(nested))

    d_edges = _import_edges(dG)
    # strip the `src_` prefix the nested layout adds to every id.
    n_edges = {
        (rel, u[4:] if u.startswith("src_") else u, v[4:] if v.startswith("src_") else v)
        for rel, u, v in _import_edges(nG)
    }
    assert d_edges, "sanity: the flat layout must produce import edges"
    assert n_edges == d_edges, (
        f"scan root changed the import graph (#2072)\n root-only: {d_edges - n_edges}\n src-only: {n_edges - d_edges}"
    )
    # Concretely, in the src layout: app<->core are connected by an import edge
    # (endpoint order is storage-dependent on an undirected graph), and no import
    # endpoint is a bare, unresolved `mypkg_*` id — every target resolved to a
    # real `src_mypkg_*` file/symbol node.
    n_imports = _import_edges(nG)
    assert any({"src_mypkg_app"} <= {u, v} and any(n.startswith("src_mypkg_core") for n in (u, v))
               for _, u, v in n_imports), f"app->core import not resolved: {n_imports}"
    endpoints = {n for _, u, v in n_imports for n in (u, v)}
    assert not any(n.startswith("mypkg_") for n in endpoints), (
        f"unresolved bare import id survived (scan-root-relative mismatch): {endpoints}"
    )


def test_same_package_in_separate_roots_scoped_to_own_root(tmp_path):
    """A dotted-module import in one src root must resolve to that root's own
    package, never fabricating edges to a sibling root (#2072)."""
    for sub in ("a", "b"):
        d = tmp_path / sub / "src" / "pkg"
        d.mkdir(parents=True)
        (d / "__init__.py").write_text("")
        (d / "mod.py").write_text("def f():\n    return 1\n")
    (tmp_path / "a" / "src" / "pkg" / "app.py").write_text("import pkg.mod\n")
    paths = [
        tmp_path / "a" / "src" / "pkg" / "app.py",
        tmp_path / "a" / "src" / "pkg" / "mod.py",
        tmp_path / "b" / "src" / "pkg" / "mod.py",
        tmp_path / "a" / "src" / "pkg" / "__init__.py",
        tmp_path / "b" / "src" / "pkg" / "__init__.py",
    ]
    res = extract(paths, cache_root=tmp_path / "c", root=tmp_path, parallel=False)
    import_edges = [
        e for e in res["edges"]
        if e.get("relation") in ("imports", "imports_from") and e.get("source") == "a_src_pkg_app"
    ]
    targets = {e["target"] for e in import_edges}
    # a/src/pkg/app.py must resolve to its own a_src_pkg_mod and NEVER b_src_pkg_mod.
    assert "a_src_pkg_mod" in targets
    assert "b_src_pkg_mod" not in targets


def test_unrelated_sibling_tree_and_stub_imports_not_fabricated(tmp_path):
    """Reviewer reproduction: src/app/main.py importing boto3.session and pkg.mod
    must NOT fabricate edges to thirdparty_stubs/boto3/session.py or
    other_project/pkg/mod.py (unrelated trees with no sys.path relationship)."""
    src_app = tmp_path / "src" / "app"
    src_app.mkdir(parents=True)
    (src_app / "__init__.py").write_text("")
    (src_app / "main.py").write_text(
        "import boto3.session\n"
        "from pkg.mod import f\n\n"
        "def run():\n"
        "    return f()\n"
    )

    stubs = tmp_path / "thirdparty_stubs" / "boto3"
    stubs.mkdir(parents=True)
    (stubs / "__init__.py").write_text("")
    (stubs / "session.py").write_text("class Session: pass\n")

    other = tmp_path / "other_project" / "pkg"
    other.mkdir(parents=True)
    (other / "__init__.py").write_text("")
    (other / "mod.py").write_text("def f(): return 1\n")

    paths = [
        src_app / "__init__.py",
        src_app / "main.py",
        stubs / "__init__.py",
        stubs / "session.py",
        other / "__init__.py",
        other / "mod.py",
    ]
    res = extract(paths, cache_root=tmp_path / "c", root=tmp_path, parallel=False)

    main_edges = [
        e for e in res["edges"]
        if e.get("source") == "src_app_main" and e.get("relation") in ("imports", "imports_from")
    ]
    main_targets = {e["target"] for e in main_edges}
    assert "thirdparty_stubs_boto3_session" not in main_targets
    assert "other_project_pkg_mod" not in main_targets


def test_stdlib_name_collision_is_not_repointed_across_trees(tmp_path):
    """A package with a stdlib-looking name (e.g. libs/logging/__init__.py)
    must not hijack `import logging` from an unrelated package tree."""
    libs = tmp_path / "libs" / "logging"
    libs.mkdir(parents=True)
    (libs / "__init__.py").write_text("def info(msg): pass\n")

    src = tmp_path / "src" / "app"
    src.mkdir(parents=True)
    (src / "__init__.py").write_text("")
    (src / "main.py").write_text("import logging\n")

    paths = [
        libs / "__init__.py",
        src / "__init__.py",
        src / "main.py",
    ]
    res = extract(paths, cache_root=tmp_path / "c", root=tmp_path, parallel=False)

    main_edges = [
        e for e in res["edges"]
        if e.get("source") == "src_app_main" and e.get("relation") in ("imports", "imports_from")
    ]
    main_targets = {e["target"] for e in main_edges}
    assert "libs_logging_init" not in main_targets


def test_non_python_import_edge_is_not_repointed(tmp_path):
    """#2072 review: the alias map is Python-only, but a non-Python import edge
    whose dangling target coincides with a Python alias must NOT be repointed
    onto a Python file (that would fabricate a cross-language import)."""
    pkg = tmp_path / "src" / "pkg"
    pkg.mkdir(parents=True)
    (pkg / "__init__.py").write_text("")
    (pkg / "mod.py").write_text("def f():\n    return 1\n")
    # Simulate a non-Python (C#) import edge whose target string collides with the
    # Python alias `pkg_mod`, by hand-building the extraction the way extract emits.
    result = extract([pkg / "__init__.py", pkg / "mod.py"], cache_root=tmp_path / "c",
                     root=tmp_path, parallel=False)
    result["nodes"].append(
        {"id": "app_cs", "label": "app.cs", "file_type": "code", "source_file": "app.cs"}
    )
    result["edges"].append(
        {"source": "app_cs", "target": "pkg_mod", "relation": "imports",
         "confidence": "EXTRACTED", "source_file": "app.cs"}
    )
    # Run _repoint_python_package_imports directly on the simulated extraction
    from graphify.extract import _repoint_python_package_imports
    _repoint_python_package_imports([pkg / "__init__.py", pkg / "mod.py"], result["nodes"], result["edges"], tmp_path)
    cs_targets = [e["target"] for e in result["edges"] if e.get("source") == "app_cs"]
    assert "pkg_mod" in cs_targets
    assert "src_pkg_mod" not in cs_targets
