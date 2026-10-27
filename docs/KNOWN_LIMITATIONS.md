# Known limitations and remaining validation

This list consolidates every unresolved item from the removed per-person handoff documents, plus issues found since. The removed documents were: foundation status (Hussain), intake (Kezia), documents and review record (Taylor), rules (Anastasia), and the computation (Anjana) and integration (Tomas) handoffs. Items resolved on branch `fix/acceptance-validation` are marked **Resolved (this branch)**, with what still remains.

## 1. Verification gaps

| Area | Status |
|---|---|
| Core automated suite | **Passed:** 471 tests with native OCR enabled on Windows, Python 3.12.14, in the October 27, 2026 local project review. See [ACCEPTANCE_RESULTS.md](ACCEPTANCE_RESULTS.md) for subsequent runs and historical results |
| `tests/integration` | **Resolved.** All integration tests run in the core command and CI, including the 23 `needs_ocr` image tests (native OCR is on by default). They skip only with `SILVERFILE_ENABLE_NATIVE_OCR=0` |
| Synthetic extraction | The orchestration, review-bound, loop-guard, parallel-extraction and draft-case tests replace image transcription with fixture ground truth (`synthetic_documents` in `tests/conftest.py`). They test everything after reading a document. They are **not** evidence that images are read correctly |
| Reading document images | **Resolved (native OCR).** Native OCR is on by default and reads the fixture images: 446 passed with no skips, and `python run.py eval` passed 18/18, with outbound networking denied on macOS 13.1 ([ACCEPTANCE_RESULTS.md](ACCEPTANCE_RESULTS.md)). **Remaining:** live vision is still unrun (no paid calls), and OCR accuracy on photos (rather than clean scans) is untested |
| Browser workflow | Not verified: full taxpayer flow, dashboard review, provenance view, accessibility with a screen reader or keyboard only. `scripts/ui_smoke.py` exists; no recorded run |
| Live Anthropic API | Not verified: real model extraction, intake interpretation, audit critique, line explanations. `tests/live` needs `ANTHROPIC_API_KEY` and `SILVERFILE_RUN_LIVE_TESTS=1`, and makes paid calls |
| Model identifier | **Resolved.** `ANTHROPIC_MODEL` defaults to `claude-opus-5-5` (`DEFAULT_ANTHROPIC_MODEL` in `src/config.py`), so live mode needs only `ANTHROPIC_API_KEY`. Anthropic mode without a key stops with `ModelConfigError`; the default `auto` mode falls back to offline. **Remaining:** no paid call has been made with the default model |
| Hard-stop routing and resume | Stops and the eval case 2 human-review round trip run with real fixture images through native OCR (`python run.py eval`, `run.py demo eval_case_2 --review`). Resuming in the browser is not verified |
| Full fixture evaluations | **Resolved.** `python run.py eval` passed 18/18 with native OCR and networking denied ([ACCEPTANCE_RESULTS.md](ACCEPTANCE_RESULTS.md)) |
| Docker | `Dockerfile` and `compose.yaml` (Python 3.12) supplied; no build or run recorded |
| CI | `.github/workflows/tests.yml` (Python 3.12) runs the expanded core command; no GitHub Actions run recorded |
| Dependency lock | `requirements.txt` pins direct dependencies only; a tested transitive lock still needs to be produced by the deployment owner |

## 2. Native OCR telemetry history and Windows validation

An earlier Windows run had its native OCR test process blocked by an automatic approval review after it attempted a Microsoft telemetry request, even though `onnxruntime.disable_telemetry_events()` was called first.

