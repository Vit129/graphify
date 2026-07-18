"""Git-clone update check for the graphify CLI.

Separate track from ``update_check.py``'s PyPI-upstream awareness: this
module is about *this fork's own* releases, for users who installed by
`git clone` rather than a package manager. It compares this checkout's
``CURRENT_VERSION`` against ``version.json`` on this repo's GitHub `main`
branch and, only in an interactive terminal with a clean working tree,
asks for y/n confirmation before running `git pull origin main`. It never
pulls on its own.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

CURRENT_VERSION = 2  # bump alongside version.json at the repo root whenever a feature ships
REPO = "Vit129/graphify"
VERSION_URL = f"https://raw.githubusercontent.com/{REPO}/main/version.json"
FETCH_TIMEOUT_SECONDS = 2.5
CHECK_INTERVAL_SECONDS = 24 * 60 * 60
CONFIG_DIR = Path.home() / ".config" / "graphify"
CONFIG_PATH = CONFIG_DIR / "config.json"
DISMISS_FILE = CONFIG_DIR / "update-dismissed"


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


def _should_check(config: dict) -> bool:
    last_checked = config.get("lastGitUpdateCheckAt")
    if not last_checked:
        return True
    try:
        last = datetime.fromisoformat(last_checked)
    except ValueError:
        return True
    if last.tzinfo is None:
        last = last.replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - last).total_seconds() >= CHECK_INTERVAL_SECONDS


def _find_git_root(start_dir: Path) -> Path | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=start_dir,
            capture_output=True,
            text=True,
            timeout=3,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    top = result.stdout.strip()
    return Path(top) if top else None


def _is_working_tree_dirty(git_root: Path) -> bool:
    try:
        result = subprocess.run(
            ["git", "status", "--short", "--untracked-files=normal"],
            cwd=git_root,
            capture_output=True,
            text=True,
            timeout=3,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return result.returncode == 0 and bool(result.stdout.strip())


def _fetch_remote_version() -> tuple[dict | None, str | None]:
    try:
        with urllib.request.urlopen(VERSION_URL, timeout=FETCH_TIMEOUT_SECONDS) as response:
            data = json.load(response)
        if not isinstance(data.get("version"), int):
            return None, 'version.json missing an integer "version" field'
        return data, None
    except Exception as error:  # noqa: BLE001 - best-effort network check, never fatal
        return None, str(error)


def _read_dismissed_version() -> int | None:
    try:
        return int(DISMISS_FILE.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return None


def _write_dismissed_version(version: int) -> None:
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        DISMISS_FILE.write_text(f"{version}\n", encoding="utf-8")
    except OSError:
        pass


def check_git_clone_update(start_dir: Path | None = None, *, force: bool = False) -> None:
    """Best-effort, non-fatal: never raises, never blocks a non-interactive run
    for more than the fetch timeout, never pulls without explicit y/n
    confirmation, never pulls a dirty working tree.
    """
    if os.environ.get("CI"):
        return
    try:
        git_root = _find_git_root(start_dir or Path(__file__).resolve().parent)
        if git_root is None:
            return

        config = _read_config()
        if not force and not _should_check(config):
            return
        _write_config({"lastGitUpdateCheckAt": datetime.now(timezone.utc).isoformat()})

        data, error = _fetch_remote_version()
        if error:
            print(f"graphify update check failed: {error}", file=sys.stderr)
            return

        remote_version = data["version"]
        if remote_version <= CURRENT_VERSION:
            return

        dismissed = _read_dismissed_version()
        if dismissed is not None and dismissed >= remote_version:
            return

        updated = data.get("updated", "unknown date")
        summary = data.get("summary", "")
        version_label = f"v{CURRENT_VERSION} -> v{remote_version}"

        if _is_working_tree_dirty(git_root):
            print(
                f"graphify update available ({version_label}): working tree has "
                f"uncommitted changes, pull manually later.",
                file=sys.stderr,
            )
            return

        print(f"graphify update available ({version_label}, {updated}): {summary}", file=sys.stderr)

        if not sys.stdin.isatty() or not sys.stdout.isatty():
            _write_dismissed_version(remote_version)
            return

        try:
            answer = input("Pull now with `git pull origin main`? [y/N] ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            answer = ""
            print()

        if answer not in ("y", "yes"):
            _write_dismissed_version(remote_version)
            return

        result = subprocess.run(
            ["git", "pull", "origin", "main"],
            cwd=git_root,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            print(result.stdout.strip() or "git pull complete.")
        else:
            print(
                "git pull failed — resolve manually:\n" + (result.stderr or result.stdout).strip(),
                file=sys.stderr,
            )
    except Exception:
        return
