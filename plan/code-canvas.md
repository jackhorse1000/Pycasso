# Code Canvas Implementation Plan

## 1. Summary

**Goal**: Build "Pycasso"—a CLI tool that transforms Python repositories into deterministic, Synthwave-styled generative art by analysing AST structure and rendering geometric primitives.

**Success Criteria**: Running `pycasso /path/to/repo --seed 42 -o art.png` produces a reproducible 4K PNG where the same code + seed always yields an identical image. Users can customise palette, canvas size, and exclusions via a TOML config file.

---

## 2. Repo Notes

| Item | Value |
|------|-------|
| Language | Python 3.11+ |
| Package Manager | Poetry |
| Project Config | `pyproject.toml` |
| Test Framework | pytest |
| Test Command | `poetry run pytest` |
| Source Layout | `src/pycasso/` |
| Test Layout | `tests/` (mirrors `src/pycasso/`) |

**Style rules** (from [python-style.instructions.md](.github/instructions/python-style.instructions.md)):
- No useless comments; self-documenting code
- Type hints required
- Tests in `tests/test_<module>.py`

---

## 3. Scope

### In Scope
- CLI entry point (`pycasso` command)
- `harvest()`: recursive `.py` file discovery with exclusions
- `parse()`: AST parsing, metric extraction (mass, complexity, fingerprint)
- `render()`: Pillow-based 4K renderer with Synthwave palette
- TOML config file for colours, canvas size, exclusions
- CLI flags for seed, output path, config path
- Deterministic output via global seed + node hashes
- Warning logs for unparseable files

### Out of Scope
- SVG or other output formats
- Abstract renderer protocol (premature—just use Pillow directly)
- GUI / web interface
- Support for non-Python languages
- Package distribution to PyPI

---

## 4. Assumptions and Contracts

| Assumption | Contract |
|------------|----------|
| Input is a valid directory path | CLI validates path exists and is a directory |
| `.py` files use UTF-8 encoding | Harvester decodes as UTF-8; logs warning on decode errors |
| AST parsing uses Python's `ast` module | Files with syntax errors are skipped with warning |
| Seed is a 32-bit integer | Default seed = 0; CLI accepts `--seed` flag |
| Config file is optional | Falls back to hardcoded defaults if missing |
| Canvas aspect ratio is 16:9 | Default 3840×2160; configurable via TOML |

---

## 5. Functional Requirements

| ID | Requirement |
|----|-------------|
| FR1 | CLI accepts a positional `path` argument (repo root) |
| FR2 | CLI accepts `--seed` (int), `--output` (path), `--config` (path) flags |
| FR3 | Config loader reads TOML with colours, canvas size, exclusions; falls back to defaults |
| FR4 | `harvest()` walks directory, filters `.py`, excludes dirs from config |
| FR5 | `parse()` parses each file into AST; extracts Functions, Classes, Loops, Conditionals |
| FR6 | Each entity has: `mass` (line count), `complexity` (nesting depth), `fingerprint` (hash) |
| FR7 | `render()` creates canvas with colours from config, draws shapes, saves PNG |
| FR8 | Entity position = `Random(seed + fingerprint)` within file's sector |
| FR9 | Unparseable files logged as warnings; processing continues |

---

## 6. Non-Functional Requirements

| ID | Requirement |
|----|-------------|
| NFR1 | Determinism: identical inputs + seed → byte-identical PNG |
| NFR2 | Performance: process 10k-line repo in < 5 seconds |
| NFR3 | Compatibility: Python 3.11+ |

---

## 7. Behaviour and Edge Cases

### Normal Behaviour
- Repo with 50 `.py` files → each file gets a sector; entities scattered within
- Seed change → full layout rearrangement
- Code change → affected entity fingerprints change → localised visual diff

### Edge Cases

| Case | Expected Behaviour |
|------|-------------------|
| Empty repo (no `.py` files) | Output blank canvas with background; log info message |
| Single file with 1 function | One circle rendered in centre sector |
| File with syntax error | Skip file, log warning with filename and error |
| Deeply nested code (depth > 10) | Cap complexity at 10 for sizing |
| Very large file (> 10k lines) | Clamp mass to reasonable max |

---

## 8. Decisions