- **Network-isolated verification (done).** On macOS 13.1, with outbound IP and DNS denied by `sandbox-exec`, the full suite passed with native OCR on (446 passed, 0 skipped, including `tests/native_ocr` and the `needs_ocr` tests), and `python run.py eval` passed 18/18. The OCR models ship inside `rapidocr-onnxruntime`, and the package contains no download code, so the reader needs no network.
- **Telemetry.** ONNX Runtime's telemetry is a Windows-only (ETW) feature, so it does not exist on macOS, Linux or the Docker image. The code still calls `disable_telemetry_events()` before initializing OCR.
- **Pin.** `onnxruntime` is pinned to 1.21.1: 1.31.0 has no macOS 13 wheel, and the 1.22–1.23 wheels need macOS 13.4 or later. 1.21.1 has Python 3.12 wheels for Windows, Linux and macOS.
- **Default.** Native OCR is now on by default; `SILVERFILE_ENABLE_NATIVE_OCR=0` turns it off.
- **Windows validation:** the October 27, 2026 project review passed 469 core tests with OCR enabled, including all native OCR tests. The follow-up full suite passed 471 tests with the 1.21.1 pin, and fixture evaluation passed 19/19 cases; see [ACCEPTANCE_RESULTS.md](ACCEPTANCE_RESULTS.md). This does not establish that Windows telemetry is absent or network-isolated.

## 3. Calculation and audit limitations

- **Audit recomputation of 6b and 13b.** **Resolved (this branch).**
  - The audit calls a new MCP tool, `recheck_social_security_and_senior`, which re-derives 6a, 6b, 11b and 13b from the published source-document amounts, confirmed direct inputs and dates of birth. It does not use the proposed lines, and fails the audit when they disagree.
  - It is a separate implementation (closed-form worksheet; it does not call the production 6b/13b functions). It is in the same module and was written by the same AI tool, so it is not an independent-author oracle.
  - The recheck rounds to cents at the same worksheet steps as production, so 6a, 6b, 11b and 13b are compared exactly and a $1 error fails the audit ([ASSUMPTIONS.md](ASSUMPTIONS.md) Q-07).
  - Regression tests: `tests/audit/test_audit_recheck.py` and `tests/integration/test_orchestration_synthetic.py`.
- **Remaining audit gaps.** Lines other than the source-recomputed 6a, 6b, 11b, 13b and 25c are still checked only for internal consistency (`verify_return`). Source values themselves are re-verified against `source_facts`, not against the images.
- **Line 16 re-check is a consistency check, not an oracle.** `verify_return` re-checks qualified-dividend line 16 using the same worksheet implementation.
- **Line 25c Additional Medicare withholding: resolved.** The MCP tool computes each W-2's actual box 6 withholding less 1.45% of box 5, floored at zero and zero when box 5 is at or below $200,000. Computation aggregates the results with source provenance; audit rechecks from published W-2 facts. Schedule 2 tax remains a direct input. The high-wage fixture is included in the evaluation catalogue with independently calculated expected results. Other out-of-scope withholding forms remain excluded.
- **Zero-tolerance wage comparison (kept).**
  - Any difference between stated wages and a W-2 asks the taxpayer one confirmation question, and an unresolved one escalates. This is an engineering choice, not a professor-specified threshold.
  - Intake does not record how approximate an estimate was, so extra questions are possible. The wage-conflict clarification wording was reviewed across the intake and rules workstreams and retained as the agreed behavior.
- **Eval-case expectations and zero tolerance. Resolved (this branch).**
  - `eval_case_1`, `grader_style_unseen`, `case_mfj_high_income` and `case_hoh_dependent` now answer the `conflict-wages` follow-up with "The W-2 is right", in both their `case.json` files and `data/generate_fixtures.py`. `eval_case_2` keeps "My number is right" and its reviewer action.
  - [demo/eval_case_1.md](../demo/eval_case_1.md) has the extra step.
  - Behavior was checked with synthetic extraction only: all four reach a draft after one confirmation, and eval case 1 without the answer stops for a person. The image-based runs are still unverified.
- **Conservative QCD age screen.** Uncertain age or timing cases go to a person. Review this and other assumptions against the assignment.
- **Test-only tool stub.** The Decimal summation and comparison in `tests/rules/conftest.py` do not substitute for the production MCP tools.

## 4. Document extraction, provenance and output

