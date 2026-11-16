# KNOWN_ISSUES.md — Brigade Harmony Engine

**Дата актуализации:** 2026-11-16  
**HEAD:** `fe8f94285c48385ec6ff93cb3567652e44066f71`  
**Live gates:** 901 pytest passed, 0 failed/skipped; ruff passed; frontend build passed.

Этот документ содержит текущие открытые дефекты, ограничения и долг. Закрытые волны перенесены в [.redteam/HANDOFF.md](.redteam/HANDOFF.md) и [TASK_LOG.md](TASK_LOG.md).

---

## KI-001. 64-нотные мелодии не проходят в текущем performance budget

**Severity:** Major / architecture debt  
**Status:** OPEN  
**Evidence:** HANDOFF §8; AUDIT M5.  
**Impact:** Длинные мелодии могут возвращать `success=False` или достигать timeout 4s.  
**Verification:** `python scripts/benchmark_harmonize.py`, pytest performance tests.  
**Constraint:** Performance wave authorized separately.

---

## KI-002. Низкая выживаемость гармонических планов

**Severity:** Major / architecture debt  
**Status:** OPEN  
**Evidence:** `scripts/grammar_metrics.py`: survival ~21.3%, диапазон 0–45% по корпусу.  
**Impact:** Основной путь опирается на bounded replanning.  
**Root hypothesis:** План-генератор слишком узко генерирует допустимые последовательности.  
**Planned direction:** K-best / beam diversification / CP-SAT hybrid — только после отдельного architectural approval.

---

## KI-003. Хроматический словарь и corpus failures

**Severity:** Major  
**Status:** OPEN  
**Evidence:** `REMEDIATION_PLAN.md:58` и `AUDIT_2026-11-13.md:76`: chromatic fuzz 60% failures; HANDOFF §6 подтверждает частичную поддержку N/bVI/altered chords.  
**Impact:** Некоторые хроматические аккорды и модуляции не разрешаются strict solver.  
**Not a bug:** Строгий отказ для неразрешимых short cases является осознанным, если diagnostics объясняют причину.

---

## KI-004. MIDI round-trip off-by-one

**Severity:** Major  
**Status:** OPEN  
**Evidence:** HANDOFF §8: parse MIDI 6 vs 7 notes.  
**Impact:** Импорт/экспорт длинных MIDI может терять последнюю ноту.  
**Verification path:** `backend/importers.py`, round-trip tests, `scripts/test_e2e_api.py`.  
**Note:** Не фиксировать opportunistically без repro and approval.

---

## KI-005. NCT classify blind spots

**Severity:** Minor/Major depending on corpus  
**Status:** OPEN  
**Evidence:** HANDOFF §6: whitelist NCT — passing/neighbor/suspension; anticipation не распознаётся, а первый/последний срез партитуры не проверяется из-за отсутствия контекста.  
**Impact:** Legal non-chord tones may produce false violations.  
**Required direction:** Add explicit NCT classification context or documented whitelist.

---

## KI-006. Natural/melodic minor missing in canonical UI key catalog

**Severity:** Minor / P3  
**Status:** OPEN  
**Evidence:** HANDOFF §6: UI catalog exposes 24 canonical keys; backend/grammar can distinguish more modes.  
**Impact:** UI users cannot select natural/melodic minor directly.  
**Scope control:** Fix requires UI + API contract review.

---

## KI-007. Roman numeral grader mapping not wired end-to-end

**Severity:** Minor / P3  
**Status:** OPEN  
**Evidence:** HANDOFF §8.4 и REMEDIATION_PLAN P3; HANDOFF §6 также подтверждает, что grader API принимает только канонические символы функций.  
**Impact:** Some Roman numeral I/IV/V inputs may not grade as expected despite `normalize_roman` existing.  
**Risk:** API alias handling could silently fail.

---

## KI-008. Packaging mismatch: wheel vs `src.harmony.*` imports

