# Independent Review — phrase boundary forwarding

## Decision

**Classification: YELLOW. Recommendation: approve for Orchestrator integration after reviewing this report alongside the implementation evidence.** The patch changes internal phrase context supplied to solver and replanning, which can change eligible harmonic plans. It preserves the existing public REST schema and does not modify musical rules or solver transition costs.

## Scope reviewed

- `src/harmony/pipeline.py`: copying explicit boundary metadata into the preprocessed melody and using it in replanning syntax transition checks.
- `tests/test_replanning.py`: true/false forwarding checks for canonical name and existing alias.
- `backend/api.py`: `MelodyNoteItem`/`HarmonizeRequest` schema.
- `src/harmony/solver/viterbi.py`: existing canonical/alias lookup and fallback heuristic.
- `src/harmony/syntax/grammar.py`: phrase boundary's existing effect on syntax checks.

The REST input model has no `phrase_boundary` or `is_phrase_boundary` field. I agree with leaving it unchanged: the alias is supported by the solver's internal dict input, but no current API contract establishes either field for REST clients.

## Findings

- **No blocking findings.** Canonical explicit `True` and `False` values are copied without coercion; `is_phrase_boundary` is normalized to the solver's canonical `phrase_boundary` key. Missing or `None` fields are omitted so existing solver heuristics remain active.
- The main solver path and `_replan` receive the same processed melody list. Replanning syntax filtering now passes the boundary at the current target/tail note to the existing grammar API.
- No changes were found to transition costs, rule definitions, grammar tables, result formats, or public API fields.
- The regression uses a recording solver and a replanning capture stub. This directly verifies the pipeline handoff and preserves scope; it does not assert a changed musical output for a fixed chord sequence.

## Checks run independently

- `D:\aitraining\.venv\Scripts\python.exe -m pytest -q tests/test_replanning.py` — **10 passed**.
- `D:\aitraining\.venv\Scripts\ruff.exe check src/harmony/pipeline.py tests/test_replanning.py` — **passed**.

The implementation agent reports full `pytest -q` and `ruff check .` passed in the same preconfigured environment; I did not rerun the full suite independently. An initial isolated `uv run` attempt hit a Starlette TestClient dependency mismatch, so it is not evidence against the patch.

## Compatibility and unresolved questions

Python callers that supply either explicit dict key now have the intended solver behavior; inputs without a boundary preserve fallback behavior. REST callers still cannot establish explicit phrase boundaries through the current Pydantic schema. If REST support is later desired, it requires a separately scoped contract decision and tests.

No unresolved code-level issue found. This review does not grant architectural or musical-rule approval; neither appears changed here.
