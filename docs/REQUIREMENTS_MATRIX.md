# Requirements matrix

This maps each requirement in [Assignment-7-Details.md](../Assignment-7-Details.md) to the code and tests on `main` that satisfy it.

**Status key**

- **Verified:** covered by tests in the core command (514 passed, 0 skipped with native OCR; `python run.py eval` 19/19) and checked by the team in the running application. See [ACCEPTANCE_RESULTS.md](ACCEPTANCE_RESULTS.md).
- **Verified (images):** additionally run with the real fixture images through native OCR (`needs_ocr` tests, `tests/native_ocr`, `python run.py eval`).

`synthetic::` means `tests/integration/test_orchestration_synthetic.py`, and `e2e::` means `tests/integration/test_end_to_end.py`. Synthetic tests replace image transcription with fixture ground truth so that orchestration can be tested independently of OCR; the image paths are covered by the `needs_ocr` and native OCR tests.

## §2 Non-negotiable behavior

| Requirement | Implementation | Tests | Status |
|---|---|---|---|
| Never file anything; output is a draft plus audit record | `src/agents/return_assembly.py`, `src/output/pdf_writer.py` (draft banners), `src/ui/dashboard.py` ("submitted" = internal review) | `tests/documents/test_assembly_pdf.py::test_assembly_produces_draft_previews_and_audit`, `test_product_pdf_has_no_classroom_wording`; `synthetic::test_draft_cases_match_hand_worked_results` | Verified |
| Never give tax advice; note the question for a volunteer | `src/agents/intake.py` (advice detection), `src/hitl.py` `advice_request` | `tests/intake/test_intake_and_guardrails.py::test_advice_request_escalates_and_is_noted`; `e2e::test_mandatory_stops[stop_advice-…]`; `tests/live/test_live_api.py::test_live_intake_detects_advice` | Verified (offline and live) |
| Never assert an unsourced dollar amount | `src/provenance.py` `lineage_gaps`, Review/Audit, Assembly gate, no MCP fallback | `tests/documents/test_provenance.py` (4), `test_assembly_blocks_missing_provenance`, `test_unreadable_optional_amount_is_not_zero` | Verified |
| Always route to a human for §4.4 conditions | See §4.4 below | | See below |
| Handle only the §3.3 profile; escalate the rest | `src/agents/eligibility_rules.py`, `data/rule_registry.json` | `tests/rules/test_decision_table.py`; `e2e::test_mandatory_stops` (intake-only cases); `synthetic::test_document_driven_stops` | Verified |

## §3 Specification

| Requirement | Implementation | Tests | Status |
|---|---|---|---|
| §3.1 populate the listed 1040-SR lines | `src/agents/computation.py`, `src/tools/tax_calculations.py`, `src/output/pdf_fields.py` | `tests/computation/test_tax_calculations.py`; `synthetic::test_draft_cases_match_hand_worked_results` (8 cases, hand-worked expected lines); `e2e::test_draft_cases_match_hand_worked_results` (`needs_ocr`) | Verified (images) |
| §3.1 filing status and dependents from intake | `src/agents/intake.py`, `src/agents/intake_script.py` | `tests/intake/test_intake_and_guardrails.py`; synthetic draft cases (all five filing statuses) | Verified (offline intake) |
| §3.1 line 25c | Rule `R-WH-01`; W-2 box 6 extracted (`document_extraction.py`); MCP `additional_medicare_withheld`; computation aggregates with provenance; audit rechecks from source facts | `tests/documents/test_document_validation.py::test_w2_box6_is_published_with_provenance`; `tests/native_ocr/...::test_w2_image_high_wage_boxes_5_and_6`; `e2e::test_high_wage_w2_box6_reaches_source_facts`; `tests/computation/test_tax_calculations.py`; `case_high_wage_w2` in `python run.py eval` (25c = $600) | Verified (see [ASSUMPTIONS.md](ASSUMPTIONS.md) Q-01) |
| §3.2(1) 1040-SR eligibility (born before 2 Jan 1961; one spouse on a joint return) | Rules agent, registry | `tests/rules/test_decision_table.py::test_screening_decisions`; `e2e::test_mandatory_stops[stop_too_young-…]` | Verified |
| §3.2(2) standard deduction chart and 12d box count; exceptions escalate | MCP `standard_deduction`; Rules box count | `tests/computation/test_tax_calculations.py::test_standard_deduction_chart`, `test_standard_deduction_exceptions_produce_no_amount`, `test_spouse_boxes_rejected_for_single`; `tests/rules/...::test_line_12d_boxes` | Verified |
| §3.2(3) enhanced senior deduction with phase-out, separate from the additional standard deduction | MCP `enhanced_senior_deduction`; audit MCP `recheck_social_security_and_senior` | `test_enhanced_senior_deduction`, `test_enhanced_deduction_is_separate_from_additional_standard_deduction`; `tests/audit/test_audit_recheck.py` (`test_wrong_13b_with_consistent_downstream_totals_fails_recheck`, `test_phaseout_error_is_caught`) | Verified. Audit recomputes 13b from dates of birth and source income, compared exactly |
| §3.2(4) taxable Social Security and its ordering dependency | MCP `taxable_social_security`; dependency order in `computation.py`; audit recheck | `test_social_security_matches_independent_oracle`, `test_social_security_counts_tax_exempt_interest_and_adjustments`, `test_social_security_rejects_negative_benefits`; `tests/audit/test_audit_recheck.py`; `synthetic::test_audit_catches_wrong_6b_with_consistent_totals_and_recovers` | Verified. Audit recomputes 6b from sources, compared exactly |
| §3.2 accept only 900–999 test SSNs | `src/ssn.py`; intake and extraction | `tests/intake/...::test_fictional_ssn`, `test_invalid_ssn_entry_is_never_echoed`; `tests/documents/...::test_non_test_ssn_rejects_and_removes_uploaded_file`; `synthetic::test_document_driven_stops[stop_real_ssn_w2-…]` | Verified |
| §3.3 out-of-scope items escalate (Schedule A/C/D/E, 1099-NEC, digital assets, foreign, amended/prior year, state, 1099-R box 2b) | Rules registry; extraction box 2b check | `tests/rules/test_decision_table.py`; `tests/documents/...::test_box2b_survives_duplicate_order`, `test_box2b_survives_parallel_conflict`; `e2e::test_mandatory_stops`; `synthetic::test_document_driven_stops` | Verified |
| §3.3 provenance record on every monetary value | `src/provenance.py`, `computation.py`, `src/ui/provenance_view.py` | `tests/documents/test_provenance.py`, `test_extra_populated_line_also_needs_provenance`; synthetic draft cases resolve every required line | Verified |

