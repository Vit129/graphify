"""Query engine: tokenize -> score -> seed -> traverse -> render.

Extracted from serve.py (2026-07-02) purely to keep file size manageable —
no behavior change. serve.py re-exports everything here so existing imports
(`from graphify.serve import _score_nodes`, etc.) keep working unmodified.

This module owns the full lexical query pipeline: BM25 scoring, camelCase/
snake_case tokenization, trigram indexing, typo/abbreviation fuzzy fallback,
context-filter inference, BFS/DFS traversal, and text rendering. It has no
dependency on the MCP transport layer (stdio/HTTP) in serve.py — the
dependency direction is one-way: serve.py imports from here, never the
reverse.
"""
from __future__ import annotations
import math
import re
from array import array
from pathlib import Path
import networkx as nx
from graphify.security import sanitize_label
from graphify.detect import DOC_EXTENSIONS

try:
    import jieba as _jieba  # type: ignore[import-untyped]
except ImportError:
    _jieba = None


def _strip_diacritics(text: str | None) -> str:
    import unicodedata
    if not isinstance(text, str):
        text = "" if text is None else str(text)
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


_CAMEL_SPLIT_RE = re.compile(r"[A-Z]+(?![a-z])|[A-Z]?[a-z]+|[0-9]+|[^\W\d_]+")


def _search_tokens(text: str) -> list[str]:
    """Split text into word tokens on punctuation/underscore/hyphen *and*
    camelCase/PascalCase boundaries, stripping diacritics.
    """
    return [tok.lower() for tok in _CAMEL_SPLIT_RE.findall(_strip_diacritics(str(text)))]


def _has_chinese(text: str) -> bool:
    return any("一" <= ch <= "鿿" for ch in text)


def _segment_chinese(text: str) -> list[str]:
    """Segment Chinese text and keep the original term for exact matching."""
    if _jieba is not None:
        segments = [w for w in _jieba.cut(text) if len(w.strip()) > 0]
    else:
        segments = [text[i:i + 2] for i in range(len(text) - 1)] or [text]
    if len(text) > 1 and text not in segments:
        segments.append(text)
    return segments


def _is_searchable(term: str) -> bool:
    """True if term is Chinese, non-English, or an English word longer than 2 chars."""
    if all("a" <= ch <= "z" for ch in term):
        return len(term) > 2
    return True


# English question/filler words dropped from query terms so content words drive
# BFS seeding. Without this, "how does the frontier cache work" seeds on "how"/
# "the"/"work" (which prefix-match prose labels like "Working Principles" at the
# 100x prefix tier) instead of "frontier"/"cache", landing in the wrong part of
# the graph. Merged from this fork's own P1-reopen stopword set and upstream's
# independent fix for the same class of bug (#query-stopwords) — the two lists
# overlapped heavily but each had words the other missed. Applied to query terms
# only via `_query_terms`'s fallback-to-unfiltered behavior below — node text is
# never filtered, so a symbol literally named `work` stays findable via
# explain/path.
_STOPWORDS = frozenset({
    "how", "does", "is", "are", "the", "a", "an", "to", "of", "in", "on",
    "for", "and", "or", "what", "which", "that", "do", "did", "will",
    "would", "should", "can", "could", "with", "from", "at", "by", "this",
    "why", "when", "where", "who", "whom", "whose", "was", "were", "be",
    "been", "being", "shall", "may", "might", "must", "has", "have", "had",
    "but", "not", "without", "into", "onto", "off", "these", "those",
    "there", "here", "its", "their", "them", "they", "about", "any", "all",
    "some", "work", "works", "working",
})


# Lightweight query expansion: a query and the code it's about can use
# different words for the same concept ("log the user in" vs. `authenticate`)
# with zero literal terms in common, which BM25 can never bridge no matter
# how good the ranking is. Evaluated full embedding search for this same gap
# and rejected it (infra cost, network/API-key dependency for a local
# CLI/MCP tool — see agent-memory/knowledge/architecture/feature-provenance.md)
# in favor of this: a small curated synonym map riding the existing BM25
# pipeline as ordinary extra terms. Ceiling: only helps pairs actually in the
# map below, not open-ended concept similarity — a real embedding-search gap
# would need the heavier approach this deliberately avoids.
_SYNONYM_GROUPS: tuple[frozenset[str], ...] = (
    frozenset({"login", "signin", "logon", "authenticate", "auth"}),
    frozenset({"logout", "signout"}),
    frozenset({"register", "signup"}),
    frozenset({"delete", "remove", "erase"}),
    frozenset({"fetch", "retrieve", "get"}),
    frozenset({"create", "add", "new"}),
    frozenset({"update", "edit", "modify"}),
    frozenset({"start", "begin", "launch", "init", "initialize"}),
    frozenset({"stop", "halt", "terminate", "kill"}),
    frozenset({"config", "configuration", "settings", "options"}),
    frozenset({"error", "exception", "fail", "failure"}),
    frozenset({"test", "spec", "check", "verify", "validate"}),
    frozenset({"click", "tap", "press"}),
    frozenset({"send", "submit", "dispatch"}),
    frozenset({"show", "display", "render"}),
    frozenset({"hide", "dismiss"}),
)
# Separable phrasal-verb patterns ("log the user IN", "sign them UP") for
# concepts single-token expansion can't reach: the particle ("in"/"up") is a
# filtered stopword, and the verb ("log") is too ambiguous with logging to
# put in a synonym group on its own. Matched with a small bounded word-gap
# against the raw (unfiltered) question so "log in" and "log the user in"
# both hit but an unrelated "the log rotates later in production" doesn't.
_PHRASE_SYNONYMS: tuple[tuple["re.Pattern[str]", frozenset[str]], ...] = (
    (re.compile(r"\blog\b(?:\s+\w+){0,3}\s+\bin\b"), frozenset({"login", "authenticate"})),
    (re.compile(r"\blog\b(?:\s+\w+){0,3}\s+\bon\b"), frozenset({"login", "logon", "authenticate"})),
    (re.compile(r"\bsign\b(?:\s+\w+){0,3}\s+\bin\b"), frozenset({"login", "signin", "authenticate"})),
    (re.compile(r"\blog\b(?:\s+\w+){0,3}\s+\bout\b"), frozenset({"logout"})),
    (re.compile(r"\bsign\b(?:\s+\w+){0,3}\s+\bout\b"), frozenset({"logout", "signout"})),
    (re.compile(r"\bsign\b(?:\s+\w+){0,3}\s+\bup\b"), frozenset({"register", "signup"})),
)


