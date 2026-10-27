# Acceptance results

This lists only results with a recorded source. A passing count means only that the named tests passed. It does not establish behavior those tests do not exercise.

## Test layers

| Layer | Folder | What it uses | In the core command? |
|---|---|---|---|
| Unit / component | `tests/unit`, `tests/intake` … `tests/audit` | Pure functions; agents with an in-process tool stub; `tests/computation/test_mcp_contract.py` starts the real stdio MCP server | Yes |
| Integration, OCR-free | `tests/integration/test_orchestration_synthetic.py`, plus the unmarked tests in `test_end_to_end.py` and `test_live_path_mocked.py` | Real graph, real stdio MCP server, offline back end. Image transcription is replaced by fixture ground truth (`synthetic_documents`) where documents are involved | Yes |
| Integration, image-reading | Tests marked `needs_ocr` in `tests/integration` | Real fixture images through the offline OCR reader | Yes. Skipped only with `SILVERFILE_ENABLE_NATIVE_OCR=0` |
| Native OCR | `tests/native_ocr` | Native OCR engine on the fixture images | Yes. Skipped only with `SILVERFILE_ENABLE_NATIVE_OCR=0` |
| Live | `tests/live` | Real Anthropic API (paid) | No. Excluded; needs `ANTHROPIC_API_KEY` and `SILVERFILE_RUN_LIVE_TESTS=1` |

Core command (the same one CI uses):

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 LANGSMITH_TRACING=false LANGCHAIN_TRACING_V2=false \
  python -m pytest tests --ignore=tests/live -q -rs
