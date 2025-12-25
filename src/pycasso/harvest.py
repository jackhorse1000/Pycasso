from collections.abc import Iterator
from pathlib import Path


def harvest(root: Path, exclude_dirs: list[str], exclude_tests: bool = True) -> Iterator[Path]:
    exclude_set = set(exclude_dirs)

    for path in root.rglob("*.py"):
        relative_parts = path.relative_to(root).parts
        if any(part.startswith(".") or part in exclude_set for part in relative_parts):
            continue
        
        if exclude_tests:
            if path.name.startswith("test_") or path.name.endswith("_test.py"):
                continue
            if "tests" in relative_parts or "test" in relative_parts:
                continue
            if path.name == "conftest.py":
                continue
        
        yield path