def _expand_synonyms(terms: list[str], raw_question: str) -> list[str]:
    expanded = list(terms)
    seen = set(terms)
    for term in terms:
        for group in _SYNONYM_GROUPS:
            if term in group:
                for syn in group:
                    if syn not in seen:
                        seen.add(syn)
                        expanded.append(syn)
    lower_q = raw_question.lower()
    for pattern, extra_terms in _PHRASE_SYNONYMS:
        if pattern.search(lower_q):
            for syn in extra_terms:
                if syn not in seen:
                    seen.add(syn)
                    expanded.append(syn)
    return expanded


def _query_terms(question: str) -> list[str]:
    """Split a query into searchable terms, segmenting Chinese text, drop
    stopwords (falling back to the unfiltered terms if the query is all
    stopwords, e.g. "how does it work", so it still seeds on something), then
    expand synonyms."""
    terms: list[str] = []
    for raw in question.split():
        if _has_chinese(raw):
            for seg in _segment_chinese(raw.lower().strip()):
                seg = seg.strip()
                if seg and _is_searchable(seg):
                    terms.append(seg)
        else:
            for tok in re.findall(r"\w+", raw.lower()):
                if _is_searchable(tok):
                    terms.append(tok)
    content = [t for t in terms if t not in _STOPWORDS]
    return _expand_synonyms(content or terms, question)


# --- P5: typo/abbreviation cascade fallback ---
#
# Only invoked when the primary lexical pass (_score_nodes/_pick_seeds) finds
# nothing at all. Corrects failing query terms against the graph's own
# vocabulary, then hands the corrected terms back to the *unmodified*
# _score_nodes pipeline.

_NGRAM_SPAN_SIZES = (2, 3)


def _get_vocabulary(G: nx.Graph) -> tuple[set[str], dict[int, list[str]], set[str], dict[int, list[str]]]:
    """Two separate candidate pools, each length-bucketed, cached together on
    G.graph like _idf_cache / _trigram_index: typo pool (sub-words + whole
    labels + 2-/3-token spans) and abbreviation pool (sub-words + whole
    labels only, no spans — mixing them in was tried and reverted, see
    git history for the rationale).
    """
    cached = G.graph.get("_vocabulary")
    if cached is not None:
        return cached
    typo_words: set[str] = set()
    abbr_words: set[str] = set()
    for _, data in G.nodes(data=True):
        label = data.get("label") or ""
        tokens = _search_tokens(label)
        typo_words.update(tokens)
        abbr_words.update(tokens)
        whole = "".join(tokens)
        if whole:
            typo_words.add(whole)
            abbr_words.add(whole)
        for span_size in _NGRAM_SPAN_SIZES:
            for i in range(len(tokens) - span_size + 1):
                span = "".join(tokens[i:i + span_size])
                if span:
                    typo_words.add(span)
    typo_buckets: dict[int, list[str]] = {}
    for w in typo_words:
        typo_buckets.setdefault(len(w), []).append(w)
    abbr_buckets: dict[int, list[str]] = {}
    for w in abbr_words:
        abbr_buckets.setdefault(len(w), []).append(w)
    result = (typo_words, typo_buckets, abbr_words, abbr_buckets)
    G.graph["_vocabulary"] = result
    return result


def _damerau_levenshtein(a: str, b: str) -> int:
    """Edit distance with adjacent transposition as a single edit."""
    la, lb = len(a), len(b)
    d: dict[tuple[int, int], int] = {}
    for i in range(-1, la + 1):
        d[(i, -1)] = i + 1
    for j in range(-1, lb + 1):
        d[(-1, j)] = j + 1
    for i in range(la):
        for j in range(lb):
            cost = 0 if a[i] == b[j] else 1
            d[(i, j)] = min(
                d[(i - 1, j)] + 1,
                d[(i, j - 1)] + 1,
                d[(i - 1, j - 1)] + cost,
            )
            if i and j and a[i] == b[j - 1] and a[i - 1] == b[j]:
                d[(i, j)] = min(d[(i, j)], d[(i - 2, j - 2)] + cost)
    return d[(la - 1, lb - 1)]


def _subsequence_score(query: str, target: str) -> int | None:
    """Greedy ordered-subsequence match score, or None if `query`'s
    characters don't all appear in `target` in order.
    """
    ti = 0
    score = 0
    last = -1
    for qc in query:
        found = False
        while ti < len(target):
            if target[ti] == qc:
                score += 3
                if last == ti - 1:
                    score += 6
                gap = ti - (last + 1)
                if gap > 0:
                    score -= gap
                last = ti
                ti += 1
                found = True
                break
            ti += 1
        if not found:
            return None
    if target.startswith(query):
        score += 60
    return score


def _correct_term(term: str, G: nx.Graph) -> str | None:
    """Best vocabulary correction for a term that matched nothing verbatim."""
    if len(term) < 3:
        return None
    typo_words, typo_buckets, abbr_words, abbr_buckets = _get_vocabulary(G)
    if term in typo_words:
        return None

    max_dist = 1 if len(term) <= 4 else 2
    best_typo: tuple[int, str] | None = None
    for length in range(len(term) - max_dist, len(term) + max_dist + 1):
        for cand in typo_buckets.get(length, ()):
            dist = _damerau_levenshtein(term, cand)
            if dist <= max_dist and (best_typo is None or dist < best_typo[0]):
                best_typo = (dist, cand)
    if best_typo is not None:
        return best_typo[1]

    if len(term) <= 5:
        best_abbr: tuple[int, str] | None = None
        for length, cands in abbr_buckets.items():
            if length < len(term) * 2:
                continue
            for cand in cands:
                score = _subsequence_score(term, cand)
                if score is not None and (best_abbr is None or score > best_abbr[0]):
                    best_abbr = (score, cand)
        if best_abbr is not None:
            return best_abbr[1]

    return None


def _apply_vocabulary_corrections(
    G: nx.Graph, terms: list[str]
) -> tuple[list[str], list[tuple[str, str]]]:
    """Map _correct_term over `terms`."""
    corrected_terms: list[str] = []
    corrections: list[tuple[str, str]] = []
    for t in terms:
        fix = _correct_term(t, G)
        if fix is not None:
            corrected_terms.append(fix)
            corrections.append((t, fix))
        else:
            corrected_terms.append(t)
    return corrected_terms, corrections


