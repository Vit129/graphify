"""Registry tests for extractors migrated out of extract.py (see extractors/MIGRATION.md).

For each migrated language: (1) importable from its graphify.extractors.<mod> module,
(2) extract.py's facade re-export is the SAME function object (not a copy), (3) extract.py's
`_DISPATCH` dict routes the language's extension(s) to that same object. Purely structural —
behavioral coverage for each language lives in test_languages.py / test_dotnet.py / etc.
"""
from __future__ import annotations

from pathlib import Path

from graphify.extract import _DISPATCH, _get_extractor


def test_blade_migrated():
    from graphify.extractors.blade import extract_blade as module_fn
    from graphify.extract import extract_blade as facade_fn
    assert module_fn is facade_fn
    # Blade is dispatched by filename suffix (`.blade.php`), not a plain extension key.
    assert _get_extractor(Path("Widget.blade.php")) is module_fn


def test_zig_migrated():
    from graphify.extractors.zig import extract_zig as module_fn
    from graphify.extract import extract_zig as facade_fn
    assert module_fn is facade_fn
    assert _DISPATCH[".zig"] is module_fn


def test_elixir_migrated():
    from graphify.extractors.elixir import extract_elixir as module_fn
    from graphify.extract import extract_elixir as facade_fn
    assert module_fn is facade_fn
    assert _DISPATCH[".ex"] is module_fn


def test_razor_migrated():
    from graphify.extractors.razor import extract_razor as module_fn
    from graphify.extract import extract_razor as facade_fn
    assert module_fn is facade_fn
    assert _DISPATCH[".razor"] is module_fn
    assert _DISPATCH[".cshtml"] is module_fn


def test_apex_migrated():
    from graphify.extractors.apex import extract_apex as module_fn
    from graphify.extract import extract_apex as facade_fn
    assert module_fn is facade_fn
    assert _DISPATCH[".cls"] is module_fn
    assert _DISPATCH[".trigger"] is module_fn
