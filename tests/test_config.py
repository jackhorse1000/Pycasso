from pathlib import Path

from pycasso.config import Config, load_config


def test_load_config_defaults():
    config = load_config(None)

    assert config.canvas.width == 3840
    assert config.canvas.height == 2160
    assert config.colors.background == "#121212"
    assert config.colors.class_color == "#FF007F"
    assert config.colors.function == "#00FFFF"
    assert "venv" in config.exclude.dirs


def test_load_config_from_file(tmp_path: Path):
    config_file = tmp_path / "pycasso.toml"
    config_file.write_text("""
[canvas]
width = 1920
height = 1080

[colors]
background = "#000000"
class = "#FF0000"
function = "#00FF00"
loop = "#0000FF"
conditional = "#FFFF00"

[exclude]
dirs = ["custom_exclude"]
""")

    config = load_config(config_file)

    assert config.canvas.width == 1920
    assert config.canvas.height == 1080
    assert config.colors.background == "#000000"
    assert config.colors.class_color == "#FF0000"
    assert config.exclude.dirs == ["custom_exclude"]


def test_load_config_missing_file():
    config = load_config(Path("/nonexistent/pycasso.toml"))
    assert config.canvas.width == 3840
