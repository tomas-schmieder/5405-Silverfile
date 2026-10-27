"""Eligibility & Rules decision table: one row per rule boundary.

Each case builds a minimal state, runs the rules agent (with in-process tool
stub), and checks the decision and the escalation reason. Every decision must
carry citations from the registry.
"""

import pytest

from src.agents.eligibility_rules import compute_boxes, registry, rules_node


def fact(v):
    return {"value": v, "status": "confirmed", "source": {}}


def state_with(facts: dict, complete: bool = False, extractions: dict | None = None, documents: dict | None = None):
    return {"case_id": "T", "facts": {k: fact(v) for k, v in facts.items()}, "facts_version": 1,
            "intake": {"complete": complete, "followups": []}, "documents": documents or {},
            "extractions": extractions or {}, "source_facts": {}}


BASE = {"tp.first_name": "A", "tp.last_name": "B", "tp.dob": "1955-01-01", "filing_status": "single",
        "tp.ssn": "900-11-2222", "return_type_ok": True, "answerer": "self", "us_resident_all_year": True,
        "tp.claimable_dependent": False, "spouse_died_2025": False, "itemize": False, "other_income.any": False}


@pytest.mark.parametrize("overrides,reason", [
    ({"tp.dob": "1961-01-01"}, None),                                   # born before Jan 2, 1961: eligible
    ({"tp.dob": "1961-01-02"}, "out_of_scope"),                         # on the cutoff: not eligible
    ({"tp.dob": "1965-05-05", "filing_status": "mfj", "sp.dob": "1958-03-03"}, None),  # joint: one spouse suffices
    ({"tp.dob": "1965-05-05", "filing_status": "mfj", "sp.dob": "1962-03-03"}, "out_of_scope"),
    ({"itemize": True}, "out_of_scope"),
    ({"return_type_ok": False}, "out_of_scope"),
    ({"other_income.any": True, "other_income.kinds": "rental property"}, "out_of_scope"),
    ({"tp.claimable_dependent": True}, "out_of_scope"),
    ({"filing_status": "mfs", "mfs.spouse_itemizes": True}, "out_of_scope"),
    ({"us_resident_all_year": False}, "out_of_scope"),
    ({"spouse_died_2025": True, "filing_status": "mfj"}, "filing_status_ambiguity"),
    ({"filing_status": "qss", "qss.spouse_death_year": "2025", "qss.dependent_child": True}, "filing_status_ambiguity"),
    ({"filing_status": "qss", "qss.spouse_death_year": "2024", "qss.dependent_child": False}, "filing_status_ambiguity"),
    ({"filing_status": "hoh", "hoh.qualifying_person": False}, "filing_status_ambiguity"),
    ({"answerer": "helper", "helper.authority": False}, "exploitation_concern"),
    ({"answerer": "helper", "helper.authority": True}, None),
    ({"refund.method": "direct_deposit", "refund.account_own": False}, "exploitation_concern"),
    ({"dependents": [{"first": str(i)} for i in range(5)], "dependents.any": True}, "out_of_scope"),
])
def test_screening_decisions(runtime, overrides, reason):
    out = rules_node(state_with({**BASE, **overrides}), runtime)
    got = (out.get("escalation") or {}).get("reason")
    assert got == reason
    for d in out["eligibility"]["decisions"]:
        assert d["citations"], d


def test_exploitation_outranks_other_escalations(runtime):
    out = rules_node(state_with({**BASE, "itemize": True, "refund.account_own": False}), runtime)
    assert out["escalation"]["reason"] == "exploitation_concern"
    assert out["escalation"]["details"]["also"]


def test_reviewer_clearance_never_overrides_hard_exclusion(runtime):
    facts = {**BASE, "itemize": True, "review.cleared": ["out_of_scope"]}
    assert rules_node(state_with(facts), runtime)["escalation"]["reason"] == "out_of_scope"
    facts = {**BASE, "refund.account_own": False, "review.cleared": ["exploitation_concern"]}
    assert rules_node(state_with(facts), runtime).get("escalation") is None


def _r_doc(doc_id, flags=None, code="7", box2a="1000.00", ira=False):
    rec = {"doc_id": doc_id, "doc_type": "1099-R", "payer": "P", "distribution_code": code,
           "flags": {"taxable_not_determined": False, "ira_sep_simple": ira, **(flags or {})},
           "fields": {"1": {"value": "1000.00"}, "2a": {"value": box2a, "blank": box2a is None},
                      "4": {"value": "0.00"}}}
    return {doc_id: rec}, {doc_id: {"status": "extracted", "owner": "taxpayer"}}


