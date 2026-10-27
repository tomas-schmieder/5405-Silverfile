# Contributions

Each member's work is recorded in three categories:

- **Confirmed ownership:** the code areas each person owns, as confirmed by the team.
- **Completed activities (with evidence):** supported by Git history, commit messages or recorded test runs. Where a tool did the work at a member's request, that is stated.
- **Unverified:** personal reviews, tests and improvements that have not been recorded. Each member should replace their own unverified items with what they actually did, linking commits or pull requests.

Graders use Git commits to assess who did what. Committing an AI-prepared package is recorded as a commit, not as authoring the code (see [AI_DISCLOSURE.md](AI_DISCLOSURE.md)).

## Assignment specialization table (§1.1)

The assignment's individual specializations are separate from code ownership. The mapping below is **PROPOSED**. It is pending each member's agreement and is not final until every member confirms it.

| Focus area | Team member (proposed) | Confirmed by member |
|---|---|---|
| Agent memory | Hussain | Pending |
| Inter-agent communication | Tomas | Pending |
| Task division and management | Anastasia | Confirmed |
| MLOps/DevOps | Anjana | Pending |
| Guardrails and ethics | Kezia | Confirmed |
| Security | Taylor | Pending |

## Team and confirmed code ownership

| Name | Code ownership | Commits on `main` (author as recorded by Git) |
|---|---|---|
| Hussain Al Shabib | Foundation, memory, shared architecture and orchestration | `942002b` (Hussain Ghazi S Al Shabib) |
| Kezia Mally Puteri | Intake, taxpayer UI and human review | `d1ac85d` (Kezia Mally Puteri) |
| Taylor | Document extraction, provenance and return assembly | `892822d`, merge `7c4f336` (Taylor-Do) |
| Anastasia | Eligibility agent, rules and references | `f8bd44f`, revert `14db900`, re-add `df55c89`; fixes and tests in PR #5: `80f99e8`, `fa73f7b`, `4869136`, `936db4d`, `2d14c49`, `52713de` (Anastasia Patrikiadou) |
| Anjana | Computation agent, MCP tools and deployment | `d351db3` (ars476) |
| Tomas | Audit agent, dashboard, evaluation and integration | `aeda711`; also `4411794` (assignment writeup) (Tomás Schmieder) |

**Files by owner (from the package handoffs):**

| Owner | Files |
|---|---|
| Hussain | `src/state.py`, `src/contracts.py`, `src/config.py`, `src/agents/base.py`, `src/memory.py`, `src/store.py`, `tests/unit/test_merge_order.py`, `tests/unit/test_foundation_memory_store.py`. Named reviewer of `src/graph.py`, `src/service.py`, `src/llm.py` and `src/agents/orchestrator.py`, which arrived in Tomas's package |
| Kezia | `src/agents/intake.py`, `src/agents/intake_script.py`, `src/agents/human_review.py`, `src/hitl.py`, `src/ui/taxpayer.py`, `src/ui/components.py`, `src/ui/upload_helpers.py`, `src/ui_text.py`, `streamlit_app.py`, `.streamlit/config.toml`, `tests/intake/` |
| Taylor | `src/agents/document_extraction.py`, `src/agents/return_assembly.py`, `src/tools/ocr_reader.py`, `src/tools/document_input.py`, `src/provenance.py`, `src/ui/provenance_view.py`, `src/output/`, `data/generate_fixtures.py`, `data/fixtures/`, `demo/*.png`, the six blank templates in `data/reference_tax_forms/forms/`, `tests/documents/`, `tests/native_ocr/`. Security owner of `src/ssn.py` (changes reviewed with Hussain) |
| Anastasia | `src/agents/eligibility_rules.py`, `data/rule_registry.json`, `data/policy.md`, the remaining files in `data/reference_tax_forms/`, `scripts/build_source_manifest.py`, `data/source_manifest.json`, `tests/rules/` |
| Anjana | `src/agents/computation.py`, `src/tools/tax_calculations.py`, `src/tools/mcp_client.py`, `mcp_server/`, `tests/oracles/`, `evals/expected_results/`, `tests/computation/`, `Dockerfile`, `compose.yaml`, `.github/workflows/tests.yml`. Owns future numerical changes to `src/money.py` |
| Tomas | `src/agents/review_audit.py`, `src/ui/dashboard.py`, `src/driver.py`, `run.py`, `evals/cases.json`, `demo/eval_case_*.md`, `scripts/context_benchmark.py`, `scripts/ui_smoke.py`, `tests/integration/`, `tests/live/`, `tests/audit/`, `tests/unit/test_graph_shape.py`, `tests/conftest.py`, `requirements.txt`. Integration of `src/graph.py`, `src/service.py`, `src/llm.py`, `src/agents/orchestrator.py`. Coordinates the report, recording, token experiment and contribution artifacts |