def _fuzzy_substring_distance(pattern: str, text: str) -> int:
    """Minimum edit distance between `pattern` and *some* substring of `text`
    (Bitap/agrep-style approximate substring search, plain DP variant).
    """
    m, n = len(pattern), len(text)
    prev = [0] * (n + 1)
    for i in range(1, m + 1):
        curr = [i] + [0] * n
        for j in range(1, n + 1):
            cost = 0 if pattern[i - 1] == text[j - 1] else 1
            curr[j] = min(prev[j] + 1, curr[j - 1] + 1, prev[j - 1] + cost)
        prev = curr
    return min(prev)


def _fuzzy_substring_seeds(
    G: nx.Graph, terms: list[str], *, max_results: int = 5, min_term_len: int = 4
) -> list[str]:
    """Last-resort fallback when neither the primary lexical pass nor
    _correct_term's vocabulary correction finds anything.
    """
    candidates: list[tuple[int, str]] = []
    for term in terms:
        if len(term) < min_term_len:
            continue
        max_dist = max(1, len(term) // 3)
        for nid, data in G.nodes(data=True):
            whole = "".join(_search_tokens(data.get("label") or ""))
            if len(whole) < len(term):
                continue
            dist = _fuzzy_substring_distance(term, whole)
            if dist <= max_dist:
                candidates.append((dist, nid))
    candidates.sort(key=lambda c: c[0])
    seen: set[str] = set()
    seeds: list[str] = []
    for _, nid in candidates:
        if nid not in seen:
            seen.add(nid)
            seeds.append(nid)
        if len(seeds) >= max_results:
            break
    return seeds


# Opt-in, local-only dense-retrieval seed fallback (#5) - see the
# _SYNONYM_GROUPS comment above for why a hosted embedding API was rejected
# for this CLI/MCP tool. A LOCAL model has no network/API-key dependency, so
# that objection doesn't apply here; this is gated behind the `embeddings`
# extra and has zero effect on the default install (returns [] silently when
# the dependency isn't present - it never raises to a caller).
_EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
_embedding_model_cache: list = []


def _get_embedding_model():
    """Lazily load and cache the local sentence-transformers model for the
    process lifetime. Raises ImportError with install instructions (matching
    god_nodes(by="pagerank")'s pattern) if the optional dependency is missing -
    callers that want the "no effect if absent" behavior should catch this."""
    if _embedding_model_cache:
        return _embedding_model_cache[0]
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise ImportError(
            "embedding-based seed fallback requires sentence-transformers - "
            "install with `pip install graphifyy[embeddings]` or "
            "`uv tool install --with sentence-transformers graphifyy`"
        ) from exc
    model = SentenceTransformer(_EMBEDDING_MODEL_NAME)
    _embedding_model_cache.append(model)
    return _embedding_model_cache[0]


def _get_embedding_index(G: nx.Graph) -> "tuple[list[str], object] | None":
    """Build (and cache on G.graph, mirroring _get_bm25_corpus) a matrix of
    per-node label+source_file embeddings. Returns None (never raises) when
    the model can't be loaded, so callers get a clean no-op."""
    cached = G.graph.get("_embedding_index")
    if cached is not None:
        return cached
    try:
        model = _get_embedding_model()
    except ImportError:
        return None
    node_ids: list[str] = []
    texts: list[str] = []
    for nid, data in G.nodes(data=True):
        label = data.get("label") or ""
        if not label:
            continue
        source = data.get("source_file") or ""
        texts.append(f"{label} {source}".strip())
        node_ids.append(nid)
    if not texts:
        return None
    embeddings = model.encode(texts, normalize_embeddings=True)
    index = (node_ids, embeddings)
    G.graph["_embedding_index"] = index
    return index


_EMBEDDING_MIN_SIMILARITY = 0.35


def _embedding_seed_fallback(G: nx.Graph, question: str, top_k: int = 3) -> list[str]:
    """Last-resort seed selection via local dense-retrieval, tried only after
    BM25 + typo correction + fuzzy-substring matching all found nothing - the
    deliberate recall gap for a query and its target sharing zero literal or
    synonym-map terms (#5). Returns [] (never raises) whenever the optional
    dependency isn't installed, the index can't be built, or nothing clears
    _EMBEDDING_MIN_SIMILARITY - cosine similarity always returns SOME nearest
    node for ANY input, even a nonsense query with no real match anywhere in
    the graph, so an unfiltered top-k would turn a genuinely unmatched query
    into a confidently wrong one instead of "no match".
    """
    index = _get_embedding_index(G)
    if index is None:
        return []
    node_ids, embeddings = index
    try:
        model = _get_embedding_model()
    except ImportError:
        return []
    import numpy as np
    query_vec = model.encode([question], normalize_embeddings=True)[0]
    scores = embeddings @ query_vec
    top_indices = np.argsort(-scores)[:top_k]
    return [node_ids[i] for i in top_indices if scores[i] >= _EMBEDDING_MIN_SIMILARITY]


_EXACT_MATCH_BONUS = 1000.0
_PREFIX_MATCH_BONUS = 100.0
_SOURCE_MATCH_BONUS = 0.5


def _compute_idf(G: nx.Graph, terms: list[str]) -> dict[str, float]:
    """IDF weights for query terms, cached in G.graph['_idf_cache']."""
    cache: dict[str, float] = G.graph.setdefault("_idf_cache", {})
    N = G.number_of_nodes() or 1
    uncached = [t for t in terms if t not in cache]
    if uncached:
        df: dict[str, int] = {t: 0 for t in uncached}
        for _, data in G.nodes(data=True):
            norm_label = (
                data.get("norm_label") or _strip_diacritics(data.get("label") or "")
            ).lower()
            for t in uncached:
                if t in norm_label:
                    df[t] += 1
        for t in uncached:
            cache[t] = math.log(1 + N / (1 + df[t]))
    return {t: cache.get(t, math.log(1 + N)) for t in terms}


def _trigrams(text: str) -> set[str]:
    """Character trigrams of `text`; for <3-char text the whole string is the key."""
    if len(text) < 3:
        return {text} if text else set()
    return {text[i:i + 3] for i in range(len(text) - 2)}


def _node_search_text(data: dict, nid: str) -> str:
    """Concatenate every field _score_nodes / _find_node match a query against."""
    norm_label = data.get("norm_label") or _strip_diacritics(data.get("label") or "").lower()
    label_tokens = " ".join(_search_tokens(data.get("label") or ""))
    source = (data.get("source_file") or "").lower()
    source_tokens = " ".join(_search_tokens(data.get("source_file") or ""))
    return "\x00".join((norm_label, label_tokens, str(nid).lower(), source, source_tokens))


def _get_trigram_index(G: nx.Graph) -> dict:
    """Lazily build and cache a trigram -> node-position postings map on the graph."""
    idx = G.graph.get("_trigram_index")
    if idx is not None:
        return idx
    ids = list(G.nodes())
    postings: dict[str, array] = {}
    for i, nid in enumerate(ids):
        for g in _trigrams(_node_search_text(G.nodes[nid], nid)):
            bucket = postings.get(g)
            if bucket is None:
                bucket = array("i")
                postings[g] = bucket
            bucket.append(i)
    idx = {"ids": ids, "postings": postings, "set_cache": {}}
    G.graph["_trigram_index"] = idx
    return idx


def _trigram_candidates(G: nx.Graph, needles: list[str], *, guard_frac: float = 0.10) -> list[str] | None:
    """Node IDs whose text could contain any `needle` as a substring, via the
    trigram index — a *superset* the caller then re-scores with exact predicates.
    """
    idx = _get_trigram_index(G)
    ids, postings, set_cache = idx["ids"], idx["postings"], idx["set_cache"]
    n = len(ids)
    if n == 0:
        return []
    needles = [s for s in needles if s]
    thresh = int(n * guard_frac)
    for s in needles:
        tgs = _trigrams(s)
        if not tgs or any(len(g) < 3 for g in tgs):
            return None
        present = [len(postings[g]) for g in tgs if g in postings]
        if not present:
            continue
        if min(present) > thresh:
            return None
    cand: set[int] = set()
    for s in needles:
        sets: list[set] | None = []
        for g in _trigrams(s):
            bucket = postings.get(g)
            if bucket is None:
                sets = None
                break
            cached = set_cache.get(g)
            if cached is None:
                cached = set(bucket)
                set_cache[g] = cached
            sets.append(cached)
        if not sets:
            continue
        sets.sort(key=len)
        hit = set(sets[0])
        for other in sets[1:]:
            hit &= other
            if not hit:
                break
        cand |= hit
    return [ids[i] for i in sorted(cand)]


_BM25_K1 = 1.2
_BM25_B = 0.75

# Was 3 here vs. llm.py's _CHARS_PER_TOKEN = 4 for the extraction side (#6) —
# the mismatch meant a "2000-token budget" only ever filled ~1500 real tokens
# of query output, silently wasting ~25% of what the caller said it could read.
_CHARS_PER_TOKEN = 4


def _get_bm25_corpus(G: nx.Graph) -> tuple[dict[str, list[str]], dict[str, int], float, int]:
    """Tokenized label per node (BM25's "document"), term -> document-frequency
    over the *whole* graph, average document length, and node count.

    Whole-graph, not trigram-prefiltered — a term's rarity must be a
    property of the corpus, not of whatever candidate subset a different
    query happened to narrow down to. Each document also gets one extra
    pseudo-token: the label's whole concatenated form, so a query typed as
    one literal word ("foobarservice") can still match a label BM25
    tokenizes into morphemes ("FooBarService" -> foo/bar/service).

    Cached on G.graph like _idf_cache / _trigram_index.
    """
    cached = G.graph.get("_bm25_corpus")
    if cached is not None:
        return cached
    docs: dict[str, list[str]] = {}
    df: dict[str, int] = {}
    for nid, data in G.nodes(data=True):
        tokens = _search_tokens(data.get("label") or "")
        whole = "".join(tokens)
        if whole and whole not in tokens:
            tokens = tokens + [whole]
        docs[nid] = tokens
        for t in set(tokens):
            df[t] = df.get(t, 0) + 1
    N = len(docs) or 1
    avgdl = (sum(len(d) for d in docs.values()) / N) if docs else 1.0
    result = (docs, df, avgdl, N)
    G.graph["_bm25_corpus"] = result
    return result


def _bm25_idf(term: str, df: dict[str, int], N: int) -> float:
    """Standard Okapi BM25 IDF (Robertson-Sparck Jones form), floored at a
    small positive epsilon so it never goes negative and flips sign.
    """
    d = df.get(term, 0)
    return max(0.01, math.log(1 + (N - d + 0.5) / (d + 0.5)))


def _score_nodes(G: nx.Graph, terms: list[str]) -> list[tuple[float, str]]:
    scored = []
    norm_terms = [tok for t in terms for tok in _search_tokens(t)]
    if not norm_terms:
        return []
    docs, df, avgdl, N = _get_bm25_corpus(G)
    unique_terms = set(norm_terms)
    term_idf = {t: _bm25_idf(t, df, N) for t in unique_terms}
    joined = " ".join(norm_terms)
    joined_w = max((term_idf.get(t, 1.0) for t in norm_terms), default=1.0)
    candidate_ids = _trigram_candidates(G, norm_terms + ([joined] if joined else []))
    node_iter = (
        G.nodes(data=True) if candidate_ids is None
        else ((nid, G.nodes[nid]) for nid in candidate_ids)
    )
    for nid, data in node_iter:
        norm_label = data.get("norm_label") or _strip_diacritics(data.get("label") or "").lower()
        bare_label = norm_label.rstrip("()")
        label_token_list = docs.get(nid) or _search_tokens(data.get("label") or "")
        label_tokens = " ".join(label_token_list)
        source = (data.get("source_file") or "").lower()
        score = 0.0
        # Full-query tier — additive bonus on top of the BM25 sum below, so
        # `path`/`query` resolve the same node `explain` does via _find_node.
        if joined:
            nid_lower = nid.lower()
            if joined in (norm_label, bare_label, label_tokens, nid_lower):
                score += _EXACT_MATCH_BONUS * 10 * joined_w
            elif (
                norm_label.startswith(joined)
                or bare_label.startswith(joined)
                or label_tokens.startswith(joined)
            ):
                score += _PREFIX_MATCH_BONUS * 10 * joined_w
        # BM25 term-frequency sum: saturating term-frequency and document-
        # length normalization, replacing the old discrete exact/prefix/
        # substring tier system.
        dl = len(label_token_list) or 1
        b_norm = 1 - _BM25_B + _BM25_B * dl / avgdl
        tf: dict[str, int] = {}
        for tok in label_token_list:
            tf[tok] = tf.get(tok, 0) + 1
        for t in unique_terms:
            f = tf.get(t, 0)
            if f:
                score += term_idf[t] * f * (_BM25_K1 + 1) / (f + _BM25_K1 * b_norm)
            if t in source:
                score += _SOURCE_MATCH_BONUS * term_idf[t]
        if score > 0:
            scored.append((score, nid))
    scored.sort(key=lambda s: (-s[0], len(G.nodes[s[1]].get("label") or s[1]), s[1]))
    return scored


_CONCEPT_SEED_PENALTY = 0.85
_PROSE_SEED_PENALTY = 0.9


def _is_concept_node_for_seeding(G: nx.Graph, nid: str) -> bool:
    source = G.nodes[nid].get("source_file", "") or ""
    if not source:
        return True
    return "." not in source.rsplit("/", 1)[-1]


def _is_prose_node_for_seeding(G: nx.Graph, nid: str) -> bool:
    """A doc/prose file (.md, .txt, etc.) rather than code - has a real,
    openable source_file (so _is_concept_node_for_seeding doesn't already
    catch it), but a query resolving to it over an equally-plausible code
    symbol should need to be a clearly better match, same as a concept node.
    Gentler penalty than a true concept node: a doc heading is still an
    openable, legitimate answer (graphify deliberately unifies docs and code
    in one graph), just not preferred on a genuine tie.
    """
    source = G.nodes[nid].get("source_file", "") or ""
    return Path(source).suffix.lower() in DOC_EXTENSIONS


def _pick_seeds(
    scored: list[tuple[float, str]],
    max_k: int = 3,
    gap_ratio: float = 0.8,
    G: nx.Graph | None = None,
    multi_term: bool = False,
    max_communities: int = 5,
    terms: list[str] | None = None,
) -> list[str]:
    """Select BFS seed nodes, stopping when score drops too far below the top.

    `gap_ratio` default is 0.8, calibrated for BM25's smooth continuous score
    curve (raised from 0.2, which was calibrated against the old discrete
    tier system's huge multiplicative cliffs).

    Multi-term queries can hit an opposite failure: one term's exact-match
    bonus can crown a coincidental exact match over a node that
    substring-matches several OTHER query terms but lives in a different
    community. When `G`/`multi_term` are supplied, keep the best-scoring node
    from each additional distinct community, up to `max_communities`. When
    `terms` is also supplied, rank the fill candidates by IDF-weighted
    coverage rather than raw term count, so a generic word contributes little
    and a specific identifier contributes close to a full point.

    When `G` is supplied, concept nodes (no source_file, or a source_file with
    no extension - never a real, openable file) are scored down by
    `_CONCEPT_SEED_PENALTY` for THIS selection only (the original `scored`
    list passed by the caller is untouched). A concept only wins the top seed
    slot over a near-tied AST symbol if it's genuinely the better match (#4) -
    a query should resolve to the symbol with a line to open, not an
    equally-plausible abstract label with nowhere to point.

    A doc/prose node (.md, .txt, etc. - a real, openable file, just not code)
    gets a gentler `_PROSE_SEED_PENALTY` for the same reason: graphify
    deliberately unifies docs and code in one graph, so a doc heading is a
    legitimate answer and should still win when it's clearly the better
    match, just not on a near-tie against an equally-plausible code symbol.
    """
    if not scored:
        return []
    if G is not None:
        def _seed_penalty(nid: str) -> float:
            if _is_concept_node_for_seeding(G, nid):
                return _CONCEPT_SEED_PENALTY
            if _is_prose_node_for_seeding(G, nid):
                return _PROSE_SEED_PENALTY
            return 1.0

        scored = [(score * _seed_penalty(nid), nid) for score, nid in scored]
        scored.sort(key=lambda s: (-s[0], len(G.nodes[s[1]].get("label") or s[1]), s[1]))
    top_score = scored[0][0]
    seeds = []
    for score, nid in scored[:max_k]:
        if seeds and score < top_score * gap_ratio:
            break
        seeds.append(nid)
    if G is not None and multi_term:
        seen_communities = {G.nodes[n].get("community") for n in seeds}
        candidates = scored
        if terms:
            def _node_text(nid: str) -> str:
                data = G.nodes[nid]
                return f"{data.get('norm_label') or (data.get('label') or '').lower()} {(data.get('source_file') or '').lower()}"

            doc_freq = {t: 0 for t in terms}
            for _, nid in scored:
                text = _node_text(nid)
                for t in terms:
                    if t in text:
                        doc_freq[t] += 1
            term_weight = {t: 1.0 / math.log2(2 + df) for t, df in doc_freq.items()}

            def _coverage(nid: str) -> float:
                text = _node_text(nid)
                return sum(term_weight[t] for t in terms if t in text)

            candidates = sorted(scored, key=lambda s: (-_coverage(s[1]), -s[0]))
        for score, nid in candidates:
            if len(seeds) >= max_communities:
                break
            comm = G.nodes[nid].get("community")
            if comm in seen_communities:
                continue
            seen_communities.add(comm)
            seeds.append(nid)
    return seeds


_CONTEXT_HINTS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("call", ("call", "calls", "called", "invoke", "invokes", "invoked")),
    ("import", ("import", "imports", "imported", "module", "modules")),
    ("field", ("field", "fields", "member", "members", "property", "properties")),
    ("parameter_type", ("parameter", "parameters", "param", "params", "argument", "arguments")),
    ("return_type", ("return", "returns", "returned")),
    ("generic_arg", ("generic", "generics", "template", "templates")),
)


