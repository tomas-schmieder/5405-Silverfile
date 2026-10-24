# SilverFile

SilverFile is being assembled in stages to prepare draft 2025 Form 1040-SR returns with source tracking and human review.

## Current stage: shared foundation

This version contains shared state, concurrent-update reducers, typed agent contracts, configuration, memory/context helpers, the case metadata store, and focused tests. It is not yet a runnable tax application.

The agent implementations, LangGraph integration, model client, MCP tools, browser interface, tax forms, and Docker setup will be added in subsequent contributions. No tax return is produced by this stage.

## Foundation checks

Use Python 3.11 as the team's target version. Create and activate a virtual environment, then run:

```bash
python -m pip install -r requirements-foundation.txt
python -m pytest tests/unit/test_merge_order.py tests/unit/test_foundation_memory_store.py -q
```

These checks need no API key, OCR, external service, or tax documents. They do not establish that the complete application works.

## Ownership and attribution

Person 1 owns this foundation and the later orchestration/memory integration. The SSN helper is included as a dependency of memory masking; Person 3 remains its security owner. Person 5 will integrate the full application dependency configuration.

See [docs/BASELINE.md](docs/BASELINE.md) for the original source and AI attribution and [docs/FOUNDATION_STATUS.md](docs/FOUNDATION_STATUS.md) for scope and verification status.
