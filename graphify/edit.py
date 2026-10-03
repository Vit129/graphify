"""Graph-guided symbol edits: replace a body, insert after a symbol, rename, safe delete.

The graph already knows each symbol's file and exact line range (``source_location`` +
``end_line``) and every place that references it, so these operations are line-exact instead
of text-guessing. They are deliberately conservative:

* dry run unless ``apply=True`` (the result carries a unified diff either way);
* the node's start line must still contain its name - otherwise the graph is stale and the edit
  is refused (``graphify update .``);
* an ambiguous label, a node without a line range, or a file outside the project root is refused;
* a Python file that parsed before must still parse afterwards, or nothing is written;
* ``rename`` edits only the definition and the lines the graph confirms as references and
  REPORTS every other occurrence of the name instead of guessing (``all_occurrences=True`` opts in).

ponytail: no per-language syntax check beyond Python, and rename is only as complete as the graph's
reference edges - the ``unverified`` list is the honesty mechanism, not a guarantee.
"""
from __future__ import annotations

import ast
import difflib
import os
import re
import tempfile
from pathlib import Path
from typing import Any

import networkx as nx

from graphify.affected import DEFAULT_AFFECTED_RELATIONS
from graphify.textsearch import _graph_files, _rel, _start_line


class EditError(Exception):
    """Raised when an edit is unsafe or impossible; nothing has been written."""


# ---- node resolution / location ---------------------------------------------------------
def _name_of(label: str) -> str:
    return str(label).strip().removesuffix("()").lstrip(".")


def _resolve_node(G: nx.Graph, label: str) -> str:
    if label in G.nodes:
        return label
    from graphify.query import _find_node_tied_group
    from graphify.serve import _find_node

    matches = _find_node(G, label)
    if not matches:
        raise EditError(f"no node matching {label!r}")
    tied = _find_node_tied_group(G, label)
    if len(tied) >= 2:
        raise EditError(
            f"ambiguous label {label!r} matches {len(tied)} nodes ({', '.join(tied[:5])}); pass the exact node id"
        )
    return matches[0]


def _inside_root(source_file: str, root: Path) -> Path:
    root = root.resolve()
    p = Path(source_file)
    p = p if p.is_absolute() else root / p
    try:
        p = p.resolve()
        p.relative_to(root)
    except (OSError, ValueError):
        raise EditError(f"{source_file!r} is outside the project root; refusing to touch it") from None
    if not p.is_file():
        raise EditError(f"{source_file!r} does not exist on disk")
    return p


def _eol(text: str) -> str:
    return "\r\n" if "\r\n" in text else "\n"


def _read_lines(path: Path) -> list[str]:
    return path.read_bytes().decode("utf-8").splitlines(keepends=True)


def _locate(G: nx.Graph, nid: str, root: Path) -> tuple[Path, list[str], int, int]:
    d = G.nodes[nid]
    start, end = _start_line(d), d.get("end_line")
    if not d.get("source_file") or start is None or not isinstance(end, int) or end < start:
        raise EditError(f"{d.get('label', nid)!r} has no line range (only AST code nodes can be edited)")
    path = _inside_root(str(d["source_file"]), root)
    lines = _read_lines(path)
    if end > len(lines) or _name_of(d.get("label", nid)) not in lines[start - 1]:
        raise EditError(
            f"graph is stale for {_rel(str(d['source_file']))} (line {start} no longer holds "
            f"{_name_of(d.get('label', nid))!r}); run `graphify update .` first"
        )
    return path, lines, start, end


def _normalize(text: str, eol: str) -> list[str]:
    parts = text.splitlines()
    return [p + eol for p in parts]


# ---- validation / writing ----------------------------------------------------------------
def _parses(src: str) -> bool:
    try:
        ast.parse(src)
        return True
    except SyntaxError:
        return False


def _check_syntax(path: Path, old: list[str], new: list[str]) -> None:
    if path.suffix == ".py" and _parses("".join(old)) and not _parses("".join(new)):
        raise EditError(f"edit would leave {path.name} with a syntax error; nothing written")


def _write(path: Path, lines: list[str]) -> None:
    mode = path.stat().st_mode
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".graphify-edit-")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write("".join(lines).encode("utf-8"))
        os.chmod(tmp, mode)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def _diff(rel: str, old: list[str], new: list[str]) -> str:
    return "".join(difflib.unified_diff(old, new, fromfile=f"a/{rel}", tofile=f"b/{rel}"))


def _finish(op: str, label: str, root: Path, changes: dict[Path, tuple[list[str], list[str]]], apply: bool,
            unverified: list[dict] | None = None) -> dict[str, Any]:
    diff_parts = []
    for path, (old, new) in changes.items():
        _check_syntax(path, old, new)
        diff_parts.append(_diff(str(path.resolve().relative_to(root.resolve())), old, new))
    if apply:
        for path, (_, new) in changes.items():
            _write(path, new)
    return {
        "op": op,
        "node": label,
        "applied": apply,
        "files": sorted(str(p.resolve().relative_to(root.resolve())) for p in changes),
        "diff": "".join(diff_parts),
        "unverified": unverified or [],
    }


# ---- operations ---------------------------------------------------------------------------
def replace_symbol_body(G: nx.Graph, node: str, new_source: str, root: Path | str, apply: bool = False) -> dict[str, Any]:
    root = Path(root)
    nid = _resolve_node(G, node)
    path, lines, start, end = _locate(G, nid, root)
    new = lines[: start - 1] + _normalize(new_source, _eol("".join(lines))) + lines[end:]
    return _finish("replace", G.nodes[nid].get("label", nid), root, {path: (lines, new)}, apply)


