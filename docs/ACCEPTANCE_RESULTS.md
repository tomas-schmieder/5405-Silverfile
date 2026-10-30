# Acceptance results

This records the acceptance results for the submitted build. Section 1 is the final status of every check; sections 2 and 3 keep the dated runs that led there, with the environment and who ran each one.

## 1. Final verification status

| Check | How | Status |
|---|---|---|
| Core automated suite | Core command below (same as CI) | **Passed.** 471 passed, 0 skipped with native OCR on Windows 11 / Python 3.12.14; see section 2 |
| Fixture evaluation | `python run.py eval` | **Passed.** 19/19 cases: 9 drafts matching hand-worked results and 10 escalations with the expected reasons |
| Demo cases | `python run.py demo eval_case_1`; `python run.py demo eval_case_2 --review` | **Passed.** Case 1 reaches a draft; case 2 raises `user_document_conflict`, is resolved, and reaches a draft |
| Eval cases 1 and 2 in the browser | `demo/eval_case_*.md` | **Verified by the team** |
| Browser workflow and dashboard review | Taxpayer intake, employee dashboard, draft and provenance views; `scripts/ui_smoke.py` | **Verified by the team** |
| Accessibility | Keyboard-only use and screen reader | **Verified by the team** |
| Reading W-2 images | Native OCR (no key) and Anthropic vision (with a key) | **Verified.** Native OCR reads every fixture image; live vision ran in the §4.5 benchmark |
| Live Anthropic API | `python run.py check` with a key; `tests/live` with `SILVERFILE_RUN_LIVE_TESTS=1` | **Verified by the team** |
| Context-window experiment (§4.5) | `python run.py benchmark --all` | **Measured.** 173,345 input tokens off vs 42,039 on (76% fewer); see [metrics.md](metrics.md) |
| CI | `.github/workflows/tests.yml` on GitHub Actions | **Verified by the team** |
| Docker | `docker compose up --build`, then the app at http://localhost:8501 | **Verified by the team** |

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

## 2. Results on the current code

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

Live paid API calls, Docker builds, CI execution and browser workflows were outside this review; their final status is in the table at the top.


### Follow-up fixes: October 27, 2026

On the same branch, aligned the local `.venv` with `onnxruntime==1.21.1` using `uv pip install --python .venv/Scripts/python.exe onnxruntime==1.21.1`, and enabled native OCR in the git-ignored local `.env`. Other private settings were preserved. `uv pip check --python .venv/Scripts/python.exe` reports **all installed packages compatible**; `python run.py check` passes without an OCR environment override.

Added `case_high_wage_w2` to the evaluation catalogue with expected values calculated independently of the production tools: taxable income $232,250; tax $51,383; line 25c $600; payments $52,600; refund $1,217. Schedule 2 tax amounts remain direct inputs. `python run.py eval` passed **19/19 cases** with the pinned OCR dependency. The final full core command, `.venv/Scripts/python.exe -m pytest tests --ignore=tests/live -q -rs`, passed **471 tests, 0 skipped** in 529.30 seconds (run concurrently with the fixture evaluation). Traces were generated locally in `traces/` and are not included in the commit. Updated assumptions and limitations to remove obsolete statements about pending 25c implementation and untested Windows fixture OCR.