@pytest.mark.parametrize("flags,code,box2a,reason", [
    ({"taxable_not_determined": True}, "7", None, "form_1099r_2b"),
    ({}, "G", "1000.00", "out_of_scope"),
    ({}, "1", "1000.00", "out_of_scope"),
    ({}, "7", None, "document_problem"),
    ({}, "7", "1000.00", None),
])
def test_1099r_document_rules(runtime, flags, code, box2a, reason):
    ex, docs = _r_doc("r1", flags, code, box2a)
    out = rules_node(state_with({**BASE, "docs.1099r.count": 1, "qcd.any": False}, complete=True,
                                extractions=ex, documents=docs), runtime)
    assert (out.get("escalation") or {}).get("reason") == reason


def test_capital_gain_distribution_escalates(runtime):
    ex = {"d1": {"doc_id": "d1", "doc_type": "1099-DIV", "payer": "Fund", "fields": {"1a": {"value": "100.00"},
                                                                                    "2a": {"value": "50.00"}}}}
    out = rules_node(state_with({**BASE}, complete=True, extractions=ex,
                                documents={"d1": {"status": "extracted"}}), runtime)
    assert out["escalation"]["reason"] == "out_of_scope"


def test_qcd_requires_age_70_and_a_half(runtime):
    ex, docs = _r_doc("r1", ira=True)
    young = {**BASE, "tp.dob": "1956-03-03", "qcd.any": True, "qcd.amount": "100.00"}
    out = rules_node(state_with(young, complete=True, extractions=ex, documents=docs), runtime)
    assert out["escalation"]["reason"] == "taxpayer_needs_help"
    old = {**BASE, "tp.dob": "1950-03-03", "qcd.any": True, "qcd.amount": "100.00"}
    assert rules_node(state_with(old, complete=True, extractions=ex, documents=docs), runtime).get("escalation") is None


def _w2(value):
    return ({"w": {"doc_id": "w", "doc_type": "W-2", "payer": "E", "fields": {"1": {"value": value},
                                                                               "2": {"value": "0.00"}}}},
            {"w": {"status": "extracted", "owner": "taxpayer"}})


def test_conflict_asks_follow_up_then_escalates(runtime):
    ex, docs = _w2("45200.00")
    facts = {**BASE, "docs.w2.count": 1, "stated_wages": "54000.00"}
    out = rules_node(state_with(facts, complete=True, extractions=ex, documents=docs), runtime)
    assert out["eligibility"]["status"] == "need_input"
    follow = out["intake"]["followups"][0]
    assert follow["id"] == "conflict-wages" and "$45,200.00" in follow["text"] and "$54,000.00" in follow["text"]
    out2 = rules_node(state_with({**facts, "conflict.wages.answer": "stated"}, complete=True, extractions=ex,
                                 documents=docs), runtime)
    assert out2["escalation"]["reason"] == "user_document_conflict"
    out3 = rules_node(state_with({**facts, "conflict.wages.answer": "document"}, complete=True, extractions=ex,
                                 documents=docs), runtime)
    assert out3["eligibility"]["status"] == "ok"


def test_smaller_difference_still_requests_confirmation(runtime):
    ex, docs = _w2("46850.00")
    out = rules_node(state_with({**BASE, "docs.w2.count": 1, "stated_wages": "46000.00"}, complete=True,
                                extractions=ex, documents=docs), runtime)
    assert out["eligibility"]["status"] == "need_input"


@pytest.mark.parametrize("facts,expected", [
    ({"filing_status": "single", "tp.dob": "1955-01-01", "tp.blind": True}, (True, True, False, False)),
    ({"filing_status": "mfj", "tp.dob": "1955-01-01", "sp.dob": "1958-01-01", "sp.blind": True},
     (True, False, True, True)),
    ({"filing_status": "mfj", "tp.dob": "1955-01-01", "sp.dob": "1962-01-01"}, (True, False, False, False)),
    ({"filing_status": "hoh", "tp.dob": "1955-01-01", "sp.dob": "1955-01-01"}, (True, False, False, False)),
    ({"filing_status": "mfs", "tp.dob": "1955-01-01", "sp.dob": "1950-01-01", "mfs.spouse_no_income": False},
     (True, False, False, False)),
    ({"filing_status": "mfs", "tp.dob": "1955-01-01", "sp.dob": "1950-01-01", "mfs.spouse_no_income": True},
     (True, False, True, False)),
    ({"filing_status": "single", "tp.dob": "1960-12-31"}, (True, False, False, False)),
])
def test_line_12d_boxes(facts, expected):
    b = compute_boxes(facts)
    assert (b["tp_65"], b["tp_blind"], b["sp_65"], b["sp_blind"]) == expected


