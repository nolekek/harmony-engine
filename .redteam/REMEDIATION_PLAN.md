# План исправления и рефакторинга — «Бригадное Ядро Гармонизации»

> **Для исполнителей:** REQUIRED SUB-SKILL: superpowers:subagent-driven-development (рекомендуется) или superpowers:executing-plans. Шаги — чекбоксы (`- [ ]`). Каждая задача заканчивается зелёными тестами и коммитом.

**Цель:** превратить прототип, который генерирует унисонные огрызки с самооценкой «5/5» и валится на обычной диатонике, в честный строгий SATB-движок по «Бригадному» учебнику — без фейковых заявлений, без слепых зон в правилах, с внятной диагностикой.

**Спека:** [REPORT.md](REPORT.md) (карта из 64 находок), [theory-research.md](theory-research.md), [architecture-audit.md](architecture-audit.md), [backend-audit.md](backend-audit.md), [solver-audit.md](solver-audit.md), [rules-audit.md](rules-audit.md), [frontend-audit.md](frontend-audit.md), [fuzz.md](fuzz.md).

**Стек:** Python 3.14 + FastAPI (`backend/`), ядро `src/harmony/`, React 19 + OSMD (`frontend/`), pytest (515 тестов на старте).

**Рабочее окружение:** все команды из `D:\aitraining`, системный `python` (в `.venv` нет зависимостей — это само по себе задача T22).

---

## Статус исполнения (обновляется по мере работы)

Ветка `redteam-p0`. Baseline до работ: **515 passed** (`git c317fbd`).

| Волна | Задачи | Статус | Что сделано / чем подтверждено |
|---|---|---|---|
| P0-α | T1, T2, T3, T8 | ✅ | Унисоны/полнота трезвучий, канонический D43/D2/II43/II2, `parse_chord_symbol` для Enum, K64-позиция + метрика в Viterbi. |
| P0-α | T4, T5, T6, T12 | ✅ | Честный топ-3 (`select_top_candidates`), `is_downbeat` без `False→None`, строгий `allow_secondary_dominants`, CORS-whitelist, Pydantic 422 (тоника/лад/`max_plans`/длина/pitch). |
| P0-α | T10, T9-фронт, T11-фронт | ✅ | Shared `AudioContext` + cleanup, inline-баннер вместо `alert`, `AbortController`, сброс грязного стейта, `durations`/`time_signature` в экспорт. |
| P0-β | T7, T9-backend | ✅ | `chords` обязательны (422), белый список функций, grader через `RuleEngine` с `is_final_chord`, `error.code`/`diagnostics` в отказах (`NO_PLANS`, `NO_FEASIBLE_PLAN`, `SECONDARY_DOMINANTS_DISABLED`). |
| P0-γ | T11, T13 | ✅ | MusicXML: резка нот по барлайнам с лигами, суммы тактов, паузы в хвосте; `max_plans` 30→60 (CLI `--max-plans`), исправлен предикат `S→D` (4→5 вверх), приоритет секстаккордов. |
| P0 gate | — | ✅ | `pytest`: 556 passed, 2 xfailed; Lead-шлюз `verify_p0.py`: 13/13 + 8/8. |
| P1-α | T16, T15 | ✅ | Словарь `III/III6/VII/VII6/VII7/II7/II65` + `normalize_roman`; NCT (passing/neighbor) на слабых долях; нисходящая диатоника гармонизуется, xfail сняты. |
| P1-α | T19 | ✅ | Krumhansl-Schmuckler профиль вместо «+60 за последнюю ноту»; половинная каденция `C D E F G` → C-dur. |
| P1-α | T20, T14-фронт | ✅ | Раздельные состояния вкладок, таргетная подсветка тактов, durations в synth, размер в `MelodyInput`/метрономе. |
| P1-β | T14, T21 | ✅ | `core/metric.py::MetricGrid` — единый источник долей; `backend/service.py::HarmonizationService`, async+threadpool, логирование, JSON 404 на `/api/*`, 500 с `error_id`, порт из env. |
| P1-β | T17, T18 | ✅ | Единый `check_syntax_rules` для грамматики и движка; контекстный `D→S` (`phrase_boundary`); живой `brigade_rules.json`; contrary/parallel без `%12`-путаницы, `ум.5→ч.5`, ув.5/ум.7/ум.4, два скачка; удержание септимы `D7→D65`; полный VII7; неотрицательные стоимости + эвристика шага 0. |
| P1 gate | — | ✅ | `pytest`: **645 passed** (без xfail); `verify_p1.py`: волна A — 15/15, волна B — 8/8; регресс P0: 13/13 + 8/8. |
| P2 | T22 | ✅ | `pyproject`: реальные зависимости + dev-экстра; `.github/workflows/ci.yml` (pytest+ruff+frontend build); README/MATH_MODEL без «127 тестов / Bi-GRU / <10 ms»; ML-модуль честно помечен как n-gram prior. |
| P2 | T23 | ✅ | `test_scale_matrix.py`: **48/48** (12 тоник × Major/MinorHarmonic × asc/desc); `test_property_invariants.py`: 100 мелодий, отказов 11%, 0 нарушений инвариантов; harness: **5×24/24** (`--fixed-level`). |
| P2 | T24 | ✅ | Bounded replanning в `pipeline.py` (`allow_replanning`, ≤200 итераций / 2 c) + `relax_soprano_intervals`; мелодия больше не страдает от «внутренних» ограничений cantus firmus; детерминизм, честный opt-out. |
| P2 | T25 | ✅ | MIDI Format 1 (4 трека, Choir Aahs 52, из `durations`); MusicXML бемоли по `fifths`; импорт по реальным `delta_time` + MetricGrid; OSMD в lazy-чанке (главный бандл 1.73 МБ → **289 КБ**); a11y; мёртвый `App.css` удалён. |
| P2 gate | — | ✅ | `pytest`: **706 passed** (5:21); `verify_p2.py`: **13/13**; регресс P0/P1: exit 0 оба. |