_CONTEXT_FILTER_ALIASES: dict[str, str] = {
    "param": "parameter_type",
    "params": "parameter_type",
    "parameter": "parameter_type",
    "parameters": "parameter_type",
    "argument": "parameter_type",
    "arguments": "parameter_type",
    "arg": "parameter_type",
    "args": "parameter_type",
    "return": "return_type",
    "returns": "return_type",
    "returned": "return_type",
    "generic": "generic_arg",
    "generics": "generic_arg",
    "template": "generic_arg",
    "templates": "generic_arg",
    "annotation": "attribute",
    "annotations": "attribute",
    "decorator": "attribute",
    "decorators": "attribute",
    "calls": "call",
    "called": "call",
    "invoke": "call",
    "invocation": "call",
    "fields": "field",
    "property": "field",
    "properties": "field",
    "member": "field",
    "members": "field",
    "imports": "import",
    "imported": "import",
    "module": "import",
    "modules": "import",
    "exports": "export",
    "exported": "export",
}


def _normalize_context_filters(filters: list[str] | None) -> list[str]:
    if not filters:
        return []
    normalized: list[str] = []
    seen: set[str] = set()
    for value in filters:
        key = _strip_diacritics(str(value)).strip().lower()
        if not key:
            continue
        key = _CONTEXT_FILTER_ALIASES.get(key, key)
        if key not in seen:
            seen.add(key)
            normalized.append(key)
    return normalized


