# Known limitations and remaining validation

This list consolidates every unresolved item from the removed per-person handoff documents, plus issues found since. The removed documents were: foundation status (Hussain), intake (Kezia), documents and review record (Taylor), rules (Anastasia), and the computation (Anjana) and integration (Tomas) handoffs. Items resolved on branch `fix/acceptance-validation` are marked **Resolved (this branch)**, with what still remains.

## 1. Verification gaps

| Area | Status |
|---|---|
| Core automated suite | **Passed:** 372 passed and 23 skipped on Windows 11, Python 3.12.14, with the expanded core command (run by Claude Code at Hussain's request on this branch). Earlier, ChatGPT/Codex independently reported 299 passed on `aeda711`. See [ACCEPTANCE_RESULTS.md](ACCEPTANCE_RESULTS.md) |
| `tests/integration` | **Resolved (this branch).** Only tests marked `needs_ocr` are skipped. The OCR-independent tests run in the core command and CI: loop-guard cycle, restart persistence, intake-only stops, structured-output retry, plus `test_orchestration_synthetic.py`. **Remaining:** the 23 `needs_ocr` tests (real fixture images) have not run |
| Synthetic extraction | The orchestration, review-bound, loop-guard, parallel-extraction and draft-case tests replace image transcription with fixture ground truth (`synthetic_documents` in `tests/conftest.py`). They test everything after reading a document. They are **not** evidence that images are read correctly |
| Reading document images | **Not verified**, by either path. Live vision needs a key and model (none configured here); native OCR is blocked (section 2). Reading a W-2 image is graded (rubric D.3) |
| Browser workflow | Not verified: full taxpayer flow, dashboard review, provenance view, accessibility with a screen reader or keyboard only. `scripts/ui_smoke.py` exists; no recorded run |
| Live Anthropic API | Not verified: real model extraction, intake interpretation, audit critique, line explanations. `tests/live` needs `ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL` and `SILVERFILE_RUN_LIVE_TESTS=1`, and makes paid calls |
| Model identifier | **Resolved (this branch):** there is no default model. Anthropic mode without `ANTHROPIC_API_KEY` and `ANTHROPIC_MODEL` stops with a configuration error (`ModelConfigError`; `run.py check` reports which is missing, without values). **Remaining:** no `.env`, key or model is configured on the verification machine. The team must choose a vision + structured-output model available to its account ([ASSUMPTIONS.md](ASSUMPTIONS.md) Q-05) |
| Hard-stop routing and resume | Stops and the human-review round trip run with synthetic extraction (above). With real images, and resumed in the browser, they are not verified |
| Full fixture evaluations | `python run.py eval` reads images, so it has not been run on this build |
| Docker | `Dockerfile` and `compose.yaml` (Python 3.12) supplied; no build or run recorded |
| CI | `.github/workflows/tests.yml` (Python 3.12) runs the expanded core command; no GitHub Actions run recorded |
| Dependency lock | `requirements.txt` pins direct dependencies only; a tested transitive lock still needs to be produced by the deployment owner |

## 2. Native OCR telemetry issue (blocked; do not bypass)

The automatic approval review blocked the native OCR test process after it attempted a Microsoft telemetry request with an unknown payload, even though `onnxruntime.disable_telemetry_events()` was called before initializing OCR.

- No successful native OCR result is claimed. The six tests in `tests/person3_ocr/` collect but have not passed.
- The backend stays disabled unless `SILVERFILE_ENABLE_NATIVE_OCR=1`. Do not enable it in a normal environment just to bypass the block. It was not enabled for any run on this branch.
- **Next step:** coordinate with DevOps to install the optional dependencies in a disposable environment with real network isolation (for example, a container run with networking disabled) before enabling and testing. Installation needs network access beforehand; the OCR test run should not.
- Resolve native-wheel compatibility separately, using Python 3.12, rather than silently replacing pins.
- **Consequence:** offline-mode image reading and the 23 `needs_ocr` tests depend on this. The intended application path for images is Anthropic vision.

## 3. Calculation and audit limitations

- **Audit recomputation of 6b and 13b.** **Resolved (this branch).**
  - The audit calls a new MCP tool, `recheck_social_security_and_senior`, which re-derives 6a, 6b, 11b and 13b from the published source-document amounts, confirmed direct inputs and dates of birth. It does not use the proposed lines, and fails the audit when they disagree.
  - It is a separate implementation (closed-form worksheet; it does not call the production 6b/13b functions). It is in the same module and was written by the same AI tool, so it is not an independent-author oracle.
  - Production rounds each worksheet step to cents and the recheck rounds once, so 6b, 11b and 13b allow a **$1** difference; 6a is exact. A $1 error in those lines would not be caught. **This tolerance still needs team review** ([ASSUMPTIONS.md](ASSUMPTIONS.md) Q-07).
  - Regression tests: `tests/person6/test_audit_recheck.py` and `tests/integration/test_orchestration_synthetic.py`.
- **Remaining audit gaps.** Other lines are still checked only for internal consistency (`verify_return`). Source values themselves are re-verified against `source_facts`, not against the images.
- **Line 16 re-check is a consistency check, not an oracle.** `verify_return` re-checks qualified-dividend line 16 using the same worksheet implementation.
- **Line 25c is always $0. Ambiguous; behavior unchanged pending a team decision.**
  - Assignment §3.1 lists "25a–25d | Federal income tax withheld | W-2 / 1099 forms".
  - §3.3 lists in-scope amounts as coming from W-2, SSA-1099, 1099-R, 1099-INT and 1099-DIV.
  - The 2025 Form 1040 instructions (p. 39, line 25c "Other Forms") put four kinds of withholding on 25c:
    - Form W-2G
    - Additional Medicare Tax withheld (Form 8959, line 24)
    - Schedule K-1
    - Forms 1042-S, 8805 and 8288-A
  - W-2G, K-1, 1042-S, 8805 and 8288-A come from income the assignment does not list as in scope. But Additional Medicare Tax withholding is reported on an in-scope W-2 (Medicare tax in box 6 above 1.45% of box 5 wages, which applies to wages over $200,000).
  - The assignment neither includes nor excludes Form 8959. `R-WH-01` treats it as out of scope, and no fixture reaches that wage level.
  - See [ASSUMPTIONS.md](ASSUMPTIONS.md) Q-01.
- **Zero-tolerance wage comparison (kept).**
  - Any difference between stated wages and a W-2 asks the taxpayer one confirmation question, and an unresolved one escalates. This is an engineering choice, not a professor-specified threshold.
  - Intake does not record how approximate an estimate was, so extra questions are possible. Kezia (intake) should review the clarification wording with Anastasia (rules).
- **Eval-case expectations and zero tolerance. Resolved (this branch).**
  - `eval_case_1`, `grader_style_unseen`, `case_mfj_high_income` and `case_hoh_dependent` now answer the `conflict-wages` follow-up with "The W-2 is right", in both their `case.json` files and `data/generate_fixtures.py`. `eval_case_2` keeps "My number is right" and its reviewer action.
  - [demo/eval_case_1.md](../demo/eval_case_1.md) has the extra step.
  - Behavior was checked with synthetic extraction only: all four reach a draft after one confirmation, and eval case 1 without the answer stops for a person. The image-based runs are still unverified.
- **Conservative QCD age screen.** Uncertain age or timing cases go to a person. Review this and other assumptions against the assignment.
- **Test-only tool stub.** The Decimal summation and comparison in `tests/person4/conftest.py` do not substitute for the production MCP tools.

## 4. Document extraction, provenance and output

- Real-model extraction accuracy and native OCR accuracy are unproven; the core tests use injected payloads, controlled tokens and synthetic records.
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
- **Source manifests are historical.** `docs/*_sources.json` record package contents at import time, including the now-deleted handoff files and earlier hashes of edited files. They are attribution records and are intentionally not rewritten.
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
