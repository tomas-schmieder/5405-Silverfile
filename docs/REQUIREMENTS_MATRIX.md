# Requirements matrix

This maps requirements in [Assignment-7-Details.md](../Assignment-7-Details.md) to the merged build (`main` at `aeda711`).

**Status key**

- **Verified:** covered by tests in the core suite. ChatGPT/Codex ran it independently against `aeda711`: 299 passed in 6.18 s on Python 3.12. That run is **externally reported**; no team member has recorded their own run on this build. Earlier stage runs are in [ACCEPTANCE_RESULTS.md](ACCEPTANCE_RESULTS.md).
- **Unverified:** implemented, but the covering tests are skipped or not run (`tests/integration`, `tests/live`, `tests/person3_ocr`), or the behavior needs a browser, live API, Docker or a manual check that has not been recorded.
- **Incomplete:** missing, or a known gap remains. See [KNOWN_LIMITATIONS.md](KNOWN_LIMITATIONS.md).

"Verified" means only what the named tests check. It is not an end-to-end acceptance claim.

## §2 Non-negotiable behavior

| Requirement | Implementation | Tests | Status |
|---|---|---|---|
| Never file anything; output is a draft plus audit record | `src/agents/return_assembly.py`, `src/output/pdf_writer.py` (draft banners), `src/ui/dashboard.py` ("submitted" = internal review) | `tests/person3/test_assembly_pdf.py::test_assembly_produces_draft_previews_and_audit`, `test_product_pdf_has_no_classroom_wording` | Verified (components); browser flow unverified |
| Never give tax advice; note the question for a volunteer | `src/agents/intake.py` (advice detection), `src/hitl.py` `advice_request` | `tests/person2/test_intake_and_guardrails.py::test_advice_request_escalates_and_is_noted`; `tests/live/test_live_api.py::test_live_intake_detects_advice` (skipped) | Verified (offline); live model unverified |
| Never assert an unsourced dollar amount | `src/provenance.py` `lineage_gaps`, Review/Audit, Assembly gate, no MCP fallback | `tests/person3/test_provenance.py` (4), `test_assembly_blocks_missing_provenance`, `test_unreadable_optional_amount_is_not_zero` | Verified |
| Always route to a human for §4.4 conditions | See §4.4 below | | See below |
| Handle only the §3.3 profile; escalate the rest | `src/agents/eligibility_rules.py`, `data/rule_registry.json` | `tests/person4/test_decision_table.py::test_screening_decisions`, `test_1099r_document_rules`, `test_capital_gain_distribution_escalates`; `tests/integration/...::test_mandatory_stops` (skipped) | Verified (rules); end-to-end unverified |

## §3 Specification

| Requirement | Implementation | Tests | Status |
|---|---|---|---|
| §3.1 populate the listed 1040-SR lines | `src/agents/computation.py`, `src/tools/tax_calculations.py`, `src/output/pdf_fields.py` | `tests/person5/test_tax_calculations.py`; `tests/integration/...::test_draft_cases_match_hand_worked_results` (skipped) | Verified (tools); full drafts unverified |
| §3.1 filing status and dependents from intake | `src/agents/intake.py`, `src/agents/intake_script.py` | `tests/person2/test_intake_and_guardrails.py` | Verified (offline intake) |
| §3.1 line 25c | `computation.py` sets $0 (R-WH-01) | | Incomplete: review against the assignment |
| §3.2(1) 1040-SR eligibility (born before 2 Jan 1961; one spouse on a joint return) | Rules agent, registry | `tests/person4/test_decision_table.py::test_screening_decisions`; fixture `stop_too_young` | Verified (rules) |
| §3.2(2) standard deduction chart and 12d box count; exceptions escalate | MCP `standard_deduction`; Rules box count | `tests/person5/test_tax_calculations.py::test_standard_deduction_chart`, `test_standard_deduction_exceptions_produce_no_amount`, `test_spouse_boxes_rejected_for_single`; `tests/person4/...::test_line_12d_boxes` | Verified |
| §3.2(3) enhanced senior deduction with phase-out, separate from the additional standard deduction | MCP `enhanced_senior_deduction` | `test_enhanced_senior_deduction`, `test_enhanced_deduction_is_separate_from_additional_standard_deduction` | Verified (tool). Audit does not independently recompute 13b (incomplete) |
| §3.2(4) taxable Social Security and its ordering dependency | MCP `taxable_social_security`; dependency order in `computation.py` | `test_social_security_matches_independent_oracle`, `test_social_security_counts_tax_exempt_interest_and_adjustments`, `test_social_security_rejects_negative_benefits` | Verified (tool). Audit does not independently recompute 6b (incomplete) |
| §3.2 accept only 900–999 test SSNs | `src/ssn.py`; intake and extraction | `tests/person2/...::test_fictional_ssn`, `test_invalid_ssn_entry_is_never_echoed`; `tests/person3/...::test_non_test_ssn_rejects_and_removes_uploaded_file` | Verified |
| §3.3 out-of-scope items escalate (Schedule A/C/D/E, 1099-NEC, digital assets, foreign, amended/prior year, state, 1099-R box 2b) | Rules registry; extraction box 2b check | `tests/person4/test_decision_table.py`; `tests/person3/...::test_box2b_survives_duplicate_order`, `test_box2b_survives_parallel_conflict`; stop fixtures | Verified (rules and extraction); end-to-end unverified |
| §3.3 provenance record on every monetary value | `src/provenance.py`, `computation.py`, `src/ui/provenance_view.py` | `tests/person3/test_provenance.py`, `test_extra_populated_line_also_needs_provenance` | Verified (records); viewing in the browser unverified |