| Decision | Options Considered | Chosen | Reason |
|----------|-------------------|--------|--------|
| Interface | CLI / Library / Both | CLI only | User request; simpler MVP |
| Output format | PNG / SVG / JSON | PNG only | Simplest; defer extensibility |
| Config | TOML / CLI flags | TOML for theme + CLI for runtime | User wants customisable colours |
| Dependency manager | uv / pip / Poetry | Poetry | User request |
| Error handling | Skip silent / Warn / Fail | Skip with warning | User request |
| Architecture | Many modules / Few modules | Few modules | User request for minimal code |

---

## 9. Test Plan

**Local test command**: `poetry run pytest`

| Requirement | Test Description |
|-------------|------------------|
| FR3 | `harvest()` excludes `venv`, `__pycache__`, hidden dirs |
| FR4–FR5 | `parse()` extracts correct entity types and metrics |
| FR6–FR7 | `render()` produces valid PNG with expected dimensions |
| FR8 | Malformed file triggers warning, processing continues |
| NFR1 | Two runs with same seed produce identical output |

---

## 10. Implementation Checklist

| ID | Task | Type | Expected Outcome | Done |
|----|------|------|------------------|------|
| 1 | Initialise Poetry project with `pyproject.toml` | Setup | `poetry install` works | yes |
| 2 | Implement `Config` dataclass + `load_config()` in `config.py` | Functional | Loads TOML, returns typed config with defaults | yes |
| 3 | Implement `harvest()` function in `harvest.py` | Functional | Yields `.py` file paths; respects exclusions | yes |
| 4 | Implement `Entity` dataclass + `parse()` in `parse.py` | Functional | Parses AST, returns list of entities with metrics | yes |
| 5 | Implement `render()` in `render.py` | Functional | Draws shapes using config colours, saves PNG | yes |
| 6 | Implement CLI in `cli.py` + `__main__.py` | Functional | `pycasso /path --seed 42 -o art.png` works | yes |
| 7 | Write tests for core functions | Test | `tests/` passes | yes |
| 8 | Add example `pycasso.toml` + update `README.md` | Docs | Clear config reference + usage guide | yes |

---

## Config Schema (`pycasso.toml`)

```toml
[canvas]
width = 3840
height = 2160

[colors]
background = "#121212"
class = "#FF007F"       # Cyber Magenta
function = "#00FFFF"    # Electric Cyan  
loop = "#F5D300"        # Neon Yellow
conditional = "#FF6B35" # Orange

[exclude]
dirs = ["venv", "__pycache__", ".git", ".venv", "node_modules"]
```

---

## File Structure (Proposed)

```
Pycasso/
├── pyproject.toml
├── pycasso.toml          # Example config
├── README.md
├── src/
│   └── pycasso/
│       ├── __init__.py
│       ├── __main__.py   # Entry: wires CLI
│       ├── cli.py        # Arg parsing + orchestration
│       ├── config.py     # Config dataclass + loader
│       ├── harvest.py    # File discovery (one function)
│       ├── parse.py      # AST analysis + Entity dataclass
│       └── render.py     # Pillow rendering (one function)
└── tests/
    ├── test_config.py
    ├── test_harvest.py
    ├── test_parse.py
    └── test_render.py
```

---

## Next Step

**Handoff to Implementation Agent** — follow the checklist sequentially, starting with project initialisation (ID 1).

---

## Reviewer Feedback

**Reviewed by**: Reviewer Agent  
**Date**: 23 December 2025  
**Tests reported passing**: 21/21  
**Re-review after fixes**: 23 December 2025 — All blockers and should-fix items resolved.

### Blockers

None.

### Should Fix

