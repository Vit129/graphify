#!/usr/bin/env python3
"""Update Graphify's package semver and editable-check build counter."""
import json
import re
import sys
from datetime import date
from pathlib import Path


def update_release_version(root: Path, version: str) -> None:
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        raise ValueError("Expected semver X.Y.Z")
    pyproject = root / "pyproject.toml"
    text = pyproject.read_text(encoding="utf-8")
    updated, count = re.subn(r'^version = "\d+\.\d+\.\d+"$', f'version = "{version}"', text, count=1, flags=re.MULTILINE)
    if count != 1:
        raise ValueError("Could not update pyproject.toml version")
    pyproject.write_text(updated, encoding="utf-8")

    version_file = root / "version.json"
    data = json.loads(version_file.read_text(encoding="utf-8"))
    data["version"] += 1
    data["updated"] = date.today().isoformat()
    version_file.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    module = root / "graphify" / "git_update_check.py"
    source = module.read_text(encoding="utf-8")
    updated, count = re.subn(r"^CURRENT_VERSION = \d+", f"CURRENT_VERSION = {data['version']}", source, count=1, flags=re.MULTILINE)
    if count != 1:
        raise ValueError("Could not update CURRENT_VERSION in graphify/git_update_check.py")
    module.write_text(updated, encoding="utf-8")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python3 scripts/set_release_version.py X.Y.Z")
    update_release_version(Path(__file__).resolve().parents[1], sys.argv[1])
