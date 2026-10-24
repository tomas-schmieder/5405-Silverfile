# Person 4: Eligibility and Rules

## Ownership

- src/agents/eligibility_rules.py: screening and final rules agent.
- data/rule_registry.json: decision IDs, scope, citations, and inputs.
- data/policy.md: internal course-scope policy, not taxpayer-facing copy.
- data/reference_tax_forms/: seven additional PDFs and three historical SSA examples. Taylor's six existing templates are not replaced.
- scripts/build_source_manifest.py and data/source_manifest.json: reference hashes and identity checks.
- tests/person4/: decision table and reference-integrity checks, with an isolated test-only tool stub.
- requirements-person4.txt: includes the previous stage's requirements, no new dependencies.

## Source and attribution

Imported from the team's Claude-generated source repository, commit e3d2c53630c19b3295cab84e757191a79317eb12. ChatGPT/Codex packaged this stage, changed the wage-confirmation threshold, and added reference-integrity tests and a scoped tool stub. Person 4 must document their own actual review, changes, and test results. Importing this package alone is not independent authorship.

The remote main visible during preparation was d1ac85d, without Taylor's merge. Verification used that baseline plus Taylor's delivered package, then these additions. Confirm the actual merged baseline locally. No remote writes were made.

## Behavior

The agent screens known intake facts, then checks documents and conflicts at final eligibility. It produces cited decisions, intake follow-ups, or human escalation requests. It never calculates tax. Wage aggregation and comparison go through the injected tool interface.

The former $1,000/10-percent discrepancy allowance has been removed from the agent call. It explicitly passes abs_tolerance='0' and rel_tolerance='0' to compare_amounts. Any difference asks for confirmation; an unresolved difference escalates. This is a conservative engineering choice, not a professor-specified numerical threshold. The existing intake parser does not preserve how approximate an estimate was, so this may ask extra questions.

The existing conservative QCD age screen is retained: uncertain age/timing cases go to a person rather than being treated as eligible automatically. Review this and all other assumptions against the assignment before submission.

## Verification

139 core tests passed on Linux/Python 3.12.14: 39 Person 4 tests plus the prior 100. The native OCR tests were excluded and remain separately unverified. No Anthropic API or real MCP server was used.

Run with pytest plugin autoload and tracing disabled:

    python -m pytest tests/person4 tests/person3 tests/person2 tests/unit/test_merge_order.py tests/unit/test_foundation_memory_store.py -q

The tests/person4/conftest.py tool is a test-only contract stub. Its Decimal summation and comparison do not substitute for Person 5's production MCP tools. Person 5 must accept both explicit tolerance arguments and exercise the real tool transport. Full application, live-model screening, and end-to-end human-review resume are still integration work.

The source-manifest generator inspected all 16 references with zero failed PDF identity checks. Hashes and cited page ranges also pass. This establishes local file identity and page existence, not official download authentication or correctness of every citation's interpretation. References were AI-assembled, not supplied by the professor. Historical SSA GIFs are layout references only, not 2025 tax-rule authorities. No new tax guidance is asserted by this packaging step.

## Person 4 review record

Name: pending.
Branch: pending (suggested feat/Person4-eligibility).
Actual merged baseline: pending.
Files reviewed and behavior explained: pending.
Local test command/result: pending.
Real changes made and their evidence: pending.
PR and reviewer: pending.

Keep these entries pending until completed. Do not invent fixes or rewrite attribution. The assignment specialization table is separate from this file ownership assignment.
