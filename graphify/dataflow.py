"""Parameter flow for Python functions: where does a value that enters here end up?

``trace_flow`` takes a function node (and optionally one parameter and a sink regex), parses the
function's exact source range, propagates taint by name through the function body (assignments,
containers, f-strings, loops, ``with``, walrus, call results) and reports every call that
receives a tainted argument. Calls that resolve to another function through the graph's
``calls`` edges are followed (positional/keyword arguments are mapped to the callee's parameters,
``self`` skipped for methods) up to ``depth`` function levels, so a path such as
``handle(user_text) -> build() -> run(command) -> subprocess.run`` is shown end to end.

ponytail: this answers "can input reach this call" for review and impact work. It is name-based
and flow-insensitive inside a function (a tainted name stays tainted), Python only, and does not
model aliasing, globals, attribute state, closures, async hand-off or dynamic dispatch (unresolved
callees are reported as leaves). It is not a replacement for a real taint engine.
"""
from __future__ import annotations

import ast
import re
import textwrap
from pathlib import Path
from typing import Any

import networkx as nx

from graphify.edit import EditError, _inside_root, _name_of, _read_lines, _resolve_node
from graphify.textsearch import _rel, _start_line

DEFAULT_DEPTH = 4
MAX_STEPS = 300


class FlowError(Exception):
    """Raised when a flow cannot be traced; the message says why."""


def _names(expr: ast.AST) -> set[str]:
    return {n.id for n in ast.walk(expr) if isinstance(n, ast.Name)}


def _targets(t: ast.AST) -> set[str]:
    if isinstance(t, ast.Name):
        return {t.id}
    if isinstance(t, (ast.Tuple, ast.List)):
        return set().union(*[_targets(e) for e in t.elts]) if t.elts else set()
    if isinstance(t, ast.Starred):
        return _targets(t.value)
    if isinstance(t, (ast.Attribute, ast.Subscript)):
        return _names(t.value)  # writing into an object taints the object
    return set()


def _propagate(func: ast.AST, tainted: set[str]) -> set[str]:
    """Fixpoint, flow-insensitive taint propagation through the function body."""
    tainted = set(tainted)
    for _ in range(12):
        before = len(tainted)
        for node in ast.walk(func):
            if isinstance(node, ast.Assign) and _names(node.value) & tainted:
                for t in node.targets:
                    tainted |= _targets(t)
            elif isinstance(node, ast.AnnAssign) and node.value is not None and _names(node.value) & tainted:
                tainted |= _targets(node.target)
            elif isinstance(node, ast.AugAssign) and (_names(node.value) | _names(node.target)) & tainted:
                tainted |= _targets(node.target)
            elif isinstance(node, (ast.For, ast.AsyncFor)) and _names(node.iter) & tainted:
                tainted |= _targets(node.target)
            elif isinstance(node, (ast.With, ast.AsyncWith)):
                for item in node.items:
                    if item.optional_vars is not None and _names(item.context_expr) & tainted:
                        tainted |= _targets(item.optional_vars)
            elif isinstance(node, ast.NamedExpr) and _names(node.value) & tainted:
                tainted |= _targets(node.target)
        if len(tainted) == before:
            break
    return tainted


def _function(G: nx.Graph, nid: str, root: Path) -> tuple[ast.AST, list[str], int, str]:
    """(FunctionDef, param names, absolute first line, rel path) for a Python function node."""
    d = G.nodes[nid]
    start, end = _start_line(d), d.get("end_line")
    sf = str(d.get("source_file") or "")
    if not sf.endswith(".py"):
        raise FlowError(f"flow supports Python functions only ({sf or 'no source file'})")
    if start is None or not isinstance(end, int):
        raise FlowError(f"{d.get('label', nid)!r} has no line range")
    try:
        path = _inside_root(sf, root)
    except EditError as exc:
        raise FlowError(str(exc)) from None
    src = "".join(_read_lines(path)[start - 1:end])
    try:
        tree = ast.parse(textwrap.dedent(src))
    except SyntaxError as exc:
        raise FlowError(f"could not parse {_rel(sf)}:{start}-{end}: {exc.msg} (graph stale? run `graphify update .`)") from None
    fn = next((n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))), None)
    if fn is None:
        raise FlowError(f"{d.get('label', nid)!r} is not a function or method")
    a = fn.args
    names = [x.arg for x in a.posonlyargs + a.args + a.kwonlyargs]
    if a.vararg:
        names.append(a.vararg.arg)
    if a.kwarg:
        names.append(a.kwarg.arg)
    return fn, names, start, _rel(sf)


def _callee_index(G: nx.Graph, nid: str) -> dict[str, list[str]]:
    index: dict[str, list[str]] = {}
    for _u, v, data in G.out_edges(nid, data=True):
        if data.get("relation") in ("calls", "indirect_call"):
            index.setdefault(_name_of(G.nodes[v].get("label", v)), []).append(v)
    return index


