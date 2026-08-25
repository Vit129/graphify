# Framework-aware route extraction for Python, JavaScript, and TypeScript
from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Any


def _make_route_id(path: Path, method: str, path_str: str, line: int) -> str:
    """path is the source file's own path (see _file_stem's docstring for why
    this must be the full relative path, not path.stem -- two files with the
    same filename in different directories, a routine monorepo shape (e.g.
    svcA/routes.js and svcB/routes.js), would otherwise collide into one
    route node and merge their `handles` edges (#p20-review finding 3)."""
    from graphify.extract import _make_id
    from graphify.extractors.base import _file_stem
    clean_path = path_str.strip().replace(" ", "_")
    return _make_id(_file_stem(path), "route", f"{method.upper()}_{clean_path}_{line}")


def extract_python_routes(path: Path, source_text: str, result: dict[str, Any]) -> None:
    """Extract API routes (FastAPI, Flask, Django) and link them to handler functions."""
    try:
        tree = ast.parse(source_text, filename=str(path))
    except Exception:
        return

    nodes = result.setdefault("nodes", [])
    edges = result.setdefault("edges", [])
    seen_ids = {n["id"] for n in nodes}

    # Build map of function/class name -> node id in the file. Real Python
    # nodes carry file_type "code" (no dedicated "function" file_type/kind
    # value exists in this codebase) -- filtering on that, as this used to,
    # left fn_nodes permanently empty and every Django `handles` edge failed
    # to form even for a same-file view (#p20-review finding 8, but deeper:
    # this predates the same-file/cross-file split). Match on label shape
    # instead, the same convention extract_js_routes' symbol_nodes already
    # uses, which also transparently covers class-based views (label has no
    # "()" to strip, so the bare class name is used as-is).
    fn_nodes: dict[str, str] = {}
    for n in nodes:
        label = n.get("label", "")
        bare_name = label.split("(")[0].strip()
        if bare_name:
            fn_nodes[bare_name] = n["id"]

    for item in ast.walk(tree):
        # 1. FastAPI / Flask decorator routes: @app.get('/path'), @router.post('/path'), @bp.route('/path', methods=['GET', 'POST'])
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
            fn_name = item.name
            fn_id = fn_nodes.get(fn_name)
            if not fn_id:
                # Find matching function node by line if name wasn't exact
                for n in nodes:
                    if str(n.get("source_location", "")) == f"L{item.lineno}":
                        fn_id = n["id"]
                        break

            for dec in item.decorator_list:
                call_obj = dec if isinstance(dec, ast.Call) else None
                if not call_obj or not isinstance(call_obj.func, ast.Attribute):
                    continue

                attr_name = call_obj.func.attr.lower()
                http_methods: list[str] = []
                route_path = ""

                # Extract route path from first argument if string literal
                if call_obj.args and isinstance(call_obj.args[0], ast.Constant) and isinstance(call_obj.args[0].value, str):
                    route_path = call_obj.args[0].value

                if attr_name in ("get", "post", "put", "delete", "patch", "options", "head", "api_route"):
                    http_methods = [attr_name.upper()]
                elif attr_name == "route":
                    # Check methods keyword argument: methods=['GET', 'POST']
                    methods_kw = next((kw for kw in call_obj.keywords if kw.arg == "methods"), None)
                    if methods_kw and isinstance(methods_kw.value, (ast.List, ast.Tuple, ast.Set)):
                        for elt in methods_kw.value.elts:
                            if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                                http_methods.append(elt.value.upper())
                    if not http_methods:
                        http_methods = ["GET"]

                if route_path and http_methods:
                    for method in http_methods:
                        route_label = f"{method} {route_path}"
                        rid = _make_route_id(path, method, route_path, item.lineno)
                        if rid not in seen_ids:
                            seen_ids.add(rid)
                            nodes.append({
                                "id": rid,
                                "label": route_label,
                                "file_type": "route",
                                "source_file": str(path),
                                "source_location": f"L{item.lineno}",
                            })
                        if fn_id:
                            edges.append({
                                "source": rid,
                                "target": fn_id,
                                "relation": "handles",
                                "confidence": "EXTRACTED",
                            })

        # 2. Django url patterns: path('users/', views.user_list), re_path(...)
        elif isinstance(item, ast.Call) and isinstance(item.func, ast.Name) and item.func.id in ("path", "re_path"):
            if len(item.args) >= 2 and isinstance(item.args[0], ast.Constant) and isinstance(item.args[0].value, str):
                route_path = item.args[0].value
                route_label = f"ROUTE /{route_path.lstrip('/')}"
                rid = _make_route_id(path, "ROUTE", route_path, item.lineno)
                if rid not in seen_ids:
                    seen_ids.add(rid)
                    nodes.append({
                        "id": rid,
                        "label": route_label,
                        "file_type": "route",
                        "source_file": str(path),
                        "source_location": f"L{item.lineno}",
                    })
                # Check target view handler
                target_arg = item.args[1]
                target_name = ""
                if isinstance(target_arg, ast.Name):
                    target_name = target_arg.id
                elif isinstance(target_arg, ast.Attribute):
                    target_name = target_arg.attr
                elif isinstance(target_arg, ast.Call) and isinstance(target_arg.func, ast.Attribute):
                    # e.g. MyView.as_view()
                    if isinstance(target_arg.func.value, ast.Name):
                        target_name = target_arg.func.value.id

                if target_name and target_name in fn_nodes:
                    edges.append({
                        "source": rid,
                        "target": fn_nodes[target_name],
                        "relation": "handles",
                        "confidence": "EXTRACTED",
                    })
                elif target_name:
                    # Django's own convention (from . import views; path(...,
                    # views.user_list)) puts the real view in a different file
                    # -- views.py alongside this urls.py -- so it can't be
                    # resolved from this file's own nodes alone. Stash the
                    # name for graphify.build's post-pass
                    # (resolve_django_route_handlers) to resolve once the
                    # whole graph is assembled and cross-file lookup is
                    # possible; stripped back off in that same pass so it
                    # never leaks into a persisted graph.json.
                    for n in nodes:
                        if n["id"] == rid:
                            n["_django_pending_handler"] = target_name
                            break


