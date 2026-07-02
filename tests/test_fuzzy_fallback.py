"""Tests for P5 (typo/abbreviation cascade fallback).

Covers _correct_term's two correction paths (Damerau-Levenshtein for typos,
ordered-subsequence for abbreviations) and the retry wiring in
_query_graph_text / _find_node — only fires when the primary lexical pass
finds nothing, and never over-corrects a query that has no reasonable match.
"""
import networkx as nx

from graphify.serve import (
    _correct_term,
    _damerau_levenshtein,
    _subsequence_score,
    _apply_vocabulary_corrections,
    _query_graph_text,
    _find_node,
    _get_vocabulary,
    _fuzzy_substring_distance,
    _fuzzy_substring_seeds,
    _score_nodes,
)


def _make_graph() -> nx.Graph:
    G = nx.Graph()
    G.add_node("n1", label="handleUserSession", source_file="auth.ts", community=0)
    G.add_node("n2", label="logoutUser", source_file="auth.ts", community=0)
    G.add_edge("n1", "n2", relation="calls", confidence="EXTRACTED")
    return G


# --- _damerau_levenshtein / _subsequence_score (pure algorithm checks) ---

def test_damerau_levenshtein_omission_is_distance_one():
    assert _damerau_levenshtein("sesion", "session") == 1


def test_damerau_levenshtein_adjacent_transposition_is_distance_one():
    """Classic "i before e" slip — plain Levenshtein would charge 2."""
    assert _damerau_levenshtein("recieve", "receive") == 1


def test_damerau_levenshtein_unrelated_words_score_high():
    assert _damerau_levenshtein("gud", "getuserdata") > 4


def test_subsequence_score_matches_abbreviation():
    assert _subsequence_score("gud", "getuserdata") is not None


def test_subsequence_score_none_when_char_missing():
    assert _subsequence_score("resieve", "receive") is None


# --- _correct_term ---

def test_correct_term_fixes_omission_typo():
    G = _make_graph()
    assert _correct_term("sesion", G) == "session"


def test_correct_term_fixes_transposition_typo():
    G = nx.Graph()
    G.add_node("n1", label="receiveOrder", source_file="orders.ts", community=0)
    assert _correct_term("recieve", G) == "receive"


def test_correct_term_fixes_cross_word_abbreviation():
    """"hus" abbreviates handleUserSession across three sub-words — the
    per-sub-word vocabulary alone ("handle"/"user"/"session") can't satisfy
    this; the whole-label form must also be a candidate.
    """
    G = _make_graph()
    assert _correct_term("hus", G) == "handleusersession"


def test_correct_term_fixes_compound_span_typo():
    """A typo of a 2-token compound span ("wholesals" for the two adjacent
    sub-words "whole"+"sales") is neither a single sub-word typo nor a
    whole-label abbreviation — needs the n-gram-span vocabulary entries.
    """
    G = nx.Graph()
    G.add_node("n1", label="WholeSalesReport", source_file="report.py", community=0)
    assert _correct_term("wholesals", G) == "wholesales"


def test_correct_term_leaves_already_correct_term_alone():
    G = _make_graph()
    assert _correct_term("session", G) is None


def test_correct_term_returns_none_for_unfixable_term():
    G = _make_graph()
    assert _correct_term("zzzznonexistentqqqq", G) is None


def test_correct_term_returns_none_for_short_terms():
    """len<3 terms are too ambiguous to correct confidently."""
    G = _make_graph()
    assert _correct_term("ab", G) is None


# --- _apply_vocabulary_corrections ---

def test_apply_vocabulary_corrections_only_reports_changed_terms():
    G = _make_graph()
    corrected, corrections = _apply_vocabulary_corrections(G, ["user", "sesion"])
    assert corrected == ["user", "session"]
    assert corrections == [("sesion", "session")]


def test_apply_vocabulary_corrections_empty_when_nothing_to_fix():
    G = _make_graph()
    corrected, corrections = _apply_vocabulary_corrections(G, ["user", "session"])
    assert corrected == ["user", "session"]
    assert corrections == []


# --- _query_graph_text retry wiring ---

def test_query_graph_text_recovers_from_typo_with_note():
    G = _make_graph()
    text = _query_graph_text(G, "sesion")
    assert "No matching nodes found." not in text
    assert "handleUserSession" in text
    assert 'no exact match' in text.lower()
    assert '"sesion" -> "session"' in text


def test_query_graph_text_no_correction_note_when_primary_pass_succeeds():
    """A query that already matches on the first pass must not show a
    correction note or pay the correction-lookup cost.
    """
    G = _make_graph()
    text = _query_graph_text(G, "session")
    assert "Note:" not in text


def test_query_graph_text_stays_empty_for_unfixable_query():
    G = _make_graph()
    assert _query_graph_text(G, "zzzznonexistentqqqq") == "No matching nodes found."


# --- _find_node retry wiring ---

