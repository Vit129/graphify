# read-only Cypher SUBSET over graph.json: hand-written tokenizer + recursive-descent parser + bounded executor
#
# This is NOT full Cypher. Supported: one MATCH chain, WHERE, RETURN [DISTINCT]
# (property access, AS, count()), ORDER BY, SKIP, LIMIT. Everything else
# (CREATE/MERGE/DELETE/SET/REMOVE/CALL/WITH/UNION/OPTIONAL MATCH/...) is rejected
# with a CypherError naming the construct. Nothing is ever eval()'d or exec()'d,
# and the graph is never mutated.
#
# Safety rails (a bad query must not hang an MCP server):
#   - rows: default LIMIT 100, hard cap MAX_ROWS
#   - hops: variable-length `*a..b` is capped at MAX_HOPS
#   - work: every candidate node/edge/WHERE evaluation costs one step; exceeding
#     MAX_STEPS (or MAX_SECONDS of wall clock, checked between steps) raises
#   - regex (`=~`): pattern length cap, nested/excess repeats and backreferences
#     rejected before compiling, subject length cap. Python's `re` cannot be
#     interrupted mid-match, so these static limits (not a timeout) are the guard.
from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator, NamedTuple

import networkx as nx

from graphify.layers import layer_of_path

MAX_ROWS = 1000
DEFAULT_LIMIT = 100
MAX_HOPS = 5
MAX_STEPS = 1_000_000
MAX_SECONDS = 15.0
MAX_QUERY_CHARS = 4000
MAX_REGEX_CHARS = 200
MAX_REGEX_SUBJECT = 300

NODE_PROPS = (
    "id", "label", "source_file", "source_location", "community",
    "community_name", "file_type", "layer", "degree",
)
REL_PROPS = ("relation", "confidence", "context")

_UNSUPPORTED = {
    "CREATE", "MERGE", "DELETE", "DETACH", "SET", "REMOVE", "CALL", "WITH", "UNION",
    "OPTIONAL", "UNWIND", "FOREACH", "LOAD", "DROP", "USING", "EXPLAIN", "PROFILE",
}
_AGGREGATES = {"sum", "avg", "min", "max", "collect", "stdev", "stdevp", "percentilecont", "percentiledisc"}


class CypherError(ValueError):
    """Raised for syntax errors, unsupported constructs and exceeded safety limits."""


# --------------------------------------------------------------------------- tokenizer

@dataclass(frozen=True)
class _Tok:
    kind: str  # ident | num | str | op | eof
    value: Any
    start: int
    end: int
    quoted: bool = False

    @property
    def kw(self) -> str:
        return self.value.upper() if self.kind == "ident" and not self.quoted else ""


_TWO_CHAR_OPS = ("=~", "<>", "<=", ">=", "..")
_ONE_CHAR_OPS = "()[]{},:.|*-<>=;"
_NUM_RE = re.compile(r"\d+(?:\.\d+)?")
_IDENT_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
_ESCAPES = {"n": "\n", "t": "\t", "r": "\r"}


def _tokenize(src: str) -> list[_Tok]:
    if len(src) > MAX_QUERY_CHARS:
        raise CypherError(f"query too long ({len(src)} chars, max {MAX_QUERY_CHARS})")
    toks: list[_Tok] = []
    i, n = 0, len(src)
    while i < n:
        c = src[i]
        if c.isspace():
            i += 1
        elif c in "'\"":
            j, buf = i + 1, []
            while True:
                if j >= n:
                    raise CypherError(f"unterminated string literal starting at position {i}")
                if src[j] == "\\" and j + 1 < n:
                    buf.append(_ESCAPES.get(src[j + 1], src[j + 1]))
                    j += 2
                elif src[j] == c:
                    break
                else:
                    buf.append(src[j])
                    j += 1
            toks.append(_Tok("str", "".join(buf), i, j + 1))
            i = j + 1
        elif c == "`":
            j = src.find("`", i + 1)
            if j < 0:
                raise CypherError(f"unterminated backtick identifier at position {i}")
            toks.append(_Tok("ident", src[i + 1:j], i, j + 1, quoted=True))
            i = j + 1
        elif c.isdigit():
            m = _NUM_RE.match(src, i)
            text = m.group(0)
            toks.append(_Tok("num", float(text) if "." in text else int(text), i, m.end()))
            i = m.end()
        elif c.isalpha() or c == "_":
            m = _IDENT_RE.match(src, i)
            if not m:
                raise CypherError(f"unexpected character {c!r} at position {i}")
            toks.append(_Tok("ident", m.group(0), i, m.end()))
            i = m.end()
        elif src[i:i + 2] in _TWO_CHAR_OPS:
            toks.append(_Tok("op", src[i:i + 2], i, i + 2))
            i += 2
        elif c in _ONE_CHAR_OPS:
            toks.append(_Tok("op", c, i, i + 1))
            i += 1
        elif c == "$":
            raise CypherError("query parameters ($name) are not supported; inline the value")
        elif c == "!":
            raise CypherError("'!=' is not Cypher; use <>")
        elif c in "+/%^":
            raise CypherError(f"arithmetic operator {c!r} is not supported")
        else:
            raise CypherError(f"unexpected character {c!r} at position {i}")
    toks.append(_Tok("eof", None, n, n))
    return toks


