# Known limitations

This document consolidates the known technical and scope limitations of the final SilverFile implementation, together with the validation completed during final integration.

## 1. Verification status

| Area | Status |
|---|---|
| Core automated suite | **Passed.** The integrated core automated suite was successfully exercised during final project validation. Historical and subsequent validation results are recorded in [ACCEPTANCE_RESULTS.md](ACCEPTANCE_RESULTS.md). |
| `tests/integration` | **Verified.** Integration tests run as part of the core command and CI, including the native-OCR image tests. Native OCR is enabled by default and can be disabled with `SILVERFILE_ENABLE_NATIVE_OCR=0`. |
| Synthetic extraction | The orchestration, review-bound, loop-guard, parallel-extraction and draft-case tests use fixture ground truth (`synthetic_documents` in `tests/conftest.py`) where appropriate. These tests validate the workflow after document reading and are complemented by native-OCR image tests. |
| Reading document images | **Verified for the supplied fixture images using native OCR.** Native OCR is enabled by default and the fixture-image workflow has been exercised successfully. The fixture set consists primarily of clean generated/scanned images; real-world phone photos, skewed images and substantially different W-2 layouts remain outside the validated image set. |
| Browser workflow | **Verified.** The integrated browser workflow was manually exercised, including the taxpayer flow, dashboard review, provenance view and human-in-the-loop review workflow. |
| Live Anthropic API | **Configured and exercised where required for final integration and measurement.** Deterministic validation, native OCR and offline paths remain available independently of the live model. |
| Model identifier | **Resolved.** `ANTHROPIC_MODEL` defaults to `claude-opus-5-5` (`DEFAULT_ANTHROPIC_MODEL` in `src/config.py`), so live mode requires `ANTHROPIC_API_KEY`. Anthropic mode without a key stops with `ModelConfigError`; the default `auto` mode can fall back to offline behavior where supported. |
| Hard-stop routing and resume | **Verified.** Hard stops and the eval case 2 human-review round trip run through the integrated workflow, including native OCR and human-review handling. The browser HITL workflow was also exercised during final integration. |
| Full fixture evaluations | **Verified.** The final fixture-evaluation workflow was exercised successfully. See [ACCEPTANCE_RESULTS.md](ACCEPTANCE_RESULTS.md) for the recorded evaluation results. |
| Docker | **Verified.** `Dockerfile` and `compose.yaml` use Python 3.12, and the final container workflow was exercised as part of submission preparation. |
| CI | `.github/workflows/tests.yml` uses Python 3.12 and runs the expanded core test command. |
| Dependency management | `requirements.txt` pins the project's direct dependencies. Deployment reproducibility additionally relies on the validated Python 3.12 environment and container configuration. |

## 2. Native OCR telemetry and platform validation

An earlier Windows run had its native-OCR test process encounter an automatic approval review after ONNX Runtime attempted a Microsoft telemetry request, even though `onnxruntime.disable_telemetry_events()` was called before OCR initialization.

- **Network-isolated verification.** On macOS, with outbound IP and DNS access denied, the full suite was successfully exercised with native OCR enabled, including the native-OCR and `needs_ocr` tests. The fixture evaluation also completed successfully. The OCR models ship inside `rapidocr-onnxruntime`, and the package contains no document-model download step, so the native reader does not require network access for its bundled models.

- **Telemetry.** ONNX Runtime's telemetry mechanism is Windows-specific through ETW and is not present in the same form on macOS, Linux or the Docker image. The application still calls `disable_telemetry_events()` before initializing OCR.

- **Pin.** `onnxruntime` is pinned to version 1.21.1 for compatibility with the supported Python and operating-system environments.

- **Default.** Native OCR is enabled by default. `SILVERFILE_ENABLE_NATIVE_OCR=0` disables it.

- **Windows validation.** The project was also exercised on Windows with Python 3.12 and OCR enabled. See [ACCEPTANCE_RESULTS.md](ACCEPTANCE_RESULTS.md) for the recorded validation results.

## 3. Calculation and audit limitations

- **Audit recomputation of 6b and 13b.** Resolved.

  - The audit calls the MCP tool `recheck_social_security_and_senior`, which independently re-derives 6a, 6b, 11b and 13b from published source-document amounts, confirmed direct inputs and dates of birth. It does not use the proposed return lines as its source and fails the audit when the recomputed values disagree.

  - The recheck uses a separate closed-form worksheet implementation rather than calling the production 6b/13b functions. It remains part of the same codebase and therefore should not be interpreted as an independent external tax oracle.

  - The recheck rounds to cents at the same worksheet stages as production. A discrepancy in the checked values therefore fails the audit. See [ASSUMPTIONS.md](ASSUMPTIONS.md) Q-07.

  - Regression coverage includes `tests/audit/test_audit_recheck.py` and `tests/integration/test_orchestration_synthetic.py`.

- **Audit scope.** Lines other than the source-recomputed 6a, 6b, 11b, 13b and 25c rely on the applicable internal-consistency checks in `verify_return`. Source facts are checked against the system's published `source_facts`; this is not equivalent to an independent external review of the original image.

- **Line 16 re-check.** The qualified-dividend line 16 check is an internal consistency check and uses the project's worksheet implementation rather than an external tax-calculation oracle.

- **Line 25c Additional Medicare withholding.** Resolved. The MCP tool computes each W-2's applicable excess Medicare withholding from box 5 and box 6 according to the implemented rule. Computation aggregates results with source provenance, and audit rechecks the value from the published W-2 facts. The high-wage fixture is included in the evaluation catalogue with expected results. Other unsupported withholding forms remain outside the project's scope.

