"""Focused foundation checks; no model, OCR, or external service calls."""
from copy import deepcopy
from src.memory import build_intake_context, confirmed_fact_lines, build_document_context
from src.state import new_case_state
from src.store import CaseStore

def test_context_trimming_preserves_saved_history_and_current_reply():
    state = new_case_state("CASE-TEST", "2026-10-24", 2025, 1)
    state["transcript"] = [
        {"role": "user" if n % 2 == 0 else "assistant", "text": f"turn-{n:02d}"}
        for n in range(20)
    ]
    original = deepcopy(state)
    selected = build_intake_context(state, "Your first name?", "Example",
                                    strategy_enabled=True, recent_turns=2, labels={})
    full = build_intake_context(state, "Your first name?", "Example",
                                strategy_enabled=False, recent_turns=2, labels={})
    selected_text = str(selected)
    assert "turn-00" not in selected_text
    assert "turn-19" in selected_text and "Example" in selected_text
    assert "turn-00" in str(full)
    assert state == original

def test_fact_summary_masks_taxpayer_and_dependent_identifiers():
    state = {"facts": {
        "tp.ssn": {"status": "confirmed", "value": "900-12-3456"},
        "dependents": {"status": "confirmed", "value": [
            {"first": "Example", "last": "Dependent", "relationship": "child", "ssn": "901-98-7654"}
        ]}
    }}
    summary = "\n".join(confirmed_fact_lines(state))
    assert "900-12-3456" not in summary and "901-98-7654" not in summary
    assert "XXX-XX-3456" in summary and "XXX-XX-7654" in summary

def test_case_metadata_survives_reopening_and_keeps_cases_separate(tmp_path):
    path = tmp_path / "cases.db"
    first = CaseStore(path)
    first.upsert({"case_id": "A", "created_at": "first", "updated_at": "1",
                  "status": "intake", "extra": {"answered": 2}})
    first.upsert({"case_id": "B", "created_at": "second", "updated_at": "2",
                  "status": "needs_human_review"})
    reopened = CaseStore(path)
    assert reopened.get("A")["extra"] == {"answered": 2}
    assert [r["case_id"] for r in reopened.list("needs_human_review")] == ["B"]
    reopened.upsert({"case_id": "A", "created_at": "must-not-replace", "updated_at": "3",
                     "status": "processing"})
    assert reopened.get("A")["created_at"] == "first"
    assert reopened.get("B")["status"] == "needs_human_review"

def test_document_context_selects_current_document_without_mutating_history():
    prior = [{"user": [{"type": "text", "text": "old-document"}], "assistant": "old-result"}]
    current = [{"type": "text", "text": "current-document"}]
    original = deepcopy(prior)
    selected = build_document_context(prior, current, "one document processed", strategy_enabled=True)
    full = build_document_context(prior, current, "one document processed", strategy_enabled=False)
    assert "old-document" not in str(selected) and "current-document" in str(selected)
    assert "old-document" in str(full)
    assert prior == original
