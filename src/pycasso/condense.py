import ast
import re
from collections import defaultdict
from pathlib import Path

from .parse import Entity, EntityType

MAX_SUMMARY_TOKENS = 2000
MAX_README_CHARS = 1000
TOKEN_TO_WORD_RATIO = 0.75


def _extract_readme(repo_path: Path) -> str | None:
    """Extract and summarize README content from the repository.
    
    Looks for README.md, README.rst, or README.txt and extracts
    the most relevant parts (title, description, features).
    """
    readme_names = ["README.md", "README.MD", "readme.md", "README.rst", "README.txt", "README"]
    
    readme_path = None
    for name in readme_names:
        candidate = repo_path / name
        if candidate.exists():
            readme_path = candidate
            break
    
    if readme_path is None:
        return None
    
    try:
        with open(readme_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
    except OSError:
        return None
    
    if not content.strip():
        return None
    
    # Clean up markdown formatting
    # Remove badge links (nested image in link): [![alt](img)](link)
    content = re.sub(r'\[!\[[^\]]*\]\([^)]*\)\]\([^)]*\)', '', content)
    # Remove standalone images: ![alt](url)
    content = re.sub(r'!\[[^\]]*\]\([^)]*\)', '', content)
    # Remove empty links: [](url)
    content = re.sub(r'\[\]\([^)]*\)', '', content)
    # Remove HTML tags
    content = re.sub(r'<[^>]+>', '', content)
    # Remove code blocks
    content = re.sub(r'```[\s\S]*?```', '', content)
    content = re.sub(r'`[^`]+`', '', content)
    # Remove links but keep text: [text](url) -> text
    content = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', content)
    # Remove markdown header symbols but keep text
    content = re.sub(r'^#{1,6}\s*', '', content, flags=re.MULTILINE)
    # Remove horizontal rules
    content = re.sub(r'^[-*_]{3,}\s*$', '', content, flags=re.MULTILINE)
    # Remove bullet points but keep text
    content = re.sub(r'^\s*[-*+]\s+', '', content, flags=re.MULTILINE)
    # Remove numbered lists but keep text
    content = re.sub(r'^\s*\d+\.\s+', '', content, flags=re.MULTILINE)
    # Remove blockquotes
    content = re.sub(r'^>\s*', '', content, flags=re.MULTILINE)
    # Remove bold/italic markers
    content = re.sub(r'\*\*([^*]+)\*\*', r'\1', content)
    content = re.sub(r'\*([^*]+)\*', r'\1', content)
    content = re.sub(r'__([^_]+)__', r'\1', content)
    content = re.sub(r'_([^_]+)_', r'\1', content)
    # Clean up excessive whitespace
    content = re.sub(r'\n{3,}', '\n\n', content)
    content = re.sub(r' {2,}', ' ', content)
    content = re.sub(r'^\s+$', '', content, flags=re.MULTILINE)
    
    # Take the first meaningful portion
    content = content.strip()
    if len(content) > MAX_README_CHARS:
        # Try to cut at a sentence boundary
        truncated = content[:MAX_README_CHARS]
        last_period = truncated.rfind('.')
        last_newline = truncated.rfind('\n')
        cut_point = max(last_period, last_newline)
        if cut_point > MAX_README_CHARS // 2:
            content = truncated[:cut_point + 1].strip()
        else:
            content = truncated.strip() + "..."
    
    return content if content else None


def _extract_imports(file_path: Path) -> list[str]:
    """Extract top-level imports from a Python file."""
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            tree = ast.parse(f.read())
    except (SyntaxError, OSError):
        return []

    imports: list[str] = []
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module.split(".")[0])
    return imports


def _extract_docstrings(file_path: Path) -> list[str]:
    """Extract docstrings from classes and functions."""
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            tree = ast.parse(f.read())
    except (SyntaxError, OSError):
        return []

    docstrings: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            docstring = ast.get_docstring(node)
            if docstring:
                # Take first sentence only
                first_sentence = docstring.split(".")[0].strip()
                if first_sentence and len(first_sentence) > 10:
                    docstrings.append(first_sentence)
    return docstrings