# --------------------------------------------------------------------------- AST

@dataclass(frozen=True)
class NodePat:
    var: str | None
    labels: tuple[str, ...]
    props: tuple[tuple[str, Any], ...]


@dataclass(frozen=True)
class RelPat:
    var: str | None
    types: tuple[str, ...]
    direction: str  # out | in | any
    lo: int
    hi: int
    varlen: bool
    props: tuple[tuple[str, Any], ...]


@dataclass(frozen=True)
class ReturnItem:
    expr: tuple
    alias: str
    text: str


@dataclass
class Query:
    nodes: list[NodePat]
    rels: list[RelPat]
    where: tuple | None
    items: list[ReturnItem]
    distinct: bool
    order: list[tuple[tuple, bool]]  # (expr | ("col", idx), descending)
    skip: int
    limit: int | None
    aggregated: bool = False


# --------------------------------------------------------------------------- regex guard

try:  # Python 3.11+ moved the sre internals under re
    from re import _constants as _sc
    from re import _parser as _sp
except ImportError:  # pragma: no cover - Python 3.10
    import sre_constants as _sc  # type: ignore[no-redef]
    import sre_parse as _sp  # type: ignore[no-redef]

_REPEAT_OPS = tuple(
    getattr(_sc, name) for name in ("MAX_REPEAT", "MIN_REPEAT", "POSSESSIVE_REPEAT") if hasattr(_sc, name)
)
_regex_cache: dict[str, re.Pattern] = {}


def _regex_children(op, av) -> list:
    if op in _REPEAT_OPS:
        return [av[2]]
    if op == _sc.SUBPATTERN:
        return [av[3]]
    if op == _sc.BRANCH:
        return list(av[1])
    if op in (_sc.ASSERT, _sc.ASSERT_NOT):
        return [av[1]]
    if hasattr(_sc, "ATOMIC_GROUP") and op == _sc.ATOMIC_GROUP:
        return [av]
    return []


def _check_regex_shape(parsed, in_repeat: bool, heavy: list[int]) -> None:
    for op, av in parsed:
        if op == _sc.GROUPREF or op == getattr(_sc, "GROUPREF_EXISTS", None):
            raise CypherError("regex backreferences/conditionals are not allowed")
        is_repeat = op in _REPEAT_OPS
        if is_repeat:
            lo, hi = av[0], av[1]
            repeats = hi > 1
            if repeats and in_repeat:
                raise CypherError("regex with nested repetition (e.g. '(a+)+') is not allowed")
            if hi == _sc.MAXREPEAT or hi > 20:
                heavy[0] += 1
                if heavy[0] > 3:
                    raise CypherError("regex has too many unbounded/large repetitions (max 3)")
            if hi != _sc.MAXREPEAT and hi > 500:
                raise CypherError("regex repetition bound too large (max 500)")
        for child in _regex_children(op, av):
            _check_regex_shape(child, in_repeat or (is_repeat and av[1] > 1), heavy)


def _compile_regex(pattern: str) -> re.Pattern:
    cached = _regex_cache.get(pattern)
    if cached is not None:
        return cached
    if len(pattern) > MAX_REGEX_CHARS:
        raise CypherError(f"regex too long ({len(pattern)} chars, max {MAX_REGEX_CHARS})")
    try:
        parsed = _sp.parse(pattern)
        compiled = re.compile(pattern)
    except (re.error, RecursionError, OverflowError) as exc:
        raise CypherError(f"invalid regex {pattern!r}: {exc}") from None
    _check_regex_shape(parsed, False, [0])
    if len(_regex_cache) > 256:
        _regex_cache.clear()
    _regex_cache[pattern] = compiled
    return compiled


# --------------------------------------------------------------------------- parser

