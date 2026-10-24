# Person 6 handoff

## Ownership
Review/Audit agent; employee dashboard; evaluation driver; shared graph/service/model integration; graph and upload-boundary tests; integration/live test scaffolding; benchmark script.

Original source: team's Claude-generated repository ENMGT5405-Assignment-7 at e3d2c53630c19b3295cab84e757191a79317eb12. ChatGPT/Codex adapted and tested these packages. Keep that attribution and record your own actual review and changes. Do not claim generated code was independently authored.

Prepared against remote main e7e16701609f22569140a9a34f5ec73763328ed0, which contains Persons 3 and 4. Person 5 must merge before Person 6 starts. Person 6 includes shared src/graph.py, src/service.py, src/llm.py and src/agents/orchestrator.py because integration depends on them. Hussain remains the reviewer for those foundation-owned components.

## Changes and checks
The computation verification tool now rechecks qualified-dividend line 16 instead of skipping it. It reuses the worksheet implementation, so this is a consistency check, not an independent oracle. Signed AGI is accepted in downstream deduction handling. Rules retain explicit zero-tolerance requests through the actual MCP interface. Other callers retain the original comparison tool defaults.

Person 6 removes assignment references from the employee dashboard and rejects multi-page PDFs instead of silently reading only their first page. Existing intake and Taylor's code are preserved.

Combined final core verification: 299 passed on Linux/Python 3.12.14. Includes a real stdio MCP call, tax-table comparisons, the previous stages, graph topology, and upload-boundary checks. No live Anthropic API, native OCR, browser automation, or Docker build was run. Docker is unavailable on the preparation host. CI configuration is supplied but no GitHub Actions run is claimed. Pins cover direct dependencies; a tested transitive lock still needs to be produced by the deployment owner.

## Local verification
Install requirements.txt into the existing virtual environment. Do not change versions silently. Set PYTEST_DISABLE_PLUGIN_AUTOLOAD=1, LANGSMITH_TRACING=false and LANGCHAIN_TRACING_V2=false.

    python -m pytest tests --ignore=tests/integration --ignore=tests/live --ignore=tests/person3_ocr -q

Person 5 alone will have fewer tests than the combined 299. Person 6 adds the graph and upload tests. Tests using images in tests/integration are explicitly skipped unless native OCR has been separately enabled in a network-isolated environment. Live tests additionally require SILVERFILE_RUN_LIVE_TESTS=1 and an API key. Do not enable either as part of the initial copy check.

## Outstanding acceptance work
- Select an available vision/structured-output Anthropic model in .env. No model identifier is assumed valid for your account. Keep keys out of Git.
- Verify the complete browser flow, real model extraction, all hard-stop routing/resume, stale-data handling and persistence. Core passes alone do not establish these.
- Native OCR is still blocked/unverified after an unexpected telemetry request. Do not bypass the block. Coordinate isolated execution with DevOps.
- Run Docker locally after both packages are merged. The provided image uses Python 3.12 to match core verification. Matplotlib is included in requirements.txt for benchmark charts.
- Audit verification is not a complete independent recomputation of Social Security and enhanced-senior amounts from original facts. Add that check before declaring full audit coverage.
- Review direct-input line 25c support against the assignment; the inherited computation path currently sets it to zero.
- Review imported evaluation expectations and scripted follow-ups against the stricter wage-confirmation rule. The full fixture evaluations have not been rerun.
- Produce actual on/off model-token measurements, the five-page report, contribution/specialization table, and demo recording. Do not present proxy counts or old source-repository results as current evidence.

## Actual contribution record
Name: pending. Branch: pending. Files reviewed: pending. Local tests: pending. Real changes and rationale: pending. PR/reviewer: pending. Update only with completed work.