def _infer_context_filters(question: str) -> list[str]:
    lowered = {
        _strip_diacritics(token).lower()
        for token in question.replace("?", " ").replace(",", " ").split()
    }
    inferred: list[str] = []
    for context, hints in _CONTEXT_HINTS:
        if any(hint in lowered for hint in hints):
            inferred.append(context)
    return inferred


def _resolve_context_filters(question: str, explicit_filters: list[str] | None = None) -> tuple[list[str], str | None]:
    normalized = _normalize_context_filters(explicit_filters)
    if normalized:
        return normalized, "explicit"
    inferred = _infer_context_filters(question)
    if inferred:
        return inferred, "heuristic"
    return [], None


def _filter_graph_by_context(G: nx.Graph, context_filters: list[str] | None) -> nx.Graph:
    filters = set(_normalize_context_filters(context_filters))
    if not filters:
        return G
    H = G.__class__()
    H.add_nodes_from(G.nodes(data=True))
    if isinstance(G, (nx.MultiGraph, nx.MultiDiGraph)):
        for u, v, key, data in G.edges(keys=True, data=True):
            if data.get("context") in filters:
                H.add_edge(u, v, key=key, **data)
    else:
        for u, v, data in G.edges(data=True):
            if data.get("context") in filters:
                H.add_edge(u, v, **data)
    return H


