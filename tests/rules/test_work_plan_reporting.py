"""Downstream agents report which planned tasks they completed (R-PLAN-01).

The unit tests exercise the comparison between the plan and an agent's result. The integration tests run the
real graph on fixtures and check that, once a draft is ready, every applicable task has been completed by its owner.
"""

import json
from pathlib import Path

import pytest

from src.agents.eligibility_rules import report_assembly_tasks, report_computation_tasks
from src.driver import load_case, run_case

ROOT = Path(__file__).resolve().parents[2]
DRAFT_CASES = [c["id"] for c in json.loads((ROOT / "evals" / "cases.json").read_text())["cases"]
               if c["expect"] == "draft"]


def task(task_id, agent, applies):
    return {"id": task_id, "agent": agent, "applies": applies, "reason": "test", "rule_id": "R-PLAN-01"}


def lines(**amounts):
    return {k.removeprefix("l"): {"value": v} for k, v in amounts.items()}


def test_computation_reports_the_applicable_tasks_it_finished():
    plan = [task("ss_worksheet", "computation", False), task("schedule_1a_deduction", "computation", True),
            task("attach_schedule_1a", "return_assembly", True)]
    done, conflicts = report_computation_tasks(plan, lines(l13b="6000", l6a="0"), ss_worksheet=None)
    assert done == ["schedule_1a_deduction"] and conflicts == []


def test_computation_does_not_claim_a_planned_task_it_skipped():
    done, conflicts = report_computation_tasks([task("ss_worksheet", "computation", True)], lines(l6a="12000"), None)
    assert done == [] and conflicts == []     # the audit, not this report, flags the missing task


@pytest.mark.parametrize("plan_task,line_values,ss", [
    ("schedule_1a_deduction", {"l13b": "6000"}, None),     # 13b above 0 but the plan says 1-A does not apply
    ("ss_worksheet", {"l6a": "12000"}, {"worksheet": 1}),  # Social Security benefits but no SSA-1099 planned
    ("additional_medicare_25c", {"l25c": "90"}, None),
])
def test_computation_raises_a_conflict_instead_of_quietly_disagreeing(plan_task, line_values, ss):
    done, conflicts = report_computation_tasks([task(plan_task, "computation", False)], lines(**line_values), ss)
    assert done == [] and [c["task"] for c in conflicts] == [plan_task]


def test_undetermined_tasks_are_neither_completed_nor_conflicts():
    plan = [task("schedule_1a_deduction", "computation", None)]
    assert report_computation_tasks(plan, lines(l13b="6000"), None) == ([], [])


def test_assembly_reports_the_attachment():
    plan = [task("attach_schedule_1a", "return_assembly", True)]
    assert report_assembly_tasks(plan, lines(l13b="6000"), True) == (["attach_schedule_1a"], [])


def test_assembly_counts_a_phased_out_deduction_as_done():
    # the writer attaches Schedule 1-A only when the deduction is above $0
    plan = [task("attach_schedule_1a", "return_assembly", True)]
    assert report_assembly_tasks(plan, lines(l13b="0"), False) == (["attach_schedule_1a"], [])


def test_assembly_flags_an_unplanned_attachment():
    plan = [task("attach_schedule_1a", "return_assembly", False)]
    done, conflicts = report_assembly_tasks(plan, lines(l13b="6000"), True)
    assert done == [] and [c["task"] for c in conflicts] == ["attach_schedule_1a"]


def test_assembly_missing_a_planned_attachment_is_not_reported_done():
    plan = [task("attach_schedule_1a", "return_assembly", True)]
    assert report_assembly_tasks(plan, lines(l13b="6000"), False) == ([], [])


def _run(service_factory, case_id):
    view = run_case(service_factory(), load_case(case_id))
    assert view["status"] == "submitted_for_internal_review", view["status"]
    return view, {t["id"]: t for t in view["eligibility"]["work_plan"]}


def test_w2_only_case_has_no_social_security_task(service_factory, synthetic_documents):
    view, plan = _run(service_factory, "eval_case_1")
    assert plan["ss_worksheet"]["applies"] is False
    assert "ss_worksheet" not in view["calc"]["completed_tasks"]


def test_married_filing_separately_case_has_no_schedule_1a(service_factory, synthetic_documents):
    view, plan = _run(service_factory, "case_mfs_lived_apart")
    assert plan["schedule_1a_deduction"]["applies"] is False and plan["attach_schedule_1a"]["applies"] is False
    assert "schedule_1a_deduction" not in view["calc"]["completed_tasks"]
    assert "attach_schedule_1a" not in view["assembly"]["completed_tasks"]


@pytest.mark.parametrize("case_id", DRAFT_CASES)
def test_every_applicable_task_is_complete_when_the_draft_is_ready(service_factory, synthetic_documents, case_id):
    view, plan = _run(service_factory, case_id)
    completed = {"computation": set(view["calc"]["completed_tasks"]),
                 "return_assembly": set(view["assembly"]["completed_tasks"])}
    for owner, done in completed.items():
        planned = {t["id"] for t in plan.values() if t["agent"] == owner and t["applies"]}
        assert planned == done, (case_id, owner, planned ^ done)
    assert view["calc"]["plan_conflicts"] == []
