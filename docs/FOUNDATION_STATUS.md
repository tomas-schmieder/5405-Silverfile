# Foundation status

## Included

| Area | Files | Responsibility |
|---|---|---|
| State and reducers | src/state.py | Case schema, merge behavior, lifecycle labels |
| Contracts | src/contracts.py | Validated agent/model response structures |
| Configuration/runtime envelope | src/config.py, src/agents/base.py | Settings and shared dependency interface |
| Memory | src/memory.py | Context construction and resume summaries |
| Metadata persistence | src/store.py | SQLite case-list records |
| Masking dependency | src/ssn.py | Fictional-SSN validation and masking used by memory |
| Tests | tests/unit/test_merge_order.py, tests/unit/test_foundation_memory_store.py | Reducer ordering/conflicts, context preservation, masking, storage persistence |

The store is a metadata index. Durable LangGraph checkpoints are not connected at this stage. State fields and response contracts include planned components that are not implemented in this package.

## Deferred

Person 1 will add src/graph.py, src/agents/orchestrator.py, src/service.py, src/llm.py, graph tests, and the actual token benchmark when their dependencies are present. Persons 2–6 will supply their assigned agents and supporting modules. The reference forms and fixtures are not needed for these foundation checks.

The imported config retains the source's configurable model default. This package makes no model requests and does not certify model access or live compatibility.

## Verification

Package preparer verification on October 24, 2026: 10 tests passed on Linux / Python 3.12.14 using pytest 9.1.1, with third-party pytest plugin autoload disabled. Imported-file hashes matched the cited source commit; all included Python files parsed; configuration, contracts, and runtime envelope imported successfully. No model, OCR, or external-service calls were made. Python 3.11 remains the team target; a run on the member's own machine is still required.

## Person 1 review record — complete after doing the work

- Date and machine:
- Checks run and results:
- Code reviewed and understood:
- Changes made:
- Commit / pull request:
- Remaining issues:

Do not fill these entries with planned or AI-only actions as if they were completed human work.