def test_find_node_recovers_from_typo():
    G = _make_graph()
    assert _find_node(G, "sesion") == ["n1"]


def test_find_node_recovers_from_abbreviation():
    G = _make_graph()
    assert _find_node(G, "hus") == ["n1"]


def test_find_node_stays_empty_for_unfixable_query():
    G = _make_graph()
    assert _find_node(G, "zzzznonexistentqqqq") == []


def test_find_node_exact_match_unaffected_by_correction_path():
    G = _make_graph()
    assert _find_node(G, "handleUserSession") == ["n1"]


# --- _get_vocabulary ---

def test_get_vocabulary_includes_both_subwords_and_whole_label():
    G = _make_graph()
    typo_words, _, abbr_words, _ = _get_vocabulary(G)
    for words in (typo_words, abbr_words):
        assert "user" in words
        assert "session" in words
        assert "handleusersession" in words


def test_get_vocabulary_ngram_spans_only_feed_typo_pool_not_abbreviation_pool():
    """A 2-token span like "handleuser" must help the typo (edit-distance)
    path but must NOT be a candidate in the abbreviation (subsequence) path
    — it's shorter than the true whole-label target, so if it were allowed
    into the abbreviation pool it would outscore the correct match purely
    for being shorter (a scoring-formula artifact, not a real target).
    """
    G = _make_graph()
    typo_words, _, abbr_words, _ = _get_vocabulary(G)
    assert "handleuser" in typo_words
    assert "handleuser" not in abbr_words


def test_get_vocabulary_is_cached_on_graph():
    G = _make_graph()
    first = _get_vocabulary(G)
    second = _get_vocabulary(G)
    assert first is second


# --- _fuzzy_substring_distance / _fuzzy_substring_seeds (Bitap-style last resort) ---
#
# "wholesalesdivisionrepot" (a typo dropping one "t" from "...Report") spans
# 4 tokens (whole+sales+division+report) — deliberately one token past the
# n-gram vocabulary's 2-3 token window, and NOT a literal substring/prefix
# of the real text (verified: an earlier draft of these tests used a typo
# that was actually a truncated *prefix* of the real word, which the
# ordinary substring tier already resolves — that tested nothing new).

def test_fuzzy_substring_distance_finds_compound_span_inside_long_text():
    text = "ts1territoryname" + "wholesalesdivisionreport"
    assert _fuzzy_substring_distance("wholesalesdivisionrepot", text) <= 1


def test_fuzzy_substring_distance_rejects_unrelated_pattern():
    text = "ts16947601territorylevel2code22namewholesales"
    assert _fuzzy_substring_distance("zzzznonexistentqqqq", text) > 10


def test_fuzzy_substring_seeds_finds_node_when_ngram_window_is_exceeded():
    G = nx.Graph()
    G.add_node(
        "n1",
        label="[TS-1] Territory -> name=WholeSalesDivisionReport",
        source_file="report.py", community=0,
    )
    G.add_node("n2", label="unrelatedOtherThing", source_file="other.py", community=0)
    # Sanity-check the premise before asserting the outcome: the primary
    # pass and the n-gram/typo path must both fail first, or this test
    # isn't exercising the Bitap tier at all.
    assert _score_nodes(G, ["wholesalesdivisionrepot"]) == []
    assert _correct_term("wholesalesdivisionrepot", G) is None
    seeds = _fuzzy_substring_seeds(G, ["wholesalesdivisionrepot"])
    assert seeds == ["n1"]


def test_fuzzy_substring_seeds_empty_for_unrelated_query():
    G = nx.Graph()
    G.add_node("n1", label="handleUserSession", source_file="auth.ts", community=0)
    assert _fuzzy_substring_seeds(G, ["zzzznonexistentqqqq"]) == []


def test_fuzzy_substring_seeds_skips_terms_shorter_than_min_len():
    """Very short terms would approximately-match almost everything —
    guarded out rather than flooding the fallback with noise.
    """
    G = nx.Graph()
    G.add_node("n1", label="handleUserSession", source_file="auth.ts", community=0)
    assert _fuzzy_substring_seeds(G, ["ab"]) == []


# --- _query_graph_text: full 3-tier cascade ---

def test_query_graph_text_falls_through_to_bitap_tier_when_ngram_insufficient():
    """End-to-end: a compound-span typo longer than the n-gram window must
    still resolve, via the third (Bitap) tier, with an explicit low-
    confidence note distinct from the ordinary typo-correction note.
    """
    G = nx.Graph()
    G.add_node(
        "n1",
        label="[TS-1] Territory -> name=WholeSalesDivisionReport",
        source_file="report.py", community=0,
    )
    text = _query_graph_text(G, "wholesalesdivisionrepot")
    assert "No matching nodes found." not in text
    assert "n1" not in text  # sanity: node id shouldn't leak into label output
    assert "low confidence" in text.lower()
