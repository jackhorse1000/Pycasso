from collections.abc import Iterator
from pathlib import Path


def harvest(root: Path, exclude_dirs: list[str]) -> Iterator[Path]:
    exclude_set = set(exclude_dirs)

    for path in root.rglob("*.py"):
        relative_parts = path.relative_to(root).parts
        if any(part.startswith(".") or part in exclude_set for part in relative_parts):
            continue
        yield path
