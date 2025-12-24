from dataclasses import dataclass, field
from pathlib import Path

import tomli


@dataclass
class ExcludeConfig:
    dirs: list[str] = field(
        default_factory=lambda: ["venv", "__pycache__", ".git", ".venv", "node_modules"]
    )


@dataclass
class AIConfig:
    style: str = "Synthwave / Dark Mode IDE aesthetic, neon colors, abstract"
    prompt_model: str = "anthropic/claude-haiku-4.5"
    image_model: str = "google/gemini-2.5-flash-preview-05-20"


@dataclass
class Config:
    exclude: ExcludeConfig = field(default_factory=ExcludeConfig)
    ai: AIConfig = field(default_factory=AIConfig)


def load_config(config_path: Path | None = None) -> Config:
    if config_path is None or not config_path.exists():
        return Config()

    with open(config_path, "rb") as f:
        data = tomli.load(f)

    exclude_data = data.get("exclude", {})
    ai_data = data.get("ai", {})

    default_dirs = ["venv", "__pycache__", ".git", ".venv", "node_modules"]
    exclude = ExcludeConfig(dirs=exclude_data.get("dirs", default_dirs))

    ai = AIConfig(
        style=ai_data.get("style", AIConfig.style),
        prompt_model=ai_data.get("prompt_model", AIConfig.prompt_model),
        image_model=ai_data.get("image_model", AIConfig.image_model),
    )

    return Config(exclude=exclude, ai=ai)

