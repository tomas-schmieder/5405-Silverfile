# Person 2: intake and human-review interaction

## Scope and source

This package extends the foundation on new-repository commit 942002b40faba624180885d2210456dc46f272cd.
Original application source: https://github.com/tomas-schmieder/ENMGT5405-Assignment-7
Original commit: e3d2c53630c19b3295cab84e757191a79317eb12

The inherited code was generated with Claude Code. ChatGPT/Codex assembled this package, revised the wording, isolated the filename-suggestion helper, and added focused checks. This is not a claim that a team member has already reviewed or tested it. The member must record their actual work below.

## Files and ownership

- Person 2: src/agents/intake.py, intake_script.py, human_review.py; src/hitl.py.
- Person 2: src/ui/taxpayer.py, components.py, upload_helpers.py, __init__.py; src/ui_text.py; streamlit_app.py; .streamlit/config.toml.
- Person 2: tests/person2/; this document and person2_sources.json. Dependencies are listed in requirements.txt.
- Shared dependencies imported unchanged: src/money.py (Person 5 owns future numerical changes), src/provenance.py (Person 3 owns future provenance changes).
- No existing Person 1 file is replaced. The root README is not replaced.

Later packages must retain these changes rather than overwrite them with old copies. A filename suggestion is only a UI default; it is never evidence of document identity.

## Wording improvements

The taxpayer flow no longer describes itself as a classroom demo. Fictional-only identifiers and no-filing/no-advice notices remain. Submission messages describe the internal review queue without promising contact. Pending-review wording says waiting, rather than asserting a volunteer is already looking. Technical model/API/MCP diagnostics appear only in the employee view. The general validation helper src/ssn.py remains owned by Person 3; intake translates its old classroom wording into the product's fictional-SSN instruction.

Other agents' messages, employee-dashboard grading references, and PDF labels are outside this package and still need their owners' cleanup.

## Dependencies and current limitations

The intake handlers and human-review node can be tested with the foundation and this package. The browser application CANNOT run yet: src/service.py, the full graph and agents, src/ui/dashboard.py, and src/ui/provenance_view.py are supplied later. No fake service or substitute tax engine has been added.

The interrupt tests use real LangGraph interrupts with an in-memory checkpointer. They do not establish SQLite restart persistence, full graph routing, live-model behavior, document extraction, or browser accessibility.

The wage-conflict tolerance defect belongs to the Rules/Computation collaboration. This package does not claim to fix it. Person 2 should review the eventual clarification wording with Person 4.

## Tests

From the repository root, with a virtual environment active:

```bash
python -m pip install -r requirements.txt
python -m pytest tests/person2 tests/unit/test_merge_order.py tests/unit/test_foundation_memory_store.py -q
```

No API key, OCR, document templates, or MCP server is needed. Disable third-party pytest plugin autoload for isolated checks if the environment has unrelated plugins. Do not run scripts that start live services.

## Member contribution record — fill after doing the work

- Member:
- Branch:
- Code personally reviewed:
- Improvements made:
- Test command / machine / actual result:
- Remaining issues:
- Commit and pull request:

The package contains AI-assisted changes. Importing it is not evidence of independently authoring all its files. Keep accurate attribution and record meaningful review, testing, and subsequent improvements.

## Package preparer verification

October 24, 2026: 54 tests passed (44 Person 2 checks plus 10 foundation checks) on Linux / Python 3.12.14, pytest 9.1.1. Third-party pytest plugin autoload and LangSmith tracing were disabled. Tests used the actual remote foundation at commit 942002b plus this additive package. All included Python files parsed. No foundation files were overwritten. No API, OCR, browser, or full-application run is claimed. The team target remains Python 3.11; the member must run and record checks on their own machine.
