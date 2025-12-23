import ast
import hashlib
import logging
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


class EntityType(Enum):
    CLASS = "class"
    FUNCTION = "function"
    LOOP = "loop"
    CONDITIONAL = "conditional"


@dataclass
class Entity:
    entity_type: EntityType
    name: str
    mass: int
    complexity: int
    fingerprint: int
    file_path: Path


def _compute_fingerprint(source: str) -> int:
    return int(hashlib.sha256(source.encode()).hexdigest()[:8], 16)


def _get_nesting_depth(node: ast.AST, current_depth: int = 0) -> int:
    max_depth = current_depth
    for child in ast.iter_child_nodes(node):
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.For, ast.While, ast.If)):
            child_depth = _get_nesting_depth(child, current_depth + 1)
            max_depth = max(max_depth, child_depth)
        else:
            child_depth = _get_nesting_depth(child, current_depth)
            max_depth = max(max_depth, child_depth)
    return max_depth


def _extract_entities(node: ast.AST, source_lines: list[str], file_path: Path, depth: int = 0) -> list[Entity]:
    entities: list[Entity] = []

    for child in ast.iter_child_nodes(node):
        entity_type: EntityType | None = None
        name = ""

        if isinstance(child, ast.ClassDef):
            entity_type = EntityType.CLASS
            name = child.name
        elif isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
            entity_type = EntityType.FUNCTION
            name = child.name
        elif isinstance(child, (ast.For, ast.While)):
            entity_type = EntityType.LOOP
            name = f"loop_{child.lineno}"
        elif isinstance(child, ast.If):
            entity_type = EntityType.CONDITIONAL
            name = f"if_{child.lineno}"

        if entity_type is not None:
            start_line = child.lineno - 1
            end_line = getattr(child, "end_lineno", child.lineno)
            source_chunk = "\n".join(source_lines[start_line:end_line])
            mass = min(end_line - start_line, 1000)
            complexity = min(_get_nesting_depth(child, depth), 10)
            fingerprint = _compute_fingerprint(source_chunk)

            entities.append(
                Entity(
                    entity_type=entity_type,
                    name=name,
                    mass=mass,
                    complexity=complexity,
                    fingerprint=fingerprint,
                    file_path=file_path,
                )
            )

        entities.extend(_extract_entities(child, source_lines, file_path, depth + 1))

    return entities


def parse(file_path: Path) -> list[Entity]:
    try:
        source = file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError as e:
        logger.warning("Failed to decode %s: %s", file_path, e)
        return []

    try:
        tree = ast.parse(source, filename=str(file_path))
    except SyntaxError as e:
        logger.warning("Syntax error in %s: %s", file_path, e)
        return []

    source_lines = source.splitlines()
    return _extract_entities(tree, source_lines, file_path)