def extract_js_routes(path: Path, source_text: str, result: dict[str, Any]) -> None:
    """Extract API routes (Express, NestJS, Next.js App Router) from JS/TS source."""
    nodes = result.setdefault("nodes", [])
    edges = result.setdefault("edges", [])
    seen_ids = {n["id"] for n in nodes}

    # Map function/class labels to node ids
    symbol_nodes: dict[str, str] = {}
    for n in nodes:
        label = n.get("label", "")
        bare = label.split("(")[0].strip()
        if bare:
            symbol_nodes[bare] = n["id"]

    # 1. Express / Router: app.get('/path', handler), router.post('/path', ...).
    # The 3rd argument is either a named handler reference (foo, foo.bar) or
    # an inline handler -- an arrow function ((req, res) => ...) or a
    # function expression (function(req, res) {...}), the most common
    # Express idiom of all. Without the inline alternatives the whole match
    # failed and no route node was created at all, not just a missing
    # `handles` edge (#p20-review finding 7).
    express_pattern = re.compile(
        r"""(?:app|router|server)\.(get|post|put|delete|patch|options|head)\s*\(\s*['"`]([^'"`]+)['"`]\s*,\s*(?:async\s+)?([a-zA-Z0-9_$.]+|\([^)]*\)\s*=>|function\b)""",
        re.MULTILINE | re.IGNORECASE,
    )
    for match in express_pattern.finditer(source_text):
        method = match.group(1).upper()
        route_path = match.group(2)
        handler_token = match.group(3)
        is_inline_handler = handler_token.endswith("=>") or handler_token.lower() == "function"
        handler_ref = None if is_inline_handler else handler_token.split(".")[-1]
        line_num = source_text[:match.start()].count("\n") + 1
        route_label = f"{method} {route_path}"
        rid = _make_route_id(path, method, route_path, line_num)
        if rid not in seen_ids:
            seen_ids.add(rid)
            nodes.append({
                "id": rid,
                "label": route_label,
                "file_type": "route",
                "source_file": str(path),
                "source_location": f"L{line_num}",
            })
        if handler_ref and handler_ref in symbol_nodes:
            edges.append({
                "source": rid,
                "target": symbol_nodes[handler_ref],
                "relation": "handles",
                "confidence": "EXTRACTED",
            })

    # 2. NestJS Controllers: @Controller('users') + @Get(':id')
    controller_match = re.search(r"""@Controller\s*\(\s*['"`]([^'"`]*)['"`]\s*\)""", source_text)
    base_prefix = controller_match.group(1).strip("/") if controller_match else ""
    if base_prefix:
        base_prefix = f"/{base_prefix}"

    nest_method_pattern = re.compile(
        r"""@(Get|Post|Put|Delete|Patch|Options|Head)\s*\(\s*(?:['"`]([^'"`]*)['"`])?\s*\)\s*(?:async\s+)?([a-zA-Z0-9_$]+)\s*\(""",
        re.MULTILINE,
    )
    for match in nest_method_pattern.finditer(source_text):
        method = match.group(1).upper()
        sub_path = (match.group(2) or "").strip("/")
        fn_name = match.group(3)
        full_path = f"{base_prefix}/{sub_path}".rstrip("/") if sub_path else (base_prefix or "/")
        if not full_path.startswith("/"):
            full_path = f"/{full_path}"
        line_num = source_text[:match.start()].count("\n") + 1
        route_label = f"{method} {full_path}"
        rid = _make_route_id(path, method, full_path, line_num)
        if rid not in seen_ids:
            seen_ids.add(rid)
            nodes.append({
                "id": rid,
                "label": route_label,
                "file_type": "route",
                "source_file": str(path),
                "source_location": f"L{line_num}",
            })
        if fn_name in symbol_nodes:
            edges.append({
                "source": rid,
                "target": symbol_nodes[fn_name],
                "relation": "handles",
                "confidence": "EXTRACTED",
            })

    # 3. Next.js App Router: app/api/.../route.ts -> export async function GET()
    norm_path = path.as_posix()
    if "/app/" in norm_path and (norm_path.endswith("/route.ts") or norm_path.endswith("/route.js")):
        sub = norm_path.split("/app/", 1)[1]
        route_dir = str(Path(sub).parent)
        api_route_path = "/" + route_dir.replace("\\", "/") if route_dir != "." else "/"

        for method in ("GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"):
            m_pattern = re.compile(rf"""export\s+(?:async\s+)?function\s+({method})\s*\(""", re.MULTILINE)
            for m in m_pattern.finditer(source_text):
                line_num = source_text[:m.start()].count("\n") + 1
                route_label = f"{method} {api_route_path}"
                rid = _make_route_id(path, method, api_route_path, line_num)
                if rid not in seen_ids:
                    seen_ids.add(rid)
                    nodes.append({
                        "id": rid,
                        "label": route_label,
                        "file_type": "route",
                        "source_file": str(path),
                        "source_location": f"L{line_num}",
                    })
                if method in symbol_nodes:
                    edges.append({
                        "source": rid,
                        "target": symbol_nodes[method],
                        "relation": "handles",
                        "confidence": "EXTRACTED",
                    })