## Member records

### Hussain Al Shabib

| Category | Record |
|---|---|
| Completed (with evidence) | Foundation package committed and pushed to `main` as `942002b`; Claude Code ran the commit and push at Hussain's request |
| Completed (with evidence) | Local checks on Hussain's machine (Windows 11, Python 3.14.7, isolated `.venv`), run by Claude Code at Hussain's request: 10 passed (foundation tests on `942002b`), then 54 passed (`tests/intake` plus the foundation tests on `d1ac85d`). See [ACCEPTANCE_RESULTS.md](ACCEPTANCE_RESULTS.md) |
| Completed (with evidence) | Documentation consolidation, committed as `d87de06` and merged into `main` in PR #1 (`beda21d`). Prepared, committed and pushed by Claude Code at Hussain's request |
| Completed (with evidence) | Acceptance fixes, committed as `90ff333` and merged into `main` in PR #2 (`196967b`). Written by Claude Code at Hussain's request:<br>• fixture wage confirmations<br>• OCR-independent integration tests in the core suite<br>• audit recheck of 6b/13b through a new MCP tool<br>• no default model<br>• Python 3.12 standard<br>Local result: 372 passed, 23 skipped on Python 3.12.14 (see [ACCEPTANCE_RESULTS.md](ACCEPTANCE_RESULTS.md)) |
| Completed (with evidence) | Context benchmark hand-off, committed as `3ecac4a` and merged into `main` in PR #4 (`5847f0f`). Written by Claude Code at Hussain's request: `python run.py benchmark --all`, a fake-client test, and README steps for a teammate with an API key. Core suite: 378 passed, 23 skipped (Windows 11, Python 3.12). The live benchmark has not been run, and `docs/metrics.md` does not exist yet |
| Reported by Hussain (not recorded in the repository) | Used ChatGPT/Codex for planning and for reviewing code and documentation. Configured his Anthropic API key locally and launched the application from VS Code. Ran the application with a teammate on that teammate's laptop and on his own machine, and reports that it worked; the steps and results were not recorded, so this does not show that every agent, image reading or the full workflow passed |
| Not documented | Any personal code review of the foundation modules, or of `graph.py`, `service.py`, `llm.py` and `orchestrator.py` (he is their named reviewer in the package handoffs, a team arrangement rather than an assignment requirement), is not recorded. No teammate review is recorded on PRs #1, #2 or #4 |

### Kezia Mally Puteri

