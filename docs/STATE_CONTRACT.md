# State contract

This is derived from `src/state.py`, `src/contracts.py`, the agent nodes in `src/agents/` and `src/service.py`. A case is one LangGraph thread (`thread_id = case_id`) whose `CaseState` is checkpointed in SQLite after every step. All values are JSON-serializable, and money is stored as strings.

## How agents write state

- Every agent node returns a partial update. Most agents build it through `AgentResult(...).to_update(now)` (`src/contracts.py`), which:
  - copies the agent's `patch`
  - appends a `trace` entry (`at`, `agent`, `outcome`, `summary`)
  - sets `escalation` when the agent requests human review
- Agents never pause the graph themselves. Only `intake` (taxpayer questions) and `human_review` (reviewer decisions) call `interrupt`.
- The service never writes state fields directly. It creates the initial state (`new_case_state`) and resumes interrupts with `Command(resume=...)`. Taxpayer input can only answer a `taxpayer_question`, and reviewer input can only answer a pending `human_review` event, after `validate_decision`.
- Fields without a reducer are replaced wholesale by whichever node writes them. A writer must therefore send the complete value (agents copy the current dict, modify it and return it).

## Fields

| Field | Reducer | Written by | Contents |
|---|---|---|---|
| `case_id`, `tax_year`, `schema_version`, `created_at` | — | service (initial state only) | Identity |
| `status` | — | orchestrator (each hop); `human_review` (`referred_out_of_scope`) | One of `STATUS_LABELS` |
| `facts` | `merge_dict` | `intake`, `human_review` (`correct_fact`, `set_filing_status`, conflict resolution) | `fact_id → {value, status, history, source, …}`; only `status == "confirmed"` facts are used |
| `facts_version` | — | `intake` and `human_review`: +1 whenever they write `facts` | Monotonic counter |
| `intake` | — | `intake`; `eligibility_rules` and `aggregate_extractions` (append follow-ups); `human_review` | Asked questions, completion, follow-ups, volunteer notes, cursor |
| `documents` | `merge_documents` | `intake` (queues uploads); orchestrator (`queued → extracting`); `extract_document`; `aggregate_extractions`; `review_audit` (re-queue for recheck); `human_review` (corrections) | `doc_id → {doc_type, path, sha256, source, uploaded_at, revision, status, …}` |
| `extractions` | `merge_extractions` | `extract_document` (parallel); `human_review` (corrected record) | `doc_id → typed record` (fields, flags, masked SSN info, issues) |
| `source_facts` | — | `aggregate_extractions` only | `doc:{doc_id}:{box}` and `doc:{doc_id}:meta` facts published for downstream use |
| `extraction_summary` | — | `aggregate_extractions`; `human_review` sets `stale: true` after a correction | Usable / rejected counts |
| `eligibility` | — | `eligibility_rules` only | `status` (`screening`, `need_input`, `escalate` or `ok`), `mode` (`screening` or `final`), cited `decisions`, `boxes`, `conflict`, `facts_version`, `source_version` |
| `lines` | `merge_dict` | `computation` only | `line → {value, facts_version, …}` |
| `provenance` | `merge_dict` | `computation` (`line:*`), `aggregate_extractions` (`doc:*`), `intake` (`fact:*`, direct input), `human_review` (`review:*`) | One record per line, document box, fact or review decision |
| `calc` | — | `computation` only | `calc_id`, `facts_version`, `source_version`, tool calls, `box_count`, `runs` |
| `review` | — | `review_audit`; `human_review` (on `retry_processing`) | `status` (`passed` or `revision_requested`), `for_calc`, `passed_for`, `passes`, `open_issues`, `targets`, `history` |
| `assembly` | — | `return_assembly` only | `status` (`ready`, `gaps`, `awaiting_audit` or `error`), `version`, `calc`, PDF and audit-record paths, `pdf_check` |
| `escalation` | — | any agent through `AgentResult`; orchestrator (`loop_guard`); `human_review` clears it to `None` on a valid decision | Pending escalation request |
| `human_events` | `append_unique` (by `id`) | `human_review` | Escalation events and their resolution: who, when, action, rationale, evidence, changes |
| `transcript` | `operator.add` | `intake`; `human_review` (reviewer messages relayed to the taxpayer) | Full conversation; never trimmed. SSN answers are stored as a placeholder |
| `routing` | — | orchestrator; `human_review` (resets on retry) | `next`, `history` (last 60 hops), `handoffs_this_run`, `signature_counts`, `marker`, `run` |
| `metrics` | `operator.add` | every agent that calls a model or tool | Tool-call and model-call records, including token usage in live mode |
| `trace` | `operator.add` | every node | Agent, outcome and summary per step |
| `error` | — | initial state | Present in the schema. Processing errors are surfaced by the service through the case store, not written into state |

## Reducers

| Reducer | Guarantee |
|---|---|
| `merge_dict` | Key-wise merge; the update wins for the keys it names |
| `merge_documents` | Merge by `doc_id`. A status only moves forward (`uploaded < queued < extracting < extracted/needs_attention < rejected/duplicate`), unless the update carries a higher `revision`, which is an explicit re-queue |
| `merge_extractions` | Order-independent. A new id is added, an identical record is a no-op, and a higher `revision` wins. If the same revision arrives with different content, both candidates are kept, sorted by fingerprint, and flagged `conflict: true`, so the aggregator escalates instead of picking one |
| `append_unique` | Appends; a record with an existing `id` replaces it in place |
| `operator.add` | Append-only |

These are covered by `tests/unit/test_merge_order.py`.

## Versions and staleness

| Marker | Meaning | Used for |
|---|---|---|
| `facts_version` | Incremented on every fact change | Rules, calculation, audit and assembly must all match the current value |
| `source_version` | First 12 hex characters of a SHA-256 over `source_facts` (`eligibility_rules.source_version`) | Detects document changes |
| `documents[*].revision` | Incremented on re-upload or audit re-queue | Lets a re-extraction replace an older record |
| `calc.calc_id` | New id on every computation run | Ties audit (`review.for_calc`, `review.passed_for.calc`) and assembly (`assembly.calc`) to one calculation |

The orchestrator re-routes when these disagree (see [IMPLEMENTATION_NOTES.md](IMPLEMENTATION_NOTES.md#why-a-rule-based-orchestrator)):
- `eligibility.facts_version` or `source_version` is out of date → `rules`
- `calc` is out of date → `computation`
- `review.for_calc != calc.calc_id` → `review`
- `assembly.calc != calc.calc_id` → `assembly`

## Invariants

1. Only `computation` writes `lines`, and every value in it is copied from an MCP tool result with a `line:*` provenance record.
2. Only `aggregate_extractions` writes `source_facts`. Downstream agents read document values only from there.
3. `return_assembly` produces a draft only when `review.status == "passed"` and `review.passed_for == {"facts_version": <current>, "calc": <current calc_id>}`, and no required line is stale or missing provenance.
4. Only confirmed facts are used (`fact_value`, `flat_facts`). Unknown values are absent, never zero.
5. Stored SSNs are fictional (900–999) and masked in extraction records and model context. A document showing a non-test SSN is rejected and its file deleted.
6. A human-review event id is a deterministic hash of its inputs, and it is marked resolved once. The service rejects a second resolution.
7. `status` in `TERMINAL_STATUSES` (`submitted_for_internal_review`, `referred_out_of_scope`, `closed`) ends the graph.
8. The transcript and facts are never trimmed. Model context is built separately by `src/memory.py`.
