#!/usr/bin/env python3
"""Check the package semver, changelog, and editable-check build counter agree."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
version_match = re.search(r'^version = "(\d+\.\d+\.\d+)"$', pyproject, re.MULTILINE)
if not version_match:
    raise SystemExit("pyproject.toml has no valid semver version")
version = version_match.group(1)

changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
latest = re.search(r'^## \[(\d+\.\d+\.\d+)\]', changelog, re.MULTILINE)
if not latest or latest.group(1) != version:
    raise SystemExit(f"CHANGELOG.md latest version {latest.group(1) if latest else 'missing'} does not match {version}")

release = json.loads((ROOT / "version.json").read_text(encoding="utf-8"))
module = (ROOT / "graphify/git_update_check.py").read_text(encoding="utf-8")
current = re.search(r"^CURRENT_VERSION = (\d+)", module, re.MULTILINE)
if not isinstance(release.get("version"), int) or not current or int(current.group(1)) != release["version"]:
    raise SystemExit("version.json build counter does not match graphify/git_update_check.py")

print(f"version surfaces agree: {version} (build {release['version']})")