@pytest.mark.parametrize("facts,expected", [
    # single 65+ with a valid SSN qualifies
    ({"filing_status": "single", "tp.dob": "1955-01-01", "tp.ssn": "900-11-2222"}, (True, False)),
    # no SSN, no enhanced deduction (R-ESD-01)
    ({"filing_status": "single", "tp.dob": "1955-01-01"}, (False, False)),
    # born on the cutoff date is not a qualifying person
    ({"filing_status": "single", "tp.dob": "1961-01-02", "tp.ssn": "900-11-2222"}, (False, False)),
    # joint: each qualifying spouse counts separately
    ({"filing_status": "mfj", "tp.dob": "1955-01-01", "tp.ssn": "900-11-2222",
      "sp.dob": "1958-01-01", "sp.ssn": "900-33-4444"}, (True, True)),
    ({"filing_status": "mfj", "tp.dob": "1955-01-01", "tp.ssn": "900-11-2222",
      "sp.dob": "1958-01-01"}, (True, False)),
    # married filing separately gets no enhanced deduction (R-ESD-02)
    ({"filing_status": "mfs", "tp.dob": "1955-01-01", "tp.ssn": "900-11-2222",
      "sp.dob": "1950-01-01", "sp.ssn": "900-33-4444", "mfs.spouse_no_income": True}, (False, False)),
])
def test_enhanced_senior_deduction_qualification(facts, expected):
    b = compute_boxes(facts)
    assert (b["tp_senior_deduction"], b["sp_senior_deduction"]) == expected


def test_every_rule_cites_a_source():
    for rule_id, rule in registry().items():
        assert rule["citations"], rule_id
        for c in rule["citations"]:
            assert c["doc"] == "assignment" or c.get("page"), (rule_id, c)


def _w2_with_medicare_wages(box5):
    ex, docs = _w2("250000.00")
    ex["w"]["fields"]["5"] = {"value": box5}
    return ex, docs


@pytest.mark.parametrize("box5,expected", [
    ("200000.01", True),    # just over the Additional Medicare Tax threshold
    ("200000.00", False),   # the tax applies only to wages over $200,000
    ("45200.00", False),
    (None, False),          # box 5 not extracted: no decision, no crash
])
def test_additional_medicare_withholding_flagged_for_line_25c(runtime, box5, expected):
    ex, docs = _w2_with_medicare_wages(box5)
    if box5 is None:
        del ex["w"]["fields"]["5"]
    out = rules_node(state_with({**BASE, "docs.w2.count": 1}, complete=True, extractions=ex, documents=docs), runtime)
    flagged = [d for d in out["eligibility"]["decisions"]
               if d["rule_id"] == "R-WH-01" and "Additional Medicare" in d["detail"]]
    assert bool(flagged) is expected
    assert out.get("escalation") is None
    for d in flagged:
        assert d["result"] == "info" and d["citations"]


def test_line_12d_decision_says_none_when_no_box_applies(runtime):
    out = rules_node(state_with({**BASE, "tp.dob": "1970-05-05"}), runtime)
    d = next(d for d in out["eligibility"]["decisions"] if d["rule_id"] == "R-SD-01")
    assert d["detail"] == "Line 12d boxes: none"
    out = rules_node(state_with({**BASE, "tp.blind": True}), runtime)
    d = next(d for d in out["eligibility"]["decisions"] if d["rule_id"] == "R-SD-01")
    assert d["detail"] == "Line 12d boxes: tp_65, tp_blind"


def _div(box2a):
    return ({"d1": {"doc_id": "d1", "doc_type": "1099-DIV", "payer": "Fund",
                    "fields": {"1a": {"value": "100.00"}, "2a": {"value": box2a}}}},
            {"d1": {"status": "extracted"}})


@pytest.mark.parametrize("box2a,escalates", [
    ("0.00", False), ("0", False), ("0.0", False), ("", False), (None, False), ("$0.00", False),
    ("50.00", True), ("1,250.00", True), ("0.01", True),
])
def test_capital_gain_distribution_amount_formats(runtime, box2a, escalates):
    ex, docs = _div(box2a)
    out = rules_node(state_with({**BASE}, complete=True, extractions=ex, documents=docs), runtime)
    assert (out.get("escalation") is not None) is escalates


@pytest.mark.parametrize("box5,escalates", [
    ("-250.00", True), ("(250.00)", True), ("-$250.00", True),
    ("-0.00", False), ("0.00", False), ("12000.00", False), (None, False),
])
def test_negative_ssa_benefits_formats(runtime, box5, escalates):
    ex = {"s1": {"doc_id": "s1", "doc_type": "SSA-1099", "payer": "SSA", "fields": {"5": {"value": box5}}}}
    out = rules_node(state_with({**BASE, "docs.ssa1099.count": 1}, complete=True, extractions=ex,
                                documents={"s1": {"status": "extracted"}}), runtime)
    assert (out.get("escalation") is not None) is escalates
    if escalates:
        assert out["escalation"]["reason"] == "out_of_scope"


