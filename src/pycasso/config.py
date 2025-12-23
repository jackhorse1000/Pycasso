from dataclasses import dataclass, field
from pathlib import Path

import tomli


@dataclass
class CanvasConfig:
    width: int = 3840
    height: int = 2160


@dataclass
class ColorsConfig:
    background: str = "#121212"
    class_color: str = "#FF007F"
    function: str = "#00FFFF"
    loop: str = "#F5D300"
    conditional: str = "#FF6B35"


@dataclass
class ExcludeConfig:
    dirs: list[str] = field(
        default_factory=lambda: ["venv", "__pycache__", ".git", ".venv", "node_modules"]
    )


@dataclass
class Config:
    canvas: CanvasConfig = field(default_factory=CanvasConfig)
    colors: ColorsConfig = field(default_factory=ColorsConfig)
    exclude: ExcludeConfig = field(default_factory=ExcludeConfig)


def load_config(config_path: Path | None = None) -> Config:
    if config_path is None or not config_path.exists():
        return Config()

    with open(config_path, "rb") as f:
        data = tomli.load(f)

    canvas_data = data.get("canvas", {})
    colors_data = data.get("colors", {})
    exclude_data = data.get("exclude", {})

    canvas = CanvasConfig(
        width=canvas_data.get("width", 3840),
        height=canvas_data.get("height", 2160),
    )

    colors = ColorsConfig(
        background=colors_data.get("background", "#121212"),
        class_color=colors_data.get("class", "#FF007F"),
        function=colors_data.get("function", "#00FFFF"),
        loop=colors_data.get("loop", "#F5D300"),
        conditional=colors_data.get("conditional", "#FF6B35"),
    )

    default_dirs = ["venv", "__pycache__", ".git", ".venv", "node_modules"]
    exclude = ExcludeConfig(dirs=exclude_data.get("dirs", default_dirs))

    return Config(canvas=canvas, colors=colors, exclude=exclude)
