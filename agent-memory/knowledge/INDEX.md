# Knowledge Index — graphify

## Files

| File | Domain | Tags | Summary |
|------|--------|------|---------|
| architecture/feature-provenance.md | Search/Matching, Language Coverage | Zoekt, DeusData, SocratiCode, fzf, zoxide, ripgrep, harness-terminal, Bitap, agrep, BM25, camelCase, typo, fuzzy, n-gram, compound-span, YAML, Robot Framework, CSS, HTML, LSP, tree-sitter, P1, P2, P3, P4, P5, P6, P7 | Where each search/matching feature's concept came from: tokenization fix traced to DeusData's FTS5 tokenizer, typo fallback traced to a 4-way algorithm comparison (Damerau-Levenshtein adopted, fzf's DP considered and rejected for this domain, zoxide's frecency rejected as solving a different problem), fuzzy-abbreviation matcher ported directly from harness-terminal's own FuzzyPathResolver.swift, compound-span typo gap closed via bounded n-gram vocabulary spans + a Bitap/agrep-style approximate-substring-search fallback, `_score_nodes`'s hand-rolled tier system replaced with real BM25 (superseding two earlier, shallower P1 fix attempts), full semantic/embedding search evaluated and rejected on infra cost, LSP evaluated and rejected as a bulk-extraction mechanism (DeusData/SocratiCode both use tree-sitter as the primary coverage mechanism, LSP only as an optional enhancement on ~9 languages), YAML + Robot Framework + CSS + HTML extractors added as new bespoke `extractors/` modules closing the largest real-project format gaps found by direct audit, plus two zero-cost wins (`.resource`->`extract_robot`, `.gs`->`extract_js`) found by diffing the full file census instead of guessing at formats |

## Source Map

| Knowledge | Implementation Files |
|-----------|---------------------|
| architecture/feature-provenance.md | `graphify/serve.py` (`_search_tokens`, `_score_nodes`, `_get_bm25_corpus`, `_bm25_idf`, `_pick_seeds`, `_query_terms`, `_correct_term`, `_get_vocabulary`, `_damerau_levenshtein`, `_subsequence_score`, `_fuzzy_substring_distance`, `_fuzzy_substring_seeds`), `graphify/extract.py` (`_js_extra_walk`, `_DISPATCH`), `graphify/extractors/yaml_.py`, `graphify/extractors/robot.py`, `graphify/extractors/css.py`, `graphify/extractors/html.py` |
