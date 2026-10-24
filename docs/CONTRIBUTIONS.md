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
| Task division and management | Anastasia | Pending |
| MLOps/DevOps | Anjana | Pending |
| Guardrails and ethics | Kezia | Pending |
| Security | Taylor | Pending |

## Team and confirmed code ownership

| Person | Name | Code ownership | Commits on `main` (author as recorded by Git) |
|---|---|---|---|
| 1 | Hussain Al Shabib | Foundation, memory, shared architecture and orchestration | `942002b` (Hussain Ghazi S Al Shabib) |
| 2 | Kezia Mally Puteri | Intake, taxpayer UI and human review | `d1ac85d` (Kezia Mally Puteri) |
| 3 | Taylor | Document extraction, provenance and return assembly | `892822d`, merge `7c4f336` (Taylor-Do) |
| 4 | Anastasia | Eligibility agent, rules and references | `f8bd44f`, revert `14db900`, re-add `df55c89` (Anastasia) |
| 5 | Anjana | Computation agent, MCP tools and deployment | `d351db3` (ars476) |
| 6 | Tomas | Audit agent, dashboard, evaluation and integration | `aeda711`; also `4411794` (assignment writeup) (Tomás Schmieder) |

**Files by owner (from the package handoffs):**

| Owner | Files |
|---|---|
| Hussain | `src/state.py`, `src/contracts.py`, `src/config.py`, `src/agents/base.py`, `src/memory.py`, `src/store.py`, `tests/unit/test_merge_order.py`, `tests/unit/test_foundation_memory_store.py`. Named reviewer of `src/graph.py`, `src/service.py`, `src/llm.py` and `src/agents/orchestrator.py`, which arrived in Tomas's package |
| Kezia | `src/agents/intake.py`, `src/agents/intake_script.py`, `src/agents/human_review.py`, `src/hitl.py`, `src/ui/taxpayer.py`, `src/ui/components.py`, `src/ui/upload_helpers.py`, `src/ui_text.py`, `streamlit_app.py`, `.streamlit/config.toml`, `tests/person2/` |
| Taylor | `src/agents/document_extraction.py`, `src/agents/return_assembly.py`, `src/tools/ocr_reader.py`, `src/tools/document_input.py`, `src/provenance.py`, `src/ui/provenance_view.py`, `src/output/`, `data/generate_fixtures.py`, `data/fixtures/`, `demo/*.png`, the six blank templates in `data/reference_tax_forms/forms/`, `tests/person3/`, `tests/person3_ocr/`. Security owner of `src/ssn.py` (changes reviewed with Hussain) |
| Anastasia | `src/agents/eligibility_rules.py`, `data/rule_registry.json`, `data/policy.md`, the remaining files in `data/reference_tax_forms/`, `scripts/build_source_manifest.py`, `data/source_manifest.json`, `tests/person4/` |
| Anjana | `src/agents/computation.py`, `src/tools/tax_calculations.py`, `src/tools/mcp_client.py`, `mcp_server/`, `tests/oracles/`, `evals/expected_results/`, `tests/person5/`, `Dockerfile`, `compose.yaml`, `.github/workflows/tests.yml`. Owns future numerical changes to `src/money.py` |
| Tomas | `src/agents/review_audit.py`, `src/ui/dashboard.py`, `src/driver.py`, `run.py`, `evals/cases.json`, `demo/eval_case_*.md`, `scripts/context_benchmark.py`, `scripts/ui_smoke.py`, `tests/integration/`, `tests/live/`, `tests/person6/`, `tests/unit/test_graph_shape.py`, `tests/conftest.py`, `requirements.txt`. Integration of `src/graph.py`, `src/service.py`, `src/llm.py`, `src/agents/orchestrator.py`. Coordinates the report, recording, token experiment and contribution artifacts |

## Member records

### 1. Hussain Al Shabib

| Category | Record |
|---|---|
| Completed (with evidence) | Foundation package committed and pushed to `main` as `942002b`; Claude Code ran the commit and push at Hussain's request |
| Completed (with evidence) | Local checks on Hussain's machine (Windows 11, Python 3.14.7, isolated `.venv`), run by Claude Code at Hussain's request: 10 passed (foundation tests on `942002b`), then 54 passed (`tests/person2` plus the foundation tests on `d1ac85d`). See [ACCEPTANCE_RESULTS.md](ACCEPTANCE_RESULTS.md) |
| Completed (with evidence) | Branch `chore/submission-documentation`: documentation consolidation, committed as `d87de06` and pushed. Prepared, committed and pushed by Claude Code at Hussain's request; pull request not yet merged |
| In progress (uncommitted) | Branch `fix/acceptance-validation`, prepared by Claude Code at Hussain's request and not yet reviewed:<br>• fixture wage confirmations<br>• OCR-independent integration tests in the core suite<br>• audit recheck of 6b/13b through a new MCP tool<br>• no default model<br>• Python 3.12 standard<br>Local result: 372 passed, 23 skipped on Python 3.12.14 (see [ACCEPTANCE_RESULTS.md](ACCEPTANCE_RESULTS.md)) |
| Unverified | Personal review of the foundation code; review of `graph.py`, `service.py`, `llm.py` and `orchestrator.py`; own improvements; pull request and reviewer |

