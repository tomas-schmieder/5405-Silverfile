# AI-use disclosure (assignment §5.3)

## Summary paragraph

AI tools produced most of this repository's code, and the team has not yet independently reviewed most of it.

- **Original generation.** The application was first generated with Claude Code in the team's earlier repository, [tomas-schmieder/ENMGT5405-Assignment-7](https://github.com/tomas-schmieder/ENMGT5405-Assignment-7), at commit `e3d2c53630c19b3295cab84e757191a79317eb12` on branch `claude/sharp-wozniak-038bl3`. That covers the agents, graph, service, MCP tax tools, UI, PDF output and the original tests.
- **Staged packages.** ChatGPT/Codex split that code into six packages, one per team member, and imported them into this repository as files, without the old Git history. While packaging, it also:
  - adapted the code (removed "classroom demo" wording, isolated a filename helper, made unreadable amounts stay unknown rather than zero, made 1099-R box 2b escalate before deduplication, reworked duplicate signatures and SSN digests, extended provenance gap and cycle checks, removed the $1,000 / 10% wage tolerance in favor of zero tolerance, made line 16 re-checks apply to qualified dividends, and rejected multi-page PDFs)
  - regenerated the fictional fixtures
  - assembled the reference-form corpus and its hash manifests
  - wrote additional regression tests and every per-package handoff document
- **Imports and commits.** Team members used Claude Code (Claude Opus 5.5 and Claude Sonnet 5.5) and Cursor to import, check, commit and merge those packages. Claude Code also ran local test checks and prepared this documentation consolidation.
- **Acceptance fixes.** Claude Code also wrote the fixes on `fix/acceptance-validation` (fixtures, test gating, audit recheck, model configuration).
- **Inside the product.** At run time, SilverFile calls Anthropic Claude models through the API: vision extraction of W-2 images, interpretation of intake replies, an advisory audit critique, and plain-language line explanations. Every dollar amount still comes from deterministic MCP tools, not from the model.
- **Human work.** Human review, testing and changes by individual members are recorded in [CONTRIBUTIONS.md](CONTRIBUTIONS.md), and most of them are still pending. Members must not describe AI-generated code as independently authored.

## Inherited source

| Item | Value |
|---|---|
| Source repository | https://github.com/tomas-schmieder/ENMGT5405-Assignment-7 |
| Source branch | `claude/sharp-wozniak-038bl3` |
| Exact source commit | `e3d2c53630c19b3295cab84e757191a79317eb12` |
| How it was generated | Claude Code |
| How it was transferred | File-based staged import, not a transfer of Git history |
| File hashes | [BASELINE.md](BASELINE.md), `docs/foundation_sources.json`, `docs/intake_sources.json` … `docs/audit_sources.json` |

## AI assistance by stage

