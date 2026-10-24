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
| C-01 | Wage conflict uses **zero tolerance**: any difference asks one confirmation question, and an unresolved one escalates | Conservative project choice, not a professor-specified threshold. It replaced the inherited $1,000 / 10% allowance. See Q-02 | `R-CONFLICT-01` |
| C-02 | QCD requires age 70½ at distribution; uncertain age or timing escalates | Conservative screen | `R-IRA-02` |
| C-03 | Line 25c is $0, because none of its source forms (W-2G, 8959, K-1, 1042-S) are in scope. See Q-01 | Derived from scope | `R-WH-01` |
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
| C-15 | Native OCR is off by default and enabled only with `SILVERFILE_ENABLE_NATIVE_OCR=1` | Unexplained telemetry request (see [KNOWN_LIMITATIONS.md](KNOWN_LIMITATIONS.md#2-native-ocr-telemetry-issue-blocked-do-not-bypass)) | `src/tools/ocr_reader.py` |

## 3. Unresolved questions

| ID | Question | Where it matters |
|---|---|---|
| Q-01 | Should line 25c accept a direct input instead of always being $0? | `R-WH-01`, `src/agents/computation.py` |
| Q-02 | Keep zero wage tolerance, or restore a tolerance? Under zero tolerance, eval case 1 and other draft fixtures may need a scripted confirmation answer | [KNOWN_LIMITATIONS.md](KNOWN_LIMITATIONS.md#3-calculation-and-audit-limitations) |
| Q-03 | Should the audit independently recompute 6b and 13b from original facts? | `src/agents/review_audit.py` |
| Q-04 | Which Python version is the team target: 3.11 (foundation note) or 3.12 (Docker, CI, the reported core run)? | README, Dockerfile, CI |
| Q-05 | Which Anthropic model should the demo and grading use? No identifier is assumed valid for every account | `.env.example`, `src/config.py` |
| Q-06 | How will W-2 image reading be demonstrated: live vision, or native OCR in an isolated environment? | Rubric D.3 |
