# P12 — CODE_EXTENSIONS Classifier Gap (critical: real CLI never saw the new languages)

Status: **Done** (2026-07-02)
Priority: **P0** — every extractor added this session (P2, P6, P7, P8, P10, P11) was unreachable
from the actual `graphify extract`/`graphify update` CLI commands until this fix
Owner surface: `graphify/detect.py` (`CODE_EXTENSIONS`, `DOC_EXTENSIONS`)
Created: 2026-07-02
Depends on: all of P2/P6/P7/P8/P10/P11

---

## Why — how this was missed for the entire session

`graphify/extract.py`'s `_DISPATCH` table (which extractor handles which extension) and
`graphify/detect.py`'s `CODE_EXTENSIONS` set (which extensions the file-discovery walker treats
as "code, worth AST-extracting") are two **separate** allowlists. Every validation this session
called `graphify.extract.extract()` directly with a hand-built file list — which only goes through
`_DISPATCH` and never touches `detect.py` at all. The real CLI (`graphify extract`/`graphify
update`) discovers files via `detect()` first, which calls `classify_file()` per file; only files
classified `FileType.CODE` ever become `code_files` and get passed to `extract()`.

`detect.py`'s `CODE_EXTENSIONS` was never updated this whole session. Consequence, verified with
`classify_file()` directly before the fix:

| Extension | Classified as (before) | Real effect |
|---|---|---|
| `.robot` `.resource` `.css` `.scss` `.feature` `.toml` `.fish` `.hook` `.gs` `.htm` | `None` | File invisible to *every* pipeline — not code, not document, not anything. Silently dropped by `detect()`. |
| `.yaml` `.yml` `.html` | `FileType.DOCUMENT` | Routed to the LLM-backed semantic/document path instead of the new free local `extract_yaml`/`extract_html` AST extractors — worked, but wrong pipeline, wrong cost profile, and not what the P2/P7 plan docs claimed ("no changes needed to search, extracted locally with no API calls"). |

Every "0 errors" and "N nodes extracted" claim made in P2/P6/P7/P8/P10/P11's real-project
validation was **true for `extract()` called directly** but **not representative of what a real
user running `graphify extract .` would get** — those files would never have reached `extract()`
at all (or, for yaml/html, would have gone through the LLM path and required an API key). This
was caught only when asked to "แก้ปัญหาตัวสุดท้าย" and re-examining the SocratiCode-fallback
comparison led to checking the actual file-discovery path instead of assuming `_DISPATCH`
registration was sufficient.

## What's done

- Added the 10 fully-missing extensions to `CODE_EXTENSIONS`: `.css`, `.scss`, `.html`, `.htm`,
  `.robot`, `.resource`, `.feature`, `.toml`, `.fish`, `.hook`, `.gs`.
- Moved `.html`, `.yaml`, `.yml` from `DOC_EXTENSIONS` to `CODE_EXTENSIONS` — `classify_file()`
  checks `CODE_EXTENSIONS` first, so this correctly routes them to the free local AST extractors
  built this session instead of the LLM document path.
- `graphify/watch.py` and `graphify/analyze.py` both import `CODE_EXTENSIONS` from `detect.py`
  (single source of truth, no duplicate allowlists found elsewhere) — the fix propagates to
  incremental watch-mode and analysis without any other code change.
- Re-derived `tests/test_manifest_ingest.py::test_manifests_classify_as_code_not_document` — its
  "a generic yaml stays a document" assertion was correct *when written* (before `extract_yaml`
  existed, no yaml had a deterministic parser except recognized manifests) and is now stale;
  updated to assert `FileType.CODE` with a comment explaining why.
- Full suite: 2855 passed, 0 failures (no count change — this is a classification-routing fix,
  not new extraction code).
- **Real end-to-end re-validation using the actual `detect()` -> `code_files` -> `extract()` path**
  (not calling `extract()` directly, unlike every prior validation this session):
  - `cpi-qa-automation`: 101 code files detected (7 of them `.yaml`/`.yml`, previously would have
    gone to the LLM document path or been silently dropped depending on exact filename), 709
    nodes, 0 errors.
  - `harness-terminal`: 643 code files detected, including 12 `.robot`, 1 `.resource`, 2 `.fish`,
    1 `.toml` — all of which `classify_file()` returned `None` for before this fix, meaning
    `detect()` would have silently excluded every one of them from `graphify extract`/`graphify
    update`'s output.

## Lesson

Validating a new extractor by calling `graphify.extract.extract()` directly proves the extractor
itself is correct, but proves nothing about whether a real user's `graphify extract`/`graphify
update` invocation would ever reach it. Two allowlists needed updating for each new language this
session — `_DISPATCH` (which extractor) and `CODE_EXTENSIONS` (whether the file is even offered to
an extractor) — and only one was consistently touched. Future language additions must update both,
and validation should include at least one real run through `detect()`, not just `extract()`.
