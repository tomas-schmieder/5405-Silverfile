# Known limitations and remaining validation

This list consolidates every unresolved item from the removed per-person handoff documents, plus issues found while consolidating them. The removed documents were: foundation status (Hussain), intake (Kezia), documents and review record (Taylor), rules (Anastasia), and the computation (Anjana) and integration (Tomas) handoffs. Nothing here has been fixed by the documentation cleanup.

## 1. Verification gaps

| Area | Status |
|---|---|
| Core automated suite | **Externally reported:** ChatGPT/Codex ran it independently against `aeda711`: 299 passed in 6.18 s on Python 3.12. No team member has recorded their own run on this build. Earlier stage results are in [ACCEPTANCE_RESULTS.md](ACCEPTANCE_RESULTS.md) |
| `tests/integration` (end-to-end) | **Not run.** `tests/integration/conftest.py` skips the whole folder unless `SILVERFILE_ENABLE_NATIVE_OCR=1`, and the core command also `--ignore`s it. This folder holds the only tests for the eval cases, mandatory stops, parallel extraction, the bounded review cycle, the **loop guard**, and restart persistence. Several of these do not read images (see below) |
| `tests/integration/test_live_path_mocked.py` | Fake-client live-path checks. Skipped with the folder above |
| Browser workflow | Not verified: full taxpayer flow, dashboard review, provenance view, accessibility with a screen reader or keyboard only. `scripts/ui_smoke.py` exists; no recorded run |
| Live Anthropic API | Not verified: real model extraction, intake interpretation, audit critique, line explanations. `tests/live` needs a key and `SILVERFILE_RUN_LIVE_TESTS=1` |
| Model identifier | No model identifier is assumed valid for any account. `src/config.py` falls back to a built-in default when `ANTHROPIC_MODEL` is empty; each user must set a model available to them. Keep keys out of Git |
| Hard-stop routing and resume | Not verified end to end: every §4.4 condition, stale-data handling, SQLite persistence across restart |
| Full fixture evaluations | `python run.py eval` has not been re-run on the merged build |
| Docker | `Dockerfile` and `compose.yaml` supplied; no build or run recorded (Docker was unavailable on the preparation host) |
| CI | `.github/workflows/tests.yml` supplied; no GitHub Actions run claimed |
| Dependency lock | `requirements.txt` pins direct dependencies only; a tested transitive lock still needs to be produced by the deployment owner |

### Which integration tests need image OCR (from reading the tests; nothing was run)

All of these use `service_factory` (`tests/conftest.py`): the real stdio MCP server and `OfflineLLM`. In offline mode, an uploaded image is read by OCR, so a test needs OCR exactly when it uploads an image and waits for extraction.

| Test (`tests/integration/…`) | Uploads images? | Needs OCR? |
|---|---|---|
| `test_loop_guard_breaks_pathological_handoff_cycle` | No. `create_case()` only, with a stuck `rules` override | **No** |
| `test_persistence_across_restart` | No. Three intake answers, then a new service on the same data directory | **No** |
| `test_mandatory_stops[...]` for `stop_advice`, `stop_spouse_died`, `stop_exploitation`, `stop_third_party`, `stop_crypto`, `stop_itemize`, `stop_too_young` | No (fixtures have no documents) | **No** |
| `test_mandatory_stops[...]` for `stop_1099r_2b`, `stop_capital_gain_dist`, `stop_real_ssn_w2` | Yes | Yes |
| `test_out_of_scope_can_only_be_referred` | Yes (`stop_1099r_2b`) | Yes |
| `test_done_without_files_explains_and_waits` | Only in its final step | Only the final step |
| `test_loop_guard_handoff_cap` | Yes (`eval_case_1` must reach assembly) | Yes, as written |
| `test_review_revise_cycle_is_bounded_and_recovers`, `test_review_bound_escalates` | Yes (`eval_case_1`) | Yes, as written |
| `test_parallel_extraction_and_aggregation` | Yes (`case_mfj_high_income`, three images) | Yes, as written |
| `test_draft_cases_match_hand_worked_results`, `test_eval_case_1_w2_source_chain`, `test_eval_case_2_hitl_round_trip`, `test_duplicate_upload_and_duplicate_content`, `test_correction_after_draft_invalidates_and_recomputes` | Yes | Yes |
| `test_live_path_mocked.py::test_invalid_structured_output_is_retried_once` | No (fake client, no service) | **No** |
| `test_live_path_mocked.py::test_live_mode_runs_case_1_with_model_calls`, `test_context_strategy_flattens_intake_tokens` | Yes (the fake client uses OCR for images) | Yes |

The reducer behavior behind parallel extraction is already covered without OCR by `tests/unit/test_merge_order.py`, which is in the core suite.

**Proposed separation (not implemented; it would change tests):**

