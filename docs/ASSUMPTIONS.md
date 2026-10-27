# Assumptions

This separates what the assignment explicitly requires from what the team chose and what is still open. The authority for scope is [Assignment-7-Details.md](../Assignment-7-Details.md). Where it differs from an IRS document, the assignment governs ([data/policy.md](../data/policy.md)). Each rule's citation is in [data/rule_registry.json](../data/rule_registry.json).

**About the IDs.** Code and the rule registry cite `A-01`, `A-04`, `A-11`, `A-12` and `A-14`. The original assumptions document from the source repository was never imported, so those meanings are reconstructed from the citing comments and rule descriptions. Choices that nothing cites yet use `C-` ids; open questions use `Q-` ids.

## 1. Explicit assignment requirements

These are restated briefly. They are not choices.

| Requirement | Assignment | Rules / implementation |
|---|---|---|
| Never file; never give tax advice; never assert an unsourced amount; escalate the §4.4 conditions; handle only the §3.3 profile | §2 | `R-FILE-01`, `R-ADVICE-01`, `R-AMOUNT-01`, `R-HITL-01`…`06`, `R-SCOPE-01` |
| Populate the §3.1 line subset, with filing status and dependents from intake | §3.1 | Mapping rules `R-W2-01` … `R-PAY-02` |
| 1040-SR eligibility: born before 2 Jan 1961; on a joint return one spouse suffices; no income limit | §3.2(1) | `R-ELIG-01` |
| Standard deduction from the chart: $15,750 / $31,500 / $23,625 plus $2,000 or $1,600 per 12d box; the three exceptions escalate | §3.2(2) | `R-SD-01`…`03` |
| Enhanced senior deduction: $6,000 per qualifying person, 6% phase-out above $75,000 / $150,000 MAGI, separate from the additional standard deduction | §3.2(3) | `R-ESD-01`, `R-ESD-03` |
| Taxable Social Security worksheet ($25,000 / $32,000 and $34,000 / $44,000), with 6b computed before AGI | §3.2(4) | `R-SS-01`, `R-SS-02` |
| Accept only 900–999 test SSNs | §3.2 | `R-SSN-01`, `src/ssn.py` |
| Box 2b "taxable amount not determined" always escalates | §3.3 | `R-1099R-01` |
| Six distinct agents plus orchestration; the agent constraints in the §4 table | §4 | [IMPLEMENTATION_NOTES.md](IMPLEMENTATION_NOTES.md#agents) |
| Conditional routing, a parallel branch with a reducer, a bounded review cycle, and a tested loop guard | §4.1 | [IMPLEMENTATION_NOTES.md](IMPLEMENTATION_NOTES.md#orchestration) |
| At least four §4.3 accessibility areas | §4.3 | [IMPLEMENTATION_NOTES.md](IMPLEMENTATION_NOTES.md#intake-accessibility-and-dignity-43) |
| One context strategy, measured on vs off with `--no-context-strategy`, in `docs/metrics.md` | §4.5 | `src/memory.py`, `scripts/context_benchmark.py` |

## 2. Interpretations and implementation choices

| ID | Choice | Why / caveat | Cited by |
|---|---|---|---|
| A-01 | Return Assembly & Provenance is a separate, sixth functional agent | The assignment names six agents plus orchestration but lists five functional roles besides the orchestrator. This agent owns the "every number has a source" gate and the official-form output | `src/agents/return_assembly.py` |
| A-04 | The §4.5 "10 invoices" are ten distinct 2025 tax documents (`data/fixtures/bench_ten_docs`), extracted sequentially in one thread with the same model, prompt and schema in both runs | The assignment's batch scenario refers to invoices, which this domain has none of | `scripts/context_benchmark.py` |
| A-11 | "Rate schedule" for line 16 includes the Qualified Dividends and Capital Gain Tax Worksheet when line 3a is positive | Otherwise qualified dividends would be taxed as ordinary income | `R-TAX-02` |
| A-12 | Whole-dollar rounding, half-up. When several amounts feed one line, cents are kept while adding and only the total is rounded | Permitted by the Form 1040 instructions | `src/money.py`, `R-ROUND-01` |
| A-14 | Lines 4a and 5a are filled with the gross total even when fully taxable | The assignment's §3.1 table lists both lines. IRS instructions would leave 4a blank in that case | `R-IRA-01`, `R-PEN-01` |
| C-01 | Wage conflict uses **zero tolerance**: any difference asks one confirmation question, and an unresolved one escalates | Conservative project choice, not a professor-specified threshold. It replaced the inherited $1,000 / 10% allowance. The team confirmed keeping it. Clean-run fixtures whose stated wages are estimates answer the question with "The W-2 is right" (`WAGES_MATCH_W2` in `data/generate_fixtures.py`) | `R-CONFLICT-01` |
| C-02 | QCD requires age 70½ at distribution; uncertain age or timing escalates | Conservative screen | `R-IRA-02` |
| C-03 | Line 25c holds only Additional Medicare Tax withheld on an in-scope W-2 (W-2 box 6 less 1.45% of box 5, Medicare wages over $200,000); W-2G, K-1, 1042-S, 8805 and 8288-A stay $0 because their income is not in scope. Decided Q-01 | Assignment §3.1 and §3.3; Form 1040 instructions p. 39 | `R-WH-01` |
| C-04 | Schedules 1, 2 and 3 are entered as totals and recorded as direct user input | §3.3 says the "user just directly inputs values" | `R-SCHED-01` |
| C-05 | More than four dependents escalates (the form has four rows). Dependent credits (Schedule 8812) are not calculated; line 19 is direct input only | Form layout | `R-DEP-01` |
| C-06 | Married filing separately gets no enhanced senior deduction | IRS rule for the deduction | `R-ESD-02` |
| C-07 | A W-2 must be an uploaded image; typing in a W-2 is rejected. Other supported forms may be typed in | Rubric D.3 tests reading W-2 amounts from an image | `src/agents/document_extraction.py`, `src/service.py` |
| C-08 | Multi-page PDFs are rejected; single-page PDFs are converted to an image | Avoids silently reading only page 1 | `src/service.py` |
| C-09 | Orchestration is deterministic code, not a model | Explainable routing and guaranteed termination | [IMPLEMENTATION_NOTES.md](IMPLEMENTATION_NOTES.md#why-a-rule-based-orchestrator) |
| C-10 | Loop control: 3 review passes, 30 hand-offs per run, 4 repeats of one routing signature | Project choices; the assignment requires a bound but no values | `src/config.py` |
| C-11 | No in-process fallback when the MCP tool server is unavailable; the case stops with an error | Every number must come from a tool call | `src/tools/mcp_client.py` |
| C-12 | "Submitted" means submitted internally for Kushim human review | §2: never file | `src/state.py`, dashboard |
| C-13 | Reviewer identity is a self-declared name; there is no login | Prototype scope | `src/ui/dashboard.py` |
| C-14 | Only the reasons in `src/hitl.py` have reviewer actions, and there is no generic approve. Hard exclusions can only be referred out, or have a fact corrected with evidence | §2 says breaches are "the assignment" | `src/hitl.py` |
| C-15 | Native OCR is off by default and enabled only with `SILVERFILE_ENABLE_NATIVE_OCR=1`. Anthropic vision is the intended path for document images | Unexplained telemetry request (see [KNOWN_LIMITATIONS.md](KNOWN_LIMITATIONS.md#2-native-ocr-telemetry-issue-blocked-do-not-bypass)) | `src/tools/ocr_reader.py`, `src/llm.py` |
| C-16 | The audit re-derives 6a, 6b, 11b and 13b from sources with a separate closed-form implementation and compares all four exactly | The closed form rounds to cents at the same steps as the worksheet, so a correct return always matches and a $1 error is caught | `recheck_social_security_and_senior` |
| C-17 | There is no default Anthropic model; anthropic mode needs `ANTHROPIC_MODEL` explicitly | No identifier is assumed to be available to every account | `src/config.py`, `src/llm.py` |
| C-18 | Python 3.12 is the team standard | Matches Docker, CI and the reported verification runs | `.python-version`, `Dockerfile`, CI |

## 3. Unresolved questions

| ID | Question | Where it matters |
|---|---|---|
| Q-01 | **Line 25c. Decided:** include Additional Medicare Tax withheld on an in-scope W-2 (C-03). Implementation is pending: W-2 box 6 must be extracted, and a Computation MCP tool must derive the amount | `R-WH-01`, `src/agents/computation.py`, `src/agents/document_extraction.py` |
| Q-02 | Keep zero wage tolerance? **Decided:** keep it (C-01) | — |
| Q-03 | Should the audit independently recompute 6b and 13b? **Done:** C-16 | — |
| Q-04 | Which Python version? **Decided:** 3.12 (C-18) | — |
| Q-05 | **Model (open).** Which Anthropic vision + structured-output model will the demo and grading use, and whose account and key? No identifier is assumed | `.env.example`, `src/config.py` |
| Q-06 | **W-2 image reading (open).** Live vision (needs Q-05), or native OCR in an isolated environment? | Rubric D.3 |
| Q-07 | Audit rounding tolerance on the 6b/11b/13b recheck? **Decided:** no tolerance; the recheck mirrors the worksheet's per-step cent rounding and compares exactly (C-16) | — |

### Q-01 passages

- **Assignment §3.1 table:** "25a–25d | Federal income tax withheld | W-2 / 1099 forms".
- **Assignment §3.3:** "In scope: Amounts from W-2, SSA-1099, 1099-R, 1099-INT, 1099-DIV; … Schedules 1, 2 and 3 - user just directly inputs values." The out-of-scope list does not mention Forms W-2G, 8959, K-1, 1042-S, 8805 or 8288-A.
- **2025 Instructions for Form 1040 and 1040-SR, p. 39, "Line 25c—Other Forms":** "Include on line 25c any:
  - Federal income tax withheld on your Form(s) W-2G …
  - Additional Medicare Tax you had withheld. Include the amount shown on Form 8959, line 24 …
  - Federal income tax withheld that is shown on a Schedule K-1.
  - Tax withheld that is shown on Form 1042-S, Form 8805, or Form 8288-A."
- **Rule `R-WH-01`:** "Line 25c: other forms (W-2G, 8959, K-1, 1042-S) - none are in scope, so 25c is $0."

The conflict:
- W-2G, K-1, 1042-S, 8805 and 8288-A come from income outside the §3.3 list, so $0 is defensible for them.
- Additional Medicare Tax withholding is reported on an in-scope W-2: box 6 above 1.45% of box 5, for Medicare wages over $200,000. The matching tax is on Schedule 2, whose totals the user enters directly. §3.1's "W-2 / 1099 forms" source for 25a–25d could include it.
- No fixture reaches that wage level. Behavior is unchanged until the team decides.