def insert_after_symbol(G: nx.Graph, node: str, text: str, root: Path | str, apply: bool = False) -> dict[str, Any]:
    root = Path(root)
    nid = _resolve_node(G, node)
    path, lines, _, end = _locate(G, nid, root)
    new = lines[:end] + _normalize(text, _eol("".join(lines))) + lines[end:]
    return _finish("insert-after", G.nodes[nid].get("label", nid), root, {path: (lines, new)}, apply)


def _reference_sites(G: nx.Graph, nid: str, root: Path) -> list[tuple[Path, int]]:
    sites: list[tuple[Path, int]] = []
    for u, _v, data in G.in_edges(nid, data=True):
        if data.get("relation") not in DEFAULT_AFFECTED_RELATIONS:
            continue
        sf = data.get("source_file") or G.nodes[u].get("source_file")
        line = _start_line({"source_location": data.get("source_location")})
        if not sf or line is None:
            continue
        try:
            sites.append((_inside_root(str(sf), root), line))
        except EditError:
            continue
    return sites


def rename_symbol(G: nx.Graph, node: str, new_name: str, root: Path | str, apply: bool = False,
                  all_occurrences: bool = False) -> dict[str, Any]:
    root = Path(root)
    if not new_name.isidentifier():
        raise EditError(f"{new_name!r} is not a valid identifier")
    nid = _resolve_node(G, node)
    d = G.nodes[nid]
    old_name = _name_of(d.get("label", nid))
    path, lines, start, _ = _locate(G, nid, root)
    for other, od in G.nodes(data=True):
        if other != nid and od.get("source_file") == d.get("source_file") and _name_of(od.get("label", "")) == new_name:
            raise EditError(f"{new_name!r} already exists in {_rel(str(d['source_file']))}")

    word = re.compile(rf"(?<![\w]){re.escape(old_name)}(?![\w])")
    originals: dict[Path, list[str]] = {path: lines}
    edited: dict[Path, list[str]] = {path: list(lines)}
    touched: set[tuple[Path, int]] = set()

    def lines_of(p: Path) -> list[str]:
        if p not in originals:
            originals[p] = _read_lines(p)
            edited[p] = list(originals[p])
        return edited[p]

    # definition line: first occurrence only (do not rename a same-named parameter)
    edited[path][start - 1] = word.sub(new_name, lines[start - 1], count=1)
    touched.add((path, start))
    # graph-confirmed reference lines
    for p, line in _reference_sites(G, nid, root):
        cur = lines_of(p)
        if 1 <= line <= len(cur) and (p, line) not in touched:
            cur[line - 1] = word.sub(new_name, cur[line - 1])
            touched.add((p, line))
    # everything else that still spells the old name
    files = _graph_files(G, root, [], [])
    unverified: list[dict] = []
    for rel, p in sorted(files.items()):
        p = p.resolve()
        cur = lines_of(p)
        for i, text in enumerate(cur, start=1):
            if (p, i) in touched or not word.search(text):
                continue
            if all_occurrences:
                cur[i - 1] = word.sub(new_name, text)
            else:
                unverified.append({"file": rel, "line": i, "text": text.rstrip("\r\n").strip()[:200]})
    changes = {p: (originals[p], edited[p]) for p in edited if edited[p] != originals[p]}
    return _finish("rename", d.get("label", nid), root, changes, apply, unverified)


def delete_symbol(G: nx.Graph, node: str, root: Path | str, apply: bool = False) -> dict[str, Any]:
    root = Path(root)
    nid = _resolve_node(G, node)
    path, lines, start, end = _locate(G, nid, root)
    d = G.nodes[nid]
    dependents = []
    for u, _v, data in G.in_edges(nid, data=True):
        if data.get("relation") not in DEFAULT_AFFECTED_RELATIONS:
            continue
        ud = G.nodes[u]
        us, ul = _start_line(ud), ud.get("end_line")
        inside = (ud.get("source_file") == d.get("source_file") and us is not None
                  and isinstance(ul, int) and start <= us and ul <= end)
        if not inside:  # a reference from the symbol's own body (recursion) does not block deletion
            dependents.append(f"{ud.get('label', u)} [{data.get('relation')}] {_rel(str(ud.get('source_file', '')))}")
    if dependents:
        shown = "; ".join(dependents[:8]) + (" ..." if len(dependents) > 8 else "")
        raise EditError(
            f"cannot delete {d.get('label', nid)!r}: it has {len(dependents)} dependent(s) - {shown}"
        )
    j = end
    while j < len(lines) and not lines[j].strip():
        j += 1  # swallow the blank lines that separated it from what follows
    new = lines[: start - 1] + lines[j:]
    while new and not new[-1].strip():
        new.pop()
    if new and not new[-1].endswith(("\n", "\r")):
        new[-1] += _eol("".join(lines))
    return _finish("delete", d.get("label", nid), root, {path: (lines, new)}, apply)


def format_edit_result(result: dict[str, Any]) -> str:
    head = (
        f"Applied {result['op']} on {result['node']}: {len(result['files'])} file(s) changed."
        if result["applied"]
        else f"Dry run - nothing written ({result['op']} on {result['node']}). Re-run with --apply to write."
    )
    out = [head, "", result["diff"].rstrip("\n") or "(no changes)"]
    if result["unverified"]:
        out += ["", f"Not renamed - {len(result['unverified'])} occurrence(s) with no graph reference "
                    "(comments, strings, dynamic use?); review them or pass --all-occurrences:"]
        out += [f"  {u['file']}:{u['line']}: {u['text']}" for u in result["unverified"][:25]]
        if len(result["unverified"]) > 25:
            out.append(f"  ... and {len(result['unverified']) - 25} more")
    return "\n".join(out)
