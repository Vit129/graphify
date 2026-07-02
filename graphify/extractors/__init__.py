"""Per-language extractors, incrementally migrated out of graphify/extract.py.

Dispatch still flows through graphify.extract (the facade re-exports every
moved name), so importing from graphify.extract keeps working unchanged.
LANGUAGE_EXTRACTORS is the registry seed; wiring dispatch through it is a
later, separate step. See MIGRATION.md for how to port another language.
"""
from __future__ import annotations

from pathlib import Path
from typing import Callable

from graphify.extractors.blade import extract_blade
from graphify.extractors.css import extract_css
from graphify.extractors.elixir import extract_elixir
from graphify.extractors.html import extract_html
from graphify.extractors.razor import extract_razor
from graphify.extractors.robot import extract_robot
from graphify.extractors.yaml_ import extract_yaml
from graphify.extractors.zig import extract_zig

LANGUAGE_EXTRACTORS: dict[str, Callable[[Path], dict]] = {
    "blade": extract_blade,
    "css": extract_css,
    "elixir": extract_elixir,
    "html": extract_html,
    "razor": extract_razor,
    "robot": extract_robot,
    "yaml": extract_yaml,
    "zig": extract_zig,
}
