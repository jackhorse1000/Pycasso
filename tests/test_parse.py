from pathlib import Path

from pycasso.parse import parse


def test_parse_function(tmp_path: Path):
    py_file = tmp_path / "sample.py"
    py_file.write_text("def hello():\n    pass\n")

    entities = parse(py_file)

    assert len(entities) == 1
    assert entities[0].entity_type == "function"
    assert entities[0].name == "hello"


def test_parse_class(tmp_path: Path):
    py_file = tmp_path / "sample.py"
    py_file.write_text("class MyClass:\n    pass\n")

    entities = parse(py_file)

    assert len(entities) == 1
    assert entities[0].entity_type == "class"
    assert entities[0].name == "MyClass"


def test_parse_nested_entities(tmp_path: Path):
    py_file = tmp_path / "sample.py"
    py_file.write_text("""
class Outer:
    def method(self):
        pass
""")

    entities = parse(py_file)

    types = {e.entity_type for e in entities}
    assert "class" in types
    assert "function" in types


def test_parse_syntax_error(tmp_path: Path):
    py_file = tmp_path / "broken.py"
    py_file.write_text("def broken(\n")

    entities = parse(py_file)

    assert entities == []


def test_parse_async_function(tmp_path: Path):
    py_file = tmp_path / "sample.py"
    py_file.write_text("async def async_hello():\n    pass\n")

    entities = parse(py_file)

    assert len(entities) == 1
    assert entities[0].entity_type == "function"
    assert entities[0].name == "async_hello"
