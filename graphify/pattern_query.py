# Lightweight Cypher-like pattern query engine for NetworkX graphs
from __future__ import annotations

import re
from typing import Any
import networkx as nx
from graphify.build import edge_data, edge_datas


class PatternQueryError(Exception):
    pass


# Backstop against pathological patterns: recursion depth equals step count,
# and an unpruned traversal's cost multiplies per hop (#p20-review findings
# 4 & 5). Kept generous enough for any realistic query.
MAX_PATTERN_STEPS = 20
MAX_LIMIT = 1000

_WHERE_COND_RE = re.compile(
    r"""^([a-zA-Z0-9_]+)\.([a-zA-Z0-9_]+)\s*(=|!=|CONTAINS|STARTS\s+WITH)\s*['"]([^'"]+)['"]$""",
    re.IGNORECASE,
)


def _parse_where_clauses(where_str: str, known_vars: set[str]) -> list[tuple[str, str, str, str]]:
    """Parse `a AND b AND ...` into (var, field, OP, value) tuples, once,
    up front -- a clause that doesn't parse, or references a variable not
    bound anywhere in the MATCH pattern, is a query error, not something to
    silently skip (a silently-ignored clause previously made the engine
    return confidently wrong results, e.g. all nodes for an unquoted-value
    typo instead of an error)."""
    if not where_str:
        return []
    parsed: list[tuple[str, str, str, str]] = []
    for clause in re.split(r"\s+AND\s+", where_str, flags=re.IGNORECASE):
        clause = clause.strip()
        m = _WHERE_COND_RE.match(clause)
        if not m:
            raise PatternQueryError(
                f"Could not parse WHERE clause: {clause!r} "
                "(expected \"var.field OP 'value'\", OP one of = != CONTAINS 'STARTS WITH')"
            )
        var_name, field, op, target_val = m.groups()
        if var_name not in known_vars:
            raise PatternQueryError(
                f"WHERE clause references {var_name!r}, which is not bound in the MATCH pattern"
            )
        parsed.append((var_name, field, re.sub(r"\s+", " ", op.upper()), target_val))
    return parsed


def _apply_where_op(op: str, val: str, target_val: str) -> bool:
    val, target_val = val.lower(), target_val.lower()
    if op == "=":
        return val == target_val
    if op == "!=":
        return val != target_val
    if op == "CONTAINS":
        return target_val in val
    if op == "STARTS WITH":
        return val.startswith(target_val)
    raise PatternQueryError(f"Unsupported WHERE operator: {op!r}")


