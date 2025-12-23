from pathlib import Path

from pycasso.parse import parse, EntityType


def test_parse_function(tmp_path: Path):
    py_file = tmp_path / "sample.py"
    py_file.write_text("def hello():\n    pass\n")

    entities = parse(py_file)

    assert len(entities) == 1
    assert entities[0].entity_type == EntityType.FUNCTION
    assert entities[0].name == "hello"
    assert entities[0].mass > 0
    assert entities[0].fingerprint > 0


def test_parse_class(tmp_path: Path):
    py_file = tmp_path / "sample.py"
    py_file.write_text("class MyClass:\n    pass\n")

    entities = parse(py_file)

    assert len(entities) == 1
    assert entities[0].entity_type == EntityType.CLASS
    assert entities[0].name == "MyClass"


def test_parse_loop(tmp_path: Path):
    py_file = tmp_path / "sample.py"
    py_file.write_text("for i in range(10):\n    pass\n")

    entities = parse(py_file)

    assert len(entities) == 1
    assert entities[0].entity_type == EntityType.LOOP


def test_parse_conditional(tmp_path: Path):
    py_file = tmp_path / "sample.py"
    py_file.write_text("if True:\n    pass\n")

    entities = parse(py_file)

    assert len(entities) == 1
    assert entities[0].entity_type == EntityType.CONDITIONAL


def test_parse_nested_entities(tmp_path: Path):
    py_file = tmp_path / "sample.py"
    py_file.write_text("""
class Outer:
    def method(self):
        for i in range(10):
            if i > 5:
                pass
""")

    entities = parse(py_file)

    types = {e.entity_type for e in entities}
    assert EntityType.CLASS in types
    assert EntityType.FUNCTION in types
    assert EntityType.LOOP in types
    assert EntityType.CONDITIONAL in types


def test_parse_syntax_error(tmp_path: Path, caplog):
    py_file = tmp_path / "broken.py"
    py_file.write_text("def broken(\n")

    entities = parse(py_file)

    assert entities == []
    assert "Syntax error" in caplog.text


def test_parse_complexity_capped(tmp_path: Path):
    py_file = tmp_path / "deep.py"
    nested = "if True:\n" + "    if True:\n" * 15 + "        pass\n"
    py_file.write_text(nested)

    entities = parse(py_file)

    for entity in entities:
        assert entity.complexity <= 10


def test_parse_deterministic_fingerprint(tmp_path: Path):
    py_file = tmp_path / "sample.py"
    py_file.write_text("def test():\n    return 42\n")

    entities1 = parse(py_file)
    entities2 = parse(py_file)

    assert entities1[0].fingerprint == entities2[0].fingerprint
