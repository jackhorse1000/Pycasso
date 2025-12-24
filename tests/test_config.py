from pathlib import Path

from pycasso.config import Config, load_config


def test_load_config_defaults():
    config = load_config(None)

    assert "venv" in config.exclude.dirs
    assert config.ai.style
    assert config.ai.prompt_model
    assert config.ai.image_model


def test_load_config_from_file(tmp_path: Path):
    config_file = tmp_path / "pycasso.toml"
    config_file.write_text("""
    [exclude]
    dirs = ["custom_exclude"]

    [ai]
    style = "Custom art style"
    prompt_model = "custom/prompt-model"
    image_model = "custom/image-model"
    """)

    config = load_config(config_file)

    assert config.exclude.dirs == ["custom_exclude"]
    assert config.ai.style == "Custom art style"
    assert config.ai.prompt_model == "custom/prompt-model"
    assert config.ai.image_model == "custom/image-model"


def test_load_config_missing_file():
    config = load_config(Path("/nonexistent/pycasso.toml"))
    assert "venv" in config.exclude.dirs
    assert config.ai.style
