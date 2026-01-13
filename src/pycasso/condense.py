import ast
import re
from collections import defaultdict
from pathlib import Path

from .parse import Entity

MAX_SUMMARY_TOKENS = 2000
MAX_README_CHARS = 1000
TOKEN_TO_WORD_RATIO = 0.75


def _extract_readme(repo_path: Path) -> str | None:
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
        content = readme_path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return None
    
    if not content.strip():
        return None
    
    content = _clean_markdown(content)
    content = _truncate_to_limit(content.strip(), MAX_README_CHARS)
    
    return content if content else None


def _clean_markdown(content: str) -> str:
    patterns = [
        (r'\[!\[[^\]]*\]\([^)]*\)\]\([^)]*\)', ''),
        (r'!\[[^\]]*\]\([^)]*\)', ''),
        (r'\[\]\([^)]*\)', ''),
        (r'<[^>]+>', ''),
        (r'```[\s\S]*?```', ''),
        (r'`[^`]+`', ''),
        (r'\[([^\]]+)\]\([^)]+\)', r'\1'),
        (r'^#{1,6}\s*', ''),
        (r'^[-*_]{3,}\s*$', ''),
        (r'^\s*[-*+]\s+', ''),
        (r'^\s*\d+\.\s+', ''),
        (r'^>\s*', ''),
        (r'\*\*([^*]+)\*\*', r'\1'),
        (r'\*([^*]+)\*', r'\1'),
        (r'__([^_]+)__', r'\1'),
        (r'_([^_]+)_', r'\1'),
        (r'\n{3,}', '\n\n'),
        (r' {2,}', ' '),
        (r'^\s+$', ''),
    ]
    
    for pattern, replacement in patterns:
        flags = re.MULTILINE if pattern.startswith('^') else 0
        content = re.sub(pattern, replacement, content, flags=flags)
    
    return content


def _truncate_to_limit(content: str, max_chars: int) -> str:
    if len(content) <= max_chars:
        return content
    
    truncated = content[:max_chars]
    last_period = truncated.rfind('.')
    last_newline = truncated.rfind('\n')
    cut_point = max(last_period, last_newline)
    
    if cut_point > max_chars // 2:
        return truncated[:cut_point + 1].strip()
    return truncated.strip() + "..."


def _extract_imports(file_path: Path) -> list[str]:
    try:
        tree = ast.parse(file_path.read_text(encoding="utf-8", errors="ignore"))
    except (SyntaxError, OSError):
        return []

    imports: list[str] = []
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module.split(".")[0])
    return imports


def _extract_docstrings(file_path: Path) -> list[str]:
    try:
        tree = ast.parse(file_path.read_text(encoding="utf-8", errors="ignore"))
    except (SyntaxError, OSError):
        return []

    docstrings: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            docstring = ast.get_docstring(node)
            if docstring:
                first_sentence = docstring.split(".")[0].strip()
                if first_sentence and len(first_sentence) > 10:
                    docstrings.append(first_sentence)
    return docstrings


def _extract_function_calls(file_path: Path) -> list[str]:
    try:
        tree = ast.parse(file_path.read_text(encoding="utf-8", errors="ignore"))
    except (SyntaxError, OSError):
        return []

    calls: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                calls.append(node.func.id)
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

    for entity in entities:
        files.add(entity.file_path)

        if entity.entity_type == "class":
            if not entity.name.startswith("Test") and "Mock" not in entity.name:
                classes.append(entity.name)
        elif entity.entity_type == "function":
            if not entity.name.startswith("_") and not entity.name.startswith("test_"):
                functions.append(entity.name)

    directories: set[str] = set()
    for file_path in files:
        try:
            rel_path = file_path.relative_to(repo_path)
            if len(rel_path.parts) > 1:
                directories.add(rel_path.parts[0])
        except ValueError:
            pass

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

    generic_names = {
        # Common CRUD/data operations
        "get", "set", "put", "delete", "remove", "add", "pop", "push",
        "read", "write", "load", "save", "dump", "fetch", "store", "create",
        "init", "__init__", "setup", "teardown", "close", "open", "start", "stop",
        "run", "execute", "call", "invoke", "apply",
        # Serialization
        "to_dict", "to_json", "to_string", "to_list", "from_dict", "from_json",
        "as_dict", "as_json", "dict", "json", "str", "repr",
        # Collection operations
        "copy", "clone", "update", "merge", "clear", "reset", "refresh",
        "validate", "check", "verify", "ensure", "assert",
        "items", "keys", "values", "len", "size", "count", "length",
        "first", "last", "next", "prev", "head", "tail",
        # Testing
        "test", "mock", "patch", "fixture",
        # Logging
        "log", "debug", "info", "warn", "error", "print", "format",
        "ok", "err", "do", "is", "has", "can",
        # Python built-ins that show up as function calls
        "super", "list", "dict", "set", "tuple", "int", "float", "bool",
        "type", "isinstance", "issubclass", "hasattr", "getattr", "setattr", "delattr",
        "append", "extend", "insert", "join", "split", "strip", "replace",
        "filter", "map", "reduce", "sorted", "reversed", "enumerate", "zip",
        "range", "iter", "any", "all", "min", "max", "sum", "abs",
        "id", "hash", "ord", "chr", "hex", "bin", "oct",
        "round", "divmod", "pow", "complex",
        "input", "output", "encode", "decode",
        "annotate", "order_by", "reverse",
        # String/collection methods
        "lower", "upper", "title", "capitalize", "swapcase",
        "find", "index", "rfind", "rindex", "startswith", "endswith",
        "match", "search", "sub", "compile", "group", "groups",
        "exists", "isdir", "isfile", "isabs", "islink",
        "setdefault", "fromkeys", "popitem",
        # Common short method names
        "send", "recv", "emit", "bind", "wrap", "seek", "tell", "flush",
        # Numpy/Pandas common operations
        "array", "zeros", "ones", "arange", "reshape", "transpose",
        "asarray", "dtype", "take", "view", "mean", "std",
        # Generic algorithm/data operations
        "solution", "main", "func", "sort", "swap", "compare",
        # Presentation/rendering operations  
        "show", "hide", "draw", "display", "paint",
    }
    
    defined_functions = set(functions)
    internal_calls = [
        (name, count) for name, count in all_function_calls.items()
        if name in defined_functions 
        and count > 1
        and name.lower() not in generic_names
        and len(name) > 3
        and not name.startswith("_")
    ]
    top_called_functions = sorted(internal_calls, key=lambda x: x[1], reverse=True)[:10]

    local_modules = {f.stem for f in files}
    external_imports = [
        (name, count) for name, count in all_imports.items()
        if name not in local_modules and not name.startswith("_")
    ]
    top_imports = sorted(external_imports, key=lambda x: x[1], reverse=True)[:10]

    readme_content = _extract_readme(repo_path)

    lines = [
        f"Repository: {repo_name}",
        f"Files: {len(files)} Python files",
    ]

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
    ])

    if top_called_functions:
        lines.extend([
            "",
            "Key Functions (by usage frequency):",
        ])
        for name, count in top_called_functions:
            lines.append(f"  - {name} (called {count}x)")

    if all_docstrings:
        unique_docstrings = list(dict.fromkeys(all_docstrings))[:8]
        lines.extend([
            "",
            "What the code does (from docstrings):",
        ])
        for doc in unique_docstrings:
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
    words = text.split()
    return int(len(words) / TOKEN_TO_WORD_RATIO)


def _truncate_summary(summary: str, max_tokens: int) -> str:
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