| Stage / commit | AI tools recorded | What the AI did | Human verification recorded |
|---|---|---|---|
| Original application (source repo) | Claude Code | Generated the application code and the reducer tests | None recorded in this repository |
| Foundation, Hussain (`942002b`) | ChatGPT/Codex; Claude Code (Opus 5.5, commit trailer) | Codex selected the dependency-complete subset, packaged it, wrote its docs, and added the memory/storage tests. Claude Code committed and pushed it, and ran the local checks at Hussain's request | Pending (see CONTRIBUTIONS.md) |
| Intake, Kezia (`d1ac85d`) | ChatGPT/Codex | Assembled the package, revised user-facing wording, isolated the filename-suggestion helper, added focused tests | Reviewed and verified by Kezia on the integrated main branch. |
| Documents, Taylor (`892822d`, `7c4f336`) | ChatGPT/Codex; Claude Code (Opus 5.5) | Codex adapted the stage, wrote regression tests, regenerated fixtures, and wrote the handoff. Claude Code did the import checks, dependency install, test run, commit and merge at Taylor's request | Pending |
| Rules, Anastasia (`f8bd44f`, `14db900`, `df55c89`) | ChatGPT/Codex; Claude Code (Sonnet 5.5, commit trailers) | Codex packaged the stage, changed the wage-confirmation threshold, added reference-integrity tests and a test-only tool stub, and assembled the reference corpus | Pending |
| Computation, Anjana (`d351db3`) | ChatGPT/Codex | Adapted the computation tools and MCP interface, the line 16 consistency check and signed-AGI handling. Supplied Docker/Compose and CI configuration | Pending |
| Integration, Tomas (`aeda711`) | ChatGPT/Codex; Cursor (commit trailer) | Codex adapted the audit agent, dashboard, graph/service/model integration, tests and benchmark script, and removed assignment references from the dashboard. Cursor is recorded as co-author of this commit, which also consolidated `requirements.txt` | Pending |
| Assignment writeup, Tomas (`4411794`) | Cursor (commit trailer) | Co-authored the commit adding the assignment text | — |
| Merged-build verification (`aeda711`) | ChatGPT/Codex | Ran the core suite independently: 299 passed in 6.18 s on Python 3.12, with `tests/integration`, `tests/live` and `tests/native_ocr` excluded | Externally reported; not a team member's run |
| Acceptance fixes, Hussain (branch `fix/acceptance-validation`, uncommitted) | Claude Code (Opus 5.5) | Wrote all of these at Hussain's request:<br>• fixture wage-confirmation answers and their regeneration check<br>• `needs_ocr` marker gating and the synthetic-extraction integration tests<br>• the `recheck_social_security_and_senior` MCP tool, its audit wiring and tests<br>• no-default-model configuration<br>• Python 3.12 pin and CI command<br>• the related documentation<br>Also ran the tests (372 passed, 23 skipped, Python 3.12.14) | Pending team review |
| W-2 image reading fix, Taylor (branch `fix/ocr-w2-image-reading`) | Claude Code (Opus 5.5) | At Taylor's request:<br>• diagnosed that neither image path could run for a grader<br>• found that `onnxruntime==1.31.0` does not install on macOS 13, and chose the 1.21.1 pin<br>• verified that RapidOCR bundles its models and makes no network calls, by running the suite and `run.py eval` with networking denied<br>• turned native OCR on by default and set the default model<br>• fixed two stale image tests<br>• updated the related documentation | Pending Taylor's review |
| Documentation consolidation, Hussain (branch `chore/submission-documentation`) | Claude Code (Opus 5.5) | Consolidated the per-person handoffs into README.md, IMPLEMENTATION_NOTES.md, REQUIREMENTS_MATRIX.md, KNOWN_LIMITATIONS.md, CONTRIBUTIONS.md and this file. Wrote ASSUMPTIONS.md, STATE_CONTRACT.md and ACCEPTANCE_RESULTS.md from the code and existing docs | Pending team review |

## AI-produced material that needs particular care

- **Reference forms and citations** in `data/reference_tax_forms/`, `data/rule_registry.json` and `data/source_manifest.json` were AI-assembled, not supplied by the professor. The hash and identity checks show file identity, not that the forms are official or that the citations are interpreted correctly.
- **Fixtures and hand-worked expected results** in `data/fixtures/` and `evals/expected_results/` are AI-generated supporting material. The authoritative requirements remain [Assignment-7-Details.md](../Assignment-7-Details.md) and the professor's assignment.
- **Reported test results.** The 100, 139 and 299 passing-test counts, including the 299 run on `aeda711`, were produced by ChatGPT/Codex, except where [ACCEPTANCE_RESULTS.md](ACCEPTANCE_RESULTS.md) records a run on a member's own machine.

## Before submission

Each member should check the row for their stage, add any further AI assistance they used (tool, what it produced, what they verified or changed), and keep this paragraph accurate. The pull-request template (`.github/pull_request_template.md`) has an "AI use in this change" section for the same purpose.
