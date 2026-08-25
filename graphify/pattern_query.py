# Lightweight Cypher-like pattern query engine for NetworkX graphs
from __future__ import annotations

import re
from typing import Any
import networkx as nx
from graphify.build import edge_data, edge_datas


class PatternQueryError(Exception):
    pass


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
    limit = int(limit_part.group(1)) if limit_part else 100

    # Parse node and edge sequence: (a:type)-[:rel]->(b:type)
    # Tokenize pattern:
    step_pattern = re.compile(
        r"""\((?P<nvar>[a-zA-Z0-9_]+)?(?::(?P<ntype>[a-zA-Z0-9_]+))?\)(?:\s*(?P<arrow_left><)?-(?:\[:(?P<rel>[a-zA-Z0-9_]+)\])?-(?P<arrow_right>>)?\s*)?"""
    )

    steps: list[dict[str, Any]] = []
    pos = 0
    while pos < len(match_str):
        m = step_pattern.match(match_str, pos)
        if not m:
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

    # Helper to check node type
    def _node_type_matches(nid: str, req_type: str) -> bool:
        if not req_type:
            return True
        d = G.nodes[nid]
        ft = str(d.get("file_type", "")).lower()
        lbl = str(d.get("label", "")).lower()
        return req_type == ft or req_type in ft or req_type in lbl

    # Helper to check where condition
    def _eval_where(env: dict[str, str]) -> bool:
        if not where_str:
            return True
        # Simple evaluation of clauses split by AND
        clauses = re.split(r"\s+AND\s+", where_str, flags=re.IGNORECASE)
        for clause in clauses:
            clause = clause.strip()
            # var.field = 'val' or var.field CONTAINS 'val' or var.field != 'val'
            m_cond = re.match(
                r"""([a-zA-Z0-9_]+)\.([a-zA-Z0-9_]+)\s*(=|!=|CONTAINS|STARTS\s+WITH)\s*['"]([^'"]+)['"]""",
                clause,
                re.IGNORECASE,
            )
            if m_cond:
                var_name, field, op, target_val = m_cond.groups()
                nid = env.get(var_name)
                if not nid or nid not in G.nodes:
                    return False
                d = G.nodes[nid]
                val = str(d.get(field, nid if field in ("id", "name") else ""))
                op = op.upper()
                if op == "=":
                    if val.lower() != target_val.lower():
                        return False
                elif op == "!=":
                    if val.lower() == target_val.lower():
                        return False
                elif op == "CONTAINS":
                    if target_val.lower() not in val.lower():
                        return False
                elif "STARTS" in op:
                    if not val.lower().startswith(target_val.lower()):
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

        if step_idx == 0:
            for nid in G.nodes():
                if _node_type_matches(nid, req_type):
                    current_env[var] = nid
                    _search(step_idx + 1, current_env)
                    current_env.pop(var, None)
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
                if _node_type_matches(cand, req_type):
                    current_env[var] = cand
                    _search(step_idx + 1, current_env)
                    current_env.pop(var, None)
                    if len(results) >= limit:
                        return

    _search(0, {})

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
