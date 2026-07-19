import json
from pathlib import Path
from graphify.__main__ import _install_claude_hook, _uninstall_claude_hook

def test_claude_hook_install_uninstall(tmp_path):
    # Test installation into a new/empty settings file
    _install_claude_hook(tmp_path)
    
    settings_file = tmp_path / ".claude" / "settings.json"
    assert settings_file.exists()
    
    settings = json.loads(settings_file.read_text(encoding="utf-8"))
    assert "hooks" in settings
    hooks = settings["hooks"]
    assert "PreToolUse" in hooks
    assert "PostToolUse" in hooks
    
    # Check that PostToolUse contains exactly one hook and it is our hook
    post_hooks = hooks["PostToolUse"]
    assert len(post_hooks) == 1
    assert post_hooks[0]["matcher"] == "Edit|Write|MultiEdit"
    
    # Test idempotent re-install does not duplicate the hook
    _install_claude_hook(tmp_path)
    settings = json.loads(settings_file.read_text(encoding="utf-8"))
    assert len(settings["hooks"]["PostToolUse"]) == 1
    assert len(settings["hooks"]["PreToolUse"]) == 2  # The two PreToolUse hooks
    
    # Test uninstall removes it cleanly
    _uninstall_claude_hook(tmp_path)
    settings = json.loads(settings_file.read_text(encoding="utf-8"))
    assert len(settings["hooks"].get("PostToolUse", [])) == 0
    assert len(settings["hooks"].get("PreToolUse", [])) == 0
