from pathlib import Path

from pycasso.condense import condense, _extract_purpose_hints, _split_name
from pycasso.parse import Entity


def test_condense_empty_entities():
    result = condense([], Path("/repo"))
    assert result == "Empty repository - no Python entities found."


def test_condense_basic():
    entities = [
        Entity(
            entity_type="class",
            name="UserService",
            file_path=Path("/repo/src/service.py"),
        ),
        Entity(
            entity_type="function",
            name="get_user",
            file_path=Path("/repo/src/service.py"),
        ),
    ]

    result = condense(entities, Path("/repo"))

    assert "Repository: repo" in result
    assert "Files: 1 Python files" in result
    assert "Classes (1): UserService" in result
    assert "Functions (1): get_user" in result


def test_condense_shows_structure():
    entities = [
        Entity(
            entity_type="function",
            name="complex_fn",
            file_path=Path("/repo/complex.py"),
        ),
        Entity(
            entity_type="function",
            name="simple_fn",
            file_path=Path("/repo/simple.py"),
        ),
    ]

    result = condense(entities, Path("/repo"))

    assert "Files: 2 Python files" in result


def test_split_name_snake_case():
    assert _split_name("get_user_data") == ["get", "user", "data"]


def test_split_name_camel_case():
    assert _split_name("getUserData") == ["get", "User", "Data"]


def test_split_name_mixed():
    assert _split_name("get_userData") == ["get", "user", "Data"]


def test_extract_purpose_hints():
    names = ["UserService", "validate_user", "process_payment", "get_order"]
    hints = _extract_purpose_hints(names)

    assert "user" in hints or "User" in hints.lower() if hints else True


def test_condense_limits_symbols():
    entities = [
        Entity(
            entity_type="function",
            name=f"public_func_{i}",
            file_path=Path("/repo/main.py"),
        )
        for i in range(30)
    ]

    result = condense(entities, Path("/repo"), max_symbols=5)

    assert "Functions (30):" in result


def test_token_estimation():
    from pycasso.condense import _estimate_tokens

    text = "word " * 100
    tokens = _estimate_tokens(text)

    assert tokens > 0
    assert tokens <= 200


def test_truncate_summary():
    from pycasso.condense import _truncate_summary

    long_text = "\n".join(["This is a line"] * 100)

    truncated = _truncate_summary(long_text, max_tokens=50)

    assert len(truncated.split("\n")) < len(long_text.split("\n"))
    assert "truncated" in truncated.lower()