class _Parser:
    def __init__(self, src: str):
        self.src = src
        self.toks = _tokenize(src)
        self.pos = 0

    # -- token helpers
    @property
    def tok(self) -> _Tok:
        return self.toks[self.pos]

    def _peek(self, k: int = 1) -> _Tok:
        return self.toks[min(self.pos + k, len(self.toks) - 1)]

    def _next(self) -> _Tok:
        t = self.toks[self.pos]
        if t.kind != "eof":
            self.pos += 1
        return t

    def _is_op(self, v: str) -> bool:
        return self.tok.kind == "op" and self.tok.value == v

    def _eat_op(self, v: str) -> bool:
        if self._is_op(v):
            self.pos += 1
            return True
        return False

    def _expect_op(self, v: str, ctx: str = "") -> None:
        if not self._eat_op(v):
            raise self._unexpected(f"expected {v!r}{ctx}")

    def _eat_kw(self, *names: str) -> bool:
        if self.tok.kw in names:
            self.pos += 1
            return True
        return False

    def _expect_kw(self, name: str) -> None:
        if not self._eat_kw(name):
            raise self._unexpected(f"expected {name}")

    def _describe(self, t: _Tok) -> str:
        return "end of query" if t.kind == "eof" else repr(self.src[t.start:t.end])

    def _unexpected(self, msg: str) -> CypherError:
        return CypherError(f"{msg}, found {self._describe(self.tok)} at position {self.tok.start}")

    def _check_unsupported(self) -> None:
        kw = self.tok.kw
        if kw in _UNSUPPORTED:
            if kw == "OPTIONAL" and self._peek().kw == "MATCH":
                kw = "OPTIONAL MATCH"
            raise CypherError(
                f"unsupported Cypher construct: {kw} (graphify's Cypher subset is read-only: "
                "MATCH ... [WHERE ...] RETURN ... [ORDER BY ...] [SKIP n] [LIMIT n])"
            )

    def _ident(self, what: str) -> str:
        if self.tok.kind != "ident":
            raise self._unexpected(f"expected {what}")
        return self._next().value

    # -- query
    def parse(self) -> Query:
        self._check_unsupported()
        if self.tok.kw != "MATCH":
            raise self._unexpected("query must start with MATCH")
        self._next()
        nodes, rels = self._pattern()
        if self._is_op(","):
            raise CypherError(
                "comma-separated patterns are not supported; chain one path, e.g. (a)-[]->(b)-[]->(c)"
            )
        if self.tok.kw == "MATCH":
            raise CypherError("multiple MATCH clauses are not supported; use one MATCH chain")
        self._check_unsupported()
        where = self._expr() if self._eat_kw("WHERE") else None
        self._check_unsupported()
        if self.tok.kw != "RETURN":
            raise self._unexpected("expected RETURN (queries must end with RETURN)")
        self._next()
        distinct = self._eat_kw("DISTINCT")
        items = self._return_items()
        order: list[tuple[tuple, bool]] = []
        skip, limit = 0, None
        self._check_unsupported()
        if self._eat_kw("ORDER"):
            self._expect_kw("BY")
            while True:
                e = self._expr()
                desc = False
                if self._eat_kw("DESC", "DESCENDING"):
                    desc = True
                else:
                    self._eat_kw("ASC", "ASCENDING")
                order.append((e, desc))
                if not self._eat_op(","):
                    break
        if self._eat_kw("SKIP"):
            skip = self._int_literal("SKIP")
        if self._eat_kw("LIMIT"):
            limit = self._int_literal("LIMIT")
        self._eat_op(";")
        self._check_unsupported()
        if self.tok.kind != "eof":
            raise self._unexpected("unexpected input after query")
        q = Query(nodes, rels, where, items, distinct, order, skip, limit)
        _validate(q)
        return q

    def _int_literal(self, clause: str) -> int:
        if self.tok.kind != "num" or not isinstance(self.tok.value, int):
            raise self._unexpected(f"{clause} requires a non-negative integer literal")
        return self._next().value

    def _return_items(self) -> list[ReturnItem]:
        if self._is_op("*"):
            raise CypherError("RETURN * is not supported; list the columns explicitly")
        items: list[ReturnItem] = []
        while True:
            start = self.tok.start
            e = self._expr()
            text = " ".join(self.src[start:self.toks[self.pos - 1].end].split())
            alias = text
            if self._eat_kw("AS"):
                alias = self._ident("alias after AS")
            items.append(ReturnItem(e, alias, text))
            if not self._eat_op(","):
                break
        names = [i.alias for i in items]
        if len(set(names)) != len(names):
            raise CypherError("duplicate column names in RETURN; disambiguate with AS")
        return items

    # -- pattern
    def _pattern(self) -> tuple[list[NodePat], list[RelPat]]:
        if self.tok.kind == "ident" and self._peek().kind == "op" and self._peek().value == "=":
            raise CypherError("path variables (p = (a)-->(b)) are not supported")
        nodes = [self._node()]
        rels: list[RelPat] = []
        while self._is_op("<") or self._is_op("-"):
            rels.append(self._rel())
            nodes.append(self._node())
        return nodes, rels

    def _node(self) -> NodePat:
        if self.tok.kind == "ident" and self._peek().kind == "op" and self._peek().value == "(":
            raise CypherError(f"function {self.tok.value}() is not supported in MATCH")
        self._expect_op("(", " to start a node pattern")
        var = None
        if self.tok.kind == "ident":
            var = self._next().value
        labels = []
        while self._eat_op(":"):
            labels.append(self._ident("label"))
        props = self._prop_map() if self._is_op("{") else ()
        self._expect_op(")", " to close the node pattern")
        return NodePat(var, tuple(labels), props)

    def _prop_map(self) -> tuple[tuple[str, Any], ...]:
        self._expect_op("{")
        pairs = []
        while not self._is_op("}"):
            key = self._ident("property name")
            self._expect_op(":", " after property name")
            pairs.append((key, self._literal("property map values must be literals")))
            if not self._eat_op(","):
                break
        self._expect_op("}", " to close the property map")
        return tuple(pairs)

    def _literal(self, err: str) -> Any:
        t = self.tok
        neg = False
        if self._is_op("-") and self._peek().kind == "num":
            neg = True
            self._next()
            t = self.tok
        if t.kind in ("num", "str"):
            self._next()
            return -t.value if neg else t.value
        if t.kw in ("TRUE", "FALSE", "NULL"):
            self._next()
            return {"TRUE": True, "FALSE": False, "NULL": None}[t.kw]
        raise self._unexpected(err)

    def _rel(self) -> RelPat:
        left = self._eat_op("<")
        self._expect_op("-", " in relationship pattern")
        var, types, lo, hi, varlen, props = None, [], 1, 1, False, ()
        if self._eat_op("["):
            if self.tok.kind == "ident":
                var = self._next().value
            if self._eat_op(":"):
                types.append(self._ident("relationship type"))
                while self._eat_op("|"):
                    self._eat_op(":")
                    types.append(self._ident("relationship type"))
            if self._eat_op("*"):
                varlen = True
                lo, hi = self._hops()
            if self._is_op("{"):
                props = self._prop_map()
            self._expect_op("]", " to close the relationship pattern")
        self._expect_op("-", " in relationship pattern")
        right = self._eat_op(">")
        if left and right:
            raise CypherError("a relationship cannot point both ways (<-->)")
        direction = "in" if left else "out" if right else "any"
        return RelPat(var, tuple(types), direction, lo, hi, varlen, props)

    def _hops(self) -> tuple[int, int]:
        lo, hi = 1, MAX_HOPS
        if self.tok.kind == "num" and isinstance(self.tok.value, int):
            lo = self._next().value
            if self._eat_op(".."):
                if self.tok.kind == "num" and isinstance(self.tok.value, int):
                    hi = self._next().value
            else:
                hi = lo
        elif self._eat_op(".."):
            if self.tok.kind == "num" and isinstance(self.tok.value, int):
                hi = self._next().value
        if lo < 1:
            raise CypherError("zero-length variable paths (*0..) are not supported; minimum is 1 hop")
        if hi > MAX_HOPS:
            raise CypherError(f"variable-length hops are capped at {MAX_HOPS} (requested {hi})")
        if lo > hi:
            raise CypherError(f"invalid hop range *{lo}..{hi}")
        return lo, hi

    # -- expressions (precedence: OR < AND < NOT < comparison < primary)
    def _expr(self) -> tuple:
        left = self._and()
        while self._eat_kw("OR"):
            left = ("or", left, self._and())
        return left

    def _and(self) -> tuple:
        left = self._not()
        while self._eat_kw("AND"):
            left = ("and", left, self._not())
        return left

    def _not(self) -> tuple:
        if self._eat_kw("NOT"):
            return ("not", self._not())
        return self._cmp()

    def _cmp(self) -> tuple:
        left = self._primary()
        t = self.tok
        if t.kind == "op" and t.value in ("=", "<>", "<", "<=", ">", ">="):
            self._next()
            return ("cmp", t.value, left, self._primary())
        if t.kind == "op" and t.value == "=~":
            self._next()
            return ("cmp", "REGEX", left, self._primary())
        if t.kw == "IN":
            self._next()
            return ("cmp", "IN", left, self._primary())
        if t.kw == "CONTAINS":
            self._next()
            return ("cmp", "CONTAINS", left, self._primary())
        if t.kw in ("STARTS", "ENDS"):
            self._next()
            self._expect_kw("WITH")
            return ("cmp", t.kw, left, self._primary())
        if t.kw == "IS":
            self._next()
            neg = self._eat_kw("NOT")
            self._expect_kw("NULL")
            return ("isnull", left, neg)
        return left

    def _primary(self) -> tuple:
        t = self.tok
        if t.kind in ("num", "str"):
            self._next()
            return ("lit", t.value)
        if t.kind == "op":
            if t.value == "(":
                self._next()
                e = self._expr()
                self._expect_op(")", " to close the parenthesised expression")
                return e
            if t.value == "[":
                self._next()
                items = []
                while not self._is_op("]"):
                    items.append(self._literal("list elements must be literals"))
                    if not self._eat_op(","):
                        break
                self._expect_op("]", " to close the list")
                return ("lit", tuple(items))
            if t.value == "-" and self._peek().kind == "num":
                self._next()
                return ("lit", -self._next().value)
            raise self._unexpected("expected an expression")
        if t.kind == "ident":
            if t.kw in ("TRUE", "FALSE", "NULL"):
                self._next()
                return ("lit", {"TRUE": True, "FALSE": False, "NULL": None}[t.kw])
            if self._peek().kind == "op" and self._peek().value == "(":
                return self._call()
            self._next()
            if self._eat_op("."):
                return ("prop", t.value, self._ident("property name"))
            return ("var", t.value)
        raise self._unexpected("expected an expression")

    def _call(self) -> tuple:
        name = self._next().value
        low = name.lower()
        self._expect_op("(")
        if low == "count":
            distinct = self._eat_kw("DISTINCT")
            if self._eat_op("*"):
                arg = None
                if distinct:
                    raise CypherError("count(DISTINCT *) is not valid")
            else:
                arg = self._expr()
            self._expect_op(")", " to close count(")
            return ("count", arg, distinct)
        if low == "type":
            arg = self._expr()
            self._expect_op(")", " to close type(")
            return ("type", arg)
        if low in _AGGREGATES:
            raise CypherError(f"aggregate function {name}() is not supported (only count)")
        raise CypherError(f"function {name}() is not supported (available: count, type)")


