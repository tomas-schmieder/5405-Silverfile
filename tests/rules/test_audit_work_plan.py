"""The audit flags planned tasks that were not done, aimed at the agent responsible (R-PLAN-01).

A tampered computation result stands in for an agent that skipped a planned task or quietly disagreed with the plan.
The audit sends the work back through the existing review cycle; the orchestrator's routing is unchanged.
"""

from src.agents.computation import computation_node
from src.driver import load_case, run_case


def tampering_computation(change, times=1):
    calls = {"n": 0}

    def node(state, rt):
        upd = computation_node(state, rt)
        calls["n"] += 1
        if calls["n"] <= times:
            change(upd["calc"])
        return upd

    return node


def drop_schedule_1a(calc):
    calc["completed_tasks"] = [t for t in calc["completed_tasks"] if t != "schedule_1a_deduction"]


def disagree_with_plan(calc):
    calc["plan_conflicts"] = [{"task": "ss_worksheet", "agent": "computation",
                               "detail": "The plan says 'ss_worksheet' does not apply but the result contains its output."}]


def test_audit_flags_a_planned_task_the_owner_did_not_complete_and_recovers(service_factory, synthetic_documents):
    view = run_case(service_factory(overrides={"computation": tampering_computation(drop_schedule_1a)}),
                    load_case("case_single_retiree_mixed"))
    first = view["review"]["history"][0]["issues"]
    assert [(i["check"], i["target"], i["id"]) for i in first] == \
        [("plan_task", "computation", "plan_task:schedule_1a_deduction")]
    assert "schedule_1a_deduction" in first[0]["detail"]
    assert view["status"] == "submitted_for_internal_review" and view["review"]["status"] == "passed"
    assert "schedule_1a_deduction" in view["calc"]["completed_tasks"]


def test_audit_flags_a_result_that_contradicts_the_plan(service_factory, synthetic_documents):
    view = run_case(service_factory(overrides={"computation": tampering_computation(disagree_with_plan)}),
                    load_case("eval_case_1"))
    first = view["review"]["history"][0]["issues"]
    assert [(i["check"], i["target"], i["id"]) for i in first] == \
        [("plan_conflict", "computation", "plan_conflict:ss_worksheet")]
    assert view["status"] == "submitted_for_internal_review"


def test_a_task_that_is_never_completed_reaches_the_review_bound(service_factory, synthetic_documents):
    view = run_case(service_factory(overrides={"computation": tampering_computation(drop_schedule_1a, times=99)}),
                    load_case("case_single_retiree_mixed"))
    event = view["pending"]["event"]
    assert event["reason"] == "review_bound"
    assert any(e.get("check") == "plan_task" for e in event["evidence"])
    assert not view["assembly"]


def test_clean_runs_raise_no_plan_issues(service_factory, synthetic_documents):
    view = run_case(service_factory(), load_case("case_single_retiree_mixed"))
    assert all(not i["check"].startswith("plan_") for h in view["review"]["history"] for i in h["issues"])
    assert view["review"]["status"] == "passed"
