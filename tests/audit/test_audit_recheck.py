"""Audit re-derivation of lines 6a, 6b, 11b and 13b from source amounts.

The recheck tool is a separate implementation from the production worksheet
(closed form; no calls to taxable_social_security / enhanced_senior_deduction).
These tests check that it agrees with production on valid returns, and that a
wrong 6b or 13b fails the audit even when every downstream total is recomputed
consistently around the wrong value (which ``verify_return`` alone accepts).
"""

import random
from decimal import Decimal

import pytest

from src.agents.review_audit import recheck_inputs
from src.tools import tax_calculations as tc


def _sum(items):
    return sum((tc.parse_money(a) for a in items), Decimal("0"))


def build_return(fs, sources, direct, dobs, lived_apart=False, override=None):
    """A complete, internally consistent set of lines built with the production tools.

    ``override`` replaces 6b and/or 13b with a wrong value; every later line is then
    recomputed from it, so the totals stay consistent with the wrong amount.
    """
    override = override or {}
    line = lambda items: str(tc.round_dollar(_sum(items)))  # noqa: E731
    lines = {"1z": line(sources.get("wages", [])), "2a": line(sources.get("tax_exempt_interest", [])),
             "2b": line(sources.get("taxable_interest", [])), "3a": "0",
             "3b": line(sources.get("ordinary_dividends", [])),
             "4b": str(tc.round_dollar(max(Decimal(0), _sum(sources.get("ira_taxable", [])) - tc.parse_money(direct.get("qcd", "0"))))),
             "5b": line(sources.get("pension_taxable", [])), "7a": "0", "8": line([direct.get("schedule1_line10", "0")]),
             "10": line([direct.get("schedule1_line26", "0")])}
    lines["4a"], lines["5a"] = lines["4b"], lines["5b"]
    ss = tc.taxable_social_security(fs, str(_sum(sources.get("ssa_net_benefits", []))), lines["1z"], lines["2b"],
                                    lines["3b"], lines["4b"], lines["5b"], "0", lines["8"], lines["2a"],
                                    direct.get("schedule1_line26", "0"), direct.get("schedule1_line21", "0"),
                                    lived_apart)["outputs"]
    lines["6a"], lines["6b"] = ss["6a"], override.get("6b", ss["6b"])
    lines["9"] = tc.total_income(*(lines[k] for k in ["1z", "2b", "3b", "4b", "5b", "6b", "7a", "8"]))["outputs"]["9"]
    agi = tc.adjusted_gross_income(lines["9"], lines["10"])["outputs"]
    lines["11a"], lines["11b"] = agi["11a"], agi["11b"]
    tp65 = dobs[0] < "1961-01-02"
    sp65 = fs == "mfj" and dobs[1] is not None and dobs[1] < "1961-01-02"
    sd = tc.standard_deduction(fs, tp65, False, sp65, False, False, False, False)["outputs"]
    lines["12e"] = sd["12e"]
    esd = tc.enhanced_senior_deduction(fs, lines["11b"], tp65, sp65)["outputs"]["13b"]
    lines["13a"], lines["13b"] = "0", override.get("13b", esd)
    dti = tc.deductions_and_taxable_income(lines["11b"], lines["12e"], "0", lines["13b"])["outputs"]
    lines["14"], lines["15"] = dti["14"], dti["15"]
    lines["16"] = tc.income_tax(fs, lines["15"], "0", "0")["outputs"]["16"]
    tt = tc.total_tax(lines["16"], "0", "0", "0", "0")["outputs"]
    lines.update({k: tt[k] for k in ["18", "21", "22", "24"]}, **{"17": "0", "19": "0", "20": "0", "23": "0"})
    pay = tc.total_payments("1000", "0", "0", "0", "0")["outputs"]
    lines.update({"25a": "1000", "25b": "0", "25c": "0", "26": "0", "31": "0", **{k: pay[k] for k in ["25d", "32", "33"]}})
    res = tc.refund_or_amount_owed(lines["24"], lines["33"])["outputs"]
    lines.update({k: res[k] for k in ["34", "35a", "37"]})
    return lines, int(sd["12d_box_count"])


def recheck(fs, sources, direct, dobs, lines, lived_apart=False):
    return tc.recheck_social_security_and_senior(
        fs, sources, direct, lived_apart, dobs[0], dobs[1], True, dobs[1] is not None,
        {k: lines[k] for k in ("6a", "6b", "11b", "13b")})["outputs"]