1. Mark tests by need instead of skipping the whole folder: add a pytest marker such as `needs_ocr`, and change `tests/integration/conftest.py` to skip only items carrying it (rather than every item whose path contains `integration`).
2. Move the OCR-independent tests above into their own module, for example `tests/integration_core/`, and add it to the core command and CI. They need the stdio MCP server, which the core suite already starts in `tests/person5/test_mcp_contract.py`.
3. Give the remaining orchestration tests (review bound, hand-off cap, parallel extraction) an OCR-free path. Typed-in documents (`SilverFileService.add_manual_document`) are accepted for non-W-2 forms and skip image reading. A fixture with, for example, a 1099-INT and an SSA-1099 entered manually would exercise the parallel fan-out and the downstream review/assembly loop without OCR. The W-2 image path stays in the OCR-gated or live suite.
4. Keep `tests/person3_ocr` and the image-based end-to-end cases gated until native OCR has been validated in an isolated environment.

## 2. Native OCR telemetry issue (blocked; do not bypass)

The automatic approval review blocked the native OCR test process after it attempted a Microsoft telemetry request with an unknown payload, even though `onnxruntime.disable_telemetry_events()` was called before initializing OCR.

- No successful native OCR result is claimed. The six tests in `tests/person3_ocr/` collect but have not passed.
- The backend stays disabled unless `SILVERFILE_ENABLE_NATIVE_OCR=1`. Do not enable it in a normal environment just to bypass the block.
- **Next step:** coordinate with DevOps to install the optional dependencies in a disposable environment with real network isolation (for example, a container run with networking disabled) before enabling and testing. Installation needs network access beforehand; the OCR test run should not.
- Resolve native-wheel compatibility separately, using the team Python target rather than silently replacing pins.
- **Consequence:** offline-mode image reading, and therefore the integration suite, depends on this. Reading a W-2 image is a graded item (rubric D.3), so it must be shown working through live vision or isolated OCR.

## 3. Calculation and audit limitations

- **Audit coverage is incomplete.** The audit does not independently recompute taxable Social Security (6b) or the enhanced senior deduction (13b) from original facts. Add that check before claiming full audit coverage.
- **Line 16 re-check is a consistency check, not an oracle.** `verify_return` re-checks qualified-dividend line 16 using the same worksheet implementation.
- **Line 25c is always $0.** The inherited computation path sets it to zero (rule R-WH-01: no other withholding forms in scope). Review against the assignment's direct-input expectations.
- **Zero-tolerance wage comparison.** Any difference between stated wages and a W-2 asks the taxpayer, and an unresolved one escalates. This is an engineering choice, not a professor-specified threshold. Intake does not record how approximate an estimate was, so extra questions are possible. Kezia (intake) should review the clarification wording with Anastasia (rules).
- **Eval expectations are not reconciled with that rule.** This comes from reading the code; the case has not been run, so no pass or fail is claimed.
  - **The rule.** `src/agents/eligibility_rules.py` (final mode, `R-CONFLICT-01`) calls MCP `compare_amounts` with `abs_tolerance="0"` and `rel_tolerance="0"`. `compare_amounts` (`src/tools/tax_calculations.py`) marks the difference material when `abs(document − stated) > max(0, 0)`. For eval case 1, $46,850.00 − $46,000.00 = $850.00 > $0, so it is material. Unless `conflict.wages.answer` is already `document`, Rules adds a follow-up with id `conflict-wages`: *"Your W-2 form shows wages of $46,850.00, but earlier you said about $46,000.00. Which is right?"* The options are *The W-2 is right*, *My number is right* and *I'm not sure*.
  - **Instructions.** [demo/eval_case_1.md](../demo/eval_case_1.md) has no step for that question and says the stated wages are "within tolerance … so no conflict is raised", which describes the old $1,000 / 10% rule.
  - **Scripted runs.** `data/fixtures/eval_case_1/case.json` has no `followup_answers`. For any `followup:*` question without a matching key, `src/driver.py` (`run_case`) answers `"not sure"`. In offline mode, `src/agents/intake.py` treats that as intent `unsure` and escalates `taxpayer_needs_help`. Eval case 1 has no `reviewer_actions`, so `python run.py demo eval_case_1`, `python run.py eval`, and the integration tests that run eval case 1 would be expected to stop at human review instead of reaching a draft. Live-mode interpretation of "not sure" was not traced.
  - **Other draft fixtures with stated wages that differ from their W-2 totals and no `followup_answers`:** `grader_style_unseen` (61,000 vs $61,321), `case_mfj_high_income` ("about 192,000" vs $192,500) and `case_hoh_dependent` (38,000 vs $38,400). `eval_case_2` already answers `conflict-wages` with "My number is right", as intended.
  - **Proposed smallest correction, keeping zero tolerance (not applied):**
    1. In `data/fixtures/eval_case_1/case.json`, add `"followup_answers": {"conflict-wages": "The W-2 is right"}`. Add the same to the three fixtures above.
    2. In `demo/eval_case_1.md`, add a step after confirming the summary: when asked whether the W-2 ($46,850.00) or "about $46,000.00" is right, click **The W-2 is right**. Replace the "within tolerance" sentence with one saying the run asks one confirmation question and continues without human review.
    3. Re-run `python run.py demo eval_case_1` (with working image reading) and record the result in [ACCEPTANCE_RESULTS.md](ACCEPTANCE_RESULTS.md).

    The alternative is to change `stated_wages` to `46,850`, which avoids the question but no longer shows the confirmation behavior. Choosing a non-zero tolerance is a rules decision (see [ASSUMPTIONS.md](ASSUMPTIONS.md) Q-02).
