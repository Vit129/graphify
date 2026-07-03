import os
import sys
from pathlib import Path
from typing import Any, Dict

def load_project_config(proj_dir: Path) -> Dict[str, Any]:
    """Load configuration from graphify.toml or [tool.graphify] in pyproject.toml."""
    config: Dict[str, Any] = {}
    proj_dir = proj_dir.resolve()

    # 1. Helper to load a toml file safely using tomllib/tomli
    def _parse_toml(path: Path) -> Dict[str, Any]:
        if not path.exists():
            return {}
        try:
            import tomllib  # type: ignore[import-not-found]
        except ImportError:
            try:
                import tomli as tomllib  # type: ignore[import-not-found,no-redef]
            except ImportError:
                print(
                    "[graphify config] Warning: tomllib/tomli not found. Config loading skipped.",
                    file=sys.stderr
                )
                return {}
        try:
            with open(path, "rb") as f:
                return tomllib.load(f)
        except Exception as e:
            print(f"[graphify config] Warning: failed to parse {path.name}: {e}", file=sys.stderr)
            return {}

    # 2. Check graphify.toml first (highest priority)
    toml_path = proj_dir / "graphify.toml"
    toml_data = _parse_toml(toml_path)
    if toml_data:
        # Check if they nested it under [graphify]
        if "graphify" in toml_data and isinstance(toml_data["graphify"], dict):
            config.update(toml_data["graphify"])
        else:
            config.update(toml_data)

    # 3. Check pyproject.toml (fallback)
    pyproject_path = proj_dir / "pyproject.toml"
    if pyproject_path.exists():
        pyproject_data = _parse_toml(pyproject_path)
        tool_data = pyproject_data.get("tool", {})
        graphify_data = tool_data.get("graphify", {})
        if isinstance(graphify_data, dict):
            # Update only keys that are not already set by graphify.toml
            for k, v in graphify_data.items():
                if k not in config:
                    config[k] = v

    return config