- Real-model extraction accuracy is unproven. Native OCR reads every fixture image correctly (`tests/native_ocr`, `python run.py eval`), but the fixtures are clean generated images; phone photos, skew and other W-2 layouts are untested. The reader reports unreadable boxes rather than guessing.
- Uploads must be normalized image bytes. Multi-page PDFs are now rejected; page selection or splitting with page provenance is not implemented.
- The service contract uses `uploaded_at` for manual-entry provenance timestamps; integration must preserve it.
- The full-SSN digest is an equality token for fictional data, not anonymization of real SSNs. Redaction is not production PII security, and there is no pre-model upload privacy filter.
- PDF checks are field/readback and rendered-text checks, not a guarantee of layout quality. Long names and other visual edge cases are untested beyond the inspected samples.
- Template hashes must be preserved and reconciled when adding references or the final dependency lock.

## 5. Rules and references

- References in `data/reference_tax_forms/` were AI-assembled, not supplied by the professor. `data/source_manifest.json` establishes local file identity and page existence, not official download authentication or the correctness of every citation's interpretation. A separate reference packet was added under `tax-forms/` on `main` (`da02590`); it is not wired into the code.
- The historical SSA GIFs are layout references only, not 2025 tax-rule authorities.
- Live-model screening is unverified.

## 6. Documentation and wording gaps

- **Documents referenced by code.** [ASSUMPTIONS.md](ASSUMPTIONS.md), [STATE_CONTRACT.md](STATE_CONTRACT.md) and [ACCEPTANCE_RESULTS.md](ACCEPTANCE_RESULTS.md) exist, so the references in `data/policy.md`, `data/rule_registry.json`, `src/money.py`, `src/agents/return_assembly.py`, `scripts/context_benchmark.py`, `src/state.py`, `src/contracts.py` and `tests/conftest.py` resolve. Still unresolved:
  - `tests/unit/test_graph_shape.py` docstring mentions `docs/graph.png`, which does not exist. The README Mermaid diagram is the diagram of record.
  - `docs/metrics.md` (referenced by `run.py` and `scripts/context_benchmark.py`) and `docs/graph.mmd` (`run.py`) are generated outputs that have not been produced.
- **Classroom wording.** Some "classroom" wording remains: the SSN rejection message (`src/ssn.py`; intake translates it), the intake system prompt, and comments. Other agents' messages and PDF labels still need their owners' wording review.
- **Source manifests are historical.** `docs/*_sources.json` record import-time hashes, including removed handoff files and earlier hashes of files edited since import. Paths in those records use the current directory names. |
- **Python version. Resolved (this branch).**
  - The standard is Python 3.12: Docker `python:3.12-slim`, CI `3.12`, `.python-version`.
  - Verification on this branch used CPython 3.12.14, installed with `uv` into a separate environment. Existing environments were not removed.
  - Earlier member runs used 3.11.16 (Taylor) and 3.14.7 (Hussain's `.venv`); those results stay as recorded.
- **Dashboard identity.** The dashboard has no login; reviewer names are self-declared.

## 7. Outstanding submission deliverables

| Deliverable | Status |
|---|---|
| Real on/off token measurements in `docs/metrics.md` (§4.5) | **Not produced.** Needs a configured model. Proxy counts or old source-repository results must not be presented as measurements |
| Five-page report (bonus) | **Not written.** [REPORT_AND_DEMO_CHECKLIST.md](REPORT_AND_DEMO_CHECKLIST.md) is an outline only |
| Demo video, 5–10 minutes | **Not recorded** |
| Specialization table (assignment §1.1) | **Proposed, pending each member's agreement.** See [CONTRIBUTIONS.md](CONTRIBUTIONS.md) |
| Member contribution records | Personal reviews pending for all six members. See [CONTRIBUTIONS.md](CONTRIBUTIONS.md) |
| Orchestration diagram | The README has a Mermaid diagram transcribed from `src/graph.py`. No image file exists |
| `traces/` | Not committed; `python run.py eval` writes it |
| Docker acceptance (bonus) | Unverified (see section 1) |