def _walk(G: nx.Graph, nid: str, tainted_params: set[str], depth: int, root: Path,
          visited: set, budget: list[int]) -> tuple[list[dict[str, Any]], bool]:
    fn, params, first_line, rel = _function(G, nid, root)
    tainted = _propagate(fn, tainted_params & set(params))
    callees = _callee_index(G, nid)
    is_method = str(G.nodes[nid].get("label", "")).startswith(".")
    returned = any(
        isinstance(n, ast.Return) and n.value is not None and _names(n.value) & tainted
        for n in ast.walk(fn)
    )
    steps: list[dict[str, Any]] = []
    calls = sorted((n for n in ast.walk(fn) if isinstance(n, ast.Call)), key=lambda n: (n.lineno, n.col_offset))
    for call in calls:
        flowing: list[tuple[Any, set[str]]] = []
        for i, a in enumerate(call.args):
            expr = a.value if isinstance(a, ast.Starred) else a
            hit = _names(expr) & tainted
            if hit:
                flowing.append(("*" if isinstance(a, ast.Starred) else i, hit))
        for kw in call.keywords:
            hit = _names(kw.value) & tainted
            if hit:
                flowing.append(("**" if kw.arg is None else kw.arg, hit))
        if not flowing:
            continue
        if budget[0] <= 0:
            break
        budget[0] -= 1
        callee_text = ast.unparse(call.func)
        last = call.func.id if isinstance(call.func, ast.Name) else (
            call.func.attr if isinstance(call.func, ast.Attribute) else None
        )
        targets = callees.get(last, []) if last else []
        step: dict[str, Any] = {
            "call": callee_text,
            "file": rel,
            "line": first_line + call.lineno - 1,
            "args": [{"arg": a, "via": sorted(v)} for a, v in flowing],
            "resolved": None,
            "sink": False,
            "next": [],
        }
        if len(targets) == 1 and depth > 1:
            tgt = targets[0]
            try:
                _tfn, tparams, _l, _r = _function(G, tgt, root)
            except FlowError:
                tparams = []
            if tparams:
                step["resolved"] = str(G.nodes[tgt].get("label", tgt))
                shift = 1 if (str(G.nodes[tgt].get("label", "")).startswith(".")
                              and isinstance(call.func, ast.Attribute)) else 0
                positional = tparams[shift:]
                mapped: set[str] = set()
                for a, _v in flowing:
                    if isinstance(a, int) and a < len(positional):
                        mapped.add(positional[a])
                    elif isinstance(a, str) and a in tparams:
                        mapped.add(a)
                    elif a in ("*", "**"):
                        mapped.update(tparams)
                key = (tgt, frozenset(mapped))
                if mapped and key not in visited:
                    visited.add(key)
                    step["next"], _ret = _walk(G, tgt, mapped, depth - 1, root, visited, budget)
        steps.append(step)
    return steps, returned


def _prune(steps: list[dict[str, Any]], sink: re.Pattern) -> list[dict[str, Any]]:
    kept = []
    for s in steps:
        s["sink"] = bool(sink.search(s["call"]))
        s["next"] = _prune(s["next"], sink)
        if s["sink"] or s["next"]:
            kept.append(s)
    return kept


def trace_flow(G: nx.Graph, node: str, root: Path | str, param: str | None = None, to: str | None = None,
               depth: int = DEFAULT_DEPTH) -> dict[str, Any]:
    root = Path(root)
    try:
        nid = _resolve_node(G, node)
    except EditError as exc:
        raise FlowError(str(exc)) from None
    sink = None
    if to:
        try:
            sink = re.compile(to)
        except re.error as exc:
            raise FlowError(f"invalid --to regex: {exc}") from None
    fn, params, line, rel = _function(G, nid, root)
    usable = [p for p in params if not (p in ("self", "cls") and params and p == params[0])]
    if param is not None and param not in params:
        raise FlowError(f"{param!r} is not a parameter of {G.nodes[nid].get('label', nid)}; parameters: {', '.join(usable)}")
    roots = {param} if param else set(usable)
    budget = [MAX_STEPS]
    steps, returned = _walk(G, nid, roots, max(1, int(depth)), root, {(nid, frozenset(roots))}, budget)
    if sink is not None:
        steps = _prune(steps, sink)
    else:
        def mark(ss):
            for s in ss:
                mark(s["next"])
        mark(steps)
    return {
        "entry": str(G.nodes[nid].get("label", nid)),
        "file": rel,
        "line": line,
        "param": param,
        "params": usable,
        "steps": steps,
        "returned": returned,
        "sink_regex": to,
        "reaches_sink": (bool(steps) if sink is not None else None),
        "truncated": budget[0] <= 0,
    }


def format_flow(res: dict[str, Any]) -> str:
    who = f"`{res['param']}`" if res["param"] else "parameters " + ", ".join(res["params"])
    out = [f"Flow of {who} in {res['entry']} [{res['file']}:{res['line']}]"]

    def render(steps: list[dict[str, Any]], indent: int) -> None:
        for s in steps:
            args = ", ".join(
                f"arg {a['arg']} <- {'/'.join(a['via'])}" for a in s["args"]
            )
            resolved = f"  -> {s['resolved']}" if s["resolved"] else ""
            mark = "   <== SINK" if s["sink"] else ""
            out.append(f"{'  ' * indent}{s['file']}:{s['line']}  {s['call']}(...)  [{args}]{resolved}{mark}")
            render(s["next"], indent + 1)

    render(res["steps"], 1)
    if not res["steps"]:
        out.append("  (no call receives a value derived from it)")
    if res["returned"]:
        out.append("  returned: a value derived from it is returned to the caller")
    if res["sink_regex"]:
        out.append(
            f"\nREACHES SINK /{res['sink_regex']}/" if res["reaches_sink"]
            else f"\nDoes not reach a call matching /{res['sink_regex']}/ within the traced depth."
        )
    if res["truncated"]:
        out.append("Output capped; narrow with --param / --to or lower --depth.")
    out.append(
        "\nNote: name-based, flow-insensitive, Python only; unresolved callees are leaves "
        "(aliasing, globals and dynamic dispatch are not modelled)."
    )
    return "\n".join(out)
