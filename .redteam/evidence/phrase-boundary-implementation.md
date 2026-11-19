# Implementation Report — explicit phrase boundary forwarding

## Classification and scope

**YELLOW.** This internal pipeline change can alter which syntax transitions are considered during harmonization, so independent review was required. Work was done on `codex/phrase-boundary-forwarding`, based on `b9e8796529fe21e7675fc5d3826a3499c0331e00`, in the separate worktree `D:\aitraining-phrase-boundary`. No integration was performed.

The `Harmonizer.harmonize` preprocessing path now carries an explicit `phrase_boundary` unchanged, or maps the existing solver-supported `is_phrase_boundary` input alias to the canonical field. Absent and `None` values remain omitted, preserving solver fallback behavior. Replanning syntax-transition checks now receive the boundary at the relevant note, and solver calls in replanning already use the same processed melody.

The REST Pydantic `MelodyNoteItem` schema declares neither field. The public REST contract was left unchanged because there is no existing contract basis to add them. Python callers can supply the dict keys.

## Changed files

- `src/harmony/pipeline.py` — preserve explicit boundary metadata and pass it into replanning syntax checks.
- `tests/test_replanning.py` — regression coverage for `True` and `False`, canonical field and supported alias, through the pipeline's main solver handoff and replanning handoff.
- `.redteam/evidence/phrase-boundary-implementation.md` — this report.
- `.redteam/evidence/phrase-boundary-review.md` — separate independent reviewer report.

## Contract and compatibility impact

No public API schema, result format, phrase heuristic, transition cost, solver rule, grammar table, or normative musical documentation changed. Python dict inputs with an explicit boundary now reach the solver and replanning with the requested bool value. Inputs without a boundary retain the existing heuristic. REST callers still cannot send explicit phrase boundaries under the current schema.

## Verification performed

Environment used: `D:\aitraining\.venv` from the original checkout, with commands run from the isolated worktree.

- `D:\aitraining\.venv\Scripts\python.exe -m pytest -q tests/test_replanning.py` — **10 passed**.
- `D:\aitraining\.venv\Scripts\python.exe -m pytest -q` — **passed; all collected tests reached 100%**. Output contained the existing Starlette TestClient deprecation warning. (The quiet configuration did not print a numeric summary.)
- `D:\aitraining\.venv\Scripts\ruff.exe check .` — **passed** (`All checks passed!`).
- `git diff --check` — **passed**.

An initial attempt to run the full suite in a fresh `uv` environment failed during collection because its latest Starlette TestClient expected the `httpx2` package. The full suite then passed in the repository's preconfigured environment; the independent reviewer also reran the focused test and Ruff checks there.

## Evidence paths

- Implementation diff and worktree: `D:\aitraining-phrase-boundary` (branch `codex/phrase-boundary-forwarding`).
- Independent review: `.redteam/evidence/phrase-boundary-review.md`.
- Repository test strategy: `docs/development/TESTING_STRATEGY.md` in the source checkout.

## Independent review

The independent Reviewer found **no blocking findings** and recommended approval for Orchestrator integration. Reviewer report is separate at `.redteam/evidence/phrase-boundary-review.md`. The Reviewer independently ran the focused `tests/test_replanning.py` (10 passed) and Ruff on changed source/test files (passed), and confirmed that the REST schema has no phrase-boundary fields.

## Unresolved questions

No code-level issue remains from this scope. REST clients still lack an explicit boundary field; adding one would require a separate API contract decision. Integration and final integration gates remain for the Orchestrator.