def _extract_function_calls(file_path: Path) -> list[str]:
    """Extract all function/method calls from a Python file."""
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            tree = ast.parse(f.read())
    except (SyntaxError, OSError):
        return []

    calls: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            # Direct function call: func()
            if isinstance(node.func, ast.Name):
                calls.append(node.func.id)
            # Method call: obj.method()
            elif isinstance(node.func, ast.Attribute):
                calls.append(node.func.attr)
    return calls


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

    # Collect imports and docstrings from files
    all_imports: dict[str, int] = defaultdict(int)
    all_docstrings: list[str] = []
    all_function_calls: dict[str, int] = defaultdict(int)
    for file_path in files:
        for imp in _extract_imports(file_path):
            all_imports[imp] += 1
        all_docstrings.extend(_extract_docstrings(file_path))
        for call in _extract_function_calls(file_path):
            all_function_calls[call] += 1

    # Find the most frequently called functions that are defined in this repo
    # Filter out generic/common method names that don't reveal domain meaning
    generic_names = {
        # Common accessors/mutators
        "get", "set", "put", "delete", "remove", "add", "pop", "push",
        "read", "write", "load", "save", "dump", "fetch", "store",
        # Common lifecycle methods
        "init", "__init__", "setup", "teardown", "close", "open", "start", "stop",
        "run", "execute", "call", "invoke", "apply",
        # Common converters
        "to_dict", "to_json", "to_string", "to_list", "from_dict", "from_json",
        "as_dict", "as_json", "dict", "json", "str", "repr",
        # Common utilities
        "copy", "clone", "update", "merge", "clear", "reset", "refresh",
        "validate", "check", "verify", "ensure", "assert",
        # Common getters/properties
        "items", "keys", "values", "len", "size", "count", "length",
        "first", "last", "next", "prev", "head", "tail",
        # Testing
        "test", "mock", "patch", "fixture",
        # Logging/debug
        "log", "debug", "info", "warn", "error", "print", "format",
        # Common short names
        "ok", "err", "do", "is", "has", "can",
    }
    
    defined_functions = set(functions)
    internal_calls = [
        (name, count) for name, count in all_function_calls.items()
        if name in defined_functions 
        and count > 1
        and name.lower() not in generic_names
        and len(name) > 3  # Skip very short names
        and not name.startswith("_")  # Skip private methods
    ]
    top_called_functions = sorted(internal_calls, key=lambda x: x[1], reverse=True)[:10]

    # Filter to external libraries (not local modules)
    local_modules = {f.stem for f in files}
    external_imports = [
        (name, count) for name, count in all_imports.items()
        if name not in local_modules and not name.startswith("_")
    ]
    top_imports = sorted(external_imports, key=lambda x: x[1], reverse=True)[:10]

    # Extract README for project description
    readme_content = _extract_readme(repo_path)

    lines = [
        f"Repository: {repo_name}",
        f"Files: {len(files)} Python files",
    ]

    # Add README description first (most important context)
    if readme_content:
        lines.extend([
            "",
            "Project Description (from README):",
            readme_content,
        ])

    lines.extend([
        "",
        "Project Structure:",
    ])

    if directories:
        for d in sorted(directories)[:5]:
            lines.append(f"  - {d}/")
    else:
        lines.append("  - (flat structure)")

    # Add key dependencies
    if top_imports:
        lines.extend([
            "",
            "Key Dependencies:",
        ])
        for name, _ in top_imports:
            lines.append(f"  - {name}")

    lines.extend([
        "",
        "Code Components:",
        f"  - Classes ({len(classes)}): {', '.join(classes[:max_symbols]) or 'none'}",
        f"  - Functions ({len(functions)}): {', '.join(functions[:max_symbols]) or 'none'}",
        f"  - Loops: {loop_count} (indicates iterative/data processing patterns)",
        f"  - Conditionals: {conditional_count} (indicates branching logic)",
        "",
        "Complexity Hotspots (most complex modules):",
    ])

    for i, (file_path, complexity) in enumerate(top_files, 1):
        try:
            rel_path = file_path.relative_to(repo_path)
            lines.append(f"  {i}. {rel_path} (complexity: {complexity})")
        except ValueError:
            lines.append(f"  {i}. {file_path.name} (complexity: {complexity})")

    # Add key functions (most frequently called)
    if top_called_functions:
        lines.extend([
            "",
            "Key Functions (by usage frequency):",
        ])
        for name, count in top_called_functions:
            lines.append(f"  - {name} (called {count}x)")

    # Add docstring insights (what the code actually does)
    if all_docstrings:
        unique_docstrings = list(dict.fromkeys(all_docstrings))[:8]  # Dedupe, take top 8
        lines.extend([
            "",
            "What the code does (from docstrings):",
        ])
        for doc in unique_docstrings:
            # Truncate long docstrings
            doc_text = doc[:80] + "..." if len(doc) > 80 else doc
            lines.append(f"  - {doc_text}")

    all_names = classes + functions
    purpose_words = _extract_purpose_hints(all_names)
    if purpose_words:
        lines.extend([
            "",
            f"Domain concepts (inferred from names): {', '.join(purpose_words[:10])}",
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