## §4 Agents

| Requirement | Implementation | Tests | Status |
|---|---|---|---|
| Six distinct agents plus orchestration | Orchestrator plus Intake, Document Extraction, Eligibility & Rules, Computation, Review/Audit, Return Assembly (see [IMPLEMENTATION_NOTES.md](IMPLEMENTATION_NOTES.md#agents)) | `tests/unit/test_graph_shape.py::test_graph_nodes_and_edges` | Verified (topology) |
| Orchestrator does not extract, compute or converse | `src/agents/orchestrator.py` (routing only) | `test_graph_nodes_and_edges` | Verified (structure) |
| Intake is the only agent that talks to the taxpayer; no arithmetic or rule interpretation | `src/agents/intake.py` | `tests/person2/test_copy_and_interrupts.py::test_intake_actually_interrupts_and_resumes`, `test_money_parsing_is_exact` | Verified |
| Document Extraction: typed records, no interpretation; W-2 from image | `src/agents/document_extraction.py`, `src/tools/ocr_reader.py`, `src/llm.py` | `tests/person3/test_document_validation.py`, `test_ocr_layout.py`; `tests/person3_ocr` (skipped); `tests/live/...::test_live_w2_image_extraction` (skipped) | Validation verified. **Reading a real image is unverified** (native OCR blocked; live vision not run) |
| Eligibility & Rules grounded in the reference corpus and cites | `eligibility_rules.py`, `data/rule_registry.json`, `data/source_manifest.json` | `tests/person4/...::test_every_rule_cites_a_source`, `tests/person4/test_reference_integrity.py` | Verified (citations exist). Interpretation not independently checked |
| Computation: every number from a deterministic MCP tool call | `src/agents/computation.py`, `mcp_server/server.py`, `src/tools/mcp_client.py` | `tests/person5/test_mcp_contract.py` (real stdio call), `test_tax_calculations.py` | Verified |
| Review/Audit checks provenance, recomputes, finds contradictions, sends work back without fixing | `src/agents/review_audit.py`, MCP `verify_return` | `tests/person5/...::test_verify_return_detects_contradictions`, `test_qualified_dividend_tax_is_not_exempt_from_audit`; `tests/integration/...::test_review_revise_cycle_is_bounded_and_recovers` (skipped) | Contradiction checks verified; send-back loop **unverified**; 6b/13b recomputation **incomplete** |

### §4.1 Orchestration

| Requirement | Implementation | Tests | Status |
|---|---|---|---|
| Conditional, state-based routing | `orchestrator.decide()`, `graph.add_conditional_edges` | `test_graph_nodes_and_edges` (all orchestrator edges conditional) | Verified |
| Parallel branch, aggregation step and order-independent reducer | `Send` fan-out → `aggregate_extractions`; `src/state.py` reducers | `tests/unit/test_merge_order.py` (6); `tests/integration/...::test_parallel_extraction_and_aggregation` (skipped) | Reducers verified; parallel run **unverified** |
| Review → revise cycle with an explicit, tested bound | `MAX_REVIEW_PASSES = 3` in `review_audit.py` | `tests/integration/...::test_review_revise_cycle_is_bounded_and_recovers`, `test_review_bound_escalates` (skipped) | **Unverified:** tests exist but are skipped |
| Loop guard, with a test that triggers it | `MAX_HANDOFFS_PER_RUN`, `MAX_SIGNATURE_REPEATS` in `orchestrator.py` | `tests/integration/...::test_loop_guard_breaks_pathological_handoff_cycle`, `test_loop_guard_handoff_cap` (skipped) | **Unverified:** tests exist but are skipped |
| Orchestration diagram in the README | [README.md](../README.md#orchestration) (Mermaid, hand-transcribed from `src/graph.py`); `python run.py graph` writes `docs/graph.mmd` | | Present |

### §4.2 Provenance view

| Requirement | Implementation | Tests | Status |
|---|---|---|---|
| Sample filled form where each number's calculation and sources can be seen | `src/ui/provenance_view.py`, "Draft & provenance" view, dashboard case detail | `tests/integration/...::test_eval_case_1_w2_source_chain` (skipped) | **Unverified** in the browser |
| Direct user input recorded with date and who entered it | Intake direct-input provenance; `test_manual_nonw2_has_entry_timestamp` | `tests/person3/test_document_validation.py` | Verified (records) |

### §4.3 Accessibility and dignity (at least four required)

| Area | Implementation | Tests | Status |
|---|---|---|---|
| One question at a time | `intake_script.py`, `src/ui/taxpayer.py` | `test_each_question_is_a_single_question`, `test_first_step_is_one_question` | Verified (logic); UI unverified |
| Plain language | Glosses in `intake_script.py`; `src/ui_text.py` | `test_user_status_copy_does_not_promise_contact_or_active_review` | Partly verified (copy) |
| Repetition and drift | Corrections and go-back in `intake.py` | `test_corrections_keep_history_and_go_back_keeps_answers`; `tests/integration/...::test_correction_after_draft_invalidates_and_recomputes` (skipped) | Verified (intake) |
| No unnecessary PII; volunteered SSN handling | Redaction in `intake.py`; `src/ssn.py` | `test_volunteered_ssn_is_removed_and_not_stored`, `test_redaction`, `tests/unit/...::test_fact_summary_masks_taxpayer_and_dependent_identifiers` | Verified |
| Resumability with a summary | SQLite checkpointer (`service.py`); `memory.resume_summary` | `tests/unit/...::test_case_metadata_survives_reopening_and_keeps_cases_separate`; `tests/integration/...::test_persistence_across_restart` (skipped) | Metadata verified; checkpoint restart **unverified** |
| Honest uncertainty, reachable from the agent | `UNSURE_RE` and `taxpayer_needs_help` in `intake.py` | `test_unsure_is_not_stored_as_a_name`, `test_offline_intents` | Verified (offline) |
| Demo shows them working | | | **Incomplete:** no recording |

### §4.4 Human-in-the-loop escalation (LangGraph interrupt)

| Condition | Reason code | Tests | Status |
|---|---|---|---|
| Interrupt raised and resumed | `src/agents/human_review.py` | `tests/person2/test_copy_and_interrupts.py::test_human_review_actually_interrupts_and_records_resolution` (in-memory checkpointer) | Verified (node); SQLite resume unverified |
| (1) Out-of-scope item | `out_of_scope` | `tests/person4/test_decision_table.py`; `tests/integration/...::test_out_of_scope_can_only_be_referred` (skipped) | Verified (rules) |
| (2) User/document conflict | `user_document_conflict` | `test_conflict_asks_follow_up_then_escalates`, `test_smaller_difference_still_requests_confirmation`; `tests/integration/...::test_eval_case_2_hitl_round_trip` (skipped) | Verified (rules); round trip unverified |
| (3) 1099-R box 2b | `form_1099r_2b` | `test_1099r_document_rules`, `test_box2b_survives_*` | Verified |
| (4) Advice request | `advice_request` | `test_advice_request_escalates_and_is_noted` | Verified (offline) |
| (5) Filing-status ambiguity (spouse died) | `filing_status_ambiguity` | `test_screening_decisions`; fixture `stop_spouse_died` | Verified (rules) |
| (6) Exploitation / third-party pressure | `exploitation_concern` | `test_exploitation_outranks_other_escalations`, `test_reviewer_clearance_never_overrides_hard_exclusion`; fixtures `stop_exploitation`, `stop_third_party` | Verified (rules) |
| Reviewer actions constrained; no generic approve | `src/hitl.py` | `test_reviewer_decisions_are_constrained`, `test_no_reason_has_a_generic_approve`, `test_event_ids_are_deterministic` | Verified |

### §4.5 Context-window strategy

| Requirement | Implementation | Tests | Status |
|---|---|---|---|
| Trimming, rolling summary or selective recall | Selective recall in `src/memory.py` | `test_context_trimming_preserves_saved_history_and_current_reply`, `test_document_context_selects_current_document_without_mutating_history`, `test_context_strategy_bounds_model_input`; `test_context_strategy_flattens_intake_tokens` (skipped, fake client) | Verified (context construction) |
| `--no-context-strategy` flag | `run.py benchmark`, `scripts/context_benchmark.py` | | Present; not run |
| Per-document input-token table in `docs/metrics.md`, on vs off | `context_benchmark.py --report` | | **Incomplete:** no real measurements |

## §5 Deliverables

| Deliverable | Location | Status |
|---|---|---|
| README with detailed run instructions | [README.md](../README.md) | Present; instructions not yet exercised end to end on the merged build |
| `requirements.txt`, `.env.example`, `run.py` | Repository root | Present |
| `src/state.py`, `graph.py`, `memory.py`, `agents/` | `src/` | Present |
| `data/generate_fixtures.py`, `policy.md`, `fixtures/` | `data/` | Present |
| `evals/cases.json` | `evals/` (19 cases plus expected results) | Present; full eval not re-run |
| `tests/test_merge_order.py`, `test_decision_table.py` | `tests/unit/test_merge_order.py`, `tests/person4/test_decision_table.py` | Verified |
| `traces/` | Generated by `python run.py eval` | Incomplete (not generated) |
| `docs/graph.png`, `metrics.md`, `IMPLEMENTATION_NOTES.md`, `AI_DISCLOSURE.md` | `docs/` | Implementation notes and AI disclosure present. No graph image; the README Mermaid diagram is used instead. `metrics.md` missing (needs the live experiment) |
| §5.2 `demo/eval_case_1.md`, `eval_case_2.md`, W-2 images | `demo/` (images are `.png`) | Present. Eval case 1 instructions may not match zero-tolerance wage behavior (unverified) |
| Demo video, 5–10 minutes | | **Incomplete** |
| §5.3 AI-use disclosure | [AI_DISCLOSURE.md](AI_DISCLOSURE.md) | Present; members must confirm their own entries |
| §1.1 specialization table | [CONTRIBUTIONS.md](CONTRIBUTIONS.md) | **Incomplete:** assignments pending |

## §6 Rubric D (evaluation) and bonus

| Item | Status |
|---|---|
| D.1 clean run from eval_case_1 produces a filled 1040-SR | Unverified (and see the eval case 1 tolerance note) |
| D.2 dashboard exists | Present (`src/ui/dashboard.py`); browser unverified |
| D.3 W-2 amounts read from an image | **Unverified:** needs live vision or isolated native OCR |
| D.4 eval_case_2 HITL triggered and resolved | Unverified |
| D.5 grader-invented clean run | Unverified (`grader_style_unseen` fixture exists) |
| Bonus: HITL links in dashboard | Implemented (review queue, Open, constrained review form); unverified in the browser |
| Bonus: five-page report | **Incomplete** (outline only in [REPORT_AND_DEMO_CHECKLIST.md](REPORT_AND_DEMO_CHECKLIST.md)) |
| Bonus: Docker container | Supplied; unverified |