```

## 1. Results on the current code

### Local project review: October 27, 2026

Branch: `fix/medicare-and-project-validation`. Run by Codex on this Windows workspace with CPython 3.12.14 and the existing `.venv`. These results apply to this branch and do not replace the historical results below.

Changes: added the `additional_medicare_withheld` MCP tool; calculate each W-2's credit from actual box 6 minus 1.45% of box 5, floored at zero and zero at or below $200,000; aggregate cents before rounding line 25c. Provenance follows each result to boxes 5 and 6. Audit rechecks 25c from published source facts and verifies sources referenced by intermediate calculations. Existing payment totals already include 25c; regression tests now cover nonzero withholding. Schedule 2 tax inputs are unchanged. Fixed the synthetic W-2 extraction helper, which omitted box 6.

Validation:

- Baseline with native OCR disabled: **422 passed, 32 skipped**.
- Final full core suite with native OCR disabled: **437 passed, 32 skipped** in 72.15 seconds.
- Final full core suite with native OCR enabled: **469 passed, 0 skipped** in 269.97 seconds. Command: `$env:SILVERFILE_ENABLE_NATIVE_OCR='1'; .venv/Scripts/python.exe -m pytest tests --ignore=tests/live -q -rs`.
- Affected computation, audit and synthetic integration tests after the helper fix: **209 passed**.
- `python run.py check` with `SILVERFILE_ENABLE_NATIVE_OCR=1`: **all checks passed**; 16 MCP tools; sample W-2 wages read as 46,850.00.
- Python compilation of `src`, `mcp_server`, `scripts`, `run.py`, and `streamlit_app.py`: passed.
- Streamlit `AppTest` startup smoke check: **0 exceptions**; the three sidebar views are present. This does not verify a complete browser workflow.
- All **40 tracked JSON/YAML files** parsed successfully.
- `git diff --check`: passed.

Environment findings: the default local configuration disables native OCR, so `run.py check` reports that uploaded images cannot be read until OCR is enabled. The installed `onnxruntime` is **1.31.0**, while `requirements.txt` pins **1.21.1**. Installed package metadata satisfies its other declared runtime dependency constraints. This virtual environment has no `pip` module; dependency checks used `importlib.metadata` and `packaging` instead. No dependencies or private configuration were changed. Tests require permission to launch MCP subprocesses and access pytest temporary directories on this machine; sandbox permission failures are excluded from the code results above.

Live paid API calls, Docker builds, CI execution, and complete browser workflows were not run in this review. Passing tests do not establish that every possible error is absent.


### Follow-up fixes: October 27, 2026

On the same branch, aligned the local `.venv` with `onnxruntime==1.21.1` using `uv pip install --python .venv/Scripts/python.exe onnxruntime==1.21.1`, and enabled native OCR in the git-ignored local `.env`. Other private settings were preserved. `uv pip check --python .venv/Scripts/python.exe` reports **all installed packages compatible**; `python run.py check` passes without an OCR environment override.

Added `case_high_wage_w2` to the evaluation catalogue with expected values calculated independently of the production tools: taxable income $232,250; tax $51,383; line 25c $600; payments $52,600; refund $1,217. Schedule 2 tax amounts remain direct inputs. `python run.py eval` passed **19/19 cases** with the pinned OCR dependency. The final full core command, `.venv/Scripts/python.exe -m pytest tests --ignore=tests/live -q -rs`, passed **471 tests, 0 skipped** in 529.30 seconds (run concurrently with the fixture evaluation). Traces were generated locally in `traces/` and are not included in the commit. Updated assumptions and limitations to remove obsolete statements about pending 25c implementation and untested Windows fixture OCR.


| Code | Result | Environment | Command | Who ran it |
|---|---|---|---|---|
| Branch `fix/ocr-w2-image-reading` (native OCR on by default), rebased on `main` at `c8b4fc3` | **446 passed, 0 skipped** in 139 s, including the 23 `needs_ocr` image tests and the 6 `tests/native_ocr` accuracy tests | macOS 13.1 arm64, CPython 3.12.14 (separate `uv` environment), `onnxruntime` 1.21.1, `SILVERFILE_ENABLE_NATIVE_OCR` unset (default on), no API key. **Outbound networking denied** with `sandbox-exec` (IP and DNS blocked; checked first with a failing `urlopen`) | Core command above, plus `-p no:cacheprovider`, inside the sandbox | Claude Code at Taylor's request, on Taylor's machine |
| Branch `feat/w2-box6-medicare` (W-2 box 6 extraction and the `case_high_wage_w2` fixture, on top of `fix/ocr-w2-image-reading`) | **453 passed, 0 skipped**; `python run.py eval` 18/18; `python run.py demo case_high_wage_w2` reaches a draft with box 6 read as 4,225.00 (25c stays $0 until the Computation tool exists) | Same as above, network denied | Core command, `run.py eval`, `run.py demo case_high_wage_w2` | Claude Code at Taylor's request |
| Same | `python run.py eval`: **18/18 cases passed** (8 drafts, 10 escalations with the expected reasons); `traces/` written. `python run.py demo eval_case_1`: draft, lines match `evals/expected_results/eval_case_1.json`. `python run.py demo eval_case_2 --review`: `user_document_conflict` raised, resolved with `confirm_document_value`, every line matches `eval_case_2.json`. `python run.py check`: all checks passed, built-in OCR read `demo/w2_image_1.png` box 1 as 46,850.00 | Same, network denied | As listed | Claude Code at Taylor's request |
| `f605ea5` before this change | 372 passed, 23 skipped (same as the Windows run below). `python run.py demo eval_case_1` in offline mode stopped at the upload with `document_problem` and no draft | macOS 13.1, CPython 3.12.14. `requirements.txt` did not install: `onnxruntime==1.31.0` has no macOS 13 wheel, and 1.22–1.23 wheels need macOS 13.4+ | Core command (old form) | Claude Code at Taylor's request |
| Branch `fix/acceptance-validation` (uncommitted working tree on top of `d87de06`) | **372 passed, 23 skipped** in 111 s. The skips are exactly the `needs_ocr` image tests | Windows 11, CPython 3.12.14 (installed with `uv`, in a separate virtual environment), `SILVERFILE_ENABLE_NATIVE_OCR=0`, no API key or model configured | Core command above, plus `-p no:cacheprovider` | Claude Code at Hussain's request, on Hussain's machine |
| `d87de06` (documentation commit; code identical to `aeda711`), before this branch's changes | **299 passed** in 33 s | Same | Previous core command: `python -m pytest tests --ignore=tests/integration --ignore=tests/live --ignore=tests/native_ocr -q` | Claude Code at Hussain's request, on Hussain's machine |
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
| `d1ac85d` + intake requirements | 54 passed, 13 warnings (third-party `langsmith` deprecation) | Same as above | `.venv/Scripts/python.exe -m pytest tests/intake tests/unit/test_merge_order.py tests/unit/test_foundation_memory_store.py -q` | Claude Code at Hussain's request, on Hussain's machine |
| `d1ac85d` + documents package | 100 passed (46 + 54), 7 SWIG deprecation warnings | macOS 13.1 arm64, Python 3.11.16 | `.venv/bin/python -m pytest tests/documents tests/intake tests/unit/test_merge_order.py tests/unit/test_foundation_memory_store.py -q` (plugin autoload and tracing disabled) | Claude Code at Taylor's request, on Taylor's machine |
| Package preparation (each stage) | 10; 54; 100; 139 (plus the rules stage); 299 (plus the computation and audit stages) | Linux, Python 3.12.14, pytest 9.1.1 | Stage-specific subsets, then the previous core command | **Externally reported** by the ChatGPT/Codex package preparer |
| Rules reference check | `scripts/build_source_manifest.py` inspected 16 references with zero failed PDF identity checks; hashes and cited page ranges passed | Linux, Python 3.12.14 | `python scripts/build_source_manifest.py` | **Externally reported** by the package preparer. This shows file identity and page existence, not official authentication |
| Documents visual check | All six pages of a synthetic draft with Schedule 1-A rendered and reviewed; representative W-2, SSA-style, 1099-R and 1099-DIV fixture images inspected | — | — | **Externally reported** by the package preparer. Samples only |

Results from the original source repository are not results for this build and are not listed.

## 3. Not run / unverified

| Behavior | Covering tests or tooling | Status |
|---|---|---|
| Reading document images with Anthropic vision | `tests/live/test_live_api.py::test_live_w2_image_extraction` | Not run; no paid calls were made. Native OCR reading is verified (section 1) |
| Native OCR on Windows | `tests/native_ocr` | Passed in the October 27, 2026 local project review; see section 1 |
| Eval cases 1 and 2 in the browser | `demo/eval_case_*.md` | Not run. The same service calls pass through `python run.py demo` (section 1) |
| Real Anthropic calls | `tests/live`; `python run.py check` with a key | Not run; no paid calls were made |
| Browser workflow and accessibility | `scripts/ui_smoke.py`; manual | Not run |
| Docker | `docker compose up --build` | Not run |
| CI | `.github/workflows/tests.yml` | No GitHub Actions run recorded |
| Context-window experiment | `python run.py benchmark [--no-context-strategy]`, `python run.py metrics` | Not run; no real token counts |

## 4. Outstanding acceptance work

See [KNOWN_LIMITATIONS.md](KNOWN_LIMITATIONS.md) for the complete list. The minimum before submission:

1. Run eval cases 1 and 2 in the browser and record what happens here.
2. Optionally configure an Anthropic key in `.env` (the model defaults to `claude-opus-5-5`) and run `python run.py check`.
3. Run `tests/live` once with `SILVERFILE_RUN_LIVE_TESTS=1` (paid) and record the result.
4. Run the live token experiment and generate `docs/metrics.md`.
5. Build and run the Docker image; confirm a GitHub Actions run of the core command.
