# Document extraction, provenance, and return assembly

Implementation owner: Taylor (Person 3).

## Scope and attribution

This stage builds on new-repository commit `d1ac85d2143ff9e9bd7a74aea3165ae02818b377`, which contains the foundation and intake/UI work. It preserves that work and adds two functional agents and their support files.

Original implementation: https://github.com/tomas-schmieder/ENMGT5405-Assignment-7, commit `e3d2c53630c19b3295cab84e757191a79317eb12`. Original implementation was generated with Claude. ChatGPT/Codex adapted this stage, prepared the additional regression tests, regenerated fictional fixtures, and assembled this handoff. These are baseline facts, not a claim that Taylor has already reviewed or modified it. Taylor's actual work is recorded separately in TAYLOR_REVIEW.md.

Source hashes, package hashes, and the expected prior hash of the single replacement file are recorded in `person3_sources.json`. The authoritative instructions remain `Assignment-7-Details.md` and the original professor assignment; AI-generated fixtures and documentation are supporting materials.

## File ownership

| Area | Paths |
| --- | --- |
| Document Extraction agent and aggregation | `src/agents/document_extraction.py` |
| Return Assembly agent | `src/agents/return_assembly.py` |
| OCR and model-image payload helper | `src/tools/ocr_reader.py`, `src/tools/document_input.py`, `src/tools/__init__.py` |
| Shared provenance model | `src/provenance.py` (the only replacement of an existing file) |
| Reviewer provenance view | `src/ui/provenance_view.py` |
| PDF fields, filling, verification, and previews | `src/output/` |
| Fictional document generation | `data/generate_fixtures.py`, `data/fixtures/`, `demo/*.png` |
| Six blank document/output templates needed here | `data/reference_tax_forms/forms/` |
| Core dependencies and tests | `requirements-person3.txt`, `tests/person3/` |
| Optional native OCR dependencies and checks | `requirements-person3-ocr.txt`, `tests/person3_ocr/` |
| Handoff and actual review record | `docs/TAYLOR_DOCUMENTS.md`, `docs/TAYLOR_REVIEW.md`, `docs/person3_sources.json` |

`src/ssn.py` already arrived with the foundation; this stage uses it without replacing it. Future changes to it should be reviewed with Hussain. `src/money.py` already arrived with intake and remains unchanged. Do not overwrite any teammate's completed changes with the original repository copies.

## Behavior and changes

- The extraction agent uses an injected structured model client, a manual-entry path for supported non-W-2 forms, or an explicitly enabled local OCR backend. W-2 manual entry is rejected. The agent transcribes and validates; it does not calculate tax.
- An explicitly unreadable amount, even in an optional box, remains unknown and causes a follow-up. It is not converted to zero. Explicit blanks retain the original documented zero convention for optional boxes.
- An unknown/unreadable form is rejected rather than accepted under the user's selected label. A positively identified supported form can be reclassified.
- Box 2b on a 1099-R triggers an escalation before duplicate detection, including when one of the conflicting parallel readings carries the flag. This complements, but does not replace, the later eligibility agent's checks.
- Duplicate signatures now include year, ownership, flags, and distribution code. Different distribution codes or IRA flags cannot silently disappear as duplicates.
- Full fictional-number equality uses a digest instead of retaining a second clear-text copy in extraction records. Masked-only forms with ambiguous spouse matching require follow-up. The digest is only an equality token for fictional data, not anonymization for real SSNs.
- Non-test SSNs reject the document and invoke the existing uploaded-file deletion behavior. Free-form model notes are not persisted; payer/name text is redacted; exception text is not copied into extraction records. These checks are not a claim of production PII security or a pre-model upload privacy filter.
- Manually entered document amounts keep source, submitter role, submission timestamp when supplied, and extraction timestamp. The current service contract uses `uploaded_at`; integration must preserve it.
- Provenance validation now checks populated extra lines as well as the required lines, follows transitive references, and detects cycles.
- Assembly requires a current passed audit for the same calculation and facts version. It blocks stale lines and broken lineage. It creates a draft PDF, page previews, and a JSON audit record without performing tax arithmetic.
- PDF checks compare field values, selected checkboxes, the canonical AcroForm field data, and text within the field bounds. Unknown requested text fields raise an error. Checks are accurately described as field/readback and rendered-text checks, not an automatic guarantee of layout quality.
- Draft banners retain fictional-data, not-filed, and human-review labels. Classroom/demo language was removed from these product messages and newly generated fixture banners.

## Fixtures

