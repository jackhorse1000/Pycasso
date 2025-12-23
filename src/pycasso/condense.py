from collections import defaultdict
from pathlib import Path

from .parse import Entity, EntityType

MAX_SUMMARY_TOKENS = 2000
TOKEN_TO_WORD_RATIO = 0.75


def condense(entities: list[Entity], repo_path: Path, max_symbols: int = 20) -> str:
    if not entities:
        return "Empty repository - no Python entities found."

    repo_name = repo_path.name

    files: set[Path] = set()
    classes: list[str] = []
    functions: list[str] = []
    loop_count = 0
    conditional_count = 0

    file_complexity: dict[Path, int] = defaultdict(int)

    for entity in entities:
        files.add(entity.file_path)
        file_complexity[entity.file_path] += entity.complexity

        if entity.entity_type == EntityType.CLASS:
            classes.append(entity.name)
        elif entity.entity_type == EntityType.FUNCTION:
            functions.append(entity.name)
        elif entity.entity_type == EntityType.LOOP:
            loop_count += 1
        elif entity.entity_type == EntityType.CONDITIONAL:
            conditional_count += 1

    directories: set[str] = set()
    for file_path in files:
        try:
            rel_path = file_path.relative_to(repo_path)
            if len(rel_path.parts) > 1:
                directories.add(rel_path.parts[0])
        except ValueError:
            pass

    top_files = sorted(file_complexity.items(), key=lambda x: x[1], reverse=True)[:5]

    lines = [
        f"Repository: {repo_name}",
        f"Files: {len(files)} Python files",
        "",
        "Structure:",
    ]

    if directories:
        for d in sorted(directories)[:5]:
            lines.append(f"  - {d}/")
    else:
        lines.append("  - (flat structure)")

    lines.extend([
        "",
        "Entities:",
        f"  - Classes ({len(classes)}): {', '.join(classes[:max_symbols]) or 'none'}",
        f"  - Functions ({len(functions)}): {', '.join(functions[:max_symbols]) or 'none'}",
        f"  - Loops: {loop_count}",
        f"  - Conditionals: {conditional_count}",
        "",
        "Top modules by complexity:",
    ])

    for i, (file_path, complexity) in enumerate(top_files, 1):
        try:
            rel_path = file_path.relative_to(repo_path)
            lines.append(f"  {i}. {rel_path} (complexity: {complexity})")
        except ValueError:
            lines.append(f"  {i}. {file_path.name} (complexity: {complexity})")

    all_names = classes + functions
    purpose_words = _extract_purpose_hints(all_names)
    if purpose_words:
        lines.extend([
            "",
            f"Purpose hints (from names): {', '.join(purpose_words[:10])}",
        ])

    summary = "\n".join(lines)

    token_count = _estimate_tokens(summary)
    if token_count > MAX_SUMMARY_TOKENS:
        summary = _truncate_summary(summary, MAX_SUMMARY_TOKENS)

    return summary


def _extract_purpose_hints(names: list[str]) -> list[str]:
    common_words = {
        "get", "set", "init", "main", "run", "test", "setup", "teardown",
        "create", "delete", "update", "read", "write", "load", "save",
        "handle", "process", "parse", "render", "build", "make",
    }

    words: dict[str, int] = defaultdict(int)
    for name in names:
        parts = _split_name(name)
        for part in parts:
            lower = part.lower()
            if lower not in common_words and len(lower) > 2:
                words[lower] += 1

    sorted_words = sorted(words.items(), key=lambda x: x[1], reverse=True)
    return [word for word, _ in sorted_words[:10]]


def _split_name(name: str) -> list[str]:
    parts: list[str] = []
    current = ""

    for char in name:
        if char == "_":
            if current:
                parts.append(current)
                current = ""
        elif char.isupper() and current and current[-1].islower():
            parts.append(current)
            current = char
        else:
            current += char

    if current:
        parts.append(current)

    return parts


def _estimate_tokens(text: str) -> int:
    """Rough token estimation using word count. Approximates OpenAI's tokenizer."""
    words = text.split()
    return int(len(words) / TOKEN_TO_WORD_RATIO)


def _truncate_summary(summary: str, max_tokens: int) -> str:
    """Truncate summary to fit within token limit, keeping high-level structure."""
    lines = summary.split("\n")

    result: list[str] = []
    current_tokens = 0

    for line in lines:
        line_tokens = _estimate_tokens(line)

        if current_tokens + line_tokens > max_tokens:
            if result and not result[-1].endswith("..."):
                result.append("(summary truncated for token limit)")
            break

        result.append(line)
        current_tokens += line_tokens

    return "\n".join(result)