- **Zero-tolerance wage comparison.**

  - Any difference between taxpayer-stated wages and a W-2 prompts a confirmation question. An unresolved conflict escalates for human review.

  - Intake does not attempt to quantify how approximate an estimate was, so additional clarification may occasionally be requested.

  - The wage-conflict clarification wording was reviewed across the Intake and Rules workstreams and retained as the agreed system behavior.

- **Evaluation-case wage conflicts.** The applicable evaluation cases include the required wage-conflict follow-up responses, while the designated HITL case preserves the taxpayer/document disagreement and reviewer action. The integrated evaluation workflow exercises this behavior.

- **Conservative QCD age screen.** Uncertain age or timing cases are intentionally routed to a person rather than automatically resolved.

- **Test-only tool stub.** Decimal summation and comparison in `tests/rules/conftest.py` support testing and do not replace the production MCP tools.

## 4. Document extraction, provenance and output

- Native OCR successfully reads the supplied fixture images, but the fixtures are predominantly clean generated/scanned documents. Accuracy on phone photos, significant skew, unusual image degradation and substantially different W-2 layouts is not guaranteed. The reader is designed to report unreadable boxes rather than guess.

- Uploads must be provided in a supported normalized image format. Multi-page PDF processing with page selection, splitting and page-level provenance is not implemented.

- The service contract uses `uploaded_at` for manual-entry provenance timestamps; integrations must preserve this field.

- The full-SSN digest is designed as an equality token for fictional test data. It is not intended as production anonymization for real SSNs. The project's redaction controls should not be interpreted as a complete production-grade PII security architecture.

- PDF checks validate fields, readback and rendered text. They do not guarantee perfect visual layout across every possible input, such as unusually long names or other visual edge cases.

- Template hashes and reference integrity must be maintained when changing tax-form references or dependency artifacts.

## 5. Rules and references

- References in `data/reference_tax_forms/` were assembled for the project and are tracked through `data/source_manifest.json`. The manifest establishes local file identity and page existence; it should not be interpreted as independent authentication of every source download or every tax-rule interpretation.

- A separate reference packet exists under `tax-forms/`. Where references are not directly wired into runtime behavior, they serve as supporting project materials rather than executable rule sources.

- Historical SSA GIFs are used as layout references and are not treated as 2025 tax-rule authorities.

- The rules layer is intentionally limited to the supported 2025 Form 1040-SR subset defined by the project. Unsupported or ambiguous tax situations are routed to human review or referred out of scope rather than guessed.

## 6. Documentation and implementation notes

- **Documents referenced by code.** [ASSUMPTIONS.md](ASSUMPTIONS.md), [STATE_CONTRACT.md](STATE_CONTRACT.md) and [ACCEPTANCE_RESULTS.md](ACCEPTANCE_RESULTS.md) provide supporting documentation for the corresponding runtime and test references.

- **Orchestration diagram.** The README Mermaid diagram is the primary architecture/orchestration diagram and corresponds to the integrated graph structure.

- **Context-window benchmark.** The §4.5 benchmark artifacts document the measured comparison between the full-context and selective-recall strategies. See `docs/metrics.md` and the associated benchmark artifacts for the final measured results.

- **Intake wording.** The live Intake system prompt was updated to remove the previous "classroom prototype" wording. Remaining occurrences of classroom-oriented language, where present in internal comments or defensive validation messages, do not define the live Intake prompt or the system's user-facing purpose.

- **Source manifests.** `docs/*_sources.json` are historical import/source records. They may contain import-time hashes or references to earlier file states and should be interpreted as provenance records rather than current-content hashes.

- **Python version.** The project standard is Python 3.12, including the Docker `python:3.12-slim` base image, CI configuration and `.python-version`.

- **Dashboard identity.** The project dashboard does not implement a production authentication system. Reviewer names are self-declared. This is appropriate for the project's prototype scope but would require stronger identity and access controls in a production deployment.

## 7. Final submission artifacts

| Deliverable | Status |
|---|---|
| Context-window benchmark (§4.5) | **Completed.** Final benchmark artifacts and measured results are provided in `docs/metrics.md` and the associated trace/chart outputs. |
| Five-page report (bonus) | **Completed for final submission.** The report documents the system design, agents, architecture, failure modes, scope and team responsibilities. |
| Demo video, 5–10 minutes | **Completed for final submission.** The demonstration covers the integrated SilverFile workflow and key system controls. |
| Specialization table (assignment §1.1) | **Completed.** Team specializations are recorded in [CONTRIBUTIONS.md](CONTRIBUTIONS.md). |
| Member contribution records | **Completed.** Team member responsibilities and contribution evidence are recorded in [CONTRIBUTIONS.md](CONTRIBUTIONS.md). |
| Orchestration diagram | **Completed.** The README contains the Mermaid orchestration diagram corresponding to the integrated graph. |
| Evaluation and benchmark traces | **Completed as part of final evaluation and benchmark execution.** |
| Docker acceptance (bonus) | **Completed for final submission.** The supplied Docker configuration provides the containerized project workflow. |

## 8. Scope boundary

SilverFile is a project implementation for preparing a **draft 2025 Form 1040-SR for human review**. It does not file tax returns, replace a qualified tax professional, or provide individualized tax-planning advice.

The system deliberately escalates or refers cases when required information is ambiguous, conflicting, unsupported or outside the implemented scope. Its guardrails, provenance, deterministic calculations, audit checks and human-in-the-loop workflow are intended to make those boundaries visible rather than conceal uncertainty.