| Category | Record |
|---|---|
| Completed (with evidence) | The intake package was committed to `main` as `d1ac85d`. The remote branch `feat/Keziamally-intake` exists at the same commit |
| Completed (with evidence) | The package preparer reported 54 passed on Linux / Python 3.12.14 (externally reported; not Kezia's own run) |
| Completed (with evidence) | Reviewed the integrated intake, taxpayer UI, human-review/HITL flow, and guardrails on the merged main branch. Also reviewed the wage-conflict clarification behavior with the rules workstream. |
| Completed (with evidence) | Fixed Intake guardrails so shorthand monetary amounts such as `46k` and `46 thousand` are rejected rather than mathematically expanded, and removed `classroom prototype` wording from the live Intake prompt. Personally validated with 45/45 Intake tests and the full core suite with 446 passing tests. |

### Taylor

| Category | Record |
|---|---|
| Completed (with evidence) | Created branch `feat/Taylor-documents` from `main` at `d1ac85d` on 2026-10-24, after a clean fast-forward check |
| Completed (with evidence) | Pre-copy checks by Claude Code at Taylor's request: `src/provenance.py` was the only overlap; its prior SHA-256 matched `expected_prior_sha256` (`2e8f1ba1…14cf`) and the copied file matches `package_sha256` (`58076e6a…c2df`); the other 81 files were new and none gitignored |
| Completed (with evidence) | Installed the documents-package requirements with pins unchanged, then ran the tests: 100 passed on macOS 13.1 arm64 with Python 3.11.16. Both done by Claude Code at Taylor's request |
| Completed (with evidence) | Committed `892822d` and merged `7c4f336` into `main`, directly at Taylor's request, without a pull request or teammate review (per the commit message) |
| In progress (branch `fix/ocr-w2-image-reading`, not yet merged) | Fix for rubric D.3 (graders could not read a W-2 image without an API key), prepared by Claude Code at Taylor's request:<br>• native OCR verified with outbound networking denied and turned on by default<br>• `onnxruntime` pinned to 1.21.1 so `requirements.txt` installs on macOS 13<br>• default model `claude-opus-5-5`, and `.env.example` set to `auto`<br>• `run.py check` reads the demo W-2<br>• two stale `needs_ocr` tests fixed<br>Result: 446 passed, 0 skipped; `python run.py eval` 18/18 (see [ACCEPTANCE_RESULTS.md](ACCEPTANCE_RESULTS.md)) |
| In progress (branch `feat/w2-box6-medicare`, not yet merged) | Line 25c groundwork requested by Anastasia (R-WH-01), prepared by Claude Code at Taylor's request: W-2 box 6 (Medicare tax withheld) added to `FORM_BOXES`, optional like box 5; high-wage fixture `case_high_wage_w2` (boxes 1 and 5 $250,000.00, box 6 $4,225.00); extraction, OCR and end-to-end tests. The 25c Computation tool is Anjana's. Result: 453 passed, 0 skipped |
| Unverified | Line-by-line implementation review; a behavior traced and explained; native OCR on Windows; final PR and teammate review |

Suggested review exercises from the handoff:
- Follow an unreadable withholding box into its taxpayer follow-up.
- Trace a 1099-R box 2b flag through aggregation.
- Trace a line's provenance to its document.
- Inspect all pages of a generated draft.

Improvements should come from an observed gap (for example, a cropped or rotated document, a long name in a PDF field, or ambiguous masked identity) and be reproduced first.

### Anastasia

| Category | Record |
|---|---|
| Completed (with evidence) | Committed the rules package (`f8bd44f`), reverted it (`14db900`), and re-added it (`df55c89`). Claude Sonnet 5.5 is a co-author in the commit trailers of the first three commits in PR #5 |
| Completed (with evidence) | Reviewed `eligibility_rules.py` and the rule registry and fixed three defects, each with tests: the enhanced senior deduction was granted to married-filing-separately filers (`80f99e8`, rule R-ESD-02); the "Line 12d boxes" message could never say "none" (`936db4d`); capital gain and SSA repayment amounts were compared as raw strings and are now parsed as decimals (`2d14c49`). Rules tests went from 39 to 69 passing; full suite 402 passed, 32 skipped |
| Completed (with evidence) | Decided that line 25c includes Additional Medicare Tax withheld on an in-scope W-2 (`fa73f7b`, `4869136`; `R-WH-01`, ASSUMPTIONS.md Q-01). W-2 box 6 extraction and the computation tool were then implemented by Taylor and Anjana and are covered by `case_high_wage_w2` |
| Completed (with evidence) | Task division: the rules agent records which schedules apply (`b4df5b7`) and publishes a work plan with an owner for each task (`3400b27`, rule `R-PLAN-01`); computation and assembly report which planned tasks they completed (`8731b2c`); the audit flags planned tasks that were not done, aimed at the owner (`0ada604`). Design and limits in IMPLEMENTATION_NOTES.md, "Task division and the work plan". Commits `8731b2c` and `0ada604` touch Anjana's `computation.py`, Taylor's `return_assembly.py` and Tomas's `review_audit.py`; the hashes may change if those PRs were rebase-merged |
| Unverified | Review of the zero-tolerance wage and QCD age assumptions against the assignment; review of the work-plan changes in the other members' files by their owners |


### Anjana

| Category | Record |
|---|---|
| Completed (with evidence) | The computation package was committed to `main` as `d351db3` (Git author `ars476`) |
| Unverified | Personal review; own test run; Docker build and run; CI run; transitive dependency lock; real changes and rationale; pull request and reviewer |

### Tomas

| Category | Record |
|---|---|
| Completed (with evidence) | Added the assignment writeup (`4411794`) and committed the audit and integration package (`aeda711`), which replaced the per-person requirement files with one `requirements.txt`. Cursor is a co-author in both commit trailers. A remote branch for that package exists |
| Completed (with evidence) | ChatGPT/Codex independently ran the core suite against `aeda711`: 299 passed in 6.18 s on Python 3.12 (externally reported; see [ACCEPTANCE_RESULTS.md](ACCEPTANCE_RESULTS.md)) |
| Unverified | Personal review; own test run; browser, live API and full evaluation runs; token experiment; report and recording coordination; pull request and reviewer |

## Remaining team artifacts

- Specialization table (above)
- Five-page report
- Demo recording
- Real token measurements

See [REPORT_AND_DEMO_CHECKLIST.md](REPORT_AND_DEMO_CHECKLIST.md) and [KNOWN_LIMITATIONS.md](KNOWN_LIMITATIONS.md#7-outstanding-submission-deliverables).
