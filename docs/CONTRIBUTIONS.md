# Contributions

This records who did what, taken from the Git commit and merge history of `main`. Each member owned one area of the code end to end and one §1.1 specialization. AI assistance for each stage is disclosed in [AI_DISCLOSURE.md](AI_DISCLOSURE.md).

## Assignment specialization table (§1.1)

| Focus area | Team member |
|---|---|
| Agent memory | Hussain Al Shabib |
| Inter-agent communication | Tomás Schmieder |
| Task division and management | Anastasia Patrikiadou |
| MLOps/DevOps | Anjana |
| Guardrails and ethics | Kezia Mally Puteri |
| Security | Taylor Do |

## Code ownership

| Owner | Files |
|---|---|
| Hussain Al Shabib | `src/state.py`, `src/contracts.py`, `src/config.py`, `src/agents/base.py`, `src/memory.py`, `src/store.py`, `tests/unit/test_merge_order.py`, `tests/unit/test_foundation_memory_store.py`. Reviewer of `src/graph.py`, `src/service.py`, `src/llm.py` and `src/agents/orchestrator.py` |
| Kezia Mally Puteri | `src/agents/intake.py`, `src/agents/intake_script.py`, `src/agents/human_review.py`, `src/hitl.py`, `src/ui/taxpayer.py`, `src/ui/components.py`, `src/ui/upload_helpers.py`, `src/ui_text.py`, `streamlit_app.py`, `.streamlit/config.toml`, `tests/intake/` |
| Taylor Do | `src/agents/document_extraction.py`, `src/agents/return_assembly.py`, `src/tools/ocr_reader.py`, `src/tools/document_input.py`, `src/provenance.py`, `src/ui/provenance_view.py`, `src/output/`, `data/generate_fixtures.py`, `data/fixtures/`, `demo/*.png`, the blank form templates in `data/reference_tax_forms/forms/`, `tests/documents/`, `tests/native_ocr/`. Security owner of `src/ssn.py` |
| Anastasia Patrikiadou | `src/agents/eligibility_rules.py`, `data/rule_registry.json`, `data/policy.md`, the reference files in `data/reference_tax_forms/`, `scripts/build_source_manifest.py`, `data/source_manifest.json`, `tests/rules/` |
| Anjana | `src/agents/computation.py`, `src/tools/tax_calculations.py`, `src/tools/mcp_client.py`, `mcp_server/`, `tests/oracles/`, `evals/expected_results/`, `tests/computation/`, `Dockerfile`, `compose.yaml`, `.github/workflows/tests.yml`, numerical changes to `src/money.py` |
| Tomás Schmieder | `src/agents/review_audit.py`, `src/ui/dashboard.py`, `src/driver.py`, `run.py`, `evals/cases.json`, `demo/eval_case_*.md`, `scripts/context_benchmark.py`, `scripts/ui_smoke.py`, `tests/integration/`, `tests/live/`, `tests/audit/`, `tests/unit/test_graph_shape.py`, `tests/conftest.py`, `requirements.txt`. Integration of `src/graph.py`, `src/service.py`, `src/llm.py` and `src/agents/orchestrator.py` |

## Member records

Commit hashes are on `main`. "Merged" means the member performed the merge recorded in Git.

### Hussain Al Shabib (foundation, memory)