# --------------------------------------------------------------------------- static validation

def _walk(e: tuple) -> Iterator[tuple]:
    yield e
    kind = e[0]
    if kind in ("and", "or"):
        yield from _walk(e[1])
        yield from _walk(e[2])
    elif kind == "not":
        yield from _walk(e[1])
    elif kind == "cmp":
        yield from _walk(e[2])
        yield from _walk(e[3])
    elif kind == "isnull":
        yield from _walk(e[1])
    elif kind == "type":
        yield from _walk(e[1])
    elif kind == "count" and e[1] is not None:
        yield from _walk(e[1])


def _validate(q: Query) -> None:
    kinds: dict[str, str] = {}  # var -> node | rel | relpath
    for n in q.nodes:
        if n.var:
            if kinds.setdefault(n.var, "node") != "node":
                raise CypherError(f"variable '{n.var}' is used for both a node and a relationship")
        for k, _ in n.props:
            if k not in NODE_PROPS:
                raise CypherError(f"unknown node property '{k}' (available: {', '.join(NODE_PROPS)})")
    for r in q.rels:
        if r.var:
            if r.var in kinds:
                raise CypherError(f"variable '{r.var}' is declared more than once")
            kinds[r.var] = "relpath" if r.varlen else "rel"
        for k, _ in r.props:
            if k not in REL_PROPS:
                raise CypherError(f"unknown relationship property '{k}' (available: {', '.join(REL_PROPS)})")

    def check(e: tuple, allow_count: bool) -> None:
        for sub in _walk(e):
            if sub[0] == "var" and sub[1] not in kinds:
                raise CypherError(f"unknown variable '{sub[1]}'")
            elif sub[0] == "prop":
                if sub[1] not in kinds:
                    raise CypherError(f"unknown variable '{sub[1]}'")
                allowed = NODE_PROPS if kinds[sub[1]] == "node" else REL_PROPS
                what = "node" if kinds[sub[1]] == "node" else "relationship"
                if sub[2] not in allowed:
                    raise CypherError(f"unknown {what} property '{sub[1]}.{sub[2]}' (available: {', '.join(allowed)})")
            elif sub[0] == "type":
                if sub[1][0] != "var" or kinds.get(sub[1][1]) not in ("rel", "relpath"):
                    raise CypherError("type() takes a relationship variable, e.g. type(r)")
            elif sub[0] == "count" and not allow_count:
                raise CypherError("count() is only allowed as a RETURN column")
            elif sub[0] == "cmp" and sub[1] == "REGEX" and sub[3][0] == "lit":
                if not isinstance(sub[3][1], str):
                    raise CypherError("=~ needs a string pattern")
                _compile_regex(sub[3][1])

    if q.where is not None:
        check(q.where, False)
    for it in q.items:
        top_count = it.expr[0] == "count"
        check(it.expr, top_count)
        if top_count and it.expr[1] is not None:
            check(it.expr[1], False)
    q.aggregated = any(it.expr[0] == "count" for it in q.items)
    # resolve ORDER BY to return-column references where possible
    aliases = {it.alias: i for i, it in enumerate(q.items)}
    resolved: list[tuple[tuple, bool]] = []
    for e, desc in q.order:
        col = None
        if e[0] == "var" and e[1] in aliases:
            col = aliases[e[1]]
        else:
            for i, it in enumerate(q.items):
                if it.expr == e:
                    col = i
                    break
        if col is not None:
            resolved.append((("col", col), desc))
        elif q.aggregated or q.distinct:
            raise CypherError("ORDER BY must reference a RETURN column (or its alias) when using DISTINCT or count()")
        else:
            check(e, False)
            resolved.append((e, desc))
    q.order = resolved


