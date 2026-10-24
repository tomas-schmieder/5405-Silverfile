# Acceptance results

This lists only results with a recorded source. A passing count means only that the named tests passed. It does not establish behavior those tests do not exercise.

## Test layers

From `tests/conftest.py`:

| Layer | Folder | What it uses | In the core command? |
|---|---|---|---|
| Unit / component | `tests/unit`, `tests/person2` … `tests/person6` | Pure functions; agents with an in-process tool stub; `tests/person5/test_mcp_contract.py` starts the real stdio MCP server | Yes |
| Integration | `tests/integration` | Real graph, real stdio MCP server, offline model back end (OCR for images) | No. Excluded, and also skipped by `tests/integration/conftest.py` unless `SILVERFILE_ENABLE_NATIVE_OCR=1` |
| Native OCR | `tests/person3_ocr` | Native OCR engine | No. Skipped unless native OCR is enabled |
| Live | `tests/live` | Real Anthropic API | No. Needs `ANTHROPIC_API_KEY` and `SILVERFILE_RUN_LIVE_TESTS=1` |

Core command (the same one CI uses):

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 LANGSMITH_TRACING=false LANGCHAIN_TRACING_V2=false \
  python -m pytest tests --ignore=tests/integration --ignore=tests/live --ignore=tests/person3_ocr -q
```

## 1. Results on the merged build (`main` at `aeda711`)

| Result | Environment | Command | Who ran it |
|---|---|---|---|
| **299 passed in 6.18 s** | Python 3.12 | Core command above (excludes `tests/integration`, `tests/live`, `tests/person3_ocr`) | **Externally reported:** run independently by ChatGPT/Codex against `aeda711`. Not run by a team member or by Claude Code |

This is the only recorded result for the merged build.

## 2. Results on earlier stages

| Commit / stage | Result | Environment | Command | Who ran it |
|---|---|---|---|---|
| `942002b` foundation | 10 passed | Windows 11, Python 3.14.7, project `.venv`, plugin autoload disabled | `.venv/Scripts/python.exe -m pytest tests/unit/test_merge_order.py tests/unit/test_foundation_memory_store.py -q` | Claude Code at Hussain's request, on Hussain's machine |
| `d1ac85d` + Person 2 requirements | 54 passed, 13 warnings (third-party `langsmith` deprecation) | Same as above | `.venv/Scripts/python.exe -m pytest tests/person2 tests/unit/test_merge_order.py tests/unit/test_foundation_memory_store.py -q` | Claude Code at Hussain's request, on Hussain's machine |
| `d1ac85d` + Person 3 package | 100 passed (46 + 54), 7 SWIG deprecation warnings | macOS 13.1 arm64, Python 3.11.16 | `.venv/bin/python -m pytest tests/person3 tests/person2 tests/unit/test_merge_order.py tests/unit/test_foundation_memory_store.py -q` (plugin autoload and tracing disabled) | Claude Code at Taylor's request, on Taylor's machine |
| Package preparation (each stage) | 10; 54; 100; 139 (+ Person 4); 299 (+ Persons 5 and 6) | Linux, Python 3.12.14, pytest 9.1.1 | Stage-specific subsets, then the core command | **Externally reported** by the ChatGPT/Codex package preparer |
| Person 4 references | `scripts/build_source_manifest.py` inspected 16 references with zero failed PDF identity checks; hashes and cited page ranges passed | Linux, Python 3.12.14 | `python scripts/build_source_manifest.py` | **Externally reported** by the package preparer. This shows file identity and page existence, not official authentication |
| Person 3 visual check | All six pages of a synthetic draft with Schedule 1-A rendered and reviewed; representative W-2, SSA-style, 1099-R and 1099-DIV fixture images inspected | — | — | **Externally reported** by the package preparer. Samples only |

Results from the original source repository are not results for this build and are not listed.

## 3. Not run / unverified

| Behavior | Covering tests or tooling | Status |
|---|---|---|
| End-to-end draft cases against the hand-worked expected results | `tests/integration/test_end_to_end.py::test_draft_cases_match_hand_worked_results`; `python run.py eval` | Not run |
| Eval case 1 clean run and W-2 provenance chain | `test_eval_case_1_w2_source_chain`; `python run.py demo eval_case_1` | Not run. May be affected by the zero-tolerance wage rule ([KNOWN_LIMITATIONS.md](KNOWN_LIMITATIONS.md#3-calculation-and-audit-limitations)) |
| Eval case 2 human-review round trip | `test_eval_case_2_hitl_round_trip`; `python run.py demo eval_case_2 --review` | Not run |
| Mandatory stops, parallel extraction, review bound, loop guard, restart persistence, duplicate uploads, correction after draft | `tests/integration/test_end_to_end.py` | Not run (skipped) |
| Live-mode plumbing with a fake client | `tests/integration/test_live_path_mocked.py` | Not run (skipped) |
| Real Anthropic calls | `tests/live/test_live_api.py`; `python run.py check` | Not run |
| Native OCR | `tests/person3_ocr` | Blocked by the telemetry issue; 6 tests collect but have not passed |
| Browser workflow and accessibility | `scripts/ui_smoke.py`; manual | Not run |
| Docker | `docker compose up --build` | Not run |
| CI | `.github/workflows/tests.yml` | No GitHub Actions run recorded |
| Context-window experiment | `python run.py benchmark [--no-context-strategy]`, `python run.py metrics` | Not run; no real token counts |

## 4. Outstanding acceptance work

See [KNOWN_LIMITATIONS.md](KNOWN_LIMITATIONS.md) for the complete list. The minimum before submission:

1. A team member re-runs the core command on the merged build and records the result here.
2. Run the OCR-independent integration tests once they are separated from the OCR-gated suite (proposal in [KNOWN_LIMITATIONS.md](KNOWN_LIMITATIONS.md#1-verification-gaps)).
3. Run eval cases 1 and 2 in the browser with live vision, and record what happens.
4. Run the live token experiment and generate `docs/metrics.md`.
5. Build and run the Docker image.