There are 19 scenario definitions and 29 generated document images, plus four convenience copies under `demo/`. The input types cover W-2, 1099-INT, 1099-DIV, 1099-R, and SSA-1099-style statements. Scenarios include the ten-document benchmark inputs and explicit escalation cases. A negative security fixture deliberately contains a made-up non-900 number to test rejection; it must never be used as an accepted case.

Six existing blank template PDFs are imported unchanged from the source repository: W-2, 1099-R, 1099-INT, 1099-DIV, 1040-SR, and Schedule 1-A. SSA examples are generated statements, not an official blank SSA-issued form. No new expected tax totals are asserted here. Tax-rule/source verification and independent numeric oracles belong to the rules, computation, and evaluation stages.

Fixtures can be regenerated with `python data/generate_fixtures.py` after installing the core dependencies. Run that only when intentionally updating the fixtures, because it rewrites the fixture directories and demo images.

## Verified here

Applied this package over an archive of the actual merged baseline, not over an imagined directory layout.

Linux, Python 3.12.14, pytest 9.1.1. Command:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 LANGSMITH_TRACING=false LANGCHAIN_TRACING_V2=false .venv/bin/python -m pytest tests/person3 tests/person2 tests/unit/test_merge_order.py tests/unit/test_foundation_memory_store.py -q
```

The command used the existing verification environment's equivalent Python path. Result: **100 passed, 0 failed, 0 skipped**. This is 46 new core tests plus the 54 foundation/intake tests. Native OCR was not included in that result.

Coverage includes injected model-payload handling, manual-entry validation, low-confidence layout handling with controlled tokens, box 2b before deduplication/conflicts, fictional identity matching, provenance gaps/cycles, stale-audit blocking, PDF field readback, all five filing statuses, tampered-checkbox detection, appended Schedule 1-A, draft previews, and JSON audit export. No Anthropic API was called. The core tests do not prove real-model accuracy or native OCR accuracy.

Rendered all six pages of a synthetic draft with Schedule 1-A for visual review and inspected representative generated W-2, SSA-style, 1099-R, and 1099-DIV images. This validates those samples' appearance, not every possible long name, scan, or future form layout. The synthetic PDF test values are writer fixtures, not tax calculation oracles.

## Native OCR remains unverified

Automatic approval review blocked the native OCR test process after it attempted a Microsoft telemetry request with an unknown payload, despite calling `onnxruntime.disable_telemetry_events()` before initializing OCR. No successful native OCR result is claimed for this package.

The native backend is now disabled unless `SILVERFILE_ENABLE_NATIVE_OCR=1`. Tests in `tests/person3_ocr/` are skipped unless that same variable is set. The six optional tests collect successfully; they have not passed here. The three layout tests use controlled tokens and are separate from native-engine verification.

Do not enable this backend in the current environment merely to bypass the block. Coordinate with the DevOps owner to install the optional dependencies in a disposable environment and establish actual network isolation (for example, a prepared container run with networking disabled) before enabling and testing it. Installation needs network access beforehand; the OCR test execution should not. Resolve native-wheel compatibility separately, using the team Python target rather than silently replacing pins. Live Anthropic vision also remains unverified and requires the later model-client integration.

## Integration work still required

1. Hussain adds the shared model client, service, graph, orchestrator, and persistence integration. `transcribe` accepts the existing structured-client interface; `src/tools/document_input.py` avoids importing a missing future `src/llm.py` merely to encode an image. A mocked payload test passes, but that is not a live API test.
2. The rules owner supplies `src/agents/eligibility_rules.py` and the verified rule registry. The provenance view loads the registry only when displaying calculation details. Do not call that part of the view before rules are installed.
3. The computation owner supplies MCP-backed calculation results and line provenance. The audit owner must produce `review.status == "passed"` and `review.passed_for == {"facts_version": current_version, "calc": current_calc_id}` before assembly.
4. The dashboard and full application tests arrive later. Do not label the full browser workflow complete based on these component tests.
5. Uploads reaching extraction must be normalized image bytes. The original service converts only the first PDF page; the integrated service must explicitly reject multiple-page input or implement page selection/splitting with accurate page provenance. This package does not silently claim that issue is fixed.
6. PDF/long-name visual edge cases, real Anthropic responses, native OCR accuracy, full hard-stop routing/resume, and merged end-to-end behavior still need integration checks. No live token benchmark results are supplied.
7. Rules/DevOps owners should preserve these six template PDFs and reconcile their hashes when adding remaining references and final dependency locks.

The six assignment specializations (memory, inter-agent communication, task division, DevOps, guardrails, security) are separate from code ownership. The team must retain its actual specialization table; this file does not silently assign Taylor a grading specialization.