### 2. Kezia Mally Puteri

| Category | Record |
|---|---|
| Completed (with evidence) | Person 2 package committed to `main` as `d1ac85d`. The remote branch `feat/Keziamally-intake` exists at the same commit |
| Completed (with evidence) | The package preparer reported 54 passed on Linux / Python 3.12.14 (externally reported; not Kezia's own run) |
| Unverified | Personal code review; own test run and machine; improvements made; review of the conflict clarification wording with Anastasia; pull request and reviewer |

### 3. Taylor

| Category | Record |
|---|---|
| Completed (with evidence) | Created branch `feat/Taylor-documents` from `main` at `d1ac85d` on 2026-10-24, after a clean fast-forward check |
| Completed (with evidence) | Pre-copy checks by Claude Code at Taylor's request: `src/provenance.py` was the only overlap; its prior SHA-256 matched `expected_prior_sha256` (`2e8f1ba1…14cf`) and the copied file matches `package_sha256` (`58076e6a…c2df`); the other 81 files were new and none gitignored |
| Completed (with evidence) | Installed the Person 3 requirements with pins unchanged, then ran the tests: 100 passed on macOS 13.1 arm64 with Python 3.11.16. Both done by Claude Code at Taylor's request |
| Completed (with evidence) | Committed `892822d` and merged `7c4f336` into `main`, directly at Taylor's request, without a pull request or teammate review (per the commit message) |
| Unverified | Line-by-line implementation review; a behavior traced and explained; a real issue reproduced or an improvement made, with evidence; native OCR verification (blocked); final PR and teammate review |

Suggested review exercises from the handoff:
- Follow an unreadable withholding box into its taxpayer follow-up.
- Trace a 1099-R box 2b flag through aggregation.
- Trace a line's provenance to its document.
- Inspect all pages of a generated draft.

Improvements should come from an observed gap (for example, a cropped or rotated document, a long name in a PDF field, or ambiguous masked identity) and be reproduced first.

### 4. Anastasia

| Category | Record |
|---|---|
| Completed (with evidence) | Committed the Person 4 package (`f8bd44f`), reverted it (`14db900`), and re-added it (`df55c89`). Claude Sonnet 5.5 is a co-author in the commit trailers. The remote branch `anastasia-work` exists |
| Completed (with evidence) | The package preparer reported 139 passed and a source-manifest check over 16 references (externally reported) |
| Unverified | Personal review of the rules and behavior; own test run; real changes and evidence; review of the zero-tolerance and QCD assumptions against the assignment; pull request and reviewer |

### 5. Anjana

| Category | Record |
|---|---|
| Completed (with evidence) | Person 5 package committed to `main` as `d351db3` (Git author `ars476`) |
| Unverified | Personal review; own test run; Docker build and run; CI run; transitive dependency lock; real changes and rationale; pull request and reviewer |

### 6. Tomas

| Category | Record |
|---|---|
| Completed (with evidence) | Added the assignment writeup (`4411794`) and committed the Person 6 audit/integration package (`aeda711`), which replaced the per-person requirement files with one `requirements.txt`. Cursor is a co-author in both commit trailers. The remote branch `feat/Person6-audit-integration` exists |
| Completed (with evidence) | ChatGPT/Codex independently ran the core suite against `aeda711`: 299 passed in 6.18 s on Python 3.12 (externally reported; see [ACCEPTANCE_RESULTS.md](ACCEPTANCE_RESULTS.md)) |
| Unverified | Personal review; own test run; browser, live API and full evaluation runs; token experiment; report and recording coordination; pull request and reviewer |

## Remaining team artifacts

- Specialization table (above)
- Five-page report
- Demo recording
- Real token measurements

See [REPORT_AND_DEMO_CHECKLIST.md](REPORT_AND_DEMO_CHECKLIST.md) and [KNOWN_LIMITATIONS.md](KNOWN_LIMITATIONS.md#7-outstanding-submission-deliverables).