def _bfs(G: nx.Graph, start_nodes: list[str], depth: int) -> tuple[set[str], list[tuple]]:
    # p99 of degree distribution, floored at 50, so hubs aren't expanded as transit.
    degrees = [G.degree(n) for n in G.nodes()]
    if degrees:
        degrees_sorted = sorted(degrees)
        p99_idx = int(len(degrees_sorted) * 0.99)
        hub_threshold = max(50, degrees_sorted[p99_idx])
    else:
        hub_threshold = 50
    seed_set = set(start_nodes)
    visited: set[str] = set(start_nodes)
    frontier = set(start_nodes)
    edges_seen: list[tuple] = []
    for _ in range(depth):
        next_frontier: set[str] = set()
        for n in frontier:
            if n not in seed_set and G.degree(n) >= hub_threshold:
                continue
            for neighbor in G.neighbors(n):
                if neighbor not in visited:
                    next_frontier.add(neighbor)
                    edges_seen.append((n, neighbor))
        visited.update(next_frontier)
        frontier = next_frontier
    return visited, edges_seen


def _dfs(G: nx.Graph, start_nodes: list[str], depth: int) -> tuple[set[str], list[tuple]]:
    degrees = [G.degree(n) for n in G.nodes()]
    if degrees:
        degrees_sorted = sorted(degrees)
        p99_idx = int(len(degrees_sorted) * 0.99)
        hub_threshold = max(50, degrees_sorted[p99_idx])
    else:
        hub_threshold = 50
    seed_set = set(start_nodes)
    visited: set[str] = set()
    edges_seen: list[tuple] = []
    stack = [(n, 0) for n in reversed(start_nodes)]
    while stack:
        node, d = stack.pop()
        if node in visited or d > depth:
            continue
        visited.add(node)
        if node not in seed_set and G.degree(node) >= hub_threshold:
            continue
        for neighbor in G.neighbors(node):
            if neighbor not in visited:
                stack.append((neighbor, d + 1))
                edges_seen.append((node, neighbor))
    return visited, edges_seen


def _blast_radius_hops(
    G: nx.Graph, nid: str, max_hops: int, direction: str, node_cap: int = 200
) -> tuple[list[list[str]], bool, int]:
    """Walk outward from `nid` hop by hop, direction-aware (callers/callees/both).
    Returns (hops, truncated, node_cap). node_cap stops runaway on a
    highly-connected god-node; truncation trims the tail of the last hop
    reached deterministically.
    """
    visited = {nid}
    hops: list[list[str]] = []
    frontier = [nid]
    for _ in range(max_hops):
        next_frontier: list[str] = []
        for n in frontier:
            neighbors: list[str] = []
            if direction in ("callees", "both"):
                neighbors += list(G.successors(n))
            if direction in ("callers", "both"):
                neighbors += list(G.predecessors(n))
            for nb in neighbors:
                if nb not in visited:
                    visited.add(nb)
                    next_frontier.append(nb)
        if not next_frontier:
            break
        hops.append(next_frontier)
        frontier = next_frontier
        if len(visited) - 1 >= node_cap:
            break

    total = sum(len(h) for h in hops)
    truncated = total > node_cap
    if truncated:
        keep = node_cap
        trimmed: list[list[str]] = []
        for h in hops:
            if keep <= 0:
                break
            trimmed.append(h[:keep])
            keep -= len(h)
        hops = trimmed
    return hops, truncated, node_cap


def _hop_distances(nodes: set[str], edges: list[tuple], seeds: list[str]) -> dict[str, int]:
    """BFS distance in hops from the nearest seed, over the edges actually
    discovered during traversal. Undirected: a caller and a callee are equally
    'close' for ranking purposes regardless of which direction the traversal
    walked the edge. Used to rank query output by proximity to the answer
    instead of by raw degree, which favours god-nodes over relevant nodes (#1)."""
    from collections import deque
    adj: dict[str, set[str]] = {}
    for u, v in edges:
        adj.setdefault(u, set()).add(v)
        adj.setdefault(v, set()).add(u)
    dist: dict[str, int] = {s: 0 for s in seeds if s in nodes}
    q = deque(dist.keys())
    while q:
        cur = q.popleft()
        for nb in adj.get(cur, ()):
            if nb not in dist:
                dist[nb] = dist[cur] + 1
                q.append(nb)
    return dist