def parse_cypher(query: str) -> Query:
    """Parse a Cypher-subset query; raises CypherError on anything unsupported."""
    return _Parser(query).parse()


# --------------------------------------------------------------------------- execution

@dataclass
class CypherResult:
    columns: list[str]
    rows: list[list[Any]]
    truncated: bool = False
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"columns": self.columns, "rows": self.rows, "row_count": len(self.rows),
                "truncated": self.truncated, "notes": self.notes}


def load_community_names(graph_path: Path | str | None) -> dict[int, str]:
    """Community labels written next to graph.json (empty when absent or unreadable)."""
    if not graph_path:
        return {}
    p = Path(graph_path).parent / ".graphify_labels.json"
    try:
        return {int(k): str(v) for k, v in json.loads(p.read_text(encoding="utf-8")).items()}
    except (OSError, ValueError, AttributeError):
        return {}


class _Ref(NamedTuple):
    """A bound pattern variable: tag n (node id), e (edge index) or p (tuple of edge indexes)."""
    tag: str
    ref: Any


def _hkey(v: Any) -> Any:
    return json.dumps(v, sort_keys=True, default=str) if isinstance(v, (dict, list, tuple)) else (type(v).__name__, v)


def _sortkey(v: Any) -> tuple:
    if v is None:
        return (4, 0)
    if isinstance(v, bool):
        return (0, v)
    if isinstance(v, (int, float)):
        return (1, v)
    if isinstance(v, str):
        return (2, v)
    return (3, json.dumps(v, sort_keys=True, default=str))