Осознанные ограничения P1 (не дефекты, запланированы в P2):

- Стоимость больше не отрицательная (T18): UI показывает «Штраф: N», контракт `cost` сменил знак — синтетические тесты, хардкодившие `-6.0`, переведены на структурную проверку «топ-3 == глобально минимальные».
- Римские цифры `I/IV/V` нормализуются (`core/chord.py::normalize_roman`), но `GradeRequest` принимает только канонические символы — маппинг остаётся на P3 (см. ниже).
- `VII53` в основном виде запрещён каноном (тритон в басу) — разрешены `VII6`/`VII7`.
- Прерванная каденция с `A=T` унисоном остаётся запрещённой; канон реализован вариантом с ведущим тоном в сопрано.
- Случайная диатоника с крупными неаккордовыми скачками всё ещё может отказывать — это честный отказ с `error.code`; property-тест фиксирует долю отказов 11% на «заведомо гармонизуемых» мелодиях.

### Фаззинг: аудит → после P1 (тот же скрипт категорий, `max_plans=30`)

| Категория | Отказов в аудите | После P1 | Комментарий |
|---|---:|---:|---|
| control (дефолт) | 100% | **0%** | было следствием `max_plans=30` |
| 24 мажора (гаммы/арпеджио/фигуры) | 47.6% | **0%** | словарь III/VII6 + NCT |
| 24 минора | 47.6% | 57.1% | остались `S6`-тупики после `III6` — планирование в миноре (T23/T24) |
| random diatonic | 41.7% | 43.3% | отказы честные, `error.code`; нужен корпус/property (T23) |
| NCT | 12.5% | **0%** | слой NCT |
| хроматика | 80% | 60% | часть лечится NCT-проходящими; остальное — N/bVI/альтерации (P2) |

Сырые данные: `.redteam/evidence/p1_core_fuzz_results.json`, `.redteam/evidence/p1_category_stats.json`.

### P2 закрыт. Что осталось на после-релиз (P3, не блокеры)

- Римские цифры в `GradeRequest`: принимаются только канонические символы (`normalize_roman` есть, но в API не подключён).
- Натуральный/мелодический минор в UI-каталоге: детектор возвращает `MinorHarmonic`; натуральные минорные мелодии гармонизуются через replanning, но отдельного лада в селекторе нет.
- CP-SAT / честный K-best: replanning закрывает практические тупики, но глобальный K-best по решётке состояний (вместо beam по планам) остаётся архитектурным заделом.
- Golden-корпус из реального задачника: сейчас `tests/corpus/benchmark_tasks.py` (4 задачи) + property-тесты; полноценный корпус с человеческими эталонами — отдельная работа.
- `.venv` в репозитории остаётся нерабочим артефактом: источник истины — `pip install -e .[dev]` (описано в README).



---

## Глобальные ограничения (действуют для каждой задачи)

- Не менять код вне inScope задачи; чужие задачи не трогать.
- Любое изменение правила = тест ДО фикса (TDD): сначала доказать, что баг воспроизводится, потом — что исчез.
- Тесты, закрепляющие баги (`tests/unit/test_spacing.py:62`, `tests/test_solver_fuzzing.py:372`, `tests/test_rules.py:174-198`, эталоны в `tests/corpus/benchmark_tasks.py:32,57`), **переписывать под канон**, а не под текущее поведение.
- Hard-нарушения — отсечение недопустимых состояний, не «штраф 100000» в стоимости. Стоимость ≥ 0 (отрицательные бонусы убрать в T18).
- После каждого этапа: `python -m pytest -q` — зелёный (или явно задокументировано, какие тесты переписаны и почему).
- Коммит на каждую задачу, сообщение вида `fix(rules): запрет унисонов соседних голосов [P0-1]`.

## Review Focus (что вероятнее всего укусят после «готово»)