def parse_and_execute_pattern(
    G: nx.Graph, query: str, *, as_dict: bool = False
) -> list[dict[str, Any]] | str:
    """Execute a Cypher-like pattern query against G.

    Examples:
        MATCH (a:function)-[:calls]->(b) WHERE a.label CONTAINS 'main' RETURN a.label, b.label LIMIT 10
        MATCH (u)-[:handles]->(v) RETURN u.label, v.label
        MATCH (x)-[:imports]->(y:class) WHERE y.source_file CONTAINS 'auth' RETURN x.label, y.label
    """
    query = query.strip()
    match_part = re.search(r"MATCH\s+(.+?)(?=\s+WHERE|\s+RETURN|\s+LIMIT|$)", query, re.IGNORECASE)
    if not match_part:
        raise PatternQueryError("Query must start with 'MATCH <pattern>'")

    match_str = match_part.group(1).strip()
    where_part = re.search(r"WHERE\s+(.+?)(?=\s+RETURN|\s+LIMIT|$)", query, re.IGNORECASE)
    where_str = where_part.group(1).strip() if where_part else ""

    return_part = re.search(r"RETURN\s+(.+?)(?=\s+LIMIT|$)", query, re.IGNORECASE)
    return_str = return_part.group(1).strip() if return_part else ""

    limit_part = re.search(r"LIMIT\s+(\d+)", query, re.IGNORECASE)
    limit = min(int(limit_part.group(1)), MAX_LIMIT) if limit_part else 100

    # Parse node and edge sequence: (a:type)-[:rel]->(b:type)
    # Tokenize pattern:
    step_pattern = re.compile(
        r"""\((?P<nvar>[a-zA-Z0-9_]+)?(?::(?P<ntype>[a-zA-Z0-9_]+))?\)(?:\s*(?P<arrow_left><)?-(?:\[:(?P<rel>[a-zA-Z0-9_]+)\])?-(?P<arrow_right>>)?\s*)?"""
    )

    steps: list[dict[str, Any]] = []
    pos = 0
    while pos < len(match_str):
        m = step_pattern.match(match_str, pos)
        if not m or m.end() == pos:
            break
        nvar = m.group("nvar") or f"_n{len(steps)}"
        ntype = (m.group("ntype") or "").lower()
        arrow_left = bool(m.group("arrow_left"))
        arrow_right = bool(m.group("arrow_right"))
        rel = (m.group("rel") or "").lower()

        steps.append({
            "var": nvar,
            "type": ntype,
            "arrow_left": arrow_left,
            "arrow_right": arrow_right,
            "rel": rel,
        })
        pos = m.end()

    if not steps:
        raise PatternQueryError(f"Could not parse MATCH pattern: {match_str}")
    if pos < len(match_str.rstrip()):
        raise PatternQueryError(
            f"Could not parse MATCH pattern starting at {match_str[pos:]!r} "
            f"(in: {match_str!r})"
        )
    if len(steps) > MAX_PATTERN_STEPS:
        raise PatternQueryError(
            f"MATCH pattern has {len(steps)} steps, exceeding the limit of {MAX_PATTERN_STEPS}"
        )

    where_clauses = _parse_where_clauses(where_str, known_vars={s["var"] for s in steps})

    # Helper to check node type -- file_type only, exact match. Substring
    # matching against label (or against file_type) let a type filter like
    # (a:route) match any node whose *name* happens to contain "route"
    # (e.g. reroute()), which is a type filter matching on the wrong field.
    def _node_type_matches(nid: str, req_type: str) -> bool:
        if not req_type:
            return True
        return str(G.nodes[nid].get("file_type", "")).lower() == req_type

    def _eval_where(env: dict[str, str]) -> bool:
        """Only checks clauses whose variable is already bound in `env` --
        clauses on a not-yet-bound variable are deferred (not skipped: this
        is called again as later steps bind more variables, and always once
        more with the complete env at the leaf, when every clause becomes
        checkable). This lets a failing WHERE prune the search as soon as its
        variable is bound, instead of only after a full path is assembled."""
        for var_name, field, op, target_val in where_clauses:
            nid = env.get(var_name)
            if nid is None:
                continue
            if nid not in G.nodes:
                return False
            d = G.nodes[nid]
            val = str(d.get(field, nid if field in ("id", "name") else ""))
            if not _apply_where_op(op, val, target_val):
                return False
        return True

    # Backtracking search over the path pattern
    results: list[dict[str, str]] = []

    def _search(step_idx: int, current_env: dict[str, str]):
        if len(results) >= limit:
            return
        if step_idx == len(steps):
            if _eval_where(current_env):
                results.append(dict(current_env))
            return

        step = steps[step_idx]
        var = step["var"]
        req_type = step["type"]
        bound_nodes = set(current_env.values())

        def _bind_and_recurse(candidate: str) -> None:
            # Different pattern variables must bind to different nodes within
            # one match (standard Cypher MATCH semantics) -- also the cycle
            # guard: without it, a path could revisit a node it already
            # bound to an earlier variable and recurse without ever
            # terminating up to MAX_PATTERN_STEPS deep for every revisit.
            if candidate in bound_nodes or not _node_type_matches(candidate, req_type):
                return
            current_env[var] = candidate
            if _eval_where(current_env):
                _search(step_idx + 1, current_env)
            current_env.pop(var, None)

        if step_idx == 0:
            for nid in G.nodes():
                _bind_and_recurse(nid)
                if len(results) >= limit:
                    return
        else:
            prev_step = steps[step_idx - 1]
            prev_nid = current_env[prev_step["var"]]
            rel = prev_step["rel"]
            arrow_left = prev_step["arrow_left"]
            arrow_right = prev_step["arrow_right"]

            # Outgoing or incoming neighbors
            candidates: set[str] = set()
            if arrow_right or (not arrow_left and not arrow_right):
                for succ in G.successors(prev_nid) if G.is_directed() else G.neighbors(prev_nid):
                    datas = edge_datas(G, prev_nid, succ) if G.is_multigraph() else [edge_data(G, prev_nid, succ)]
                    for d in datas:
                        erel = str(d.get("relation", "")).lower()
                        if not rel or rel in erel:
                            candidates.add(succ)
            if arrow_left or (not arrow_left and not arrow_right):
                for pred in G.predecessors(prev_nid) if G.is_directed() else G.neighbors(prev_nid):
                    datas = edge_datas(G, pred, prev_nid) if G.is_multigraph() else [edge_data(G, pred, prev_nid)]
                    for d in datas:
                        erel = str(d.get("relation", "")).lower()
                        if not rel or rel in erel:
                            candidates.add(pred)

            for cand in candidates:
                _bind_and_recurse(cand)
                if len(results) >= limit:
                    return

    try:
        _search(0, {})
    except RecursionError as exc:
        raise PatternQueryError(
            "Pattern query recursed too deeply -- reduce the number of MATCH steps"
        ) from exc

    # Project return fields
    return_fields: list[tuple[str, str]] = []
    if return_str:
        for item in return_str.split(","):
            item = item.strip()
            if "." in item:
                v, f = item.split(".", 1)
                return_fields.append((v.strip(), f.strip()))
            else:
                return_fields.append((item, "label"))
    else:
        for s in steps:
            return_fields.append((s["var"], "label"))

    rows: list[dict[str, Any]] = []
    for r in results:
        row: dict[str, Any] = {}
        for var, field in return_fields:
            nid = r.get(var)
            if nid and nid in G.nodes:
                d = G.nodes[nid]
                val = d.get(field, nid if field in ("id", "name") else "")
                col_name = f"{var}.{field}" if field != "label" else var
                row[col_name] = val
        rows.append(row)

    if as_dict:
        return rows

    if not rows:
        return "No matching patterns found in graph."

    # Format tabular text
    headers = list(rows[0].keys())
    lines = [" | ".join(headers), "-" * (len(" | ".join(headers)) + 5)]
    for row in rows:
        lines.append(" | ".join(str(row.get(h, "")) for h in headers))
    lines.append(f"\n({len(rows)} result(s) returned, limit={limit})")
    return "\n".join(lines)