- **Conservative QCD age screen.** Uncertain age or timing cases go to a person. Review this and other assumptions against the assignment.
- **Test-only tool stub.** The Decimal summation and comparison in `tests/person4/conftest.py` do not substitute for the production MCP tools.

## 4. Document extraction, provenance and output

- Real-model extraction accuracy and native OCR accuracy are unproven; the core tests use injected payloads and controlled tokens.
- Uploads must be normalized image bytes. Multi-page PDFs are now rejected; page selection or splitting with page provenance is not implemented.
- The service contract uses `uploaded_at` for manual-entry provenance timestamps; integration must preserve it.
- The full-SSN digest is an equality token for fictional data, not anonymization of real SSNs. Redaction is not production PII security, and there is no pre-model upload privacy filter.
- PDF checks are field/readback and rendered-text checks, not a guarantee of layout quality. Long names and other visual edge cases are untested beyond the inspected samples.
- Template hashes must be preserved and reconciled when adding references or the final dependency lock.

## 5. Rules and references

- References in `data/reference_tax_forms/` were AI-assembled, not supplied by the professor. `data/source_manifest.json` establishes local file identity and page existence, not official download authentication or the correctness of every citation's interpretation.
- The historical SSA GIFs are layout references only, not 2025 tax-rule authorities.
- Live-model screening is unverified.

## 6. Documentation and wording gaps

- **Documents referenced by code.** [ASSUMPTIONS.md](ASSUMPTIONS.md), [STATE_CONTRACT.md](STATE_CONTRACT.md) and [ACCEPTANCE_RESULTS.md](ACCEPTANCE_RESULTS.md) now exist, so the references in `data/policy.md`, `data/rule_registry.json`, `src/money.py`, `src/agents/return_assembly.py`, `scripts/context_benchmark.py`, `src/state.py`, `src/contracts.py` and `tests/conftest.py` resolve. Still unresolved (code was not edited):
  - `tests/unit/test_graph_shape.py` docstring mentions `docs/graph.png`, which does not exist. The README Mermaid diagram is the diagram of record.
  - `docs/metrics.md` (referenced by `run.py` and `scripts/context_benchmark.py`) and `docs/graph.mmd` (`run.py`) are generated outputs that have not been produced.
- **Classroom wording.** Some "classroom" wording remains: the SSN rejection message (`src/ssn.py`; intake translates it), the intake system prompt, and comments. Other agents' messages and PDF labels still need their owners' wording review.
- **Source manifests are historical.** `docs/*_sources.json` record package contents at import time, including the now-deleted handoff files and earlier hashes of `README.md`, `IMPLEMENTATION_NOTES.md` and `REQUIREMENTS_MATRIX.md`. They are attribution records and are intentionally not rewritten.
- **Python version is inconsistent across the team.** The foundation targeted 3.11 (Taylor ran 3.11.16), while Docker, CI and the core verification use 3.12. Hussain's local checks ran on 3.14.7 (only the foundation and intake tests). Agree on one version and record it.
- **Dashboard identity.** The dashboard has no login; reviewer names are self-declared.

## 7. Outstanding submission deliverables

| Deliverable | Status |
|---|---|
| Real on/off token measurements in `docs/metrics.md` (§4.5) | **Not produced.** Proxy counts or old source-repository results must not be presented as measurements |
| Five-page report (bonus) | **Not written.** [REPORT_AND_DEMO_CHECKLIST.md](REPORT_AND_DEMO_CHECKLIST.md) is an outline only |
| Demo video, 5–10 minutes | **Not recorded** |
| Specialization table (assignment §1.1) | **Pending.** See [CONTRIBUTIONS.md](CONTRIBUTIONS.md) |
| Member contribution records | **Pending for all six members.** See [CONTRIBUTIONS.md](CONTRIBUTIONS.md) |
| Orchestration diagram | The README has a Mermaid diagram transcribed from `src/graph.py`. No image file exists |
| `traces/` | Not committed; `python run.py eval` writes it |
| Docker acceptance (bonus) | Unverified (see section 1) |
