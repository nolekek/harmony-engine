# TASK_LOG.md — Brigade Harmony Engine

Формат: задача, затронутые файлы, проверка, статус. Записи до 2026-11-14 восстановлены по [HANDOFF.md](.redteam/HANDOFF.md), AUDIT и git history. Запись 2026-11-16 подтверждена live QA.

---

## 2026-11-09 — Initial engine

**Цель:** создать SATB гармонизатор по Brigadе.  
**Результат:** core domain, grammar, Viterbi solver, rules, exports, tests.  
**Статус:** historical, later expanded.

---

## Red-team P0/P1/P2 waves

**Цель:** закрыть ранние structural/API defects.  
**Результат:** RuleEngine contracts, diagnostics, whitelist, K64/D43/D2/VII7, MetricGrid, Krumhansh–Schmuck detector, HarmonizationService, MIDI/OSMD pipeline.  
**Evidence:** `.redteam` reports and merged commits.

---

## 2026-11-12/13 — Wave P1 core fixes (`06c4437`)

**Задача:** финальный T→VI, false relation, monkey-patch cleanup.  
**Файлы:** `backend/grader.py`, `src/harmony/rules/chromatic.py`, `src/harmony/rules/doubling.py`, pipeline/solver, tests.  
**Проверка:** QA и ревью.  
**Результат:** hard gate `CADENCE_FINAL_VI_REQUIRES_DOMINANT`; monkey-patch removed; mode-aware false relation.

---

## 2026-11-13 — Wave P2 cadence/replanning fixes (`814ca5f`)

**Задача:** plagal last resort, extended ranges, fallback planning.  
**Файлы:** grammar/solver/pipeline/tests.  
**Проверка:** QA + grammar metrics.  
**Результат:** improved replanning, plagal final behavior, survival table snapshots.

---

## 2026-11-13 — Desktop shell (`29b5a5f`)

**Задача:** desktop app, single instance, logs, PyInstaller.  
**Файлы:** `desktop/`, `desktop.spec`, `backend/main.py`, tests.  
**Результат:** file-lock single-instance; Win32 focus; Uvicorn daemon thread; desktop lifecycle tests.

---

## 2026-11-13 — Wave 2 UI redesign branch (`d9c5294`, merge `078114a`)

**Задача:** redesign React UI.  
**Файлы:** `frontend/src/**`.  
**Результат:** after TS fixes merged into master.  
**Verification:** frontend build passed after wave.

---

## 2026-11-13 — Wave 1: Wave 2 UI completion (`078114a`)

**Задача:** починить 12 TS build errors.  
**Файлы:** frontend UI/components/hooks.  
**Результат:** APPROVE after review.

---

## 2026-11-13 — Wave 2: hygiene (`57ec318`)

**Задача:** убрать ruff ошибки, мусор, актуализировать README.  
**Файлы:** root Python files, scripts, backend, tests, `pyproject.toml`.  
**Verification:** `ruff check .` → 0 errors; tests green.

---

## 2026-11-14 — Wave 3: backend robustness (`7888455`)

**Задача:** import-file 400, LRU/TTL cache, grammar whitelist, remove monkey-patch, relaxed flags.  
**Файлы:** `backend/api.py`, `backend/service.py`, frontend, tests.  
**Verification:** pipeline APPROVE, QA tests.  
**Результат:** +31 tests → 879 total.

---

## 2026-11-14 — Wave 4: core defects #8/#6 (`eac4ebd`)

**Задача:** chromatic diagnostics, RuleEngine dead code cleanup.  
**Файлы:** `src/harmony/rules/chromatic.py`, `rules/engine.py`, `docs/brigade_rules.json`, pipeline/solver, tests.  
**Verification:** QA 9/9, tests 886.  
**Результат:** дефекты #8 и #6 CLOSED.

---

## 2026-11-14 — Wave 5: external score audit G1/G2/G3 (`fe8f942`)

**Задача:** `BASS_INVERSION_MISMATCH`, `FOREIGN_TONE`, external fixture.  
**Файлы:** rules/doubling, grader, docs, tests.  
**Verification:** QA 5/5; live ruff clean; grammar metrics unchanged; tests 901.  
**Статус:** CLOSED.

---

## 2026-11-14 — PROJECT_MAP generation (`7448bb7`)

**Задача:** создать structural map через Repomix.  
**Файл:** `PROJECT_MAP.md`.  
**Результат:** Repomix compressed snapshot.  
**Limitation:** status counts in header could drift.

---

## 2026-11-16 — Docs wave: create typical governance documents

**Цель:** создать типовые документы для проекта согласно AGENTS.md.

**Изменения:**

- создан [`ARCHITECTURE.md`](ARCHITECTURE.md);
- создан [`SPECIFICATION.md`](SPECIFICATION.md);
- создан [`DECISIONS.md`](DECISIONS.md);
- создан [`KNOWN_ISSUES.md`](KNOWN_ISSUES.md);
- создан [`TASK_LOG.md`](TASK_LOG.md);
- актуализирован статус в [`PROJECT_MAP.md`](PROJECT_MAP.md);
- исправлены stale live counts и формулировка `uv.lock` в [`README.md`](README.md);
- после read-only ревью критика уточнены формулировки в `ARCHITECTURE.md`, `SPECIFICATION.md`,
  `DECISIONS.md` и `KNOWN_ISSUES.md`; выявлена отдельная неконсистентность internal grade mapping — `KI-016`.

**Live verification before docs:**

| Команда | Exit | Результат |
|---|---:|---|
| `git status --short` | 0 | modified only `.redteam/HANDOFF.md` before docs wave |
| `git rev-parse HEAD` | 0 | `fe8f94285c48385ec6ff93cb3567652e44066f71` |
| `git branch --show-current` | 0 | `master` |
| `.venv\Scripts\python.exe -m pytest -q` | 0 | 901 passed, 0 failed/skipped/errors, 383s, 1 site-packages deprecation warning |
| `.venv\Scripts\python.exe -m ruff check .` | 0 | All checks passed |
| `npm run build` in `frontend/` | 0 | Vite build success, 2085 modules, 3.40s build, osmd chunk size warning |

**Verification after docs:**

| Команда | Exit | Результат |
|---|---:|---|
| `git status --short` | 0 | изменены только документация и сохранённый `.redteam/HANDOFF.md`; 5 новых документов — untracked |
| точечный `rg` / чтение файлов | 0 | README и PROJECT_MAP header актуализированы; KI-009 переведён в `MITIGATED`; исправлены 8 minor-неточностей, найденных критиком |
| read-only review критика | APPROVE | 0 blocker / 0 major; minor-формулировки исправлены в этой же docs-волне |

Python-код, frontend-код и тесты в этой волне не изменялись. Встроенное тело `PROJECT_MAP.md` сознательно
остаётся историческим снапшотом Repomix; его старые счётчики закрыты в KI-012, а не молча переписаны.

**Status:** completed.

---

## Remaining work after docs wave

- `PROJECT_MAP.md` body remains historical Repomix snapshot; regenerate only if requested.
- Packaging mismatch and uv.lock policy remain open governance issues.
- Performance, plan survival, chromatic dictionary, MIDI round-trip off-by-one remain non-doc follow-ups.
- Internal `EMPTY_SCORE` grade-mapping inconsistency is recorded in `KI-016` and was not changed in docs wave.
