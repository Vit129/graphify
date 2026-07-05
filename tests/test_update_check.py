"""Self-update check (#1568-adjacent): PyPI-backed sibling of agy-plugin-cc's
update-check.mjs. Pins the pure logic (version compare, cache interval,
autoUpdate default) and that a background install is fired without blocking
the caller — never that a real PyPI/network round-trip happens.
"""
from __future__ import annotations

import json
import subprocess

import graphify.update_check as uc


def _isolate_config(monkeypatch, tmp_path):
    config_dir = tmp_path / "config"
    monkeypatch.setattr(uc, "CONFIG_DIR", config_dir)
    monkeypatch.setattr(uc, "CONFIG_PATH", config_dir / "config.json")
    monkeypatch.setattr(uc, "INSTALL_LOG_PATH", config_dir / "update-install.log")


def test_is_newer_numeric_not_string():
    assert uc._is_newer("0.10.0", "0.9.0")
    assert not uc._is_newer("0.9.0", "0.10.0")
    assert not uc._is_newer("0.9.0", "0.9.0")


def test_should_check_true_on_first_run():
    assert uc._should_check({}, force=False) is True


def test_should_check_false_within_interval(monkeypatch):
    import datetime as real_datetime

    class FrozenDatetime(real_datetime.datetime):
        @classmethod
        def now(cls, tz=None):
            return real_datetime.datetime(2026, 1, 1, tzinfo=tz)

    monkeypatch.setattr(uc, "datetime", FrozenDatetime)
    config = {"lastUpdateCheckAt": "2026-01-01T00:00:00+00:00"}
    assert uc._should_check(config, force=False) is False
    assert uc._should_check(config, force=True) is True


def test_resolve_auto_update_defaults_false():
    # PACKAGE_NAME is upstream's own PyPI package (a different codebase) — auto-installing
    # it by default would silently replace this fork's install with the wrong software.
    assert uc._resolve_auto_update({}) is False
    assert uc._resolve_auto_update({"autoUpdate": False}) is False
    assert uc._resolve_auto_update({"autoUpdate": True}) is True


def test_upgrade_command_prefers_uv(monkeypatch):
    monkeypatch.setattr(uc.shutil, "which", lambda name: "/usr/bin/uv" if name == "uv" else None)
    assert uc._upgrade_command() == ["uv", "tool", "upgrade", "graphifyy"]


def test_upgrade_command_falls_back_to_pipx(monkeypatch):
    monkeypatch.setattr(uc.shutil, "which", lambda name: "/usr/bin/pipx" if name == "pipx" else None)
    assert uc._upgrade_command() == ["pipx", "upgrade", "graphifyy"]


def test_upgrade_command_none_when_neither_available(monkeypatch):
    monkeypatch.setattr(uc.shutil, "which", lambda name: None)
    assert uc._upgrade_command() is None


def test_check_for_update_skips_in_ci(monkeypatch, tmp_path, capsys):
    _isolate_config(monkeypatch, tmp_path)
    monkeypatch.setenv("CI", "1")
    monkeypatch.setattr(uc, "_latest_version", lambda: (_ for _ in ()).throw(AssertionError("should not hit network")))
    uc.check_for_update("0.1.0")
    assert capsys.readouterr().err == ""
    assert not uc.CONFIG_PATH.exists()


def test_check_for_update_no_op_when_current(monkeypatch, tmp_path, capsys):
    _isolate_config(monkeypatch, tmp_path)
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.setattr(uc, "_latest_version", lambda: "0.1.0")
    uc.check_for_update("0.1.0")
    assert capsys.readouterr().err == ""
    assert json.loads(uc.CONFIG_PATH.read_text())["lastUpdateCheckAt"]


def test_check_for_update_nudges_when_auto_update_disabled(monkeypatch, tmp_path, capsys):
    _isolate_config(monkeypatch, tmp_path)
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.setattr(uc, "_read_config", lambda: {"autoUpdate": False})
    monkeypatch.setattr(uc, "_latest_version", lambda: "0.2.0")
    uc.check_for_update("0.1.0")
    err = capsys.readouterr().err
    assert "0.2.0" in err
    assert "0.1.0" in err
    # Must not read as "you're behind, go run this" — this fork isn't on PyPI, so the
    # PyPI package name should only appear inside the explicit opt-in explanation.
    assert "github.com/Vit129/graphify" in err
    assert "uv tool upgrade" in err


def test_check_for_update_fires_background_install_when_enabled(monkeypatch, tmp_path, capsys):
    _isolate_config(monkeypatch, tmp_path)
    monkeypatch.delenv("CI", raising=False)
    # autoUpdate no longer defaults to True (see test_resolve_auto_update_defaults_false) —
    # this test is specifically the explicit opt-in path.
    monkeypatch.setattr(uc, "_read_config", lambda: {"autoUpdate": True})
    monkeypatch.setattr(uc, "_latest_version", lambda: "0.2.0")
    monkeypatch.setattr(uc, "_upgrade_command", lambda: ["uv", "tool", "upgrade", "graphifyy"])

    calls = []

    class FakePopen:
        def __init__(self, command, **kwargs):
            calls.append((command, kwargs))

    monkeypatch.setattr(uc.subprocess, "Popen", FakePopen)
    uc.check_for_update("0.1.0")

    assert len(calls) == 1
    command, kwargs = calls[0]
    assert command == ["uv", "tool", "upgrade", "graphifyy"]
    assert kwargs["start_new_session"] is True
    err = capsys.readouterr().err
    assert "in the background" in err


def test_check_for_update_never_raises_on_network_error(monkeypatch, tmp_path):
    _isolate_config(monkeypatch, tmp_path)
    monkeypatch.delenv("CI", raising=False)

    def boom():
        raise OSError("network down")

    monkeypatch.setattr(uc, "_latest_version", boom)
    uc.check_for_update("0.1.0")  # must not raise