1. **[render.py#L26] `hash()` is not deterministic across Python sessions** ✅ FIXED  
   `_compute_file_sector` uses `hash(str(file_path))`, but Python's `hash()` for strings is randomised per process (PYTHONHASHSEED). This breaks NFR1 (determinism) across different runs/machines.  
   **Fix**: Use a stable hash like `hashlib.sha256(str(file_path).encode()).hexdigest()[:8]` converted to int, consistent with `_compute_fingerprint` in `parse.py`.  
   **Resolution**: Added `_stable_hash()` helper function using SHA256, replaced `hash()` call.

2. **[test_config.py#L5] Unused imports** ✅ FIXED  
   `CanvasConfig`, `ColorsConfig`, `ExcludeConfig` are imported but never used in the test file.  
   **Fix**: Remove unused imports.  
   **Resolution**: Removed `pytest` and unused dataclass imports.

3. **[harvest.py#L9] Relative path bug with `..` in paths** ✅ FIXED  
   When running on repos from parent directories (e.g., `../idea_generator`), the check `part.startswith(".")` was matching `..` in `path.parts`, causing all Python files to be excluded.  
   **Fix**: Use `path.relative_to(root).parts` to check only the relative path components, not the absolute path.  
   **Resolution**: Changed to check `relative_parts = path.relative_to(root).parts`.

### Optional

1. **[harvest.py#L9] Hidden file detection may have false positives**  
   The check `part.startswith(".")` will also exclude files like `.env` at the root, which is correct, but also any path containing a segment starting with `.` (e.g., a folder named `.hidden`). This is the intended behaviour per the plan, but worth documenting in README that hidden directories are excluded.

2. **[render.py#L70-71] Sector bounds could allow shapes to be clipped**  
   `rng.randint(sector[0], sector[2])` picks x within bounds, but the shape is then drawn with `size` offset. Large entities near sector edges may be partially clipped.  
   **Suggestion**: Adjust bounds inward by `max_size` (50) or accept clipping as aesthetic choice.

3. **[cli.py] Consider adding `--version` flag**  
   Standard CLI practice; would use `pycasso.__version__`.

4. **[parse.py#L42] Depth parameter in `_extract_entities` vs `_get_nesting_depth`**  
   Both functions track nesting but calculate slightly differently. `_get_nesting_depth` calculates absolute depth from the node, while `_extract_entities` passes `depth` which is the traversal depth from root. The complexity metric is correct (uses `_get_nesting_depth`), but the `depth` parameter passed to recursive `_extract_entities` is unused for metric calculation—only passed forward.  
   **Suggestion**: Simplify by removing `depth` parameter from `_extract_entities` if not needed.

---

## Planning Improvements

1. **NFR1 (Determinism) should explicitly call out `hash()` limitation**  
   The plan states "deterministic output via global seed + node hashes" but doesn't specify that Python's built-in `hash()` is non-deterministic across sessions. Future plans should note: "Use stable hashing (e.g., SHA256) for all position calculations."

2. **Missing edge case: files with same name in different directories**  
   The plan doesn't specify behaviour when two files have identical names (e.g., `utils.py` in multiple packages). Current implementation handles this correctly via full `file_path`, but worth explicitly stating.

3. **Test Plan row FR8 mislabelled**  
   The test plan says "FR8: Malformed file triggers warning" but FR8 in the requirements is about entity position. FR9 is about warnings. Minor documentation mismatch.

4. **Acceptance criteria for visual output**  
   The plan has no way to verify the visual output is "correct" beyond dimensions. Consider adding a reference image for regression testing in future iterations.

---

## Summary

The implementation is **well-aligned with the plan**. Code is clean, minimal, and follows the style guidelines (no useless comments, type hints throughout, self-documenting names).

**Tests**: 21 tests cover all core modules including determinism, edge cases (syntax errors, empty repos, nested code), and configuration loading. Tests are well-structured and use `tmp_path` fixtures appropriately.

**Dry-run reasoning**: Traced the main flow `cli.main()` → `harvest()` → `parse()` → `render()`. Each function does what its name implies. The pipeline is linear and easy to follow.

**`[IA]` Deltas**: None identified—implementation matches plan exactly.

**Remaining items**:
- 0 Blockers
- 0 Should Fix (all resolved)
- 4 Optional improvements

**Post-implementation testing**: Tested on `../idea_generator/` repo (25 Python files, 227 entities) with 42 KB PNG output. ✅ All 21 tests pass.

**Recommendation**: ✅ **Ready for human review**.

**Tests**: 21 tests cover all core modules including determinism, edge cases (syntax errors, empty repos, nested code), and configuration loading. Tests are well-structured and use `tmp_path` fixtures appropriately.

**Dry-run reasoning**: Traced the main flow `cli.main()` → `harvest()` → `parse()` → `render()`. Each function does what its name implies. The pipeline is linear and easy to follow.

**`[IA]` Deltas**: None identified—implementation matches plan exactly.

**Remaining items**:
- 1 Should Fix (determinism bug with `hash()`)
- 1 Should Fix (unused imports in test)
- 4 Optional improvements

**Recommendation**: Fix the `hash()` determinism issue (Should Fix #1), then **ready for human review**.
