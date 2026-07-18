"""Git-clone update check: separate track from update_check.py's PyPI-upstream
awareness. Pins the pure logic (cache interval, dismissal, notice formatting)
and that pulling only ever happens after explicit y/n confirmation on a clean
tree — never that a real GitHub/git round-trip happens.
"""
from __future__ import annotations

import subprocess

import graphify.git_update_check as guc


def _isolate_config(monkeypatch, tmp_path):
    config_dir = tmp_path / "config"
    monkeypatch.setattr(guc, "CONFIG_DIR", config_dir)
    monkeypatch.setattr(guc, "CONFIG_PATH", config_dir / "config.json")
    monkeypatch.setattr(guc, "DISMISS_FILE", config_dir / "update-dismissed")
    # Pin the local version independent of the real module constant - tests
    # below mock the remote as version 2 to mean "newer than local checkout".
    # Without this, bumping the real CURRENT_VERSION alongside a release (as
    # the constant's own comment says to do) makes "remote 2 > local" false
    # the moment CURRENT_VERSION reaches 2, and every check-update test here
    # silently no-ops instead of testing the update flow at all.
    monkeypatch.setattr(guc, "CURRENT_VERSION", 1)


def test_should_check_true_on_first_run():
    assert guc._should_check({}) is True


def test_should_check_false_within_interval(monkeypatch):
    import datetime as real_datetime

    class FrozenDatetime(real_datetime.datetime):
        @classmethod
        def now(cls, tz=None):
            return real_datetime.datetime(2026, 1, 1, tzinfo=tz)

    monkeypatch.setattr(guc, "datetime", FrozenDatetime)
    config = {"lastGitUpdateCheckAt": "2026-01-01T00:00:00+00:00"}
    assert guc._should_check(config) is False


def test_dismissed_version_roundtrip(monkeypatch, tmp_path):
    _isolate_config(monkeypatch, tmp_path)
    assert guc._read_dismissed_version() is None
    guc._write_dismissed_version(5)
    assert guc._read_dismissed_version() == 5


def test_check_skips_when_not_a_git_checkout(monkeypatch, tmp_path):
    monkeypatch.setattr(guc, "_find_git_root", lambda start_dir: None)
    called = {"fetched": False}

    def fake_fetch():
        called["fetched"] = True
        return None, "should not be called"

    monkeypatch.setattr(guc, "_fetch_remote_version", fake_fetch)
    guc.check_git_clone_update(force=True)
    assert called["fetched"] is False


def test_check_reports_dirty_tree_without_prompting(monkeypatch, tmp_path, capsys):
    _isolate_config(monkeypatch, tmp_path)
    monkeypatch.setattr(guc, "_find_git_root", lambda start_dir: tmp_path)
    monkeypatch.setattr(guc, "_fetch_remote_version", lambda: ({"version": 2, "updated": "2026-01-01", "summary": "x"}, None))
    monkeypatch.setattr(guc, "_is_working_tree_dirty", lambda git_root: True)

    def fail_if_called(*args, **kwargs):
        raise AssertionError("should not prompt on a dirty tree")

    monkeypatch.setattr("builtins.input", fail_if_called)
    guc.check_git_clone_update(force=True)
    assert "uncommitted changes" in capsys.readouterr().err


def test_check_no_prompt_when_not_interactive(monkeypatch, tmp_path):
    _isolate_config(monkeypatch, tmp_path)
    monkeypatch.setattr(guc, "_find_git_root", lambda start_dir: tmp_path)
    monkeypatch.setattr(guc, "_fetch_remote_version", lambda: ({"version": 2, "updated": "2026-01-01", "summary": "x"}, None))
    monkeypatch.setattr(guc, "_is_working_tree_dirty", lambda git_root: False)
    monkeypatch.setattr(guc.sys.stdin, "isatty", lambda: False)

    def fail_if_called(*args, **kwargs):
        raise AssertionError("should not prompt in a non-interactive context")

    monkeypatch.setattr("builtins.input", fail_if_called)
    guc.check_git_clone_update(force=True)
    assert guc._read_dismissed_version() == 2


def test_check_declines_dismisses_without_pulling(monkeypatch, tmp_path):
    _isolate_config(monkeypatch, tmp_path)
    monkeypatch.setattr(guc, "_find_git_root", lambda start_dir: tmp_path)
    monkeypatch.setattr(guc, "_fetch_remote_version", lambda: ({"version": 2, "updated": "2026-01-01", "summary": "x"}, None))
    monkeypatch.setattr(guc, "_is_working_tree_dirty", lambda git_root: False)
    monkeypatch.setattr(guc.sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr(guc.sys.stdout, "isatty", lambda: True)
    monkeypatch.setattr("builtins.input", lambda prompt="": "n")

    def fail_if_called(*args, **kwargs):
        raise AssertionError("should not pull without a yes")

    monkeypatch.setattr(subprocess, "run", fail_if_called)
    guc.check_git_clone_update(force=True)
    assert guc._read_dismissed_version() == 2


def test_check_confirms_and_pulls(monkeypatch, tmp_path):
    _isolate_config(monkeypatch, tmp_path)
    monkeypatch.setattr(guc, "_find_git_root", lambda start_dir: tmp_path)
    monkeypatch.setattr(guc, "_fetch_remote_version", lambda: ({"version": 2, "updated": "2026-01-01", "summary": "x"}, None))
    monkeypatch.setattr(guc, "_is_working_tree_dirty", lambda git_root: False)
    monkeypatch.setattr(guc.sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr(guc.sys.stdout, "isatty", lambda: True)
    monkeypatch.setattr("builtins.input", lambda prompt="": "y")

    pull_calls = []

    class FakeResult:
        returncode = 0
        stdout = "Already up to date.\n"
        stderr = ""

    def fake_run(cmd, **kwargs):
        pull_calls.append(cmd)
        return FakeResult()

    monkeypatch.setattr(subprocess, "run", fake_run)
    guc.check_git_clone_update(force=True)
    assert pull_calls == [["git", "pull", "origin", "main"]]
    assert guc._read_dismissed_version() is None


def test_check_skips_when_already_dismissed(monkeypatch, tmp_path):
    _isolate_config(monkeypatch, tmp_path)
    monkeypatch.setattr(guc, "_find_git_root", lambda start_dir: tmp_path)
    monkeypatch.setattr(guc, "_fetch_remote_version", lambda: ({"version": 2, "updated": "2026-01-01", "summary": "x"}, None))
    guc._write_dismissed_version(2)

    def fail_if_called(git_root):
        raise AssertionError("should not check dirty state once dismissed")

    monkeypatch.setattr(guc, "_is_working_tree_dirty", fail_if_called)
    guc.check_git_clone_update(force=True)
