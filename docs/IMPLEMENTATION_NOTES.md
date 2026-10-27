# Implementation notes

This describes the merged build on `main` as of commit `aeda711`. It is taken from the code and module docstrings. Where behavior has only been checked by unit tests, or not at all, that is stated here and in [KNOWN_LIMITATIONS.md](KNOWN_LIMITATIONS.md).

## Architecture overview

| Layer | Files | Role |
|---|---|---|
| UI | `streamlit_app.py`, `src/ui/taxpayer.py`, `src/ui/dashboard.py`, `src/ui/provenance_view.py`, `src/ui/components.py` | Three views: taxpayer intake, employee dashboard, draft & provenance |
| Service | `src/service.py` | The only API the UI, CLI and tests use. One compiled graph and one MCP session per process; each case is a LangGraph thread checkpointed in SQLite |
| Graph | `src/graph.py`, `src/agents/*.py` | Orchestrator plus agent nodes (below) |
| Tools | `mcp_server/server.py`, `src/tools/mcp_client.py`, `src/tools/tax_calculations.py` | Deterministic tax functions served over a stdio MCP server |
| Model access | `src/llm.py` | `AnthropicLLM` (structured outputs, real token usage, and vision for document images, which is the intended path) or `OfflineLLM` (deterministic stand-ins for tests and keyless runs). Anthropic mode needs both `ANTHROPIC_API_KEY` and `ANTHROPIC_MODEL`; there is no default model, and a missing one raises `ModelConfigError` |
| Persistence | `src/state.py`, `src/store.py`, LangGraph `SqliteSaver` | Durable case state; a small metadata index for the dashboard list |
| Output | `src/output/pdf_fields.py`, `src/output/pdf_writer.py` | Fill and verify the official 2025 1040-SR and Schedule 1-A PDFs |
| CLI | `run.py`, `src/driver.py` | `ui`, `check`, `demo`, `eval`, `benchmark`, `metrics`, `fixtures`, `graph` |

**Trust boundary (service).** Taxpayer actions (`send_message`, `add_upload`) can only answer an intake question. Reviewer actions (`resolve_review`) can only answer a pending human-review event, and they are validated against that event before the graph resumes. Uploads are capped at 10 MB and normalized to images; multi-page PDFs are rejected rather than silently truncated to page 1.

## Agents

The assignment requires six agents plus orchestration. The build has the orchestrator, six functional agents and a human-review node.

