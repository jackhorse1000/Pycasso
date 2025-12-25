import ast
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Entity:
    name: str
    entity_type: str
    file_path: Path


def parse(file_path: Path) -> list[Entity]:
    try:
        source = file_path.read_text(encoding="utf-8")
        tree = ast.parse(source)
    except (UnicodeDecodeError, SyntaxError):
        return []

    entities: list[Entity] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            entities.append(Entity(node.name, "class", file_path))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            entities.append(Entity(node.name, "function", file_path))

    return entities