| Commit or merge | Work |
|---|---|
| `942002b` | Foundation layer: shared state and reducers, agent contracts, configuration, memory, case store, and their unit tests |
| `d87de06` (PR #1) | Consolidated the per-package handoffs into the README and the documents in `docs/` |
| `90ff333` (PR #2) | Acceptance fixes: OCR-independent integration tests, the audit recheck of 6b/13b through a new MCP tool, model configuration, the Python 3.12 standard |
| `3ecac4a` (PR #4) | One-command context benchmark (`python run.py benchmark --all`) with a fake-client test |
| `390de90` (PR #7) | AI disclosure and contribution records for his work |
| `041f826` (PR #14) | Ran the live §4.5 context benchmark and recorded the results in [metrics.md](metrics.md) |
| Merged | PRs #1, #2, #4, #7 and #14 |

### Kezia Mally Puteri (intake, human review, guardrails)

| Commit or merge | Work |
|---|---|
| `d1ac85d` | Intake agent and question script, human-review node and reason codes, taxpayer UI, and their tests |
| `ddbc0fc` | Final intake review documentation |
| `de30522` | Guardrail fix: shorthand amounts such as `46k` are rejected instead of expanded; classroom wording removed from the live intake prompt |
| `6f94598` | Contribution records for her work |
| `a08a379` | Final limitations and verification status |
| Merged | `7e3afa0`, `48f1d7f` and `497d353` |

### Taylor Do (document extraction, provenance, assembly, security)

| Commit or merge | Work |
|---|---|
| `892822d` | Document extraction (parallel extraction and aggregation), provenance, return assembly, PDF output, provenance view, fixtures and demo images, and their tests |
| `1d52409` | W-2 images read without an API key: native OCR on by default, `onnxruntime` pinned to 1.21.1, default model set, `run.py check` reads the demo W-2 |
| `906da02` | W-2 box 6 extraction for line 25c and the high-wage W-2 fixture `case_high_wage_w2` |
| Merged | `7c4f336`, `be5912d` and `f582d65` |

### Anastasia Patrikiadou (eligibility and rules, task division)

| Commit or merge | Work |
|---|---|
| `f8bd44f`, `14db900`, `df55c89` | Eligibility & Rules agent, rule registry, reference forms and tests (added, reverted, re-added) |
| `80f99e8` | Fix: enhanced senior deduction denied to married-filing-separately filers (R-ESD-02) |
| `936db4d` | Fix: the line 12d boxes message can say "none" |
| `2d14c49` | Fix: capital-gain and SSA-repayment amounts parsed as decimals instead of compared as strings |
| `52713de` | Tests for a pending spouse birth date, QCD without an IRA form, and extra uploaded forms |
| `fa73f7b`, `4869136` | Line 25c decision: include Additional Medicare Tax withheld on an in-scope W-2 (R-WH-01) |
| `b4df5b7` | Rules decision records which schedules apply (1-A, 1, 2, 3) |
| `3400b27`, `8731b2c`, `0ada604`, `20d18aa` | Work plan: the rules agent assigns each task an owner, computation and assembly report completed tasks, and the audit flags skipped tasks (R-PLAN-01) |
| `aa0e4c0`, `686f292`, `9c390b3`, `ff9439c`, `27a62fb` | README and contribution records |
| Merged | PRs #5, #6, #10, #11, #12 and #13 |

### Anjana (computation, MCP, deployment)

| Commit or merge | Work |
|---|---|
| `d351db3` | Computation agent, deterministic tax functions, MCP server and client, calculation oracles, expected results, Dockerfile, Compose file and CI workflow |
| `b8415ea` (PR #9) | Additional Medicare withholding: the `additional_medicare_withheld` MCP tool, line 25c computation, audit recheck and tests |
| `e60db72` | High-wage evaluation case with independently calculated expected results |
| `e52dfb5` | Final evaluation traces for every fixture case in `traces/` |
| Merged | PR #9 |

### Tomás Schmieder (review and audit, dashboard, integration)

| Commit or merge | Work |
|---|---|
| `4411794` | Assignment text added to the repository |
| `aeda711` | Review/Audit agent, employee dashboard, graph and service integration, model access, evaluation runner, and the single `requirements.txt` |
| `da02590` | 2025 tax-forms reference packet |
| `f605ea5` | Removed numbered person labels from tests, manifests and docs |
| `678658b` (PR #3) | Audit recheck of 6b/11b/13b compared exactly instead of with a $1 tolerance |
| Merged | PRs #3 and #8 |
| Repository | Hosts the team repository; the branches for PRs #1–#14 were opened on it |