def _best_anchor_neighbor(G: nx.Graph, nid: str) -> str:
    """Best-effort file anchor for a concept node that has neither a
    source_file nor a source_location of its own - the source_file of its
    highest-degree neighbor that has one, so a query resolving to a pure
    concept node still points somewhere readable instead of a dead end (#4)."""
    best_file = ""
    best_degree = -1
    if G.is_directed():
        neighbors = set(G.successors(nid)) | set(G.predecessors(nid))
    else:
        neighbors = set(G.neighbors(nid))
    for nb in neighbors:
        nb_file = G.nodes[nb].get("source_file") or ""
        if nb_file and "." in nb_file.rsplit("/", 1)[-1]:
            deg = G.degree(nb)
            if deg > best_degree:
                best_degree = deg
                best_file = nb_file
    return best_file


def _subgraph_to_text(
    G: nx.Graph, nodes: set[str], edges: list[tuple], token_budget: int = 2000, *,
    seeds: list[str] | None = None,
    hop_distances: dict[str, int] | None = None,
    relevance_scores: dict[str, float] | None = None,
) -> str:
    """Render subgraph as text, cutting at token_budget (~4 chars/token, matching
    llm.py's extraction-side estimate).

    seeds: exact-match nodes rendered first before the ranked expansion, so the
    queried symbol always appears at the top of the output.

    hop_distances/relevance_scores: when given, the non-seed nodes are ranked
    by (hop distance from nearest seed asc, BM25 relevance desc, degree desc)
    instead of raw degree — a query's token budget should fill with nodes near
    and relevant to the answer, not with whichever hubs happen to have the most
    edges (#1). Omitting both preserves the old degree-only ordering exactly,
    so callers that render a subgraph with no query context are unaffected.
    """
    char_budget = token_budget * _CHARS_PER_TOKEN
    lines = []
    overlay = getattr(G, "graph", {}).get("_learning_overlay", {}) or {}
    seed_set = set(seeds or [])
    rest = nodes - seed_set
    if hop_distances is not None or relevance_scores is not None:
        _hops = hop_distances or {}
        _rel = relevance_scores or {}
        rest_sorted = sorted(
            rest,
            key=lambda n: (_hops.get(n, 10**6), -_rel.get(n, 0.0), -G.degree(n)),
        )
    else:
        rest_sorted = sorted(rest, key=lambda n: G.degree(n), reverse=True)
    ordered = [n for n in (seeds or []) if n in nodes] + rest_sorted
    for nid in ordered:
        d = G.nodes[nid]
        # Every LLM-derived field passes through sanitize_label before being
        # concatenated into MCP tool output (F-010): an attacker who controls
        # a corpus document can otherwise inject ANSI escapes or markup into
        # the model's context via source_file / source_location / community.
        entry = overlay.get(str(nid))
        learning_suffix = ""
        if entry:
            status = sanitize_label(str(entry.get("status", "")))
            if status:
                learning_suffix = f" learning={status}{':stale' if entry.get('stale') else ''}"
        source_file = str(d.get("source_file", ""))
        source_location = str(d.get("source_location", ""))
        anchor_suffix = ""
        if not source_file and not source_location:
            anchor = _best_anchor_neighbor(G, nid)
            if anchor:
                anchor_suffix = f" anchor={sanitize_label(anchor)}"
        line = (
            f"NODE {sanitize_label(d.get('label', nid))} "
            f"[src={sanitize_label(source_file)} "
            f"loc={sanitize_label(source_location)} "
            f"community={sanitize_label(str(d.get('community_name') or d.get('community', '')))}"
            f"{anchor_suffix}{learning_suffix}]"
        )
        lines.append(line)
    for u, v in edges:
        if u in nodes and v in nodes:
            raw = G[u][v]
            d = next(iter(raw.values()), {}) if isinstance(G, (nx.MultiGraph, nx.MultiDiGraph)) else raw
            context = d.get("context")
            context_suffix = f" context={sanitize_label(str(context))}" if context else ""
            line = (
                f"EDGE {sanitize_label(G.nodes[u].get('label', u))} "
                f"--{sanitize_label(str(d.get('relation', '')))} "
                f"[{sanitize_label(str(d.get('confidence', '')))}{context_suffix}]--> "
                f"{sanitize_label(G.nodes[v].get('label', v))}"
            )
            lines.append(line)
    output = "\n".join(lines)
    if len(output) > char_budget:
        cut_at = output[:char_budget].rfind("\n")
        cut_at = cut_at if cut_at > 0 else char_budget
        total_nodes = sum(1 for l in lines if l.startswith("NODE "))
        shown_nodes = output[:cut_at].count("\nNODE ") + (1 if output.startswith("NODE ") else 0)
        cut_count = total_nodes - shown_nodes
        output = (
            output[:cut_at]
            + f"\n... (truncated — {cut_count} more nodes cut by ~{token_budget}-token budget."
            f" Narrow with context_filter=['call'] or use get_node for a specific symbol)"
        )
    return output