1. **Легальная диатоника обязана гармонизоваться**: `C5-B4-A4-G4`, 8-нотная нисходящая гамма C-dur, natural/melodic minor — ноль отказов. Тест: `tests/test_regression_redteam.py::test_descending_scales_harmonize` (T13).
2. **Каждое решение — полное 4-голосие**: `S > A > T > B` строго, терция присутствует, все pcs ∈ аккорда. Property-тест на 1000 решений (T1, T8).
3. **Grader не сертифицирует мусор**: тот же voicing с `chords` и без — разные результаты; без `chords` → 422, не «5» (T7).
4. **API и ядро детерминированно согласованы**: один JSON → один план и в `Harmonizer.harmonize`, и в `POST /api/harmonize` (T5, T6).
5. **MusicXML открывается в MuseScore/OSMD без переполнения тактов**: сумма duration в такте == размеру (T11).

---

# Фаза P0 — остановить кровь (блокерные дефекты)

Порядок важен: T1–T3 меняют допустимое множество решений, T4–T6 — контракт API, T7–T13 достраивают остальное. Параллелить можно только задачи с непересекающимися файлами (указано в inScope).

### T1: Запрет унисонов соседних голосов + полнота трезвучия [REPORT #1, #6, #59; DEF-03]

**Файлы (inScope):**
- Правка: `src/harmony/rules/spacing.py:57-94`, `src/harmony/rules/doubling.py:101-175`, `src/harmony/solver/state_generator.py:115-137`
- Тесты: `tests/unit/test_spacing.py` (удалить/инвертировать кейс `(60,60,48,48)` на строке 62), новый `tests/test_chord_completeness.py`
- Эталоны: `tests/corpus/benchmark_tasks.py:32,57` (финальные аккорды `(60,60,55,48)`, `(67,67,59,43)` — переделать под полное 4-голосие)

**Что делать:**
- `spacing.py`: строгий порядок `s > a > t > b`; нарушение → `RuleViolation("VOICE_UNISON", severity="hard_gate")`.
- `doubling.py`: новая проверка `check_triad_completeness` — для трезвучий 5/3 требовать `third in pcs` и `fifth in pcs` (коды `CHORD_THIRD_MISSING`, `CHORD_FIFTH_MISSING`); неполное трезвучие (утроенная прима без квинты) допустимо **только** на заключительном аккорде (флаг `is_final_chord` пробросить из контекста).
- `state_generator.py:135`: `bass_high = min(b_max, t - 1)` — генератор не должен даже создавать T=B.
- Вызывать новые проверки из `RuleEngine.validate` **и** из `backend/grader.py` (через T7).

- [ ] Шаг 1: тест `test_unison_rejected`: `(64,60,48,48)` для `T` в C-dur → hard-нарушение `VOICE_UNISON`; прогнать — упасть должен на assert (сейчас violations пустой).
- [ ] Шаг 2: тест `test_third_required`: `(60,60,55,48)` для `T` → `CHORD_THIRD_MISSING`; `test_fifth_required`: `(60,64,60,48)` (C-C-E-C без G, не финал) → `CHORD_FIFTH_MISSING`.
- [ ] Шаг 3: прогнать — FAIL. Реализовать проверки. Прогнать — PASS.
- [ ] Шаг 4: переписать подогнанные эталоны в `benchmark_tasks.py` и `test_spacing.py:62`; полный `python -m pytest -q`.
- [ ] Шаг 5: коммит.

**Проверка приёмки:** `generate_candidate_voicings(64, Chord("T"))` в C-dur не возвращает ни одного voicing с `S==A`, `A==T`, `T==B` или без терции.

---

### T2: D43 — терцквартаккорд, а не клон D2 [REPORT #3; BK-01; DEF-02]

**Файлы (inScope):**
- Правка: `src/harmony/solver/state_generator.py:99-105`, `src/harmony/rules/resolutions.py:67-124`, `docs/MATH_MODEL.md:73-75`, `docs/BRIGADE_RULES.md:99-102`
- Тесты: `tests/test_solver_fuzzing.py:372-377` (инвертировать assert «D43 must have 7th F in bass»), `tests/test_rules.py:174-198`, новый `tests/test_d43_d2.py`

