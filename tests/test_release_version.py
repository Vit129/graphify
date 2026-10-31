import json
import shutil
import uuid
from pathlib import Path

from scripts.set_release_version import update_release_version


def test_release_version_updates_semver_and_build_surfaces():
    root = Path(__file__).resolve().parents[1]
    temp = root / ".tmp" / f"release-version-{uuid.uuid4().hex}"
    temp.mkdir(parents=True)
    try:
        (temp / "pyproject.toml").write_text('version = "0.27.0"\n', encoding="utf-8")
        (temp / "version.json").write_text('{"version":4,"updated":"2026-01-01"}\n', encoding="utf-8")
        (temp / "graphify").mkdir()
        (temp / "graphify/git_update_check.py").write_text("CURRENT_VERSION = 4\n", encoding="utf-8")

        update_release_version(temp, "0.27.1")

        assert 'version = "0.27.1"' in (temp / "pyproject.toml").read_text(encoding="utf-8")
        assert json.loads((temp / "version.json").read_text(encoding="utf-8"))["version"] == 5
        assert "CURRENT_VERSION = 5" in (temp / "graphify/git_update_check.py").read_text(encoding="utf-8")
    finally:
        shutil.rmtree(temp)