def resolve_django_route_handlers(G) -> int:
    """Resolve `_django_pending_handler` route nodes against the whole graph.

    Django's own convention puts urls.py and views.py in different files, so
    `path('users/', views.user_list)` cannot be resolved from urls.py's own
    extraction pass alone -- see the call site in extract_python_routes.
    Called once per build, after every file's extraction is merged into one
    graph, so cross-file lookup is finally possible.

    Ambiguity is resolved by path proximity to the referencing urls.py (the
    same tie-break symbol_resolution.py already uses for cross-file call
    resolution) -- a common view name reused by several Django apps' own
    views.py must not silently wire to the wrong app's handler. Genuinely
    unresolvable names are left without an edge rather than guessing.

    Returns the number of `handles` edges added.
    """
    from graphify.paths import _path_proximity_winner

    # bare_name -> {node_id: source_file}, over every node in the graph.
    by_name: dict[str, dict[str, str]] = {}
    pending: list[tuple[str, str, str]] = []  # (route_node_id, handler_name, route_source_file)
    for nid, d in G.nodes(data=True):
        label = str(d.get("label", ""))
        bare = label.split("(")[0].strip()
        source_file = d.get("source_file")
        if bare and source_file:
            by_name.setdefault(bare, {})[nid] = str(source_file)
        handler_name = d.get("_django_pending_handler")
        if handler_name:
            pending.append((nid, str(handler_name), str(source_file or "")))

    added_edges = 0
    for route_nid, handler_name, route_source_file in pending:
        del G.nodes[route_nid]["_django_pending_handler"]
        candidates = by_name.get(handler_name)
        if not candidates:
            continue
        if len(candidates) == 1:
            target_nid = next(iter(candidates))
        else:
            target_nid = _path_proximity_winner(route_source_file, candidates)
        if not target_nid or target_nid == route_nid or G.has_edge(route_nid, target_nid):
            continue
        G.add_edge(
            route_nid, target_nid,
            relation="handles", confidence="EXTRACTED",
            _src=route_nid, _tgt=target_nid,
        )
        added_edges += 1
    return added_edges