BENSON = dict(fs="mfj", sources={"wages": ["45200.00"], "ssa_net_benefits": ["21600.00"]}, direct={},
              dobs=("1958-11-02", "1962-04-20"))


def test_correct_return_passes_both_audit_tools():
    lines, boxes = build_return(**BENSON)
    assert (lines["6b"], lines["13b"]) == ("16200", "6000")       # hand-worked in evals/expected_results/eval_case_2.json
    assert tc.verify_return(lines, "mfj", boxes)["outputs"]["passed"]
    out = recheck(BENSON["fs"], BENSON["sources"], BENSON["direct"], BENSON["dobs"], lines)
    assert out["passed"] and out["expected"]["6b"] == "16200" and out["expected"]["13b"] == "6000"


def test_wrong_6b_with_consistent_downstream_totals_fails_recheck():
    lines, boxes = build_return(**BENSON, override={"6b": "17200"})   # $1,000 too high; 9, 11b, 14-37 follow it
    assert tc.verify_return(lines, "mfj", boxes)["outputs"]["passed"], "the totals-only check cannot see this"
    out = recheck(BENSON["fs"], BENSON["sources"], BENSON["direct"], BENSON["dobs"], lines)
    assert not out["passed"]
    assert {f["check"] for f in out["findings"]} >= {"line6b_recompute", "line11b_recompute"}


def test_wrong_13b_with_consistent_downstream_totals_fails_recheck():
    # both spouses credited although Margaret (born 1962) does not qualify
    lines, boxes = build_return(**BENSON, override={"13b": "12000"})
    assert tc.verify_return(lines, "mfj", boxes)["outputs"]["passed"], "the totals-only check cannot see this"
    out = recheck(BENSON["fs"], BENSON["sources"], BENSON["direct"], BENSON["dobs"], lines)
    assert [f["check"] for f in out["findings"]] == ["line13b_recompute"]


def test_phaseout_error_is_caught():
    case = dict(fs="single", sources={"wages": ["88000.00"], "ssa_net_benefits": ["30000.00"]}, direct={},
                dobs=("1955-01-01", None))
    lines, _ = build_return(**case)
    assert int(lines["13b"]) < 6000                                  # phase-out applies above $75,000
    wrong, _ = build_return(**case, override={"13b": "6000"})        # phase-out ignored
    out = recheck(case["fs"], case["sources"], case["direct"], case["dobs"], wrong)
    assert [f["check"] for f in out["findings"]] == ["line13b_recompute"]


def test_mfs_living_with_spouse_and_no_senior_deduction():
    case = dict(fs="mfs", sources={"pension_taxable": ["20000.00"], "ssa_net_benefits": ["30000.00"]}, direct={},
                dobs=("1956-01-15", None))
    lines, _ = build_return(**case)
    out = recheck(case["fs"], case["sources"], case["direct"], case["dobs"], lines)
    assert out["passed"] and out["expected"]["13b"] == "0"
    wrong, _ = build_return(**case, lived_apart=True)                # used the lived-apart thresholds
    assert wrong["6b"] != lines["6b"]
    assert not recheck(case["fs"], case["sources"], case["direct"], case["dobs"], wrong)["passed"]


def test_recheck_agrees_with_production_on_random_valid_returns():
    rng = random.Random(5405)

    def amt(hi):
        return f"{rng.randint(0, hi * 100) / 100:.2f}" if rng.random() < 0.7 else "0.00"

    for _ in range(5000):
        fs = rng.choice(tc.FILING_STATUSES)
        apart = rng.random() < 0.5
        sources = {"ssa_net_benefits": [amt(40000) for _ in range(rng.randint(0, 2))],
                   "wages": [amt(90000) for _ in range(rng.randint(0, 2))], "taxable_interest": [amt(4000)],
                   "tax_exempt_interest": [amt(3000)], "ordinary_dividends": [amt(6000)],
                   "ira_taxable": [amt(20000)], "pension_taxable": [amt(30000)]}
        s26 = amt(3000)
        direct = {"schedule1_line10": amt(2000), "schedule1_line26": s26,
                  "schedule1_line21": f"{min(float(s26), rng.randint(0, 2500)):.2f}"}
        dobs = (rng.choice(["1950-05-05", "1961-01-01", "1961-01-02"]),
                rng.choice(["1955-01-01", "1962-02-02"]) if fs == "mfj" else None)
        lines, _ = build_return(fs, sources, direct, dobs, lived_apart=apart)
        out = recheck(fs, sources, direct, dobs, lines, lived_apart=apart)
        assert out["passed"], (fs, apart, sources, direct, dobs, out["findings"])


