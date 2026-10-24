# Acceptance results

This lists only results with a recorded source. A passing count means only that the named tests passed. It does not establish behavior those tests do not exercise.

## Test layers

| Layer | Folder | What it uses | In the core command? |
|---|---|---|---|
| Unit / component | `tests/unit`, `tests/person2` … `tests/person6` | Pure functions; agents with an in-process tool stub; `tests/person5/test_mcp_contract.py` starts the real stdio MCP server | Yes |
| Integration, OCR-free | `tests/integration/test_orchestration_synthetic.py`, plus the unmarked tests in `test_end_to_end.py` and `test_live_path_mocked.py` | Real graph, real stdio MCP server, offline back end. Image transcription is replaced by fixture ground truth (`synthetic_documents`) where documents are involved | Yes |
| Integration, image-reading | Tests marked `needs_ocr` in `tests/integration` | Real fixture images through the offline OCR reader | No. Skipped unless `SILVERFILE_ENABLE_NATIVE_OCR=1` |
| Native OCR | `tests/person3_ocr` | Native OCR engine | No. Excluded and self-skipping |
| Live | `tests/live` | Real Anthropic API (paid) | No. Excluded; needs `ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL` and `SILVERFILE_RUN_LIVE_TESTS=1` |

Core command (the same one CI uses):

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 LANGSMITH_TRACING=false LANGCHAIN_TRACING_V2=false \
  python -m pytest tests --ignore=tests/live --ignore=tests/person3_ocr -q -rs
```

## 1. Results on the current code

| Code | Result | Environment | Command | Who ran it |
|---|---|---|---|---|
| Branch `fix/acceptance-validation` (uncommitted working tree on top of `d87de06`) | **372 passed, 23 skipped** in 111 s. The skips are exactly the `needs_ocr` image tests | Windows 11, CPython 3.12.14 (installed with `uv`, in a separate virtual environment), `SILVERFILE_ENABLE_NATIVE_OCR=0`, no API key or model configured | Core command above, plus `-p no:cacheprovider` | Claude Code at Hussain's request, on Hussain's machine |
| `d87de06` (documentation commit; code identical to `aeda711`), before this branch's changes | **299 passed** in 33 s | Same | Previous core command: `python -m pytest tests --ignore=tests/integration --ignore=tests/live --ignore=tests/person3_ocr -q` | Claude Code at Hussain's request, on Hussain's machine |
| `aeda711` | **299 passed in 6.18 s** | Python 3.12 | Previous core command | **Externally reported:** run independently by ChatGPT/Codex. Not run by a team member |
| Branch `fix/acceptance-validation` | `python run.py check`: form templates ok; real stdio MCP server ok (15 tools; test call returned 12e $17,750); model mode offline; API key present: no; `ANTHROPIC_MODEL` set: no. With `SILVERFILE_LLM_MODE=anthropic`, the check reports the missing key and model and fails, as intended | Same Windows machine | `python run.py check` | Claude Code at Hussain's request. No API call was made |

What the 372 include beyond the 299:
- 25 fixture-definition checks
- 9 audit-recheck tests (one compares against production on 1,500 random valid returns)
- 6 model-configuration tests
- 10 OCR-free tests in `test_end_to_end.py` / `test_live_path_mocked.py`
- 23 synthetic-extraction orchestration tests:
  - all eight draft cases matching `evals/expected_results`
  - the four wage-confirmation cases
  - eval case 2's human-review round trip
  - document-driven stops
  - parallel extraction
  - review cycle and review bound
  - loop-guard hand-off cap
  - audit detection of a wrong 6b with consistent totals

## 2. Results on earlier stages

| Commit / stage | Result | Environment | Command | Who ran it |
|---|---|---|---|---|
| `942002b` foundation | 10 passed | Windows 11, Python 3.14.7, project `.venv`, plugin autoload disabled | `.venv/Scripts/python.exe -m pytest tests/unit/test_merge_order.py tests/unit/test_foundation_memory_store.py -q` | Claude Code at Hussain's request, on Hussain's machine |
| `d1ac85d` + Person 2 requirements | 54 passed, 13 warnings (third-party `langsmith` deprecation) | Same as above | `.venv/Scripts/python.exe -m pytest tests/person2 tests/unit/test_merge_order.py tests/unit/test_foundation_memory_store.py -q` | Claude Code at Hussain's request, on Hussain's machine |
| `d1ac85d` + Person 3 package | 100 passed (46 + 54), 7 SWIG deprecation warnings | macOS 13.1 arm64, Python 3.11.16 | `.venv/bin/python -m pytest tests/person3 tests/person2 tests/unit/test_merge_order.py tests/unit/test_foundation_memory_store.py -q` (plugin autoload and tracing disabled) | Claude Code at Taylor's request, on Taylor's machine |
| Package preparation (each stage) | 10; 54; 100; 139 (+ Person 4); 299 (+ Persons 5 and 6) | Linux, Python 3.12.14, pytest 9.1.1 | Stage-specific subsets, then the previous core command | **Externally reported** by the ChatGPT/Codex package preparer |
| Person 4 references | `scripts/build_source_manifest.py` inspected 16 references with zero failed PDF identity checks; hashes and cited page ranges passed | Linux, Python 3.12.14 | `python scripts/build_source_manifest.py` | **Externally reported** by the package preparer. This shows file identity and page existence, not official authentication |
| Person 3 visual check | All six pages of a synthetic draft with Schedule 1-A rendered and reviewed; representative W-2, SSA-style, 1099-R and 1099-DIV fixture images inspected | — | — | **Externally reported** by the package preparer. Samples only |

Results from the original source repository are not results for this build and are not listed.

## 3. Not run / unverified

| Behavior | Covering tests or tooling | Status |
|---|---|---|
| Reading real document images (W-2 from image, rubric D.3) | `needs_ocr` tests; `tests/person3_ocr`; `tests/live/test_live_api.py::test_live_w2_image_extraction` | Not run. No model configured; native OCR blocked |
| Eval cases 1 and 2 with their images, in the browser or `python run.py demo` | `demo/eval_case_*.md`; `python run.py demo …` | Not run. The synthetic-extraction equivalents pass |
| `python run.py eval` over all fixtures | `run.py eval` | Not run (reads images) |
| Live-mode plumbing with a fake client on eval case 1 | `test_live_path_mocked.py` (two `needs_ocr` tests) | Not run |
| Real Anthropic calls | `tests/live`; `python run.py check` with a configured model | Not run; no paid calls were made |
| Browser workflow and accessibility | `scripts/ui_smoke.py`; manual | Not run |
| Docker | `docker compose up --build` | Not run |
| CI | `.github/workflows/tests.yml` | No GitHub Actions run recorded |
| Context-window experiment | `python run.py benchmark [--no-context-strategy]`, `python run.py metrics` | Not run; no real token counts |

## 4. Outstanding acceptance work

See [KNOWN_LIMITATIONS.md](KNOWN_LIMITATIONS.md) for the complete list. The minimum before submission:

1. Configure an Anthropic key and a vision-capable model in `.env`, then run `python run.py check`.
2. Run eval cases 1 and 2 with their images (browser and `python run.py demo`) and record what happens here.
3. Run `tests/live` once with `SILVERFILE_RUN_LIVE_TESTS=1` (paid) and record the result.
4. Run the live token experiment and generate `docs/metrics.md`.
5. Build and run the Docker image; confirm a GitHub Actions run of the core command.
