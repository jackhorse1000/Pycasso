# Copilot Instructions

Python 3.11+ CLI tool using Poetry, httpx, and OpenRouter API to generate AI art from Python codebases.

## Critical Rules

- If you don't know a library version or import path, ASK
- No useless comments; code should be self-documenting with clear names and type hints
- All new logic requires a test in `tests/`
- Use dataclasses for structured data (see `config.py`, `parse.py`, `github.py`)
- Custom exceptions inherit from a base error class per module (see `LLMError`, `GitHubError`)

## Quick Commands

| Task | Command |
|------|---------|
| Install | `poetry install` |
| Run | `pycasso /path/to/repo -o art.png` |
| Test | `poetry run pytest` |
| Test single | `poetry run pytest tests/test_parse.py -v` |
| Lint | `[UNKNOWN: no linter configured]` |
| Format | `[UNKNOWN: no formatter configured]` |

## Setup

- Python 3.11+ required (from `pyproject.toml`)
- Poetry for dependency management
- Copy `.env.example` to `.env` and set `OPENROUTER_API_KEY`
- Optional: create `pycasso.toml` for custom style/model config

## Architecture

| Component | Purpose | Location |
|-----------|---------|----------|
| CLI entry | Argument parsing, orchestration | `src/pycasso/cli.py` |
| Harvest | Find Python files in repo | `src/pycasso/harvest.py` |
| Parse | Extract classes/functions via AST | `src/pycasso/parse.py` |
| Condense | Summarize codebase for LLM | `src/pycasso/condense.py` |
| LLM | OpenRouter API calls (prompt + image) | `src/pycasso/llm.py` |
| GitHub | Clone public repos, URL parsing | `src/pycasso/github.py` |
| Config | Load `pycasso.toml` settings | `src/pycasso/config.py` |
| Prompts | LLM prompt templates | `src/pycasso/prompts/` |

**Data flow:** CLI -> harvest files -> parse AST -> condense summary -> generate prompt (LLM) -> generate image (LLM) -> save PNG

## Code Style

- Type hints on all function signatures
- Dataclasses for structured data, not dicts
- Module-level custom exceptions (e.g., `class LLMError(Exception)`)
- Use `pathlib.Path` for file paths, not strings
- Imports: stdlib, blank line, third-party, blank line, local (relative with `.`)

## Testing

- Framework: pytest 8.x
- Location: `tests/`
- Naming: `test_<module>.py` matching `src/pycasso/<module>.py`
- Use `tmp_path` fixture for file operations (see `test_parse.py`)
- Tests are unit tests; no integration tests with external APIs

## Guardrails

- Do not commit `.env` or API keys
- Do not modify `src/pycasso/prompts/image_prompt.txt` without discussion
- Output directory `output/` is gitignored

## Golden Paths

- New module: follow structure of `src/pycasso/parse.py` (dataclass + pure function)
- New CLI option: add to `argparse` in `src/pycasso/cli.py`
- New test: copy pattern from `tests/test_parse.py`
- API integration: follow `src/pycasso/llm.py` (dataclass config, custom exception, httpx)

## File Locator

| What | Where |
|------|-------|
| Entry point | `src/pycasso/cli.py:main` |
| Package init | `src/pycasso/__init__.py` |
| Config loading | `src/pycasso/config.py` |
| Tests | `tests/` |
| Prompt templates | `src/pycasso/prompts/` |
| Example config | `pycasso.toml` |
| Env template | `.env.example` |

## Open Questions

- `[UNKNOWN: Lint command]` No linter configured in pyproject.toml or CI
- `[UNKNOWN: Format command]` No formatter configured in pyproject.toml or CI
- `[UNKNOWN: CI workflow]` No `.github/workflows/` found
