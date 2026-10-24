# Person 4 package

Target repository: https://github.com/tomas-schmieder/5405-Silverfile
Suggested branch: feat/Person4-eligibility (replace Person4 with your name if desired).

1. Read repository instructions. Check git status and preserve all existing work.
2. On a clean working tree, fetch origin, switch to main, and pull --ff-only.
3. Confirm Taylor's files are on main: src/agents/document_extraction.py, src/agents/return_assembly.py, requirements-person3.txt, and tests/person3/. They were not yet visible on remote main during packaging. If missing, stop and resolve the merge location first.
4. Create and switch to your feature branch from updated main.
5. Extract this ZIP outside the repository. Compare repository_files/ with the repository. All packaged files should be additions. Stop on any existing-file overlap; do not overwrite another member's work.
6. Copy the CONTENTS of repository_files/ to the repository root, merging folders. Do not copy the outer directory or START_HERE.md.
7. STOP before committing or pushing. Share Source Control results for review.

For the later verification step, install requirements-person4.txt in the existing virtual environment only. Use .venv/Scripts/python.exe on Windows or .venv/bin/python on macOS/Linux. Then set PYTEST_DISABLE_PLUGIN_AUTOLOAD=1, LANGSMITH_TRACING=false and LANGCHAIN_TRACING_V2=false with your shell's syntax and run:

    <venv-python> -m pytest tests/person4 tests/person3 tests/person2 tests/unit/test_merge_order.py tests/unit/test_foundation_memory_store.py -q

Expected package result: 139 passed. Do not enable native OCR or install optional OCR dependencies for this check. Report dependency failures rather than changing pins automatically.

Read docs/PERSON4_RULES.md for ownership, source attribution, assumptions and integration limits. The complete app is not ready to launch from this stage alone.