**Severity:** Minor  
**Status:** OPEN  
**Evidence:** `pyproject.toml`: package name `harmony`, packages `where=["src"]`; docs and tests use `src.harmony.*`.  
**Impact:** Installed wheel may be unusable without path hacks.  
**Not changed:** Requires explicit packaging/release decision.

---

## KI-009. `uv.lock` untracked; lock policy remains undecided

**Severity:** Minor / governance inconsistency  
**Status:** MITIGATED  
**Evidence:** `git ls-files -- uv.lock` returns empty; `git check-ignore -v uv.lock` shows `.gitignore:14:uv.lock`.
README was corrected on 2026-11-16 to state that the lock is generated locally.  
**Impact:** The repository still does not provide a committed cross-platform dependency lock.  
**Remaining options:** track a platform-neutral lock or formalize generated-lock policy. Requires approval.

---

## KI-010. ML `StylePriorModel` is experimental stub

**Severity:** Minor  
**Status:** OPEN  
**Evidence:** `src/harmony/ml/model.py`; default pipeline uses no style scorer.  
**Impact:** Code and README may create impression ML is active.  
**Direction:** Either document as disabled prototype or remove in cleanup wave.

---

## KI-011. Duplicate core domain types

**Severity:** Minor  
**Status:** OPEN  
**Evidence:** AUDIT m3: `core/types.py` and `core/key.py`/`core/voicing.py` contain overlapping Key/Voicing concepts.  
**Impact:** Import confusion, future API drift.  
**Constraint:** Refactor needs architectural approval and compatibility tests.

---

## KI-012. Repomix PROJECT_MAP body remains historical snapshot

**Severity:** Minor  
**Status:** MITIGATED, not closed  
**Evidence:** `PROJECT_MAP.md` header updated to current live gates on 2026-11-16, but embedded Repomix dump may still contain older generated content.  
**Impact:** Readers should treat header/gate sections as governance summary and body as historical artifact.  
**Recommendation:** Regenerate snapshot only when explicitly requested.

---

## KI-013. External audit error list divergences require textbook citation

**Severity:** Governance / not a defect  
**Status:** OPEN  
**Evidence:** HANDOFF §6 lists intentional divergences from an external reviewer list.  
**Impact:** Some external findings should not be treated as bugs.  
**Rule:** No rule weakening without textbook quote and user approval.

---

## KI-014. Frontend OSMD bundle size warning

**Severity:** Minor  
**Status:** ACCEPTABLE  
**Evidence:** Vite build warning: osmd chunk ~1438 KB > 500 KB.  
**Impact:** Larger lazy-loaded frontend bundle.  
**Mitigation:** lazy chunk exists; performance tuning is optional.

---

## KI-015. Performance thresholds were not changed during docs wave

**Severity:** Governance  
**Status:** OPEN  
**Evidence:** HANDOFF §8, AUDIT M5.  
**Impact:** Perf tests may be close to current measured times under load.  
**Rule:** Any threshold change must be accompanied by benchmark evidence and approval.

---

## KI-016. Internal `EMPTY_SCORE` grade mapping is inconsistent

**Severity:** Minor  
**Status:** OPEN (out of scope for docs wave)  
**Evidence:** `backend/grader.py:250-268` sets `hard_violations_count=1` but returns grade `2`; the general
mapping at `backend/grader.py:364-376` gives `1 → 3`. The branch is unreachable through `/api/grade` because
`GradeRequest.voicings` has `min_length=1` (`backend/api.py:203`).  
**Impact:** Direct Python API callers can observe a different grade rule than REST clients.  
**Required fix:** Decide whether empty input should be a separate rejection grade or a hard violation, add
tests, and obtain approval before changing behavior.

---

## Verification status

- Live QA on 2026-11-16 confirmed no current build/test regression.
- Known issues above are not treated as blockers for documentation wave.
- Code changes for any Major issue require separate task and explicit approval if architecture/rules/tests/packaging may change.