@pytest.mark.parametrize("line", ["6b", "13b"])
def test_one_dollar_error_with_consistent_downstream_totals_fails_recheck(line):
    good, boxes = build_return(**BENSON)
    lines, _ = build_return(**BENSON, override={line: str(int(good[line]) + 1)})
    assert tc.verify_return(lines, "mfj", boxes)["outputs"]["passed"], "the totals-only check cannot see this"
    out = recheck(BENSON["fs"], BENSON["sources"], BENSON["direct"], BENSON["dobs"], lines)
    assert f"line{line}_recompute" in {f["check"] for f in out["findings"]}


def test_every_line_is_compared_exactly():
    lines, _ = build_return(**BENSON)
    for line in ("6a", "6b", "11b", "13b"):
        for delta in (-1, 1):
            wrong = {**lines, line: str(int(lines[line]) + delta)}
            out = recheck(BENSON["fs"], BENSON["sources"], BENSON["direct"], BENSON["dobs"], wrong)
            assert [f["check"] for f in out["findings"]] == [f"line{line}_recompute"], (line, delta)


def test_recheck_matches_worksheet_cent_rounding_at_half_dollar_boundary():
    # 85% of $37,154.70 is $31,581.495: the worksheet enters $31,581.50 on line 17, so 6b is $31,582.
    case = dict(fs="single", sources={"wages": ["120000.00"], "ssa_net_benefits": ["37154.70"]}, direct={},
                dobs=("1950-05-05", None))
    lines, _ = build_return(**case, lived_apart=True)
    assert lines["6b"] == "31582"
    out = recheck(case["fs"], case["sources"], case["direct"], case["dobs"], lines, lived_apart=True)
    assert out["passed"] and out["expected"]["6b"] == "31582"


def test_audit_inputs_come_from_sources_not_proposed_lines():
    state = {
        "facts": {k: {"value": v, "status": "confirmed"} for k, v in {
            "filing_status": "mfj", "tp.dob": "1958-11-02", "sp.dob": "1962-04-20", "tp.ssn": "900-71-4402",
            "sp.ssn": "900-71-4403", "qcd.any": True, "qcd.amount": "500", "sched.any": False}.items()},
        "source_facts": {
            "doc:w:1": {"value": "45200.00", "doc_id": "w", "doc_type": "W-2", "box": "1"},
            "doc:w:2": {"value": "3100.00", "doc_id": "w", "doc_type": "W-2", "box": "2"},
            "doc:s:5": {"value": "21600.00", "doc_id": "s", "doc_type": "SSA-1099", "box": "5"},
            "doc:r:2a": {"value": "4000.00", "doc_id": "r", "doc_type": "1099-R", "box": "2a"},
            "doc:r:meta": {"doc_id": "r", "doc_type": "1099-R", "flags": {"ira_sep_simple": True}},
            "doc:p:2a": {"value": "7000.00", "doc_id": "p", "doc_type": "1099-R", "box": "2a"},
            "doc:p:meta": {"doc_id": "p", "doc_type": "1099-R", "flags": {}},
        },
        "lines": {"6a": "999999", "6b": "999999", "1z": "1"},     # must not be read
    }
    args = recheck_inputs(state)
    assert args["sources"] == {"wages": ["45200.00"], "ssa_net_benefits": ["21600.00"], "ira_taxable": ["4000.00"],
                               "pension_taxable": ["7000.00"]}
    assert args["direct_inputs"] == {"qcd": "500"}
    assert (args["taxpayer_dob"], args["spouse_dob"], args["filing_status"]) == ("1958-11-02", "1962-04-20", "mfj")
    assert "999999" not in repr(args)


def test_recheck_rejects_unknown_inputs_and_negative_benefits():
    with pytest.raises(tc.ToolInputError):
        tc.recheck_social_security_and_senior("single", {"line_6b": ["1"]}, {}, False, "1950-01-01", None, True,
                                              False, {})
    with pytest.raises(tc.ToolInputError):
        tc.recheck_social_security_and_senior("single", {"ssa_net_benefits": ["-5.00"]}, {}, False, "1950-01-01",
                                              None, True, False, {})