def _query_graph_text(
    G: nx.Graph,
    question: str,
    *,
    mode: str = "bfs",
    depth: int = 3,
    token_budget: int = 2000,
    context_filters: list[str] | None = None,
    include_paths: list[str] | None = None,
    exclude_paths: list[str] | None = None,
) -> str:
    def _in_path_scope(nid: str) -> bool:
        if not include_paths and not exclude_paths:
            return True
        source = G.nodes[nid].get("source_file", "") or ""
        if include_paths and not any(source.startswith(p) for p in include_paths):
            return False
        if exclude_paths and any(source.startswith(p) for p in exclude_paths):
            return False
        return True

    terms = _query_terms(question)
    scored = [(s, nid) for s, nid in _score_nodes(G, terms) if _in_path_scope(nid)]
    start_nodes = _pick_seeds(scored, G=G, multi_term=len(set(terms)) > 1, terms=terms)
    correction_note = ""
    if not start_nodes:
        corrected_terms, corrections = _apply_vocabulary_corrections(G, terms)
        if corrections:
            scored = [(s, nid) for s, nid in _score_nodes(G, corrected_terms) if _in_path_scope(nid)]
            start_nodes = _pick_seeds(
                scored, G=G, multi_term=len(set(corrected_terms)) > 1, terms=corrected_terms
            )
            if start_nodes:
                pairs = ", ".join(f'"{o}" -> "{c}"' for o, c in corrections)
                correction_note = f"Note: no exact match; corrected possible typo(s) {pairs}"
    if not start_nodes:
        # Last resort: approximate-substring (Bitap-style) match against
        # whole labels, for typos of a compound span longer than the
        # n-gram vocabulary's 3-token window.
        start_nodes = [nid for nid in _fuzzy_substring_seeds(G, terms) if _in_path_scope(nid)]
        if start_nodes:
            correction_note = (
                "Note: no exact or corrected match; showing closest approximate "
                "matches (low confidence, verify before relying on this)"
            )
    if not start_nodes:
        # Final fallback (#5): a query and its target can share zero literal
        # or synonym-map terms (e.g. "log the user in" vs. a codebase that
        # only ever says "authenticate" with none of _SYNONYM_GROUPS' words
        # nearby). Silently a no-op unless the optional `embeddings` extra is
        # installed - see _embedding_seed_fallback's docstring.
        start_nodes = [nid for nid in _embedding_seed_fallback(G, question) if _in_path_scope(nid)]
        if start_nodes:
            correction_note = (
                "Note: no lexical/typo/substring match; used local embedding-based "
                "fallback (graphifyy[embeddings]) - low confidence, verify before relying on this"
            )
    if not start_nodes:
        return "No matching nodes found."
    resolved_filters, filter_source = _resolve_context_filters(question, context_filters)
    traversal_graph = _filter_graph_by_context(G, resolved_filters)
    nodes, edges = _dfs(traversal_graph, start_nodes, depth) if mode == "dfs" else _bfs(traversal_graph, start_nodes, depth)
    header_parts = [
        f"Traversal: {mode.upper()} depth={depth}",
        f"Start: {[G.nodes[n].get('label', n) for n in start_nodes]}",
    ]
    if correction_note:
        header_parts.append(correction_note)
    if resolved_filters:
        header_parts.append(f"Context: {', '.join(resolved_filters)} ({filter_source})")
    header_parts.append(f"{len(nodes)} nodes found")
    header = " | ".join(header_parts) + "\n\n"
    hop_distances = _hop_distances(nodes, edges, start_nodes)
    relevance_scores = {nid: score for score, nid in scored}
    return header + _subgraph_to_text(
        traversal_graph, nodes, edges, token_budget,
        seeds=start_nodes, hop_distances=hop_distances, relevance_scores=relevance_scores,
    )


def _find_node(G: nx.Graph, label: str) -> list[str]:
    """_find_node_core, with one vocabulary-correction retry (P5) if the
    label matches nothing verbatim.
    """
    result = _find_node_core(G, label)
    if result:
        return result
    corrected_terms, corrections = _apply_vocabulary_corrections(G, _search_tokens(label))
    if not corrections:
        return result
    return _find_node_core(G, " ".join(corrected_terms))


def _find_node_tiers(G: nx.Graph, label: str) -> tuple[list[str], list[str], list[str], list[str]]:
    """Same matching as `_find_node_core`, but returns each precedence tier
    (source_exact, exact, prefix, substring) separately instead of one flat
    list - lets callers tell "one clear winner" from "several nodes tied for
    the top tier" (ambiguity), which a flattened list can't distinguish.
    """
    term = " ".join(_search_tokens(label))
    if not term:
        return [], [], [], []
    source_exact: list[str] = []
    exact: list[str] = []
    prefix: list[str] = []
    substring: list[str] = []
    candidate_ids = _trigram_candidates(G, [term])
    node_iter = (
        G.nodes(data=True) if candidate_ids is None
        else ((nid, G.nodes[nid]) for nid in candidate_ids)
    )
    for nid, d in node_iter:
        norm_label = d.get("norm_label") or _strip_diacritics(d.get("label") or "").lower()
        bare_label = norm_label.rstrip("()")
        label_tokens = " ".join(_search_tokens(d.get("label") or ""))
        source_tokens = " ".join(_search_tokens(d.get("source_file") or ""))
        nid_lower = nid.lower()
        if term == source_tokens:
            source_exact.append(nid)
        elif term == norm_label or term == bare_label or term == label_tokens or term == nid_lower:
            exact.append(nid)
        elif (
            norm_label.startswith(term)
            or bare_label.startswith(term)
            or label_tokens.startswith(term)
            or nid_lower.startswith(term)
        ):
            prefix.append(nid)
        elif term in norm_label or term in label_tokens:
            substring.append(nid)

    if source_exact:
        query_basename = _strip_diacritics(Path(label).name).lower()
        preferred = [
            nid
            for nid in source_exact
            if str(G.nodes[nid].get("source_location", "")) == "L1"
            and _strip_diacritics(str(G.nodes[nid].get("label") or "")).lower()
            == query_basename
        ]
        if len(preferred) == 1:
            source_exact = preferred + [nid for nid in source_exact if nid != preferred[0]]

    return source_exact, exact, prefix, substring


def _find_node_core(G: nx.Graph, label: str) -> list[str]:
    """Return node IDs whose label or ID matches the search term (diacritic-insensitive).

    Results are ordered by precedence: exact source-file path match first, then
    exact (label/ID) match, then prefix match, then substring match.
    """
    source_exact, exact, prefix, substring = _find_node_tiers(G, label)
    return source_exact + exact + prefix + substring


def _find_node_tied_group(G: nx.Graph, label: str) -> list[str]:
    """Nodes tied for the top precedence tier `_find_node` would resolve to -
    i.e. the set that's "equally plausible" for a single-node lookup. A
    duplicate label (same section title in two files, an overloaded function
    name) can fill that tier with more than one node; callers that silently
    take matches[0] (`explain`, `get_neighbors`, `blast_radius`) pick one of
    these arbitrarily and never say so. This mirrors `_find_node`'s own
    vocabulary-correction retry so the "tied group" always matches whatever
    term `_find_node` actually resolved on.
    """
    for tier in _find_node_tiers(G, label):
        if tier:
            return tier
    corrected_terms, corrections = _apply_vocabulary_corrections(G, _search_tokens(label))
    if not corrections:
        return []
    for tier in _find_node_tiers(G, " ".join(corrected_terms)):
        if tier:
            return tier
    return []
