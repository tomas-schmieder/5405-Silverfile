"""Fixture definitions in data/generate_fixtures.py match the committed case files.

Regenerating fixtures must not drop scripted answers, in particular the wage
confirmation that the zero-tolerance conflict rule (R-CONFLICT-01) asks for.
No images are rendered here.
"""

import json
from pathlib import Path

import pytest

from data.generate_fixtures import CASES, WAGES_MATCH_W2, case_record

ROOT = Path(__file__).resolve().parents[2]
CLEAN_RUNS_WITH_ESTIMATED_WAGES = ["eval_case_1", "grader_style_unseen", "case_mfj_high_income", "case_hoh_dependent"]


@pytest.mark.parametrize("case_id", sorted(CASES))
def test_generated_record_matches_committed_case_file(case_id):
    on_disk = json.loads((ROOT / "data" / "fixtures" / case_id / "case.json").read_text())
    assert case_record(case_id, CASES[case_id]) == on_disk


@pytest.mark.parametrize("case_id", CLEAN_RUNS_WITH_ESTIMATED_WAGES)
def test_clean_runs_confirm_the_w2_wages(case_id):
    assert WAGES_MATCH_W2 == {"conflict-wages": "The W-2 is right"}
    assert case_record(case_id, CASES[case_id])["followup_answers"] == WAGES_MATCH_W2
    assert not CASES[case_id].get("reviewer_actions")


def test_eval_case_2_keeps_its_unresolved_conflict():
    spec = case_record("eval_case_2", CASES["eval_case_2"])
    assert spec["followup_answers"] == {"conflict-wages": "My number is right"}
    assert [a["reason"] for a in spec["reviewer_actions"]] == ["user_document_conflict"]


def test_every_case_with_stated_wages_and_a_w2_answers_the_confirmation():
    """A clean run whose stated wages differ from its W-2s needs a scripted answer."""
    for case_id, spec in CASES.items():
        w2_total = sum(float(d["data"]["box1"]) for d in spec["documents"] if d["type"] == "W-2")
        stated = spec["answers"].get("stated_wages")
        if not stated or not w2_total or spec.get("expect_escalation") or spec.get("expect_document_rejection"):
            continue
        stated_amount = float("".join(ch for ch in stated if ch.isdigit() or ch == "."))
        if stated_amount != w2_total and case_id != "bench_ten_docs":
            assert "conflict-wages" in (spec.get("followup_answers") or {}), case_id