def _is_num(v: Any) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _eq(a: Any, b: Any) -> bool | None:
    if a is None or b is None:
        return None
    if _is_num(a) and _is_num(b):
        return a == b
    if type(a) is not type(b):
        return False
    return a == b


class _Exec:
    def __init__(self, G: nx.Graph, q: Query, community_names: dict[int, str], max_steps: int, max_seconds: float):
        self.G, self.q = G, q
        self.names = community_names
        self.max_steps = max_steps
        self.deadline = time.monotonic() + max_seconds
        self.steps = 0
        self.edges: list[tuple[str, str, dict]] = []
        self.adj: dict[Any, list[tuple[Any, int, str]]] = {}
        for u, v, d in G.edges(data=True):
            s, t = d.get("_src", u), d.get("_tgt", v)
            if {s, t} != {u, v}:
                s, t = u, v
            idx = len(self.edges)
            self.edges.append((s, t, d))
            if s == t:
                self.adj.setdefault(s, []).append((s, idx, "both"))
            else:
                self.adj.setdefault(s, []).append((t, idx, "out"))
                self.adj.setdefault(t, []).append((s, idx, "in"))
        self._layer: dict[Any, Any] = {}

    def tick(self, n: int = 1) -> None:
        self.steps += n
        if self.steps > self.max_steps:
            raise CypherError(
                f"query exceeded the step budget ({self.max_steps}); narrow it with node labels, "
                "inline properties, relationship types or fewer hops"
            )
        if (self.steps & 1023) < n and time.monotonic() > self.deadline:
            raise CypherError("query exceeded its time budget; narrow it (labels, properties, relationship types, fewer hops)")

    # -- properties
    def node_prop(self, nid: Any, key: str) -> Any:
        d = self.G.nodes[nid]
        if key == "id":
            return nid
        if key == "degree":
            return self.G.degree(nid)
        if key == "layer":
            if nid not in self._layer:
                sf = d.get("source_file")
                self._layer[nid] = layer_of_path(str(sf)) if sf else None
            return self._layer[nid]
        if key == "community_name":
            name = d.get("community_name")
            if name is None and isinstance(d.get("community"), int):
                name = self.names.get(d["community"])
            return name
        return d.get(key)

    def edge_prop(self, idx: int, key: str) -> Any:
        return self.edges[idx][2].get(key)

    def _node_ok(self, nid: Any, pat: NodePat) -> bool:
        for lab in pat.labels:
            ft = self.G.nodes[nid].get("file_type")
            if str(ft).lower() != lab.lower():
                return False
        return all(_eq(self.node_prop(nid, k), v) is True for k, v in pat.props)

    # -- matching
    def _starts(self, pat: NodePat) -> Iterator[Any]:
        for k, v in pat.props:
            if k == "id":
                if v in self.G:
                    yield v
                return
        yield from self.G.nodes

    def _walk_rel(self, cur: Any, rel: RelPat, used: set[int]) -> Iterator[tuple[Any, tuple[int, ...]]]:
        path: list[int] = []

        def rec(node: Any, depth: int) -> Iterator[tuple[Any, tuple[int, ...]]]:
            if depth >= rel.lo:
                yield node, tuple(path)
            if depth == rel.hi:
                return
            for other, ei, d in self.adj.get(node, ()):
                self.tick()
                if ei in used or (rel.direction == "out" and d == "in") or (rel.direction == "in" and d == "out"):
                    continue
                data = self.edges[ei][2]
                if rel.types and data.get("relation") not in rel.types:
                    continue
                if rel.props and not all(_eq(data.get(k), v) is True for k, v in rel.props):
                    continue
                used.add(ei)
                path.append(ei)
                yield from rec(other, depth + 1)
                path.pop()
                used.discard(ei)

        yield from rec(cur, 0)

    def _expand(self, i: int, cur: Any, b: dict, used: set[int]) -> Iterator[dict]:
        if i == len(self.q.rels):
            yield b
            return
        rel, tgt = self.q.rels[i], self.q.nodes[i + 1]
        for end, path in self._walk_rel(cur, rel, used):
            if tgt.var and tgt.var in b and b[tgt.var].ref != end:
                continue
            if not self._node_ok(end, tgt):
                continue
            nb = dict(b)
            if tgt.var:
                nb[tgt.var] = _Ref("n", end)
            if rel.var:
                nb[rel.var] = _Ref("p", path) if rel.varlen else _Ref("e", path[0])
            yield from self._expand(i + 1, end, nb, used)

    def _matches(self) -> Iterator[dict]:
        first = self.q.nodes[0]
        for nid in self._starts(first):
            self.tick()
            if not self._node_ok(nid, first):
                continue
            yield from self._expand(0, nid, {first.var: _Ref("n", nid)} if first.var else {}, set())

    # -- expressions
    def _value(self, e: tuple, b: dict) -> Any:
        kind = e[0]
        if kind == "lit":
            return e[1]
        if kind == "var":
            return b[e[1]]
        if kind == "prop":
            tag, ref = b[e[1]]
            if tag == "n":
                return self.node_prop(ref, e[2])
            if tag == "e":
                return self.edge_prop(ref, e[2])
            return tuple(self.edge_prop(i, e[2]) for i in ref)
        if kind == "type":
            tag, ref = b[e[1][1]]
            return self.edge_prop(ref, "relation") if tag == "e" else tuple(self.edge_prop(i, "relation") for i in ref)
        if kind == "isnull":
            return (self._value(e[1], b) is None) != e[2]
        if kind == "not":
            v = self._truth(self._value(e[1], b))
            return None if v is None else not v
        if kind == "and":
            left = self._truth(self._value(e[1], b))
            if left is False:
                return False
            right = self._truth(self._value(e[2], b))
            if right is False:
                return False
            return None if left is None or right is None else True
        if kind == "or":
            left = self._truth(self._value(e[1], b))
            if left is True:
                return True
            right = self._truth(self._value(e[2], b))
            if right is True:
                return True
            return None if left is None or right is None else False
        if kind == "cmp":
            return self._compare(e[1], self._value(e[2], b), self._value(e[3], b))
        raise CypherError(f"cannot evaluate {kind} here")  # unreachable after validation

    @staticmethod
    def _truth(v: Any) -> bool | None:
        if v is None or isinstance(v, bool):
            return v
        raise CypherError(f"expected a boolean condition, got {type(v).__name__} {v!r}")

    def _compare(self, op: str, a: Any, b: Any) -> bool | None:
        if op == "=":
            return _eq(a, b)
        if op == "<>":
            r = _eq(a, b)
            return None if r is None else not r
        if op == "IN":
            if b is None or a is None:
                return None
            if not isinstance(b, tuple):
                raise CypherError("IN needs a list on the right, e.g. IN ['a', 'b']")
            hits = [_eq(a, x) for x in b]
            return True if True in hits else None if None in hits else False
        if a is None or b is None:
            return None
        if op in ("<", "<=", ">", ">="):
            if not ((_is_num(a) and _is_num(b)) or (isinstance(a, str) and isinstance(b, str))):
                return None
            return {"<": a < b, "<=": a <= b, ">": a > b, ">=": a >= b}[op]
        if not (isinstance(a, str) and isinstance(b, str)):
            return None
        if op == "CONTAINS":
            return b in a
        if op == "STARTS":
            return a.startswith(b)
        if op == "ENDS":
            return a.endswith(b)
        # REGEX: Cypher semantics = whole-string match
        self.tick()
        pat = _compile_regex(b)
        return len(a) <= MAX_REGEX_SUBJECT and pat.fullmatch(a) is not None

    def _passes(self, b: dict) -> bool:
        self.tick()
        return self.q.where is None or self._truth(self._value(self.q.where, b)) is True

    # -- output values
    def _materialize(self, v: Any) -> Any:
        if isinstance(v, _Ref):
            tag, ref = v
            if tag == "n":
                return {"id": ref, **{k: self.node_prop(ref, k) for k in ("label", "source_file", "source_location")}}
            if tag == "e":
                s, t, d = self.edges[ref]
                return {"relation": d.get("relation"), "confidence": d.get("confidence"),
                        "context": d.get("context"), "source": s, "target": t}
            return [self._materialize(_Ref("e", i)) for i in ref]
        if isinstance(v, tuple):
            return list(v)
        return v

    # -- run
    def run(self, default_limit: int) -> CypherResult:
        q = self.q
        notes: list[str] = []
        limit = q.limit if q.limit is not None else default_limit
        if limit > MAX_ROWS:
            notes.append(f"LIMIT clamped to the hard cap of {MAX_ROWS} rows")
            limit = MAX_ROWS
        columns = [it.alias for it in q.items]
        self._label_notes(notes)
        bindings = (b for b in self._matches() if self._passes(b))

        if q.aggregated:
            rows, keys = self._aggregate(bindings)
        elif q.order:
            rows, keys = self._project_all(bindings)
        else:
            rows, keys = self._project_stream(bindings, q.skip + limit + 1), None

        if keys is not None and q.order:
            idx = list(range(len(rows)))
            for pos in reversed(range(len(q.order))):
                idx.sort(key=lambda i, p=pos: _sortkey(keys[i][p]), reverse=q.order[pos][1])
            rows = [rows[i] for i in idx]
        truncated = len(rows) > q.skip + limit
        rows = rows[q.skip:q.skip + limit]
        return CypherResult(columns, rows, truncated, notes)

    def _label_notes(self, notes: list[str]) -> None:
        types = {str(d.get("file_type")).lower() for _, d in self.G.nodes(data=True)}
        for n in self.q.nodes:
            for lab in n.labels:
                if lab.lower() not in types:
                    notes.append(f"label :{lab} matches no node (labels match file_type: {', '.join(sorted(types))})")
        seen = {str(d.get("relation")) for _, _, d in self.edges}
        for r in self.q.rels:
            for t in r.types:
                if t not in seen:
                    notes.append(f"relationship type '{t}' does not occur in this graph")

    def _row(self, b: dict) -> list[Any]:
        return [self._materialize(self._value(it.expr, b)) for it in self.q.items]

    def _order_vals(self, b: dict, row: list[Any]) -> list[Any]:
        return [row[e[1]] if e[0] == "col" else self._materialize(self._value(e, b)) for e, _ in self.q.order]

    def _project_stream(self, bindings: Iterator[dict], need: int) -> list[list[Any]]:
        rows: list[list[Any]] = []
        seen: set = set()
        for b in bindings:
            row = self._row(b)
            if self.q.distinct:
                k = tuple(_hkey(v) for v in row)
                if k in seen:
                    continue
                seen.add(k)
            rows.append(row)
            if len(rows) >= need:
                break
        return rows

    def _project_all(self, bindings: Iterator[dict]):
        rows, keys, seen = [], [], set()
        for b in bindings:
            row = self._row(b)
            if self.q.distinct:
                k = tuple(_hkey(v) for v in row)
                if k in seen:
                    continue
                seen.add(k)
            rows.append(row)
            keys.append(self._order_vals(b, row))
        return rows, keys

    def _aggregate(self, bindings: Iterator[dict]):
        items = self.q.items
        groups: dict[tuple, dict] = {}
        for b in bindings:
            plain = [self._materialize(self._value(it.expr, b)) if it.expr[0] != "count" else None for it in items]
            gk = tuple(_hkey(v) for it, v in zip(items, plain) if it.expr[0] != "count")
            g = groups.get(gk)
            if g is None:
                g = groups[gk] = {"plain": plain, "n": [0 if it.expr[0] == "count" else None for it in items],
                                  "seen": [set() for _ in items]}
            for i, it in enumerate(items):
                if it.expr[0] != "count":
                    continue
                if it.expr[1] is None:
                    g["n"][i] += 1
                    continue
                v = self._materialize(self._value(it.expr[1], b))
                if v is None:
                    continue
                if it.expr[2]:
                    g["seen"][i].add(_hkey(v))
                    g["n"][i] = len(g["seen"][i])
                else:
                    g["n"][i] += 1
        if not groups and all(it.expr[0] == "count" for it in items):
            groups[()] = {"plain": [None] * len(items), "n": [0] * len(items), "seen": []}
        rows, keys, seen = [], [], set()
        for g in groups.values():
            row = [g["n"][i] if it.expr[0] == "count" else g["plain"][i] for i, it in enumerate(items)]
            if self.q.distinct:
                k = tuple(_hkey(v) for v in row)
                if k in seen:
                    continue
                seen.add(k)
            rows.append(row)
            keys.append([row[e[1]] for e, _ in self.q.order])
        return rows, keys


