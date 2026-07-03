import pytest
from pathlib import Path
from graphify.config import load_project_config

def test_load_project_config_no_config(tmp_path):
    # Neither exists
    config = load_project_config(tmp_path)
    assert config == {}

def test_load_project_config_graphify_toml_toplevel(tmp_path):
    toml_path = tmp_path / "graphify.toml"
    toml_path.write_text("""
resolution = 1.5
exclude_hubs = 99.0
no_viz = true
wiki = true
""", encoding="utf-8")
    
    config = load_project_config(tmp_path)
    assert config == {
        "resolution": 1.5,
        "exclude_hubs": 99.0,
        "no_viz": True,
        "wiki": True
    }

def test_load_project_config_graphify_toml_nested(tmp_path):
    toml_path = tmp_path / "graphify.toml"
    toml_path.write_text("""
[graphify]
resolution = 2.0
no_viz = false
""", encoding="utf-8")
    
    config = load_project_config(tmp_path)
    assert config == {
        "resolution": 2.0,
        "no_viz": False
    }

def test_load_project_config_pyproject_toml(tmp_path):
    pyproject_path = tmp_path / "pyproject.toml"
    pyproject_path.write_text("""
[tool.graphify]
resolution = 1.2
exclude_hubs = 95.0
wiki = false
""", encoding="utf-8")
    
    config = load_project_config(tmp_path)
    assert config == {
        "resolution": 1.2,
        "exclude_hubs": 95.0,
        "wiki": False
    }

def test_load_project_config_override_precedence(tmp_path):
    # graphify.toml should override pyproject.toml
    toml_path = tmp_path / "graphify.toml"
    toml_path.write_text("""
resolution = 1.5
wiki = true
""", encoding="utf-8")
    
    pyproject_path = tmp_path / "pyproject.toml"
    pyproject_path.write_text("""
[tool.graphify]
resolution = 1.2
exclude_hubs = 95.0
wiki = false
""", encoding="utf-8")
    
    config = load_project_config(tmp_path)
    assert config == {
        "resolution": 1.5,
        "exclude_hubs": 95.0,
        "wiki": True
    }