| Agent | File | Responsibility | Constraint as implemented |
|---|---|---|---|
| Orchestrator | `src/agents/orchestrator.py` | Chooses the next node from state; owns termination, dashboard status and the loop guard | Pure routing code. Never extracts, computes or converses |
| Intake | `src/agents/intake.py`, `src/agents/intake_script.py` | The only agent that talks to the taxpayer. Asks one question at a time, records answers as confirmed facts with direct-input provenance, accepts corrections and "go back", relays follow-ups from other agents, collects uploads, notices red flags (advice requests, exploitation signs, out-of-scope situations, a request for a person) | No arithmetic and no rule interpretation. Follow-ups containing amounts are written by Rules from MCP output and relayed verbatim |
| Document Extraction | `src/agents/document_extraction.py` | `extract_document` runs once per document **in parallel** (Claude vision in live mode, OCR + layout rules offline). `aggregate_extractions` is the fan-in: validates form type, year, fictional SSN, owner and readable boxes; detects duplicates and conflicting parallel writes; publishes `source_facts` | Does not decide what values mean. Unreadable amounts stay unknown (never zero). A 1099-R box 2b flag escalates before duplicate detection. Non-test SSNs reject the document and delete the file |
| Eligibility & Rules | `src/agents/eligibility_rules.py`, `data/rule_registry.json`, `data/policy.md` | 1040-SR eligibility, filing-status validation, box counts, applicable schedules, in/out of scope. **Screening** mode during intake (hard stops escalate as soon as known); **final** mode adds document rules and the statement-vs-document conflict check | Every decision cites a rule id; every rule cites the assignment or a verified IRS page. Comparisons go through MCP `aggregate_amounts` / `compare_amounts` with zero tolerance |
| Computation | `src/agents/computation.py` | Populates every derived line in dependency order: source aggregates → 6b → 9 → 11a/b → 12e → 13b → 14/15 → 16 → 24 → 33 → 34/37 | Never does arithmetic. Every number is copied from an MCP tool result with a provenance record naming the tool, call id, inputs and trace. Live-mode line explanations containing numbers absent from the trace are discarded |
| Review / Audit | `src/agents/review_audit.py` | Adversarially checks the draft: MCP `verify_return` recomputation and consistency checks (totals, 6b ≤ 6a and ≤ 85% of 6a, 3a ≤ 3b, 4b ≤ 4a, 5b ≤ 5a, 12e chart, line 16 tax). MCP `recheck_social_security_and_senior` re-derives 6a, 6b, 11b and 13b from source-document amounts, direct inputs and dates of birth, not from the proposed lines. Also: provenance completeness; source re-verification; staleness; scope. In live mode a model critique is advisory, except `recheck_source`, which re-queues one document | Never fixes anything. Failures become issues with a target agent and are routed back by the orchestrator |
| Return Assembly | `src/agents/return_assembly.py` | Final "every number has a source" gate; fills the official PDF, page previews and a JSON audit record | Requires a current passed audit for the same calculation and facts version. Blocks stale lines and broken lineage. No tax arithmetic |
| Human review (node) | `src/agents/human_review.py`, `src/hitl.py` | The single LangGraph `interrupt` point for all escalations | See [Human review](#human-review-escalation) |

Return Assembly was added as a separate functional agent because the assignment names six agents plus orchestration but lists five functional roles besides the orchestrator.

## Shared state and reducers

`src/state.py` defines `CaseState`, a `TypedDict` of JSON-serializable values, so the SQLite checkpointer can persist it. Money is stored as strings (`src/money.py` uses `Decimal`; amounts on the return are rounded half-up to whole dollars, and cents are kept while summing).

The full field list, which agent writes each field, version markers and invariants are in [STATE_CONTRACT.md](STATE_CONTRACT.md). Interpretations and open questions are in [ASSUMPTIONS.md](ASSUMPTIONS.md).

Fields written by parallel branches use reducers that give the same result whatever order workers finish in:

| Field | Reducer | Behavior |
|---|---|---|
| `facts`, `lines`, `provenance` | `merge_dict` | Key-wise merge; the update wins for keys it names |
| `documents` | `merge_documents` | Merge by document id |
| `extractions` | `merge_extractions` | New id is added; identical duplicate is a no-op; higher `revision` wins; same-revision writes with different content keep both candidates (sorted by fingerprint) and flag a conflict, so the aggregator escalates instead of picking one |
| `human_events` | `append_unique` | Append without duplicates |
| `transcript`, `metrics`, `trace` | `operator.add` | Append |

Agents return an `AgentResult` (`src/contracts.py`) with an explicit outcome and a state patch. Model outputs are validated against pydantic schemas and re-checked deterministically where it matters.

## Memory

`src/memory.py` separates durable state from what a model sees:

- **Durable:** the full transcript and every fact live in the checkpointed graph state and are never trimmed.
- **Model context, strategy enabled (default): selective recall.** A deterministic summary of confirmed facts and session decisions, the last few turns (`SILVERFILE_CONTEXT_RECENT_TURNS`, default 4) and the current item only. Amounts are copied exactly or omitted; SSNs are masked.
- **Strategy disabled (`--no-context-strategy`).** The whole conversation is replayed on every call, which is the baseline for the §4.5 experiment.
- **Resumability.** `resume_summary` produces a plain-language "here is what we already covered" for a returning taxpayer. Cases resume by case number from the SQLite checkpoint.
- **Case index.** `src/store.py` keeps a small SQLite summary table refreshed after every graph run, so the dashboard can list cases without loading every checkpoint. The checkpoint remains authoritative.

**Context experiment (§4.5).** `scripts/context_benchmark.py` (also `python run.py benchmark`) processes the ten documents in `data/fixtures/bench_ten_docs` sequentially in one thread, with the same model, prompt and schema, once with the strategy and once without. Live mode records real API usage. `--proxy` records a labelled size proxy (characters plus image count) and is never reported as token counts. `--report` writes `docs/metrics.md`. **No real measurements have been produced yet.**

## Orchestration

### Topology

`src/graph.py`: hub and spoke. `START → orchestrator`, conditional edges from the orchestrator to every node, and every agent returns to the orchestrator. Document extraction fans out with LangGraph `Send` (one `extract_document` per queued document) and fans in through `aggregate_extractions`. The README has the diagram.

### Why a rule-based orchestrator

Routing is deterministic code over shared state (`decide()` in `src/agents/orchestrator.py`), not a model call. Every hop is explainable from state, recorded with a reason in `routing.history` and `trace`, and termination is guaranteed. Priority order:

1. Terminal status → end
2. Pending escalation → `human_review` (interrupt)
3. Queued documents → parallel `extract_document` × N → aggregate
4. Corrected document record → re-aggregate
5. Facts, documents or mode changed since the last rules check → `rules`
6. Open question or follow-up → `intake` (interrupt)
7. Stale calculation → `computation`
8. New calculation without an audit → `review`; audit requested revision → the agent it targeted
9. Assembly found lineage gaps → `computation`; draft not assembled → `assembly`
10. Draft ready → intake asks whether to submit; after submission → end

### Loop-control settings

Defined in `src/config.py`:

| Setting | Value | Purpose |
|---|---|---|
| `MAX_REVIEW_PASSES` | 3 | Revision passes allowed before the audit escalates (`review_bound`) |
| `MAX_HANDOFFS_PER_RUN` | 30 | Automatic hand-offs allowed per processing run |
| `MAX_SIGNATURE_REPEATS` | 4 | Repeats of an identical routing signature before the loop guard trips |
| `RECURSION_LIMIT` (`src/graph.py`) | 250 | Kept well above the business guard, so the loop guard, not LangGraph's limit, is what trips |

**Loop guard.** Every automatic hand-off is counted per processing run. The run resets whenever a person (taxpayer or reviewer) provides input, and waiting for a human never consumes the budget. The routing signature combines the next node, open audit issue ids, facts version, calculation id, source version and rules status. When the hand-off cap is exceeded, or one signature repeats `MAX_SIGNATURE_REPEATS` times, the orchestrator raises a `loop_guard` escalation with the last ten hops as evidence and routes to human review.

**Bounded review cycle.** Each failed audit increments `review.passes`. After `MAX_REVIEW_PASSES` failed revisions, the next failure escalates `review_bound`. A passing audit resets the count.

Both run in the core suite, using fault-injecting overrides:
- `tests/integration/test_end_to_end.py::test_loop_guard_breaks_pathological_handoff_cycle` (no documents)
- `tests/integration/test_orchestration_synthetic.py`: `test_review_revise_cycle_is_bounded_and_recovers`, `test_review_bound_escalates` and `test_loop_guard_handoff_cap`. These replace image transcription with fixture ground truth.

The image-based versions in `test_end_to_end.py` are marked `needs_ocr` and skipped. `tests/unit/test_graph_shape.py` checks the topology.

### Audit recheck of 6b and 13b

`recheck_social_security_and_senior` (`src/tools/tax_calculations.py`, exposed through MCP) receives:
- document amounts grouped by meaning, from `source_facts`: SSA-1099 box 5; W-2 box 1; 1099-INT boxes 1, 3 and 8; 1099-DIV boxes 1a and 12; 1099-R box 2a split by the IRA flag
- confirmed direct inputs: QCD amount and Schedule 1 lines 10, 21 and 26
- the dates of birth, and whether SSNs are present

The agent gathers these in `review_audit.recheck_inputs`, which does not read `lines`. The tool rebuilds the income lines, computes taxable benefits with the closed form of the worksheet, then AGI, then the per-person senior deduction, and compares each with the proposed 6a, 6b, 11b and 13b.

It is a separate implementation from `taxable_social_security` and `enhanced_senior_deduction`, and doesn't call them. It shares only the published 2025 amounts and the rounding conventions. It sits in the same module and was written by the same AI tool, so it is not an independent-author oracle. `tests/audit/test_audit_recheck.py` checks that it agrees with production on 5,000 random valid returns.

The closed form rounds to cents at the same points the worksheet does (one-half of benefits, one-half of line 12, the 85% products), so all four lines are compared exactly. Rounding once at the end instead would differ from the worksheet by $1 on about 1 return in 400.

## Human review (escalation)

An agent never pauses the graph itself. It returns an escalation request; the orchestrator routes to `human_review`, which raises a real LangGraph `interrupt`. The dashboard resumes the same thread with a reviewer decision, validated by `src/hitl.py`.

| Reason code | Assignment | Allowed reviewer actions |
|---|---|---|
| `out_of_scope` | §4.4(1) | refer out of scope, correct fact, request more info |
| `user_document_conflict` | §4.4(2) | confirm document value, correct fact, request more info, refer |
| `form_1099r_2b` | §4.4(3) | refer, correct fact |
| `advice_request` | §4.4(4) | note and continue, refer |
| `filing_status_ambiguity` | §4.4(5) | set filing status, request more info, refer |
| `exploitation_concern` | §4.4(6) | cleared to continue, request more info, refer |
| `taxpayer_needs_help` | §4.3 honest uncertainty | correct fact, request more info, note and continue, refer |
| `document_problem` | §2 unsourced amounts | correct fact, request more info, refer |
| `loop_guard`, `review_bound`, `system_error` | §4.1 / engineering | retry processing, refer |

- There is no generic "approve everything" action. Hard scope exclusions can only be referred out, or have a mis-recorded fact corrected with evidence, after which the rules run again.
- Every decision records who, when, action, rationale, evidence, and prior and new values.
- **Replay safety:** LangGraph re-executes the node on resume, so everything before `interrupt` is pure and the event id is a hash of its inputs. The service checks the pending event id, so an event cannot be resolved twice.
- The reviewer name is self-declared; there is no login.

**Dashboard (`src/ui/dashboard.py`):**
- status counts and filters (in progress, needs review, draft ready, submitted, referred, errors)
- a case table and a review queue with **Open** buttons
- per-case draft, provenance, conversation and agent trace
- a review form limited to the actions each reason allows

## Provenance

`src/provenance.py` defines the records attached to every money line: tool name, call id, inputs by provenance key, document boxes, or dated direct user input. `lineage_gaps` checks every populated money line (not only required lines), follows transitive references and detects cycles. `src/ui/provenance_view.py` shows each line's calculation and sources. Review re-verifies document values against `source_facts`; Assembly refuses to produce a draft with gaps.

## Intake accessibility and dignity (§4.3)

From `src/ui/taxpayer.py` and `src/agents/intake.py`:

- **One question at a time** in a large, high-contrast card. Option buttons are real, keyboard-reachable buttons with plain labels.
- **Plain language.** A short gloss sits under unavoidable terms.
- **Repetition and drift.** Corrections and "go back" are supported; answers are recorded as facts and never lost.
- **Honest uncertainty.** "I'm not sure", "Go back" and "Talk to a person" are always one click away.
  - Asking for a person escalates as `taxpayer_needs_help`.
  - An unanswered "not sure" also escalates: as `filing_status_ambiguity` for filing status, as `document_problem` for a listed form, and otherwise as `taxpayer_needs_help`. The taxpayer is told it has been flagged for a volunteer.
- **No unnecessary PII.** SSNs are accepted only where asked for, and stored in the transcript as "[Social Security number entered]". A number that looks like an SSN, volunteered elsewhere, is redacted before storage or model use, and the taxpayer is told why.
- **Resumability.** Everything is saved after each answer; a case resumes by number with a summary of what was covered.
- Status is always written in words, never shown by color alone.

Browser accessibility (screen reader, keyboard-only use) has not been tested.

## Security and privacy

- `src/ssn.py` is the single place the fictional-SSN rule lives: only the 900–999 test series is accepted (§3.2).
- Extraction keeps only defined fields and stores SSNs masked (last four). Full-number equality across documents uses a digest, which is an equality token for fictional data, not anonymization. Payer and name text is redacted, and free-form model notes and exception text are not persisted.
- Document text and model output are treated as untrusted input.
- The MCP client has no in-process fallback. If the tool server is unreachable, the case stops with an error instead of computing numbers another way.
- `.env`, runtime data (`var/`) and virtual environments are git-ignored. The Docker image runs as a non-root user and Compose binds to `127.0.0.1` only.

These are prototype measures, not production PII security.

## Output

`src/output/pdf_fields.py` maps SilverFile line ids to field names in the official `2025_Form_1040-SR.pdf` and `2025_Schedule_1-A_Form_1040.pdf`. The map was derived by inspecting widget names, positions and printed labels. `src/output/pdf_writer.py` fills them. Its checks compare field values, selected checkboxes, AcroForm data and text within field bounds; these are field/readback checks, not a guarantee of layout quality. Draft banners carry fictional-data, not-filed and human-review labels.

## Data, fixtures and references

- `data/fixtures/` holds 19 scenario definitions with 29 generated document images. `demo/` has four convenience copies.
  - Coverage: clean drafts for all five filing statuses, the ten-document benchmark, and stop cases (1099-R box 2b, advice, spouse died, exploitation, third party, crypto, itemizing, too young, capital-gain distribution, real-looking SSN).
  - `stop_real_ssn_w2` deliberately contains a made-up non-900 number and must never be used as an accepted case.
  - `python data/generate_fixtures.py` rewrites the fixtures and demo images; run it only when intentionally updating them.
- `evals/cases.json` catalogues the cases; `evals/expected_results/` has hand-worked expected lines for the draft cases.
- `tests/oracles/` has an independent calculation and IRS tax-table oracle used by the computation tests.
- `data/reference_tax_forms/` holds the blank 2025 templates and references. `data/source_manifest.json` (built by `scripts/build_source_manifest.py`) records hashes and PDF identity checks. The references were AI-assembled, not supplied by the professor. The historical SSA GIFs are layout references only.

## Implementation decisions

| Decision | Rationale and caveat |
|---|---|
| Deterministic orchestrator | Explainable, testable routing with guaranteed termination (see above) |
| Separate Return Assembly agent | Owns the provenance gate and the official-form output |
| Zero-tolerance wage comparison | Rules passes `abs_tolerance='0'` and `rel_tolerance='0'` to `compare_amounts`, replacing the inherited $1,000 / 10% allowance. Any difference asks the taxpayer; an unresolved difference escalates. This was an engineering choice, not a professor-specified threshold, and it may ask extra questions because intake does not record how approximate an estimate was |
| Conservative QCD age screen | Uncertain age or timing cases go to a person rather than being treated as eligible |
| Line 16 re-check | `verify_return` re-checks qualified-dividend line 16 using the worksheet implementation. It is a consistency check, not an independent oracle |
| Line 25c | Rule R-WH-01 now includes Additional Medicare Tax withheld on a high-wage W-2. `computation.py` still sets $0 until W-2 box 6 is extracted and a Computation tool derives the amount ([ASSUMPTIONS.md](ASSUMPTIONS.md) Q-01, C-03) |
| Audit recheck of 6b/13b | Separate closed-form implementation fed from sources, compared exactly (see above) |
| No default model | Anthropic mode requires an explicit `ANTHROPIC_MODEL`; no identifier is assumed to be available |
| Python 3.12 | Team standard for Docker, CI and `.python-version` |
| No MCP fallback | A missing tool server stops the case rather than producing unsourced numbers |
| Native OCR off by default | Blocked after an unexpected telemetry request (see limitations) |
| Single pinned `requirements.txt` | Replaced the per-person requirement files. It pins direct dependencies only; no tested transitive lock yet |