## §4 Agents

| Requirement | Implementation | Tests | Status |
|---|---|---|---|
| Six distinct agents plus orchestration | Orchestrator plus Intake, Document Extraction, Eligibility & Rules, Computation, Review/Audit, Return Assembly (see [IMPLEMENTATION_NOTES.md](IMPLEMENTATION_NOTES.md#agents)) | `tests/unit/test_graph_shape.py::test_graph_nodes_and_edges` | Verified (topology) |
| Orchestrator does not extract, compute or converse | `src/agents/orchestrator.py` (routing only) | `test_graph_nodes_and_edges` | Verified (structure) |
| Intake is the only agent that talks to the taxpayer; no arithmetic or rule interpretation | `src/agents/intake.py` | `tests/intake/test_copy_and_interrupts.py::test_intake_actually_interrupts_and_resumes`, `test_money_parsing_is_exact` | Verified |
| Document Extraction: typed records, no interpretation; W-2 from image | `src/agents/document_extraction.py`, `src/llm.py` (Anthropic vision), `src/tools/ocr_reader.py` (native OCR, on by default) | `tests/documents/test_document_validation.py`, `test_ocr_layout.py`; `tests/native_ocr`; `tests/live/...::test_live_w2_image_extraction` | Verified (images) with native OCR; live vision verified |
| Eligibility & Rules grounded in the reference corpus and cites | `eligibility_rules.py`, `data/rule_registry.json`, `data/source_manifest.json` | `tests/rules/...::test_every_rule_cites_a_source`, `tests/rules/test_reference_integrity.py` | Verified |
| Computation: every number from a deterministic MCP tool call | `src/agents/computation.py`, `mcp_server/server.py`, `src/tools/mcp_client.py` | `tests/computation/test_mcp_contract.py` (real stdio call), `test_tax_calculations.py`; synthetic draft cases check `mcp-stdio` transport | Verified |
| Review/Audit checks provenance, recomputes, finds contradictions, sends work back without fixing | `src/agents/review_audit.py`; MCP `verify_return` and `recheck_social_security_and_senior` | `tests/computation/...::test_verify_return_detects_contradictions`; `tests/audit/test_audit_recheck.py`; `synthetic::test_review_revise_cycle_is_bounded_and_recovers`, `test_audit_catches_wrong_6b_with_consistent_totals_and_recovers`, `test_persistently_wrong_6b_reaches_the_review_bound` | Verified. Lines other than 6a, 6b, 11b, 13b and 25c are consistency-checked |

### §4.1 Orchestration

| Requirement | Implementation | Tests | Status |
|---|---|---|---|
| Conditional, state-based routing | `orchestrator.decide()`, `graph.add_conditional_edges` | `test_graph_nodes_and_edges` (all orchestrator edges conditional) | Verified |
| Parallel branch, aggregation step and order-independent reducer | `Send` fan-out → `aggregate_extractions`; `src/state.py` reducers | `tests/unit/test_merge_order.py` (6); `synthetic::test_parallel_extraction_and_aggregation` (3 parallel reads, 1 fan-in) | Verified |
| Review → revise cycle with an explicit, tested bound | `MAX_REVIEW_PASSES = 3` in `review_audit.py` | `synthetic::test_review_revise_cycle_is_bounded_and_recovers`, `test_review_bound_escalates` | Verified |
| Loop guard, with a test that triggers it | `MAX_HANDOFFS_PER_RUN`, `MAX_SIGNATURE_REPEATS` in `orchestrator.py` | `e2e::test_loop_guard_breaks_pathological_handoff_cycle` (no documents); `synthetic::test_loop_guard_handoff_cap` | Verified |
| Orchestration diagram in the README | [README.md](../README.md#orchestration) (Mermaid, hand-transcribed from `src/graph.py`); machine-drawn [docs/graph.png](graph.png); `python run.py graph` writes `docs/graph.png` and `docs/graph.mmd` | | Present |

### §4.2 Provenance view

| Requirement | Implementation | Tests | Status |
|---|---|---|---|
| Sample filled form where each number's calculation and sources can be seen | `src/ui/provenance_view.py`, "Draft & provenance" view, dashboard case detail | `e2e::test_eval_case_1_w2_source_chain` (`needs_ocr`) | Verified |
| Direct user input recorded with date and who entered it | Intake direct-input provenance; `test_manual_nonw2_has_entry_timestamp` | `tests/documents/test_document_validation.py` | Verified (records) |

### §4.3 Accessibility and dignity (at least four required)

| Area | Implementation | Tests | Status |
|---|---|---|---|
| One question at a time | `intake_script.py`, `src/ui/taxpayer.py` | `test_each_question_is_a_single_question`, `test_first_step_is_one_question` | Verified |
| Plain language | Glosses in `intake_script.py`; `src/ui_text.py` | `test_user_status_copy_does_not_promise_contact_or_active_review` | Verified |
| Repetition and drift | Corrections and go-back in `intake.py` | `test_corrections_keep_history_and_go_back_keeps_answers`; `e2e::test_correction_after_draft_invalidates_and_recomputes` (`needs_ocr`) | Verified (intake) |
| No unnecessary PII; volunteered SSN handling | Redaction in `intake.py`; `src/ssn.py` | `test_volunteered_ssn_is_removed_and_not_stored`, `test_redaction`, `tests/unit/...::test_fact_summary_masks_taxpayer_and_dependent_identifiers` | Verified |
| Resumability with a summary | SQLite checkpointer (`service.py`); `memory.resume_summary` | `tests/unit/...::test_case_metadata_survives_reopening_and_keeps_cases_separate`; `e2e::test_persistence_across_restart` | Verified |
| Honest uncertainty, reachable from the agent | `UNSURE_RE` and `taxpayer_needs_help` in `intake.py` | `test_unsure_is_not_stored_as_a_name`, `test_offline_intents`; `synthetic::test_eval_case_1_without_the_scripted_confirmation_stops_for_a_person` | Verified |
| Demo shows them working | Demo video | | Verified |

### §4.4 Human-in-the-loop escalation (LangGraph interrupt)

| Condition | Reason code | Tests | Status |
|---|---|---|---|
| Interrupt raised and resumed | `src/agents/human_review.py` | `tests/intake/test_copy_and_interrupts.py::test_human_review_actually_interrupts_and_records_resolution`; `synthetic::test_eval_case_2_hitl_round_trip` (SQLite checkpointer) | Verified |
| (1) Out-of-scope item | `out_of_scope` | `tests/rules/test_decision_table.py`; `e2e::test_mandatory_stops` (crypto, itemize, too young); `synthetic::test_document_driven_stops[stop_capital_gain_dist-…]` | Verified |
| (2) User/document conflict | `user_document_conflict` | `test_conflict_asks_follow_up_then_escalates`, `test_smaller_difference_still_requests_confirmation`; `synthetic::test_eval_case_2_hitl_round_trip` | Verified |
| (3) 1099-R box 2b | `form_1099r_2b` | `test_1099r_document_rules`, `test_box2b_survives_*`; `synthetic::test_document_driven_stops[stop_1099r_2b-…]` | Verified |
| (4) Advice request | `advice_request` | `test_advice_request_escalates_and_is_noted`; `e2e::test_mandatory_stops[stop_advice-…]` | Verified |
| (5) Filing-status ambiguity (spouse died) | `filing_status_ambiguity` | `test_screening_decisions`; `e2e::test_mandatory_stops[stop_spouse_died-…]` | Verified |
| (6) Exploitation / third-party pressure | `exploitation_concern` | `test_exploitation_outranks_other_escalations`, `test_reviewer_clearance_never_overrides_hard_exclusion`; `e2e::test_mandatory_stops` (exploitation, third party) | Verified |
| Reviewer actions constrained; no generic approve | `src/hitl.py` | `test_reviewer_decisions_are_constrained`, `test_no_reason_has_a_generic_approve`, `test_event_ids_are_deterministic` | Verified |

### §4.5 Context-window strategy

| Requirement | Implementation | Tests | Status |
|---|---|---|---|
| Trimming, rolling summary or selective recall | Selective recall in `src/memory.py` | `test_context_trimming_preserves_saved_history_and_current_reply`, `test_document_context_selects_current_document_without_mutating_history`, `test_context_strategy_bounds_model_input`; `test_context_strategy_flattens_intake_tokens` (`needs_ocr`, fake client) | Verified (context construction) |
| `--no-context-strategy` flag | `run.py benchmark`, `scripts/context_benchmark.py` | `tests/unit/test_context_benchmark.py` (fake client) | Verified (live run, October 29, 2026) |
| Per-document input-token table in `docs/metrics.md`, on vs off | `context_benchmark.py --report` | `tests/unit/test_context_benchmark.py` (fake client) | **Measured** (one live run, `claude-haiku-5-5`): 173,345 off vs 42,039 on (76% fewer), 10/10 consistent. See [metrics.md](metrics.md) and [ACCEPTANCE_RESULTS.md](ACCEPTANCE_RESULTS.md) |

## §5 Deliverables

| Deliverable | Location | Status |
|---|---|---|
| README with detailed run instructions | [README.md](../README.md) | Present |
| `requirements.txt`, `.env.example`, `run.py` | Repository root | Present |
| `src/state.py`, `graph.py`, `memory.py`, `agents/` | `src/` | Present |
| `data/generate_fixtures.py`, `policy.md`, `fixtures/` | `data/` | Present; generator and `case.json` files checked equal by `tests/unit/test_fixture_definitions.py` |
| `evals/cases.json` | `evals/` (19 cases plus expected results) | Present; `python run.py eval` passes 19/19 with images |
| `tests/test_merge_order.py`, `test_decision_table.py` | `tests/unit/test_merge_order.py`, `tests/rules/test_decision_table.py` | Verified |
| `traces/` | `traces/` (written by `python run.py eval` and the benchmark) | Committed: one trace per evaluation case, `eval_results.json`, and the two benchmark runs |
| `docs/graph.png`, `metrics.md`, `IMPLEMENTATION_NOTES.md`, `AI_DISCLOSURE.md` | `docs/` | Present. `docs/graph.png` is drawn from the compiled graph by `python run.py graph`; the README has the same diagram in Mermaid |
| §5.2 `demo/eval_case_1.md`, `eval_case_2.md`, W-2 images | `demo/` (images are `.png`) | Present |
| Demo video, 5–10 minutes | Submitted with the project | Present |
| §5.3 AI-use disclosure | [AI_DISCLOSURE.md](AI_DISCLOSURE.md) | Present |
| §1.1 specialization table | [CONTRIBUTIONS.md](CONTRIBUTIONS.md) | Present |

## §6 Rubric D (evaluation) and bonus

| Item | Status |
|---|---|
| D.1 clean run from eval_case_1 produces a filled 1040-SR | Verified (images): `python run.py demo eval_case_1` with no API key reaches a draft matching `evals/expected_results/eval_case_1.json`; also verified in the browser |
| D.2 dashboard exists | Verified (`src/ui/dashboard.py`) |
| D.3 W-2 amounts read from an image | Verified (images): native OCR, on by default, needs no API key. `python run.py check` reads `demo/w2_image_1.png` box 1 as 46,850.00 |
| D.4 eval_case_2 HITL triggered and resolved | Verified (images): `python run.py demo eval_case_2 --review` raises `user_document_conflict`, resolves it, and every line matches the hand-worked result; also verified in the dashboard |
| D.5 grader-invented clean run | Verified with `grader_style_unseen` (images). Accuracy on phone photos and other W-2 layouts: see [KNOWN_LIMITATIONS.md](KNOWN_LIMITATIONS.md) |
| Bonus: HITL links in dashboard | Verified (review queue, Open, constrained review form) |
| Bonus: five-page report | Present: [Proj7_report.pdf](Proj7_report.pdf), built from [Proj7_report.tex](Proj7_report.tex) with `latexmk -pdf` |
| Bonus: Docker container | Verified: `docker compose up --build` (Python 3.12) |
