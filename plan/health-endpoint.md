# Health Endpoint Plan

## 1. Summary

**Goal**: Add a `/health` endpoint via Flask, accessible through a new `pycasso-serve` CLI command.

**Success Criteria**: Running `pycasso-serve` starts a Flask server; `GET /health` returns `{"status": "ok"}` with HTTP 200.

---

## 2. Repo Notes

| Item | Value |
|------|-------|
| Language | Python 3.11+ |
| Package Manager | Poetry |
| Test Framework | pytest (`poetry run pytest`) |
| Existing CLI | `pycasso` in `src/pycasso/cli.py` |
| Entry points | Defined in `pyproject.toml` under `[tool.poetry.scripts]` |

**Patterns to follow**:
- CLI structure from [cli.py](src/pycasso/cli.py) (argparse, logging setup)
- Module structure: one function per module when simple

---

## 3. Scope

### In Scope
- Add Flask dependency
- Create `src/pycasso/server.py` with Flask app and `/health` route
- Add `pycasso-serve` CLI command
- Unit test for health endpoint

### Out of Scope
- Authentication
- Other endpoints
- Production WSGI server (Gunicorn, uWSGI)
- Docker/container configuration

---

## 4. Assumptions and Contracts

| Assumption | Contract |
|------------|----------|
| Flask dev server is acceptable | No production WSGI config needed |
| No auth required | Endpoint is public |
| Default port 5000 | Standard Flask default; no CLI flag needed initially |

---

## 5. Functional Requirements

| ID | Requirement |
|----|-------------|
| FR1 | `pycasso-serve` command starts a Flask web server |
| FR2 | `GET /health` returns JSON `{"status": "ok"}` |
| FR3 | `GET /health` returns HTTP status 200 |

---

## 6. Non-Functional Requirements

| ID | Requirement |
|----|-------------|
| NFR1 | Server starts in < 2 seconds |
| NFR2 | No external dependencies beyond Flask |

---

## 7. Behaviour and Edge Cases

### Normal Behaviour
- `pycasso-serve` starts Flask on `http://127.0.0.1:5000`
- `curl http://127.0.0.1:5000/health` returns `{"status": "ok"}`

### Edge Cases

| Case | Behaviour |
|------|-----------|
| Port already in use | Flask default error; no custom handling |
| Invalid route | Flask 404 (default) |

---

## 8. Decisions

| Decision | Options | Chosen | Reason |
|----------|---------|--------|--------|
| Framework | Flask / FastAPI / http.server | Flask | User request |
| Command name | `pycasso serve` / `pycasso-serve` | `pycasso-serve` | User request; separate entry point |
| Response format | Plain text / JSON | JSON | Standard for health checks |

---

## 9. Test Plan

**Command**: `poetry run pytest`

| Requirement | Test |
|-------------|------|
| FR2, FR3 | `test_health_returns_ok`: Flask test client hits `/health`, asserts 200 and JSON body |

---

## 10. Implementation Checklist

| ID | Task | Type | Expected Outcome | Done | Implementation Agent Note |
|----|------|------|------------------|------|---------------------------|
| 1 | Add Flask dependency | Setup | `poetry add flask` | yes | Flask 3.1.2 installed |
| 2 | Create `src/pycasso/server.py` with Flask app | Functional | `/health` route defined | yes | |
| 3 | Add `pycasso-serve` entry in `pyproject.toml` | Setup | Command available after install | yes | |
| 4 | Write `tests/test_server.py` | Test | Health endpoint test passes | yes | 1 test passing |
| 5 | Update README with `pycasso-serve` usage | Docs | Users know how to run server | yes | Added "Running the Web Server" section |

---

## File Structure (After)

```
src/pycasso/
├── server.py      # NEW: Flask app with /health
└── ...

tests/
├── test_server.py # NEW: Health endpoint test
└── ...
```