**Канон (Бригадный, гл. 27; MIT chord table):**
- `D43` (V4/3): бас — **квинта** аккорда (II ступень, D в C-dur). Разрешение: `T53` (бас II→I) или `T6` (бас II→III).
- `D2` (V2/4): бас — **септима** (IV ступень, F). Разрешение строго `T6` (бас вниз на секунду).
- `II43`: бас — A (квинта D-F-A-C), `II2`: бас — C (септима). Убрать хардкод `tonic_pc + 5` для не-доминантовых групп (solver-audit #6): `required_bass_pc` вычислять от фактора обращения конкретного аккорда.

- [ ] Шаг 1: тест `test_d43_bass_is_fifth`: в C-dur bass pcs для `D43` == `{2}`, для `D2` == `{5}`; `test_d43_resolves_to_T_or_T6`; `test_ii2_bass_is_seventh`. Прогнать — FAIL.
- [ ] Шаг 2: исправить `state_generator.py` (бас по фактору обращения), `resolutions.py` (`check_d43_resolution` → цели `T/T53/T6` с ходом баса ∓ секунда; `D2` оставить как есть), синхронизировать `grammar.is_valid_syntax_transition`.
- [ ] Шаг 3: инвертировать подогнанные тесты (`test_solver_fuzzing.py:372`, `test_rules.py:174`), поправить `MATH_MODEL.md` и `BRIGADE_RULES.md`.
- [ ] Шаг 4: `python -m pytest -q` — PASS. Коммит.

---

### T3: `parse_chord_symbol` — обход всех проверок удвоения через `ChordDefinition` [REPORT #50; solver-audit #4]

**Файлы (inScope):** `src/harmony/core/types.py:269-307`, `src/harmony/core/chord.py`, тест `tests/test_parse_chord_symbol.py`

- [ ] Шаг 1: тест: `parse_chord_symbol(ChordDefinition(ChordFunction.T, ...))` == `"T"` (сейчас — `"ChordFunction.T"`). FAIL.
- [ ] Шаг 2: извлекать `.value` у Enum; добавить явный тест, что `check_main_triad_doubling` на `ChordDefinition` возвращает те же нарушения, что на `Chord`. Идеал — одна доменная модель аккорда; минимум — корректный парсинг + deprecated-маркер на `ChordDefinition`.
- [ ] Шаг 3: PASS, коммит.

---

### T4: Честный топ-3 [REPORT #4; BK-04]

**Файлы (inScope):** `backend/api.py:225-240`, `src/harmony/pipeline.py:150-170`, тест `tests/test_top3_selection.py`

- [ ] Шаг 1: тест на синтетике: из 5 успешных планов с cost `[-2, -6, -6, -10, 0]` API возвращает топ-3 `[-10, -6, -6]` (сейчас вернёт первые три найденных). FAIL.
- [ ] Шаг 2: убрать `if len(solutions) >= 3: break` (`api.py:229`); решать все планы, собирать успехи, `solutions.sort(key=cost)` → `[:3]`. То же в `pipeline.py:160`.
- [ ] Шаг 3: PASS; замерить latency (планов ≤ 50, Viterbi ~1 мс/план — приемлемо). Коммит.

---

### T5: `is_downbeat=false` не должен превращаться в `None` [REPORT #9; BK-03]

**Файлы (inScope):** `backend/api.py:142`, тест `tests/test_backend_api.py` (новый кейс)

- [ ] Шаг 1: тест: один и тот же JSON с явным `is_downbeat: false` даёт идентичные планы через API и через `Harmonizer.harmonize` (сейчас расходятся, §1.7). FAIL.
- [ ] Шаг 2: `"is_downbeat": m.is_downbeat` — прямой проброс. PASS, коммит.

---

### T6: `allow_secondary_dominants=false` — честный отказ вместо тихого игнора [REPORT #21; BK-05]

**Файлы (inScope):** `backend/api.py:159-167`, тест `tests/test_backend_api.py`

- [ ] Шаг 1: тест: мелодия с F# (66) в C-dur, флаг `false` → `is_success=false` + внятное сообщение «Без побочных доминант гармонизация невозможна» (сейчас возвращает `DD7`). FAIL.
- [ ] Шаг 2: `plans_to_try = filtered_plans`; если пуст — структурированный отказ (формат из T9). PASS, коммит.

---

### T7: Grader перестаёт быть слепым [REPORT #17, #10, #59; BK-07, BK-08]

**Файлы (inScope):** `backend/grader.py:249-316`, `backend/api.py` (роут `/api/grade`), тест `tests/test_grader_strictness.py`

- [ ] Шаг 1: тесты: (a) `/api/grade` без `chords` → 422; (b) `len(voicings) != len(chords)` → 422; (c) неизвестная функция (`"V"`, `"Q"`) → 422/явная ошибка, НЕ тоника; (d) voicing с S=A унисоном или без терции → `hard ≥ 1`, grade < 5. Все FAIL.
- [ ] Шаг 2: сделать `chords` обязательным полем; валидировать длины; `get_triad_tones` на неизвестный символ бросает ошибку (никакого fallback в тонику — `backend/api.py`/`grader` её перехватывают в 422); grader вызывает те же проверки унисонов/полноты из T1 через `RuleEngine` (единый источник истины).
- [ ] Шаг 3: PASS; прогнать 10 «успешных» решений из `.redteam/evidence/quality_audit.json` через новый grader — ни одно не должно получить 5. Коммит.

---

### T8: K64 по канону [REPORT §1.5, #48; theory §2.5]

**Файлы (inScope):** `src/harmony/rules/doubling.py:177-212`, `src/harmony/rules/engine.py:90`, `src/harmony/solver/viterbi.py:68`, тест `tests/test_k64.py`

- [ ] Шаг 1: тесты: (a) K64 первым аккордом плана — запрещён; (b) K64 разрешён только на сильной/относительно сильной доле непосредственно перед D/D7 в каденции; (c) бас K64 обязан быть V ступенью (`doubling.py` сейчас проверяет только «бас повторён»); (d) `T64` ≠ `K64` (проходящий T64 не мапить в кадансовый). FAIL.
- [ ] Шаг 2: реализовать; `is_downbeat` брать из метрической структуры (полная унификация — T14, здесь минимум: не `i % 2 == 0` в `viterbi.py:68`).
- [ ] Шаг 3: PASS, коммит.

---

### T9: Диагностика вместо generic-вранья [REPORT #7, §4.6; BK-06]

**Файлы (inScope):** `backend/api.py:189,243`, `src/harmony/solver/viterbi.py:199-206` (проброс diagnostics), `frontend/src/App.tsx:99-121`, тест `tests/test_api_diagnostics.py`

**Контракт ответа при отказе (фиксируется здесь, используется в T6/T13):**
```json
{
  "is_success": false,
  "candidates": [],
  "error": {
    "code": "NO_FEASIBLE_PLAN",
    "message": "...",
    "diagnostics": [{"step": 2, "chord": "D", "blocked": 21, "blocked_by": ["PARALLEL_OCTAVES"]}],
    "hint": "..."
  }
}
```

- [ ] Шаг 1: тест: отказ на `C5-B4-A4` содержит `error.diagnostics` с конкретным шагом и правилами (сейчас — одна строка-заглушка). FAIL.
- [ ] Шаг 2: API возвращает `SolverResult.message`/diagnostics в структуре выше; фронт: вместо `alert()` — inline-баннер с `error.message` + раскрывающийся список diagnostics; при неуспехе **обязательно** `setCandidates([])`, `setSelectedCandidate(null)`, `setActiveMusicXml("")`; проверка `resp.ok` с парсингом `detail` для 422/500; `AbortController` в `useRef` (отмена предыдущего запроса, игнор `AbortError`); `finally { setIsHarmonizing(false) }` гарантированно снимает спиннер.
- [ ] Шаг 3: PASS; ручная проверка сценария со скриншота (отказ → чистый экран + баннер, кнопка разблокирована). Коммит.

---

### T10: Утечка AudioContext в метрономе [REPORT #55; F-02]

**Файлы (inScope):** `frontend/src/audio/midiInput.ts:114-141`

- [ ] Шаг 1: один разделяемый `AudioContext` (синглтон модуля или из audioEngine) вместо `new AudioCtxClass()` на каждый тик; `cleanup()` отвязывает `onmidimessage` при disconnect/unmount; downbeat-логика `((beat-1)%4)+1` помечается TODO(T14) — хардкод 4/4.
- [ ] Шаг 2: проверка: сборка `npm run build` в `frontend/` без ошибок; ручной тест — 60+ тиков метронома, в DevTools число AudioContext не растёт. Коммит.

---

### T11: Экспорт — ритм и такты [REPORT #8, #15; §1.9; F-03]

**Файлы (inScope):** `src/harmony/export/musicxml.py:121-295`, `src/harmony/core/types.py:426-499`, `frontend/src/components/ExportBar.tsx:28-76`, `frontend/src/App.tsx` (проброс `durations`), тест `tests/test_musicxml_measures.py`

- [ ] Шаг 1: тест: для мелодии `half×5 + whole` в 4/4 каждый такт MusicXML имеет сумму `<duration>` == 16 divisions; нота, пересекающая барлайн, разрезана на две с `<tie>`; `<backup>` не превышает такт. FAIL (сейчас такт 3 = 24 divisions, backups=24).
- [ ] Шаг 2: `calculate_metric_structure`/экспортер — группировка по тактам из модели, резка нот на барлайне с лигами; `ExportBar` передаёт `durations` и `time_signature` (включая вкладку grader); `revokeObjectURL` через `setTimeout(..., 1000)`.
- [ ] Шаг 3: PASS + открыть сгенерированный XML в OSMD/MuseScore — сетка тактов без разрывов. Коммит.

---

### T12: CORS и валидация API [REPORT #37, #38, #61, #62; BK-08, BK-09]

**Файлы (inScope):** `backend/main.py:23-29`, `backend/api.py:32-70`, тест `tests/test_api_validation.py`

- [ ] Шаг 1: тесты: (a) preflight с `Origin: http://evil.com` не получает `access-control-allow-origin: http://evil.com` + credentials; (b) `{"tonic":"Z#","mode":"AlienMode"}` → 422; (c) `max_plans=0/-10` → 422; (d) мелодия из 1000 нот → 422; (e) pitch вне 0..127 → 422. FAIL.
- [ ] Шаг 2: `allow_origins` — белый список (`http://127.0.0.1:8000`, `http://localhost:5173`); Pydantic: `KeyRequest` — whitelist тоник/ладов, `max_plans: Field(ge=1, le=100)`, `melody: Field(max_length=128)`, `pitch: Field(ge=0, le=127)`; `Key.parse` — ошибка вместо молчаливого C-dur.
- [ ] Шаг 3: PASS, коммит.

---

### T13: Дефолты ядра — `max_plans` и приоритет секстаккордов [REPORT #44, #45; BK-02; DEF-01]

**Файлы (inScope):** `src/harmony/pipeline.py:91`, `src/harmony/cli.py:87-88`, `src/harmony/syntax/grammar.py:270-360`, тест `tests/test_regression_redteam.py` (новый)

- [ ] Шаг 1: регрессионный корпус (все кейсы §1.2–1.3, §1.15 отчёта): `C5-B4-A4-G4`; `C5…C4` (8 нот); `C5 E4 F4 G4 C5`; A natural minor up/down; A melodic minor down; дефолтная мелодия фронта через `Harmonizer()` **без явного max_plans**; 16-нотная диатоника. Сейчас — FAIL пачкой.
- [ ] Шаг 2: минимальные меры P0: дефолт `max_plans` 30 → 60 в `pipeline.py`/`cli.py`; в beam-грамматике поднять приоритет `S6`/`D6` при секундных ходах сопрано (в первую очередь запрет `S→D` в основных видах при сопрано 4→5 вверх — `grammar.py:278-284`, предикат сейчас проверяет не те ступени, REPORT #54). Полное лечение — T15/T16 (P1), здесь достаточно, чтобы корпус из шага 1 позеленел.
- [ ] Шаг 3: `python -m pytest -q` + корпус PASS. Коммит.

**Замечание:** часть отказов (нисходящая гамма `C5-B4-A4` — нет `III`/`VII6` в словаре) не лечится одним `max_plans`; такие кейсы помечать `xfail(strict=True)` со ссылкой на T16 и снимать xfail по мере готовности. Обманывать зелёными тестами запрещено.

---

# Фаза P1 — архитектурный долг

### T14: Единая модель метра `MetricGrid` [REPORT #9, §4.4; BK-03]

**Файлы:** новый `src/harmony/core/metric.py`; правки: `core/types.calculate_metric_structure`, `solver/viterbi.py:68`, `backend/grader.py:244`, `backend/api.py`, `frontend/src/components/MelodyInput.tsx:97-106`, `frontend/src/audio/midiInput.ts:114-117`, `scripts/stress_test_harness.py:148-150`

Убить **шесть** разных определений сильной доли. Один источник: `MetricGrid(time_signature, durations)` → `(measure, beat, offset, is_downbeat)` на каждую ноту; explicit downbeat от клиента уважается всегда (T5). Фронт считает доли по выбранному размеру (пробросить `timeSignature` в `MelodyInput`, пересчёт при add/remove/смене размера). Тесты: 4/4, 3/4, 2/4, 6/8, 3/8 — downbeats, номера тактов, K64-метрика; §1.8 (разные размеры → разные планы там, где должны).

### T15: Слой NCT и гармонический ритм [REPORT #2, §4.3; DEF-06; BK-12]

**Файлы:** новый `src/harmony/analysis/nct.py` (или реанимация `rules/non_chord_tones.py`), `solver/state_generator.py:88`, `pipeline.py`

Двухслойная схема из theory-research §5.3: (1) редукция мелодии — структурные ноты на сильных долях vs passing/neighbor/suspension/anticipation на слабых; (2) один аккорд на гармонический сегмент (1–4 ноты), NCT валидируются поверх. Убрать `if soprano % 12 not in allowed_pcs: return []` — заменить на «нота либо тон аккорда, либо классифицированный NCT». Тесты: `C-D-E-F-G-F-E-D-C` держит гармонию, а не долбит аккорд на каждую ноту; фраза с задержанием; §1.17 NCT-категория фазза — 8/8.

### T16: Словарь функций и проходящие обороты [REPORT #11, #60; fuzz #2]

**Файлы:** `src/harmony/syntax/grammar.py:13-21` (`ALL_FUNCTIONS`), `core/chord.py get_triad_tones`, `rules/engine.py`

Добавить `III`, `VII`, `VII6`, `VII7`, `II7`, обращения DD, проходящий `T64`; `get_triad_tones` — без fallback в тонику, поддержка римских цифр `I/IV/V`. Разблокировать нисходящую диатонику (`B4` → `III`/`VII6` вместо единственной D). Синхронизировать с T2 (басы обращений). Тесты: `C5-B4-A4-G4` без xfail; 8-нотная нисходящая гамма ≥ 1 решение; fuzz-категории 24+24 тональности — отказов 0 на гаммах/арпеджио.

### T17: Единый RuleSet — один источник правил [REPORT §4.1, #12, #28, #41; DEF-05]

**Файлы:** `rules/engine.py`, `syntax/grammar.py:146-208`, `rules/resolutions.py:21-64`, `docs/brigade_rules.json`

Грамматика и RuleEngine используют одни предикаты (`HarmonyContext` + общие чистые функции), дубли `D43→T6/T` vs `T6`, `D2→T6` vs `T/T6` устранить. Fallback'и `grammar.py:361-393` не имеют права обходить метрику K64 и финальную каденцию. `D→S`: абсолютный запрет → контекстный (внутри фразы запрещён, на цезуре/прерванном обороте допустим). `D7→D65` с удержанной септимой — не нарушение. `brigade_rules.json`: либо `RuleEngine` реально читает реестр (severity/веса из JSON), либо файл удалить и генерировать доку из кода — мёртвый декор запрещён.

### T18: Voice-leading: мёртвые и ложные правила [REPORT #22–#27, #47, #53; rules-audit #4–#8]

**Файлы:** `rules/voice_leading.py`, `rules/doubling.py:316-478`, `solver/viterbi.py:127-145`, `rules/engine.py` (веса)

- Contrary 5/8 (`voice_leading.py:79-130`): убрать `%12`-путаницу унисона с октавой, проверять реальные интервалы; исключить перемещения внутри одного аккорда.
- Parallel 5/8: ловить `dim5→P5` (6→7) при похожем движении; не применять к `prev_chord == curr_chord` (октавные перемещения легальны).
- Melodic intervals: добавить ув.5 (8), ум.7 (9), ум.4 (4), два скачка подряд; ум.5 вниз с разрешением внутрь — разрешить (не банить все 6 пт подряд).
- Doubling: правила для `II6` (удвоение баса/терции по Бригаде §18), `VII6` (вводный тон удваивать нельзя), `VII7` — только полный (убрать ветку `is_incomplete` для VII группы).
- Viterbi: начальная стоимость шага 0 — не `0.0`, а эвристика расположения (унисон/пустая квинта дорогое); `contrary_bass_bonus = -5` заменить неотрицательными весами (стоимость ≥ 0, UI показывает «штраф», не «−7»).

### T19: Grader/key detector: тональности [REPORT #18, §1.14; BK-11; fuzz #7]

**Файлы:** `backend/key_detector.py`, `core/key.py`

Бонус последней ноты +60 → взвешенная эвристика (Krumhansl-Schmuckler профиль + вес каденсовых оборотов); `C D E F G` → C Major, не G. natural/melodic minor — поддержать или честно объявить «гармонический минор only» в UI/доках; каталог: добавить es-moll/Cis-dur или явно задокументировать выбор 24. Фронт-текст «24 канонических лада» → «24 тональности» (REPORT #35).

### T20: Фронтенд: изоляция состояния и рендер [REPORT #13, #14, #16, #31–#34, #36; F-04–F-09]

**Файлы:** `frontend/src/App.tsx`, `components/ScoreDisplay.tsx`, `components/ControlPanel.tsx`, `components/GraderPanel.tsx`, `audio/synth.ts`, `components/MelodyInput.tsx`

- Разделить стейт гармонизатора и инспектора (два объекта/reducer): после grade чужая партитура не подменяет активную, экспорт не смешивает chords/voicings из разных вкладок; `timeSignature` в экспорт на вкладке grader.
- `ScoreDisplay`: подсвечивать **только** такты из `problemMeasures` (сопоставление measureIndex), очистка фильтра при сбросе, `problemMeasures` в deps `useEffect`; пустой `musicxml` очищает партитуру; guard от load-race OSMD.
- `synth.ts`: длительности из `durations` кандидата (не `beatDurationSec * 2`); `stop()` глушит активные осцилляторы; `handleSelectCandidate` вызывает `audioEngine.stop()`; планирование через `AudioContext.currentTime` (lookahead), mute/solo — `linearRampToValueAtTime`.
- `ControlPanel`: `k.name` вместо `k.title`; кнопка disabled при пустой мелодии; «стоимость» → «штраф» (после T18 неотрицательна).
- `GraderPanel`: передавать `time_signature`/`durations`; sample-задачи используют свою тональность.
- `MelodyInput`: downbeat по `timeSignature` (связка с T14).

### T21: `HarmonizationService` — один фасад [DEF-07; REPORT §5]

**Файлы:** `backend/api.py:154-245`, `src/harmony/pipeline.py`, `backend/main.py`, `run_app.py`

Удалить copy-paste пайплайна из роутера: API и CLI вызывают один `HarmonizationService`. CPU-bound вызовы — `run_in_threadpool`/async. Логирование: structured logger на все эндпоинты + exception handler (сейчас 0 строк логов, REPORT #64). `run_app.py`: проверка занятости порта 8000, graceful shutdown. SPA-fallback не должен отдавать HTML на неизвестный `/api/*` (JSON 404).

---

# Фаза P2 — доверие, качество, упаковка

### T22: Упаковка и CI [REPORT #19, #20; DEF-09]

`pyproject.toml`: реальные зависимости (`fastapi`, `uvicorn`, `pydantic`, `python-multipart`, `pytest`), `uv sync` поднимает проект с нуля (сейчас `.venv` пустой — всё живёт на глобальном Python). `frontend/dist` — в `.gitignore` (1.73 МБ бандла в git не нужен). `.github/workflows/ci.yml`: pytest + ruff + mypy/pyright + frontend build. README: 515+ тестов (бейдж динамический), реальный статус harness (20/24, не «5×24/24»), убрать «Bi-GRU/нейро-символический» или подключить `StylePriorModel` в pipeline и назвать честно «n-gram style prior» (REPORT #42, DEF-04, BK-10). `docs/MATH_MODEL.md`: убрать «<10 ms», реальные цифры бенчмарка (REPORT #52).

### T23: Property-тесты и корпус [REPORT §8; fuzz]

Новый `tests/test_properties.py`: на ≥ 1000 сгенерированных решений инварианты — `S>A>T>B`, терция есть, все pcs ∈ аккорда, нет параллельных/скрытых 5/8, каждый такт MusicXML полон. 24 тональности × 5 размеров × 4 длины на заведомо гармонизуемых мелодиях — 0 отказов. Корпус golden-SATB из реального задачника (не самосгенерированный). `scripts/stress_test_harness.py` — единое с solver определение downbeat (после T14); цель 24/24 × 5 прогонов.

### T24: K-best и объяснение неразрешимости [REPORT §4.7, §5; DEF-01 альтернатива В]

Честный K-best Viterbi (K путей на узел решетки) вместо «1-best на плане»; при infeasible — релаксация (взвешенный MaxSAT/CP-SAT) с явным списком снятых ограничений, либо structured-объяснение «какое правило и на каком шаге». Оценка миграции на OR-Tools CP-SAT (architecture-audit §3 рекомендует гибрид NCT + CP-SAT) — спайк, решение по итогам; при переходе Viterbi остаётся fallback.

### T25: Мелочи фронта и MIDI [REPORT #29, #30, #39, #40, #57, #58; BK-13; F-10–F-12]

MusicXML: бемоли для бемольных тональностей (Bb, не A#). MIDI: Format 1, 4 трека/канала, хор-патчи; импорт — реальные `delta_time` вместо хардкода `half`. Code-splitting: `React.lazy(ScoreDisplay)` + `manualChunks` для OSMD. Удалить мёртвый `App.css`; a11y (`aria-label` на инпуты voicings, role="button"/tabIndex на карточки); бейдж latency — реальные цифры; «И. И. Способин, И. В. Способин» → «И. В. Способин» (и проверить инициалы całej бригады по титулу учебника).

---

## Порядок исполнения и параллелизм

| Волна | Задачи (параллельно, файлы не пересекаются) | Барьер |
|---|---|---|
| P0-α | T1, T2, T3 (правила/ядро), T10, T12 (фронт/API-конфиг) | pytest зелёный |
| P0-β | T4, T5, T6, T9 (api.py — последовательно или одним агентом), T7, T8 | pytest + repro-кейсы §1 |
| P0-γ | T11, T13 | корпус §1.2–1.3 зелёный/xfail-помечен |
| P1 | T14 → (T15, T16, T17, T18, T19, T20, T21 частично параллельно; T15/T16/T17 сильно связаны — один исполнитель) | fuzz-категории: 0 отказов на канонических ладах |
| P2 | T22, T23, T24, T25 | CI зелёный, property-тесты, доки честные |

Ориентировочно: P0 — 1–2 дня роем, P1 — 3–5 дней, P2 — 1–2 недели (совпадает с оценкой отчёта §6).

## Критерии готовности всего плана (Definition of Done)

1. Все repro-кейсы REPORT §1.2–1.16 дают корректный результат (решение или структурированная диагностика — никогда generic-заглушку).
2. 108 решений из `quality_audit.json` через новый grader: ни одного «5» на унисонах/неполных трезвучиях.
3. `C5-B4-A4-G4`, нисходящая гамма C-dur, natural/melodic minor — гармонизуются.
4. API == ядро на любом входе (детерминизм сохранён — fuzz.md «не подтвердилось» #1 не регрессировать).
5. MusicXML/MIDI: такты полны, длительности из кандидата, открывается в MuseScore/OSMD.
6. Фронт: отказ → чистый экран + inline-диагностика; гонки и утечки AudioContext отсутствуют.
7. `pytest` + property-тесты + CI зелёные; README/доки не содержат ни одного непроверенного заявления.

## Артефакты-ссылки

- Карта находок: [REPORT.md §2](REPORT.md) (номера #1–#64 использованы в заголовках задач).
- Доказательства: `.redteam/evidence/*.json`, repro-скрипты `.redteam/scratch/`.
- Канон и источники: [theory-research.md](theory-research.md), [REPORT.md §11](REPORT.md).