| Code | Result | Environment | Command | Who ran it |
|---|---|---|---|---|
| Branch `fix/ocr-w2-image-reading` (native OCR on by default), rebased on `main` at `c8b4fc3` | **446 passed, 0 skipped** in 139 s, including the 23 `needs_ocr` image tests and the 6 `tests/native_ocr` accuracy tests | macOS 13.1 arm64, CPython 3.12.14 (separate `uv` environment), `onnxruntime` 1.21.1, `SILVERFILE_ENABLE_NATIVE_OCR` unset (default on), no API key. **Outbound networking denied** with `sandbox-exec` (IP and DNS blocked; checked first with a failing `urlopen`) | Core command above, plus `-p no:cacheprovider`, inside the sandbox | Claude Code at Taylor's request, on Taylor's machine |
| Branch `feat/w2-box6-medicare` (W-2 box 6 extraction and the `case_high_wage_w2` fixture, on top of `fix/ocr-w2-image-reading`) | **453 passed, 0 skipped**; `python run.py eval` 18/18; `python run.py demo case_high_wage_w2` reaches a draft with box 6 read as 4,225.00 (the 25c Computation tool was added afterwards in `b8415ea`) | Same as above, network denied | Core command, `run.py eval`, `run.py demo case_high_wage_w2` | Claude Code at Taylor's request |
| Same | `python run.py eval`: **18/18 cases passed** (8 drafts, 10 escalations with the expected reasons); `traces/` written. `python run.py demo eval_case_1`: draft, lines match `evals/expected_results/eval_case_1.json`. `python run.py demo eval_case_2 --review`: `user_document_conflict` raised, resolved with `confirm_document_value`, every line matches `eval_case_2.json`. `python run.py check`: all checks passed, built-in OCR read `demo/w2_image_1.png` box 1 as 46,850.00 | Same, network denied | As listed | Claude Code at Taylor's request |
| `f605ea5` before this change | 372 passed, 23 skipped (same as the Windows run below). `python run.py demo eval_case_1` in offline mode stopped at the upload with `document_problem` and no draft | macOS 13.1, CPython 3.12.14. `requirements.txt` did not install: `onnxruntime==1.31.0` has no macOS 13 wheel, and 1.22–1.23 wheels need macOS 13.4+ | Core command (old form) | Claude Code at Taylor's request |
| `3ecac4a` (PR #4): the working tree on top of `main` at `7e3afa0`, committed unchanged after the run | **378 passed, 23 skipped** in 116 s. Skip reasons were not printed (no `-rs`). No image-reading, live API or benchmark run was part of this | Windows 11, a fresh Python 3.12 virtual environment created with `uv` and installed from `requirements.txt` (patch version not recorded), `SILVERFILE_ENABLE_NATIVE_OCR` unset (native OCR was off by default at that commit), no API key or model configured | `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 LANGSMITH_TRACING=false LANGCHAIN_TRACING_V2=false python -m pytest tests --ignore=tests/live --ignore=tests/native_ocr -q -p no:cacheprovider` | Claude Code at Hussain's request, on Hussain's machine (session output, 2026-10-27) |
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

### Live context benchmark: October 29, 2026

Hussain ran `python run.py benchmark --all` on Windows 11 with CPython 3.12.14 (project `.venv` installed with `uv` from `requirements.txt`) and `claude-haiku-5-5`. Runs `bench-off-c60e30` and `bench-on-fb3643`. Input tokens: 173,345 with the strategy off versus 42,039 with it on (76% fewer); per call, 4,079 → 30,396 off and 4,103 → 4,405 on. Output tokens: 5,871 off, 4,450 on. Result consistency 10/10. The extraction checks flagged the five 1099-INT and 1099-DIV documents `wrong_year` in both runs (see [KNOWN_LIMITATIONS.md](KNOWN_LIMITATIONS.md)). Claude Code then fixed the report's file encoding and regenerated `docs/metrics.md` from the saved results, with no further API calls. `python run.py check` with the key also passed (one call). See [metrics.md](metrics.md).

## 3. Results on earlier stages

| Commit / stage | Result | Environment | Command | Who ran it |
|---|---|---|---|---|
| `942002b` foundation | 10 passed | Windows 11, Python 3.14.7, project `.venv`, plugin autoload disabled | `.venv/Scripts/python.exe -m pytest tests/unit/test_merge_order.py tests/unit/test_foundation_memory_store.py -q` | Claude Code at Hussain's request, on Hussain's machine |
| `d1ac85d` + intake requirements | 54 passed, 13 warnings (third-party `langsmith` deprecation) | Same as above | `.venv/Scripts/python.exe -m pytest tests/intake tests/unit/test_merge_order.py tests/unit/test_foundation_memory_store.py -q` | Claude Code at Hussain's request, on Hussain's machine |
| `d1ac85d` + documents package | 100 passed (46 + 54), 7 SWIG deprecation warnings | macOS 13.1 arm64, Python 3.11.16 | `.venv/bin/python -m pytest tests/documents tests/intake tests/unit/test_merge_order.py tests/unit/test_foundation_memory_store.py -q` (plugin autoload and tracing disabled) | Claude Code at Taylor's request, on Taylor's machine |
| Package preparation (each stage) | 10; 54; 100; 139 (plus the rules stage); 299 (plus the computation and audit stages) | Linux, Python 3.12.14, pytest 9.1.1 | Stage-specific subsets, then the previous core command | **Externally reported** by the ChatGPT/Codex package preparer |
| Rules reference check | `scripts/build_source_manifest.py` inspected 16 references with zero failed PDF identity checks; hashes and cited page ranges passed | Linux, Python 3.12.14 | `python scripts/build_source_manifest.py` | **Externally reported** by the package preparer. This shows file identity and page existence, not official authentication |
| Documents visual check | All six pages of a synthetic draft with Schedule 1-A rendered and reviewed; representative W-2, SSA-style, 1099-R and 1099-DIV fixture images inspected | — | — | **Externally reported** by the package preparer. Samples only |

Results from the original source repository are not results for this build and are not listed.
