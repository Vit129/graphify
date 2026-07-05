"""Self-update check for the graphify CLI.

PyPI-backed sibling of the npm-based ``update-check.mjs`` used by
agy-plugin-cc/agy-plugin-codex: bounded foreground version check (so most
invocations pay nothing thanks to the 24h cache), detached background install
so a slow `uv tool upgrade` never blocks the command that triggered it.

Fork notice: PACKAGE_NAME ("graphifyy") is upstream's own PyPI package, a different
codebase from this fork — this fork isn't published to PyPI at all (see README's
"Source-only fork" note). A "newer" PyPI release is a signal that upstream shipped
something, not that this fork is out of date, so autoUpdate defaults to False and the
default message points at this fork's own GitHub releases instead of suggesting an
install command that would silently replace this fork with upstream's package.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

PACKAGE_NAME = "graphifyy"
CHECK_INTERVAL_SECONDS = 24 * 60 * 60
PYPI_TIMEOUT_SECONDS = 2.0
CONFIG_DIR = Path.home() / ".config" / "graphify"
CONFIG_PATH = CONFIG_DIR / "config.json"
INSTALL_LOG_PATH = CONFIG_DIR / "update-install.log"


def _version_tuple(version: str) -> tuple[int, ...]:
    """Parse a dotted version string into a comparable integer tuple.

    Duplicated (not imported) from graphify.__main__._version_tuple to keep this
    module import-cycle-free — __main__ imports this module, not the other way.
    """
    parts: list[int] = []
    for segment in str(version).split("."):
        digits = ""
        for ch in segment:
            if ch.isdigit():
                digits += ch
            else:
                break
        parts.append(int(digits) if digits else 0)
    return tuple(parts)


def _is_newer(candidate: str, current: str) -> bool:
    return _version_tuple(candidate) > _version_tuple(current)


def _read_config() -> dict:
    try:
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _write_config(patch: dict) -> None:
    config = _read_config()
    config.update(patch)
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")


def _should_check(config: dict, force: bool) -> bool:
    if force:
        return True
    last_checked = config.get("lastUpdateCheckAt")
    if not last_checked:
        return True
    try:
        last = datetime.fromisoformat(last_checked)
    except ValueError:
        return True
    if last.tzinfo is None:
        last = last.replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - last).total_seconds() >= CHECK_INTERVAL_SECONDS


def _resolve_auto_update(config: dict) -> bool:
    # Defaults to False (not True): PACKAGE_NAME ("graphifyy" on PyPI) is upstream's own,
    # unrelated package — a "newer" PyPI release there is not this fork's release, so silently
    # replacing this fork's install with it by default would be installing the wrong software.
    # Opt-in only, via `{"autoUpdate": true}` in ~/.config/graphify/config.json.
    value = config.get("autoUpdate")
    return False if value is None else bool(value)


def _latest_version() -> str | None:
    url = f"https://pypi.org/pypi/{PACKAGE_NAME}/json"
    try:
        with urllib.request.urlopen(url, timeout=PYPI_TIMEOUT_SECONDS) as response:
            payload = json.load(response)
        return payload["info"]["version"]
    except Exception:
        return None


def _upgrade_command() -> list[str] | None:
    # ponytail: picks the first tool found on PATH rather than introspecting which
    # one actually installed the running copy — README's recommended install path
    # (uv tool) wins first, pipx second, else the caller falls back to a manual
    # `pip install -U` nudge instead of guessing further.
    if shutil.which("uv"):
        return ["uv", "tool", "upgrade", PACKAGE_NAME]
    if shutil.which("pipx"):
        return ["pipx", "upgrade", PACKAGE_NAME]
    return None


def _run_upgrade_in_background(command: list[str]) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(INSTALL_LOG_PATH, "a", encoding="utf-8") as log:
        subprocess.Popen(
            command,
            stdout=log,
            stderr=log,
            stdin=subprocess.DEVNULL,
            start_new_session=True,
        )


def check_for_update(current_version: str, *, force: bool = False) -> None:
    """Best-effort, non-fatal: warn (and optionally auto-upgrade) if PyPI has a
    newer graphifyy release. Prints at most one status line; never raises —
    a network hiccup or corrupt cache file must never break the CLI.
    """
    if os.environ.get("CI") or current_version in ("unknown", ""):
        return
    try:
        config = _read_config()
        if not _should_check(config, force):
            return
        latest = _latest_version()
        _write_config({"lastUpdateCheckAt": datetime.now(timezone.utc).isoformat()})
        if not latest or not _is_newer(latest, current_version):
            return

        if not _resolve_auto_update(config):
            print(
                f"  upstream graphify (PyPI `{PACKAGE_NAME}`) has released {latest}; "
                f"this fork is at {current_version}. This fork isn't published to PyPI — "
                f"see https://github.com/Vit129/graphify for this fork's own releases, "
                f"or set {{\"autoUpdate\": true}} in ~/.config/graphify/config.json to "
                f"auto-run `uv tool upgrade {PACKAGE_NAME}` (installs upstream's package, "
                f"not this fork) when this fires.",
                file=sys.stderr,
            )
            return

        command = _upgrade_command()
        if command is None:
            print(
                f"  upstream graphify (PyPI `{PACKAGE_NAME}`) released {latest}; "
                f"autoUpdate is enabled but neither uv nor pipx is on PATH to install it.",
                file=sys.stderr,
            )
            return

        _run_upgrade_in_background(command)
        print(
            f"  autoUpdate is enabled: installing upstream's `{PACKAGE_NAME}` {latest} "
            f"in the background (this replaces this fork's install with upstream's — "
            f"see {INSTALL_LOG_PATH}).",
            file=sys.stderr,
        )
    except Exception:
        return