def run_cypher(
    G: nx.Graph,
    query: str,
    *,
    limit: int | None = None,
    community_names: dict[int, str] | None = None,
    max_steps: int = MAX_STEPS,
    max_seconds: float = MAX_SECONDS,
) -> CypherResult:
    """Run a read-only Cypher-subset query on `G`.

    `limit` is the default row limit used when the query has no LIMIT of its own
    (default 100); either way output is capped at MAX_ROWS.
    """
    q = parse_cypher(query)
    if limit is not None and limit < 1:
        raise CypherError("limit must be a positive integer")
    ex = _Exec(G, q, community_names or {}, max_steps, max_seconds)
    return ex.run(limit if limit is not None else DEFAULT_LIMIT)


# --------------------------------------------------------------------------- formatting

def _cell(v: Any) -> str:
    if v is None:
        return "null"
    if isinstance(v, dict):
        if "label" in v:
            loc = v.get("source_file") or ""
            if loc and v.get("source_location"):
                loc += f":{v['source_location']}"
            return f"{v['label']} ({loc})" if loc else str(v["label"])
        if "relation" in v:
            return f"[:{v['relation']}]"
    if isinstance(v, list):
        return "[" + ", ".join(_cell(x) for x in v) + "]"
    s = str(v)
    return s if len(s) <= 120 else s[:117] + "..."


def format_table(result: CypherResult) -> str:
    """Plain-text table; footer notes row count, truncation and advisory notes."""
    cells = [[_cell(v) for v in row] for row in result.rows]
    widths = [max([len(c)] + [len(r[i]) for r in cells]) for i, c in enumerate(result.columns)]
    lines = []
    if result.columns:
        lines.append("  ".join(c.ljust(w) for c, w in zip(result.columns, widths)).rstrip())
        lines.append("  ".join("-" * w for w in widths))
    lines += ["  ".join(c.ljust(w) for c, w in zip(r, widths)).rstrip() for r in cells]
    n = len(result.rows)
    lines.append(f"({n} row{'s' if n != 1 else ''}{', more available: raise LIMIT (max %d)' % MAX_ROWS if result.truncated else ''})")
    lines += [f"note: {x}" for x in result.notes]
    return "\n".join(lines)