def test_mfj_with_unknown_spouse_birth_date_waits_for_it(runtime):
    facts = {**BASE, "filing_status": "mfj", "tp.dob": "1965-05-05"}
    out = rules_node(state_with(facts), runtime)
    assert out.get("escalation") is None
    assert "sp.dob" in out["eligibility"]["pending"]


def test_qcd_without_an_ira_form_needs_help(runtime):
    out = rules_node(state_with({**BASE, "tp.dob": "1950-03-03", "qcd.any": True}, complete=True), runtime)
    assert out["escalation"]["reason"] == "taxpayer_needs_help"


def test_extra_uploaded_form_asks_before_counting_it(runtime):
    ex = {f"w{i}": {"doc_id": f"w{i}", "doc_type": "W-2", "payer": "E", "fields": {"1": {"value": "100.00"}}}
          for i in (1, 2)}
    docs = {k: {"status": "extracted", "owner": "taxpayer"} for k in ex}
    state = state_with({**BASE, "docs.w2.count": 1}, complete=True, extractions=ex, documents=docs)
    out = rules_node(state, runtime)
    assert out["eligibility"]["status"] == "need_input"
    assert out["intake"]["followups"][0]["id"] == "conflict-count-W-2"
    confirmed = state_with({**BASE, "docs.w2.count": 1, "conflict.count.W-2": "include"}, complete=True,
                           extractions=ex, documents=docs)
    assert rules_node(confirmed, runtime)["eligibility"]["status"] == "ok"
    extra = state_with({**BASE, "docs.w2.count": 1, "conflict.count.W-2": "extra"}, complete=True,
                       extractions=ex, documents=docs)
    assert rules_node(extra, runtime)["escalation"]["reason"] == "user_document_conflict"


def _schedules(runtime, facts):
    out = rules_node(state_with({**BASE, **facts}), runtime)
    return out["eligibility"]["schedules"], out["eligibility"]["decisions"]


@pytest.mark.parametrize("facts,applies", [
    ({}, True),                                                         # single, 65+, SSN
    ({"tp.ssn": None}, False),                                          # no valid SSN
    ({"tp.dob": "1970-01-01"}, False),                                  # not a qualifying person
    ({"filing_status": "mfs", "mfs.spouse_no_income": True}, False),    # MFS gets none (R-ESD-02)
    ({"filing_status": "mfj", "tp.dob": "1970-01-01", "sp.dob": "1955-01-01", "sp.ssn": "900-33-4444"}, True),
])
def test_schedule_1a_applies_when_someone_qualifies_for_the_senior_deduction(runtime, facts, applies):
    schedules, decisions = _schedules(runtime, facts)
    assert schedules["1-A"]["applies"] is applies
    assert schedules["1-A"]["reason"]
    mentioned = [d for d in decisions if "Schedule 1-A" in d["detail"]]
    assert bool(mentioned) is applies
    for d in mentioned:
        assert d["citations"]


@pytest.mark.parametrize("facts,expected", [
    ({}, {"1": None, "2": None, "3": None}),                            # not asked yet
    ({"sched.any": False}, {"1": False, "2": False, "3": False}),
    ({"sched.any": True, "s1.l10": "1500.00", "s1.l26": "0.00", "s2.l3": "0.00", "s2.l21": "0.00",
      "s3.l8": "0.00", "s3.l15": "0.00"}, {"1": True, "2": False, "3": False}),
    ({"sched.any": True, "s1.l10": "0.00", "s1.l26": "0.00", "s2.l3": "0", "s2.l21": "250.00",
      "s3.l8": "75.00", "s3.l15": "0.00"}, {"1": False, "2": True, "3": True}),
    ({"sched.any": True, "s1.l10": "0.00"}, {"1": None, "2": None, "3": None}),   # amounts still missing
])
def test_schedules_1_2_3_follow_the_amounts_the_taxpayer_entered(runtime, facts, expected):
    schedules, decisions = _schedules(runtime, facts)
    assert {k: schedules[k]["applies"] for k in ("1", "2", "3")} == expected
    for name, applies in expected.items():
        mentioned = [d for d in decisions if f"Schedule {name} applies" in d["detail"]]
        assert bool(mentioned) is bool(applies)
        for d in mentioned:
            assert d["rule_id"] == "R-SCHED-01" and d["citations"]
