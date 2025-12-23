from pathlib import Path

from PIL import Image

from pycasso.config import Config
from pycasso.parse import Entity, EntityType
from pycasso.render import render


def test_render_empty_entities(tmp_path: Path):
    output = tmp_path / "empty.png"
    config = Config()

    render([], config, seed=0, output_path=output)

    assert output.exists()
    img = Image.open(output)
    assert img.size == (config.canvas.width, config.canvas.height)


def test_render_creates_valid_png(tmp_path: Path):
    output = tmp_path / "art.png"
    config = Config()

    entities = [
        Entity(
            entity_type=EntityType.FUNCTION,
            name="test_func",
            mass=10,
            complexity=2,
            fingerprint=12345,
            file_path=Path("test.py"),
        ),
        Entity(
            entity_type=EntityType.CLASS,
            name="TestClass",
            mass=50,
            complexity=3,
            fingerprint=67890,
            file_path=Path("test.py"),
        ),
    ]

    render(entities, config, seed=42, output_path=output)

    assert output.exists()
    img = Image.open(output)
    assert img.mode == "RGB"
    assert img.size == (3840, 2160)


def test_render_deterministic(tmp_path: Path):
    config = Config()
    entities = [
        Entity(
            entity_type=EntityType.FUNCTION,
            name="func",
            mass=20,
            complexity=1,
            fingerprint=11111,
            file_path=Path("a.py"),
        ),
    ]

    output1 = tmp_path / "run1.png"
    output2 = tmp_path / "run2.png"

    render(entities, config, seed=42, output_path=output1)
    render(entities, config, seed=42, output_path=output2)

    bytes1 = output1.read_bytes()
    bytes2 = output2.read_bytes()
    assert bytes1 == bytes2


def test_render_different_seed_different_output(tmp_path: Path):
    config = Config()
    entities = [
        Entity(
            entity_type=EntityType.FUNCTION,
            name="func",
            mass=20,
            complexity=1,
            fingerprint=11111,
            file_path=Path("a.py"),
        ),
    ]

    output1 = tmp_path / "seed1.png"
    output2 = tmp_path / "seed2.png"

    render(entities, config, seed=1, output_path=output1)
    render(entities, config, seed=2, output_path=output2)

    bytes1 = output1.read_bytes()
    bytes2 = output2.read_bytes()
    assert bytes1 != bytes2


def test_render_all_entity_types(tmp_path: Path):
    output = tmp_path / "all_types.png"
    config = Config()

    entities = [
        Entity(EntityType.CLASS, "C", 10, 1, 1, Path("a.py")),
        Entity(EntityType.FUNCTION, "f", 10, 1, 2, Path("a.py")),
        Entity(EntityType.LOOP, "loop", 10, 1, 3, Path("a.py")),
        Entity(EntityType.CONDITIONAL, "if", 10, 1, 4, Path("a.py")),
    ]

    render(entities, config, seed=0, output_path=output)

    assert output.exists()
    img = Image.open(output)
    assert img.size == (3840, 2160)
