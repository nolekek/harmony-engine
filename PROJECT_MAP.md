# PROJECT_MAP — карта проекта для ИИ

**Проект:** `D:\aitraining` — «Бригадное ядро гармонизации» (SATB-гармонизация по Способину/Дубовскому): Python-ядро + FastAPI + React SPA + pywebview-десктоп.
**Дата сборки карты:** 2026-11-14 · **статусные разделы актуализированы:** 2026-11-16

> **Оперативный документ проекта — [.redteam/HANDOFF.md](.redteam/HANDOFF.md)** (полный текст — ниже в этой карте).
> Он — источник истины по статусу волн, коммитам, дефектам и счётчикам. Эта карта — структурная навигация
> для входа в кодовую базу; при расхождении приоритет у `HANDOFF.md` и реальных прогонов, не у таблиц.
>
> Канонические документы 2026-11-16: [ARCHITECTURE.md](ARCHITECTURE.md),
> [SPECIFICATION.md](SPECIFICATION.md), [DECISIONS.md](DECISIONS.md), [KNOWN_ISSUES.md](KNOWN_ISSUES.md),
> [TASK_LOG.md](TASK_LOG.md). Встроенное ниже тело Repomix остаётся историческим снапшотом и не заменяет
> эти документы.

---

## Инструмент и команда генерации

- **Инструмент:** [repomix](https://repomix.com) через `npx -y repomix` (Node `v26.13.0`, npx `11.20.0`).
- **Режим:** `--compress` — сигнатурный уровень (Tree-sitter): сохраняются объявления классов/функций/интерфейсов,
  тела свёрнуты; блоки кода разделены маркером `⋮----`. Плюс `--style markdown`.
- **Команда (выполнена из `D:\aitraining`, exit code 0, 89 файлов / 109 988 токенов / 351 789 символов):**

```powershell
npx -y repomix --compress --style markdown `
  --include "src/**,backend/**,frontend/src/**,desktop/**,docs/**,scripts/**,pyproject.toml,README.md,.redteam/HANDOFF.md,.redteam/AUDIT_2026-11-13.md" `
  --ignore ".venv,node_modules,dist,build,.git,*.log,.redteam/scratch,.redteam/evidence,.research,.playwright-mcp,frontend/dist" `
  -o PROJECT_MAP.md
```

- **Включено:** `src/**`, `backend/**`, `frontend/src/**`, `desktop/**`, `docs/**`, `scripts/**`,
  `pyproject.toml`, `README.md`, `.redteam/HANDOFF.md`, `.redteam/AUDIT_2026-11-13.md`.
- **Исключено и почему:** `.venv`, `node_modules`, `dist`, `build`, `.git` — артефакты/окружение, не код;
  `frontend/dist` — собранный бандл; `*.log` (`hunt.log`, `hunt2.log`) — логи охот; `.redteam/scratch`,
  `.redteam/evidence`, `.research`, `.playwright-mcp` — рабочие материалы, зонды и снапшоты браузера;
  `tests/**` — тесты вне ТЗ на карту (перечислены в «Гейтах» и в `README.md`);
  `desktop.spec`, `run_app.py`, `uv.lock`, `.github/`, `models/`, `output/` — не входили в `--include`.
- **Размер:** ~386 КБ — меньше лимита 2.5 МБ, перегенерация без `scripts/` не понадобилась.

---

## Структура проекта

| Путь | Назначение |
|---|---|
| `src/harmony/core/` | доменные типы и музыкальная математика: `pitch.py`, `key.py`, `chord.py`, `voicing.py`, `metric.py`, `modulation.py`, `types.py` |
| `src/harmony/rules/` | валидаторы правил brigada: `engine.py` (ядро проверки), `voice_leading.py`, `chromatic.py`, `doubling.py`, `spacing.py`, `resolutions.py`, `non_chord_tones.py` |
| `src/harmony/solver/` | поиск гармонизации: `viterbi.py` (динамическое программирование по состояниям), `state_generator.py` |
| `src/harmony/syntax/` | `grammar.py` — синтаксис/грамматика формы мелодии (источник whitelist аккордов) |
| `src/harmony/export/` | `midi.py`, `musicxml.py`, `ascii.py`, `utils.py` — экспорт результата |
| `src/harmony/ml/` | `model.py` — ML-скоринг/обучение (опциональный слой) |
| `src/harmony/pipeline.py`, `cli.py`, `__main__.py` | сквозной оркестратор ядра + CLI REPL |
| `backend/` | REST-слой: `main.py` (app, middleware, CORS, SPA-статика), `api.py` (маршруты `/api`), `service.py` (LRU+TTL кэш гармонизации), `grader.py`, `importers.py`, `exporters.py`, `key_detector.py` |
| `frontend/src/` | React + TypeScript (Vite): `main.tsx`/`App.tsx`, `components/` (melody, grader, layout, ui-атомы), `hooks/useHarmonizer.ts`, `audio/` (synth, midiInput), `types/harmony.ts` |
| `desktop/` | pywebview-обёртка: `app.py`, `instance.py` (защита от второго экземпляра), `logging_config.py`, `__main__.py`; онбординг-сборка через корневой `desktop.spec` (PyInstaller) |
| `tests/` | pytest-сьют (вне карты): API/ядро/солвер/правила/экспорт/regression redteam |
| `docs/` | `BRIGADE_RULES.md` (правила + раздел «Переченье»), `brigade_rules.json` (каталог severity/penalty), `MATH_MODEL.md` |
| `scripts/` | дев-инструменты: `grammar_metrics.py`, `benchmark_harmonize.py`, `audit_chromatic.py`, `audit_harmonic_rhythm.py`, `generate_dataset.py`, `stress_test_harness.py`, `test_e2e_api.py` |
| `.redteam/` | `HANDOFF.md` (оперативный док), `AUDIT_2026-11-13.md` (аудит оркестратора + план волн) |

---

## Точки входа

- **Web (основной):** `python run_app.py` — pre-flight проверки порта, uvicorn `backend.main:app`, `http://127.0.0.1:8000`, автооткрытие браузера (флаги `--port/--host/--no-browser/--reload`, env `PORT`/`HOST`, `FRONTEND_DIST_DIR`).
- **Backend-приложение:** `backend/main.py` → `app = FastAPI(title="Brigade Harmony Engine Web API", version="1.0.0")`; middleware `X-Request-ID`, лимит тела 2 МБ (413), глобальный обработчик исключений → JSON 500 с `error_id`, CORS на `:8000`/`:5173`, `include_router(api_router)`, монтирование `frontend/dist`.
- **CLI ядра:** `python -m harmony` → `src/harmony/__main__.py` / `src/harmony/cli.py`.
- **Десктоп:** `python -m desktop` → `desktop/__main__.py` → `desktop/app.py` (pywebview поверх того же FastAPI).
- **Frontend:** `pnpm dev` (Vite `:5173`), точка `frontend/src/main.tsx`; прод-сборка `pnpm build` (`tsc -b && vite build`).
- **Конфигурация/зависимости:** `pyproject.toml` (setuptools, `packages where=["src"]`, extras `dev`/`desktop`), `frontend/package.json`.

---

## Ключевые контракты — 9 API-маршрутов (префикс `/api`)

| # | Маршрут | Метод | Назначение |
|---|---|---|---|
| 1 | `/api/keys` | GET | список доступных тональностей |
| 2 | `/api/detect-key` | POST | определение тональности по мелодии |
| 3 | `/api/parse-text` | POST | парсинг текстового ввода мелодии (ноты + ритм) |
| 4 | `/api/harmonize` | POST | **главный контракт:** гармонизация SATB → `HarmonizationResult` (голоса, аккорды, diagnostics, `relaxed_rule_ids`, `error.dominant_blockers`) |
| 5 | `/api/grade` | POST | проверка/градация готовой гармонизации по правилам |
| 6 | `/api/import-file` | POST | импорт файла (MIDI / MusicXML / текст); 400 на невалидном входе |
| 7 | `/api/export/midi` | POST | экспорт результата в MIDI (бинарный ответ) |
| 8 | `/api/export/musicxml` | POST | экспорт результата в MusicXML |
| 9 | `/api/health` | GET | health-проба сервиса (объявлен в `backend/main.py`) |

Служебные (не считаются контрактами): `ANY /api/{full_path}` → JSON 404 для неизвестных API-путей;
`GET /{full_path}` → раздача SPA; `GET /` → placeholder, если `frontend/dist` не собран.
Сигнатуры и Pydantic-модели — в теле карты: `## File: backend/api.py`.

---

## Гейты приёмки

| Гейт | Команда | Ожидаемый результат |
|---|---|---|
| Тесты | `pytest -q` | **901 passed** (0 failed / 0 skipped / 0 errors) — живой прогон QA 16.11, ~383 с |
| Линт | `ruff check .` | **0 ошибок** (гейт с 13.11; `line-length=120`, `select=["E","F","W"]`, `ignore=["E501"]`, `extend-exclude=[".redteam/scratch"]`, `scripts/*` E402) |
| Frontend-сборка | `pnpm build` | успех `tsc -b && vite build` (без ошибок типов) |
| Десктоп-смоук | запуск PyInstaller-exe | `health` 200, SPA 200, `NO_ORPHANS` |

Значения гейтов актуализированы 2026-11-16 по живому QA-прогону: `pytest`, `ruff` и сборка frontend
подтверждены; десктоп-смоук в этой волне не перезапускался. Встроенное ниже тело карты остаётся
историческим снапшотом от 2026-11-14 и может содержать прежние счётчики тестов.

---

## Как читать тело карты ниже

`# Repository Structure` — дерево; далее по одному блоку `## File: <путь>` на файл.
В `--compress`-режиме внутри файлов `⋮----` означает пропущенное тело между сигнатурами:
для деталей открывайте оригинал по пути из заголовка блока.

---

This file is a merged representation of a subset of the codebase, containing specifically included files and files not matching ignore patterns, combined into a single document by Repomix.
The content has been processed where content has been compressed (code blocks are separated by ⋮---- delimiter).

# File Summary

## Purpose
This file contains a packed representation of a subset of the repository's contents that is considered the most important context.
It is designed to be easily consumable by AI systems for analysis, code review,
or other automated processes.

## File Format
The content is organized as follows:
1. This summary section
2. Repository information
3. Directory structure
4. Repository files (if enabled)
5. Multiple file entries, each consisting of:
  a. A header with the file path (## File: path/to/file)
  b. The full contents of the file in a code block

## Usage Guidelines
- This file should be treated as read-only. Any changes should be made to the
  original repository files, not this packed version.
- When processing this file, use the file path to distinguish
  between different files in the repository.
- Be aware that this file may contain sensitive information. Handle it with
  the same level of security as you would the original repository.

## Notes
- Some files may have been excluded based on .gitignore rules and Repomix's configuration
- Binary files are not included in this packed representation. Please refer to the Repository Structure section for a complete list of file paths, including binary files
- Only files matching these patterns are included: src/**, backend/**, frontend/src/**, desktop/**, docs/**, scripts/**, pyproject.toml, README.md, .redteam/HANDOFF.md, .redteam/AUDIT_2026-11-13.md
- Files matching these patterns are excluded: .venv, node_modules, dist, build, .git, *.log, .redteam/scratch, .redteam/evidence, .research, .playwright-mcp, frontend/dist
- Files matching patterns in .gitignore are excluded
- Files matching default ignore patterns are excluded
- Content has been compressed - code blocks are separated by ⋮---- delimiter
- Files are sorted by Git change count (files with more changes are at the bottom)

# Directory Structure
````
.redteam/
  AUDIT_2026-11-13.md
  HANDOFF.md
backend/
  api.py
  exporters.py
  grader.py
  importers.py
  key_detector.py
  main.py
  service.py
desktop/
  __init__.py
  __main__.py
  app.py
  instance.py
  logging_config.py
docs/
  brigade_rules.json
  BRIGADE_RULES.md
  MATH_MODEL.md
frontend/
  src/
    assets/
      hero.png
      react.svg
      vite.svg
    audio/
      midiInput.ts
      synth.ts
    components/
      grader/
        GraderScoreMatrix.tsx
        GraderViolationsList.tsx
        sampleTests.ts
      layout/
        Header.tsx
      melody/
        MelodyFileUpload.tsx
        MidiInputBar.tsx
        NoteList.tsx
        PianoKeyboard.tsx
      ui/
        Badge.tsx
        Button.tsx
        Card.tsx
        Input.tsx
        Select.tsx
        Tabs.tsx
      AudioControls.tsx
      ControlPanel.tsx
      ExportBar.tsx
      GraderPanel.tsx
      MelodyInput.tsx
      ScoreDisplay.tsx
    hooks/
      useHarmonizer.ts
      useTheme.ts
    types/
      harmony.ts
    utils/
      durationUtils.ts
    App.tsx
    index.css
    main.tsx
scripts/
  audit_chromatic.py
  audit_harmonic_rhythm.py
  benchmark_harmonize.py
  generate_dataset.py
  grammar_metrics.py
  stress_test_harness.py
  test_e2e_api.py
src/
  harmony/
    core/
      __init__.py
      chord.py
      key.py
      metric.py
      modulation.py
      pitch.py
      types.py
      voicing.py
    export/
      __init__.py
      ascii.py
      midi.py
      musicxml.py
      utils.py
    ml/
      __init__.py
      model.py
    rules/
      __init__.py
      chromatic.py
      doubling.py
      engine.py
      non_chord_tones.py
      resolutions.py
      spacing.py
      voice_leading.py
    solver/
      __init__.py
      state_generator.py
      viterbi.py
    syntax/
      __init__.py
      grammar.py
    __init__.py
    __main__.py
    cli.py
    pipeline.py
pyproject.toml
README.md
````

# Files

## File: .redteam/AUDIT_2026-11-13.md
````markdown
# АУДИТ ПРОЕКТА — 2026-11-13 (оркестратор build)

> Цель: точка отсчёта для починки. Все проверки — реальные команды с exit code (QA-агент),
> разведка — read-only агенты. Ключевые цифры перепроверены живым прогоном, а не доками
> (HANDOFF.md сам предупреждает, что дважды врал).
> Связанные доки: [HANDOFF.md](HANDOFF.md), [WAVE2_WIP.md](WAVE2_WIP.md), [REMEDIATION_PLAN.md](REMEDIATION_PLAN.md).

## 1. Вердикт

**master (`231f4d5`) функционально зелёный.** Ядро, backend, frontend и CLI работают, 848 тестов проходят.
«Сломан» не master, а незавершённая работа и гигиена:

1. **Главный незавершённый кусок — Wave 2 (редизайн UI):** ветка `wip/wave2-ui-redesign` (`352b499`), билд красный — 12 ошибок TS (точный список: WAVE2_WIP.md §3). HANDOFF §8: «начинать отсюда».
2. **Гигиена:** ruff — 472 ошибки (204 в коде проекта, 268 в `.redteam/scratch`), устаревший README, мусор в корне.
3. **Два открытых дефекта ядра:** #6 (мёртвый код RuleEngine), #8 (chromatic5 `[60,63,64,62,60]` → FALSE_RELATION_PERECHENIE).
4. **Архитектурный долг:** выживаемость планов 21.3% (0–45% по корпусу) — UI держится на replanning; хроматика — 60% отказов fuzz; 64-нотные мелодии не гармонизуются (timeout 4 с).

## 2. Проверенные проверки (QA, реальные команды, 2026-11-13)

Интерпретатор: `D:\aitraining\.venv\Scripts\python.exe`, Python 3.14.0.

| # | Проверка | Команда | Exit | Статус | Детали |
|---|---|---|---|---|---|
| 1 | Окружение | `python --version` + импорт fastapi/uvicorn/pydantic/mido/pytest | 0 | PASSED | `.venv` был ПУСТОЙ → восстановлен `uv sync --extra dev --extra desktop` (правки кода нет) |
| 2 | Тесты | `python -m pytest -q` | 0 | **PASSED** | **848 passed, 0 failed, 0 skipped**, 103.1 с; 1 warning (StarletteDeprecation) |
| 3 | Линт | `python -m ruff check .` | 1 | **FAILED** | 472 ошибки: 204 в коде проекта, 268 в `.redteam/scratch`; 317 автофиксабельны |
| 4 | Backend smoke | `python -c "from backend.main import app"` | 0 | PASSED | 9 routes |
| 5 | Frontend build (master) | `npm run build` (`tsc -b && vite build`) | 0 | PASSED | node v26.13.0; 2069 модулей; warning: osmd-чанк 1438 КБ > 500 КБ |
| 6 | CLI smoke | `python -m src.harmony.cli --melody "64,65,67,62,60" --tonic C --mode Major` | 0 | PASSED | корректный SATB: T–S6–D7–D65–T |

Ruff топ правил: F401 ×237 (мёртвые импорты), W293 ×73, E402 ×49, E702 ×40, F841 ×23.
Топ файлов проекта: `src/harmony/core/key.py` (10), `backend/api.py` (9), `tests/test_backend_exhaustive.py` (8), `tests/test_backend_api.py` (8).

## 3. Хендлеры API (backend/api.py, префикс /api)

| Метод | Путь | Request | Response | Ядро |
|---|---|---|---|---|
| GET | /api/keys | — | 24 тональности | статический CANONICAL_KEYS (api.py:259) |
| POST | /api/detect-key | `list[MelodyNoteItem]` | tonic/mode/fifths | key_detector (Krumhansl-Schmuckler) (api.py:265) |
| POST | /api/parse-text | {text,key,time_signature} | list[dict] | importers.parse_text_melody (api.py:273) |
| POST | /api/harmonize | HarmonizeRequest (melody 1..128, key, флаги) | top-3 candidates + musicxml + ascii | threadpool → HarmonizationService → grammar+Viterbi+fallback (api.py:284, service.py:138) |
| POST | /api/grade | GradeRequest (voicings, chords whitelist) | GraderReport + musicxml | grader.grade_satb_solution (api.py:296) |
| POST | /api/import-file | multipart ИЛИ JSON base64/xml | melody+voicings+key | parse_musicxml_content / parse_midi_file (api.py:345) |
| POST | /api/export/midi | {voicings,bpm,...} | binary audio/midi | export_to_midi (api.py:428) |
| POST | /api/export/musicxml | {voicings,chords,key,...} | MusicXML | build_colored_musicxml (api.py:451) |
| GET | /api/health | — | status/service/version | main.py:130 |

Middleware: лимит тела 2 МБ (413), request-id, маппинг 422→400 для пустой мелодии, глобальный 500 с error_id, CORS 8000/5173 (main.py:40-124). SPA-fallback отдаёт `frontend/dist` (main.py:167-190).

**Синхрон фронт↔бэк:** все 8 вызовов фронта (App.tsx:118,141,307; MelodyInput.tsx:245,271; GraderPanel.tsx:132,191; ExportBar.tsx:30,62) существуют на бэке, поля совпадают. Расхождений контрактов нет.

**Находки по хендлерам:**
- `api.py:345-383` — import-file: параметры `file`/`json_body` объявлены, но парсинг ручной через `request.json()/form()`; `binascii.Error`/`JSONDecodeError`/ошибки XML не обработаны → **500 вместо 400**. OpenAPI-схема расходится с фактом.
- `api.py:291` — проверка `not req.melody` недостижима (`min_length=1` в схеме, api.py:172).
- `service.py:344` — `timeout_sec` читается из запроса, но поля нет в `HarmonizeRequest` → вечно 4.0 (мёртвая настройка).
- `service.py:26,244-248,493` — глобальный `_SERVICE_REQUEST_CACHE` без eviction/TTL, хранит полные MusicXML → **утечка памяти** (критично для desktop-долгожителя).
- `api.py:85-126` — `VALID_CHORD_FUNCTIONS`: ручная копия словаря грамматики; риск расхождения с `grammar.ALL_FUNCTIONS` → ложные 422 на grade/export.
- Мёртвые импорты: api.py:8,9,14,15-17,22; service.py:14.

## 4. Находки по приоритетам

### Blocker (для плана починки)
| ID | Находка | Где |
|---|---|---|
| B1 | Wave 2 не завершена: красный TS-билд, 12 ошибок (Sparkles unused; 4 несуществующих метода WebMidiManager в MidiInputBar; AudioEngine.playSingleTone не существует ×2; END_PITCH не определён ×2; CardProps.title конфликт) | ветка `wip/wave2-ui-redesign`; список: WAVE2_WIP.md:44-60 |
| B2 | `dist/HarmonyEngine/HarmonyEngine.exe` собран из СТАРОГО фронта — после Wave 2 обязательна пересборка | WAVE2_WIP.md:14; desktop.spec |

### Major
| ID | Находка | Где |
|---|---|---|
| M1 | import-file: необработанные исключения → 500 | api.py:345-383 |
| M2 | Неограниченный кэш сервиса → рост памяти | service.py:26 |
| M3 | Активный monkey-patch guard чужих модулей на import (сейчас no-op, аналог закрытого дефекта #3) | src/harmony/pipeline.py:23-35 |
| M4 | Дефект #8 OPEN: `[60,63,64,62,60]` → отказ FALSE_RELATION_PERECHENIE (тенор E3 vs Eb4) | HANDOFF.md:173; chromatic.py |
| M5 | 64-нотная мелодия не гармонизуется (success=False), timeout 4 с | hunt.log:1897, hunt2.log:1897; service.py:344 |
| M6 | План-генератор слаб: survival 21.3% (0–45%), UI держится на bounded replanning; хроматика 60% отказов fuzz — главный арх-долг (K-best/CP-SAT — P3) | HANDOFF §4; REMEDIATION_PLAN.md:58 |
| M7 | ruff: 204 ошибки в коде проекта (317/472 автофикс) | pyproject.toml [tool.ruff] |
| M8 | Дефект #6 OPEN: мёртвый/декоративный код RuleEngine; каталог brigade_rules.json грузится с `except: pass`, часть правил захардкожена | rules/engine.py:175-183,305,376; HANDOFF.md:171 |

### Minor
| ID | Находка | Где |
|---|---|---|
| m1 | `/api/parse-text` с фронта шлётся без `time_signature` → выбранный в UI размер игнорируется (дефолт 4/4) | MelodyInput.tsx:248-251; api.py:229-230 |
| m2 | UI не отправляет `allow_adjacent_unisons`/`relax_hard_gates` — relaxed-режимы недоступны из GUI | App.tsx:145-157; api.py:178-179 |
| m3 | Дубли доменных типов Key/Voicing (types.py vs key.py/voicing.py), разный экспорт core/__init__ vs импорты backend | src/harmony/core/ |
| m4 | Packaging: pyproject пакет `harmony` (where=src), а импорты `src.harmony.*` — установленный wheel бесполезен | pyproject.toml:30-31 |
| m5 | README устарел: «645 passed на redteam-p2» (ветка удалена, влита FF); реально 848 на master | README.md:294-303 |
| m6 | Мусор: `Microsoft/` (кэш PowerShell), hunt.log/hunt2.log в корне | корень репы |
| m7 | desktop: двойной вызов on_closed (event + finally), os._exit(0) при зависании | desktop/app.py:230-238 |
| m8 | ml/model.py (n-gram prior) нигде не подключён — экспериментальная заглушка | src/harmony/ml/ |
| m9 | Окружения расходятся: локально Node 26/pnpm 12, CI node 20; .venv восстановлен только сегодня | .github/workflows/ci.yml |
| m10 | UI-каталог тональностей: нет natural/melodic minor; grader не мапит римские I/IV/V (P3) | REMEDIATION_PLAN.md:64-65 |
| m11 | thread-local глобальное состояние `set_unisons_allowed` в солвере | viterbi.py:72; spacing.py |
| m12 | osmd-чанк 1438 КБ (warning сборки) — уже вынесен в lazy-чанк, приемлемо | frontend/vite.config.ts |

## 5. Разрешённые противоречия разведки

- **frontend/dist:** один агент доложил «отсутствует», второй — «на месте». Факт: **существует**, пересобран QA 13.11 19:30 из master (`npm run build` exit 0). Не блокер для master; для exe нужна пересборка после Wave 2 (B2).
- **.venv:** HANDOFF фиксировал «битый, только системный Python». Факт: был пустой, **восстановлен** `uv sync --extra dev --extra desktop` (Python 3.14.0). Код не менялся.
- **git status:** проверено оркестратором — **дерево чистое**, master = origin/master = `231f4d5`; ветки: master, wip/wave2-ui-redesign (локально и на origin).
- **hunt.log vs hunt2.log:** первая охота — 148 проблем (fifth_missing), вторая после фиксов — **0**. Артефакты: `.redteam/scratch/lead/hunt_lead_findings.json`, `hunt_lead.py` — готовый регрессионный гейт.
- **Тесты:** 63 файла, skip/xfail нет. 848 passed подтверждено живым прогоном (не доками).

## 6. План починки (рекомендуемый порядок)

> Регламент: правки в ветках; не редактировать код параллельно с pytest (ложные фейлы, HANDOFF §7);
> после каждой волны — верификация QA реальными командами; гейт master: `pytest -q` → 848 passed, exit 0.

### Волна 1 — Добивка Wave 2 UI (главная, HANDOFF §8.1)
Ветка `wip/wave2-ui-redesign`. Шаги:
1. Подтвердить красный билд: `pnpm --dir frontend install && pnpm --dir frontend build`.
2. Починить 12 TS-ошибок по WAVE2_WIP.md §3 (сверить реальные API `audio/midiInput.ts` и `audio/synth.ts`, добавить END_PITCH, `Omit<...,"title">` в Card, убрать Sparkles).
3. Фазы 3.5–5: ui/Input,Select,Tabs + перевод ControlPanel/ExportBar/AudioControls; единый скролл левой панели 380–440px; ScoreDisplay без blanket-invert (цвета ошибок #ef4444 не трогать); сохранить lazy OSMD-чанк.
4. Приёмка (WAVE2_WIP.md §4-5): lint 0/0, build exit 0, все 8 API на месте, zero-regression чек-лист (MIDI, пианино, топ-3, экспорт, grader), скриншоты 3 экранов, `pytest -q` 848 (бэкенд не трогать).
5. Пересборка exe: `python -m PyInstaller desktop.spec --noconfirm` + smoke-запуск.
6. Ревью критика диффа → merge в master → обновить handoff.

### Волна 2 — Гигиена master (быстрая, низкий риск)
1. `ruff check --fix` (317 авто) + ручной остаток (~155); `extend-exclude = [".redteam/scratch"]` в pyproject.
2. Удалить мёртвые импорты (api.py, service.py и пр.), удалить `Microsoft/`, добавить hunt*.log в .gitignore.
3. Обновить README: 848 тестов, master, актуальные команды (uv sync).
4. Гейт: pytest 848 + ruff 0.

### Волна 3 — Надёжность backend
1. import-file: валидация base64/JSON/XML → 400 с detail вместо 500; привести OpenAPI-схему к факту.
2. `_SERVICE_REQUEST_CACHE`: LRU/TTL с eviction (или убрать).
3. `timeout_sec`: добавить в HarmonizeRequest или выкинуть мёртвый код.
4. `VALID_CHORD_FUNCTIONS` генерировать из `grammar.ALL_FUNCTIONS` (сверка + тест).
5. Удалить monkey-patch guard pipeline.py:23-35 (+ регресс-тест на отсутствие патча, по образцу P1).
6. minor: parse-text time_signature с фронта (m1), relaxed-флаги в UI (m2) — можно совместить с Волной 1.
7. Гейт: pytest 848 + новые тесты на 400/кэш/whitelist.

### Волна 4 — Ядро (отдельные сессии, выше риск)
1. Дефект #8: раз FALSE_RELATION_PERECHENIE для `[60,63,64,62,60]` (тенор E3 vs Eb4) — mode-aware разбор.
2. Дефект #6: вычистить мёртвый код RuleEngine, перенести захардкоженные правила в brigade_rules.json.
3. Перф-волна: профилирование генератора планов/parse_chord_symbol, 64-нотные мелодии (M5), возврат порогов 1200/3000 мс.
4. P3: K-best/диверсификация луча (главный драйвер survival), хроматический словарь (N/bVI), survival-метрики в CI.
Гейт: pytest + hunt_lead.py (PROBLEMS: 0) + grammar_metrics.py.

## 7. Окружение (актуальное на 13.11)

- Python 3.14.0: `.venv` восстановлен (`uv sync --extra dev --extra desktop`); проект на uv (uv.lock).
- Node v26.13.0, npm 11.20.0, pnpm 12 (pnpm-lock.yaml в репе; CI — node 20, расхождение).
- Запуск: `python run_app.py` (127.0.0.1:8000), `python -m desktop`, CLI `python -m src.harmony.cli`.
- `$env:PYTHONIOENCODING='utf-8'` для скриптов с русским выводом; run_app убивать строго по PID.
````

## File: desktop/__init__.py
````python
"""
Desktop shell package for Harmony Engine.
Provides native Windows EdgeChromium/WebView2 desktop experience.
"""
⋮----
__all__ = ["run_desktop", "main"]
````

## File: desktop/__main__.py
````python
"""
Launcher for python -m desktop
"""
````

## File: desktop/app.py
````python
"""
Main entry point and lifecycle manager for Harmony Engine Desktop.
Runs FastAPI/Uvicorn in a daemon thread and hosts the React SPA via pywebview (EdgeChromium).
"""
⋮----
WINDOW_TITLE = "Brigade Harmony Engine"
DEFAULT_WIDTH = 1440
DEFAULT_HEIGHT = 900
MIN_WIDTH = 1100
MIN_HEIGHT = 700
⋮----
logger = logging.getLogger("desktop.app")
⋮----
def apply_dpi_awareness() -> None
⋮----
"""Sets per-monitor DPI awareness (V2) to prevent blurry rendering on high-DPI displays."""
⋮----
def check_webview2_runtime() -> bool
⋮----
"""Verifies that Microsoft Edge WebView2 (Chromium) is available."""
⋮----
# Fallback path check
edge_wv_path = r"C:\Program Files (x86)\Microsoft\EdgeWebView\Application"
⋮----
def show_missing_webview2_dialog() -> None
⋮----
"""Shows a native Win32 error dialog if WebView2 Evergreen Runtime is missing."""
msg = (
title = "Harmony Engine — Ошибка запуска"
⋮----
ctypes.windll.user32.MessageBoxW(0, msg, title, 0x10 | 0x0)  # MB_ICONERROR | MB_OK
⋮----
def find_free_port() -> int
⋮----
"""Allocates a guaranteed available ephemeral TCP port on localhost."""
⋮----
def wait_for_health_check(url: str, timeout_sec: float = 6.0) -> bool
⋮----
"""Polls /api/health until the FastAPI backend is ready to serve requests."""
start = time.perf_counter()
health_url = f"{url}/api/health"
⋮----
def get_window_state_file() -> Path
⋮----
def load_window_geometry() -> tuple[int, int, int | None, int | None]
⋮----
"""Loads saved window dimensions and coordinates if available."""
f = get_window_state_file()
⋮----
data = json.loads(f.read_text(encoding="utf-8"))
w = max(MIN_WIDTH, int(data.get("width", DEFAULT_WIDTH)))
h = max(MIN_HEIGHT, int(data.get("height", DEFAULT_HEIGHT)))
x = data.get("x")
y = data.get("y")
⋮----
def save_window_geometry(window: webview.Window | None) -> None
⋮----
"""Persists current window dimensions and screen coordinates."""
⋮----
data = {
⋮----
def focus_window(window: webview.Window | None) -> None
⋮----
"""
    Brings the main desktop window to the foreground using pure Win32 calls.

    Must NOT call pywebview window methods here: this runs on the IPC listener
    thread, and pywebview window APIs are not thread-safe on the WinForms/Edge
    backend (calling them from a foreign thread destroys the window and kills
    the app when a duplicate instance is launched).
    """
⋮----
hwnd = ctypes.windll.user32.FindWindowW(None, WINDOW_TITLE)
⋮----
ctypes.windll.user32.ShowWindow(hwnd, 9)  # SW_RESTORE = 9
⋮----
def run_desktop() -> None
⋮----
"""Launches the Harmony Engine Desktop application."""
⋮----
http_port = find_free_port()
base_url = f"http://127.0.0.1:{http_port}"
⋮----
# Active window reference for IPC focus callback
window_ref: list[webview.Window | None] = [None]
⋮----
def _focus_cb()
⋮----
# Enforce single instance
is_primary = acquire_single_instance(http_port=http_port, focus_callback=_focus_cb)
⋮----
# Configure and start Uvicorn in background daemon thread
uvicorn_config = uvicorn.Config(
server = uvicorn.Server(uvicorn_config)
server_thread = threading.Thread(
⋮----
# Wait for backend readiness
⋮----
create_kwargs = {
⋮----
window = webview.create_window(**create_kwargs)
⋮----
def on_closed()
⋮----
# Signal Uvicorn to exit
⋮----
# Start pywebview GUI event loop (blocks main thread until window closed)
⋮----
def main() -> None
````

## File: desktop/logging_config.py
````python
"""
Logging configuration for Harmony Engine Desktop.
Manages log directory in %LOCALAPPDATA%\\HarmonyEngine\\logs and configures
rotating file handlers with stdout/stderr redirection for windowed execution.
"""
⋮----
def get_app_data_dir() -> Path
⋮----
"""Returns the base data directory in %LOCALAPPDATA%\\HarmonyEngine."""
local_app_data = os.environ.get("LOCALAPPDATA")
⋮----
base = Path(local_app_data)
⋮----
base = Path.home() / "AppData" / "Local"
app_dir = base / "HarmonyEngine"
⋮----
def setup_desktop_logging() -> tuple[Path, logging.Logger]
⋮----
"""
    Initializes rotating file logging in %LOCALAPPDATA%\\HarmonyEngine\\logs\\desktop.log.
    Safely redirects sys.stdout and sys.stderr when running in windowed (console=False) mode.
    """
app_dir = get_app_data_dir()
logs_dir = app_dir / "logs"
⋮----
log_file = logs_dir / "desktop.log"
⋮----
# In PyInstaller windowed mode (console=False), sys.stdout and sys.stderr are None.
# Unhandled prints would crash with AttributeError. Redirect to desktop.log.
⋮----
logger = logging.getLogger("desktop")
⋮----
# Avoid duplicate handlers on re-initialization
⋮----
handler = RotatingFileHandler(
⋮----
maxBytes=10 * 1024 * 1024,  # 10 MB
⋮----
formatter = logging.Formatter(
````

## File: frontend/src/assets/react.svg
````xml
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" aria-hidden="true" role="img" class="iconify iconify--logos" width="35.93" height="32" preserveAspectRatio="xMidYMid meet" viewBox="0 0 256 228"><path fill="#00D8FF" d="M210.483 73.824a171.49 171.49 0 0 0-8.24-2.597c.465-1.9.893-3.777 1.273-5.621c6.238-30.281 2.16-54.676-11.769-62.708c-13.355-7.7-35.196.329-57.254 19.526a171.23 171.23 0 0 0-6.375 5.848a155.866 155.866 0 0 0-4.241-3.917C100.759 3.829 77.587-4.822 63.673 3.233C50.33 10.957 46.379 33.89 51.995 62.588a170.974 170.974 0 0 0 1.892 8.48c-3.28.932-6.445 1.924-9.474 2.98C17.309 83.498 0 98.307 0 113.668c0 15.865 18.582 31.778 46.812 41.427a145.52 145.52 0 0 0 6.921 2.165a167.467 167.467 0 0 0-2.01 9.138c-5.354 28.2-1.173 50.591 12.134 58.266c13.744 7.926 36.812-.22 59.273-19.855a145.567 145.567 0 0 0 5.342-4.923a168.064 168.064 0 0 0 6.92 6.314c21.758 18.722 43.246 26.282 56.54 18.586c13.731-7.949 18.194-32.003 12.4-61.268a145.016 145.016 0 0 0-1.535-6.842c1.62-.48 3.21-.974 4.76-1.488c29.348-9.723 48.443-25.443 48.443-41.52c0-15.417-17.868-30.326-45.517-39.844Zm-6.365 70.984c-1.4.463-2.836.91-4.3 1.345c-3.24-10.257-7.612-21.163-12.963-32.432c5.106-11 9.31-21.767 12.459-31.957c2.619.758 5.16 1.557 7.61 2.4c23.69 8.156 38.14 20.213 38.14 29.504c0 9.896-15.606 22.743-40.946 31.14Zm-10.514 20.834c2.562 12.94 2.927 24.64 1.23 33.787c-1.524 8.219-4.59 13.698-8.382 15.893c-8.067 4.67-25.32-1.4-43.927-17.412a156.726 156.726 0 0 1-6.437-5.87c7.214-7.889 14.423-17.06 21.459-27.246c12.376-1.098 24.068-2.894 34.671-5.345a134.17 134.17 0 0 1 1.386 6.193ZM87.276 214.515c-7.882 2.783-14.16 2.863-17.955.675c-8.075-4.657-11.432-22.636-6.853-46.752a156.923 156.923 0 0 1 1.869-8.499c10.486 2.32 22.093 3.988 34.498 4.994c7.084 9.967 14.501 19.128 21.976 27.15a134.668 134.668 0 0 1-4.877 4.492c-9.933 8.682-19.886 14.842-28.658 17.94ZM50.35 144.747c-12.483-4.267-22.792-9.812-29.858-15.863c-6.35-5.437-9.555-10.836-9.555-15.216c0-9.322 13.897-21.212 37.076-29.293c2.813-.98 5.757-1.905 8.812-2.773c3.204 10.42 7.406 21.315 12.477 32.332c-5.137 11.18-9.399 22.249-12.634 32.792a134.718 134.718 0 0 1-6.318-1.979Zm12.378-84.26c-4.811-24.587-1.616-43.134 6.425-47.789c8.564-4.958 27.502 2.111 47.463 19.835a144.318 144.318 0 0 1 3.841 3.545c-7.438 7.987-14.787 17.08-21.808 26.988c-12.04 1.116-23.565 2.908-34.161 5.309a160.342 160.342 0 0 1-1.76-7.887Zm110.427 27.268a347.8 347.8 0 0 0-7.785-12.803c8.168 1.033 15.994 2.404 23.343 4.08c-2.206 7.072-4.956 14.465-8.193 22.045a381.151 381.151 0 0 0-7.365-13.322Zm-45.032-43.861c5.044 5.465 10.096 11.566 15.065 18.186a322.04 322.04 0 0 0-30.257-.006c4.974-6.559 10.069-12.652 15.192-18.18ZM82.802 87.83a323.167 323.167 0 0 0-7.227 13.238c-3.184-7.553-5.909-14.98-8.134-22.152c7.304-1.634 15.093-2.97 23.209-3.984a321.524 321.524 0 0 0-7.848 12.897Zm8.081 65.352c-8.385-.936-16.291-2.203-23.593-3.793c2.26-7.3 5.045-14.885 8.298-22.6a321.187 321.187 0 0 0 7.257 13.246c2.594 4.48 5.28 8.868 8.038 13.147Zm37.542 31.03c-5.184-5.592-10.354-11.779-15.403-18.433c4.902.192 9.899.29 14.978.29c5.218 0 10.376-.117 15.453-.343c-4.985 6.774-10.018 12.97-15.028 18.486Zm52.198-57.817c3.422 7.8 6.306 15.345 8.596 22.52c-7.422 1.694-15.436 3.058-23.88 4.071a382.417 382.417 0 0 0 7.859-13.026a347.403 347.403 0 0 0 7.425-13.565Zm-16.898 8.101a358.557 358.557 0 0 1-12.281 19.815a329.4 329.4 0 0 1-23.444.823c-7.967 0-15.716-.248-23.178-.732a310.202 310.202 0 0 1-12.513-19.846h.001a307.41 307.41 0 0 1-10.923-20.627a310.278 310.278 0 0 1 10.89-20.637l-.001.001a307.318 307.318 0 0 1 12.413-19.761c7.613-.576 15.42-.876 23.31-.876H128c7.926 0 15.743.303 23.354.883a329.357 329.357 0 0 1 12.335 19.695a358.489 358.489 0 0 1 11.036 20.54a329.472 329.472 0 0 1-11 20.722Zm22.56-122.124c8.572 4.944 11.906 24.881 6.52 51.026c-.344 1.668-.73 3.367-1.15 5.09c-10.622-2.452-22.155-4.275-34.23-5.408c-7.034-10.017-14.323-19.124-21.64-27.008a160.789 160.789 0 0 1 5.888-5.4c18.9-16.447 36.564-22.941 44.612-18.3ZM128 90.808c12.625 0 22.86 10.235 22.86 22.86s-10.235 22.86-22.86 22.86s-22.86-10.235-22.86-22.86s10.235-22.86 22.86-22.86Z"></path></svg>
````

## File: frontend/src/assets/vite.svg
````xml
<svg xmlns="http://www.w3.org/2000/svg" width="77" height="47" fill="none" aria-labelledby="vite-logo-title" viewBox="0 0 77 47"><title id="vite-logo-title">Vite</title><style>.parenthesis{fill:#000}@media (prefers-color-scheme:dark){.parenthesis{fill:#fff}}</style><path fill="#9135ff" d="M40.151 45.71c-.663.844-2.02.374-2.02-.699V34.708a2.26 2.26 0 0 0-2.262-2.262H24.493c-.92 0-1.457-1.04-.92-1.788l7.479-10.471c1.07-1.498 0-3.578-1.842-3.578H15.443c-.92 0-1.456-1.04-.92-1.788l9.696-13.576c.213-.297.556-.474.92-.474h28.894c.92 0 1.456 1.04.92 1.788l-7.48 10.472c-1.07 1.497 0 3.578 1.842 3.578h11.376c.944 0 1.474 1.087.89 1.83L40.153 45.712z"/><mask id="a" width="48" height="47" x="14" y="0" maskUnits="userSpaceOnUse" style="mask-type:alpha"><path fill="#000" d="M40.047 45.71c-.663.843-2.02.374-2.02-.699V34.708a2.26 2.26 0 0 0-2.262-2.262H24.389c-.92 0-1.457-1.04-.92-1.788l7.479-10.472c1.07-1.497 0-3.578-1.842-3.578H15.34c-.92 0-1.456-1.04-.92-1.788l9.696-13.575c.213-.297.556-.474.92-.474H53.93c.92 0 1.456 1.04.92 1.788L47.37 13.03c-1.07 1.498 0 3.578 1.842 3.578h11.376c.944 0 1.474 1.088.89 1.831L40.049 45.712z"/></mask><g mask="url(#a)"><g filter="url(#b)"><ellipse cx="5.508" cy="14.704" fill="#eee6ff" rx="5.508" ry="14.704" transform="rotate(269.814 20.96 11.29)scale(-1 1)"/></g><g filter="url(#c)"><ellipse cx="10.399" cy="29.851" fill="#eee6ff" rx="10.399" ry="29.851" transform="rotate(89.814 -16.902 -8.275)scale(1 -1)"/></g><g filter="url(#d)"><ellipse cx="5.508" cy="30.487" fill="#8900ff" rx="5.508" ry="30.487" transform="rotate(89.814 -19.197 -7.127)scale(1 -1)"/></g><g filter="url(#e)"><ellipse cx="5.508" cy="30.599" fill="#8900ff" rx="5.508" ry="30.599" transform="rotate(89.814 -25.928 4.177)scale(1 -1)"/></g><g filter="url(#f)"><ellipse cx="5.508" cy="30.599" fill="#8900ff" rx="5.508" ry="30.599" transform="rotate(89.814 -25.738 5.52)scale(1 -1)"/></g><g filter="url(#g)"><ellipse cx="14.072" cy="22.078" fill="#eee6ff" rx="14.072" ry="22.078" transform="rotate(93.35 31.245 55.578)scale(-1 1)"/></g><g filter="url(#h)"><ellipse cx="3.47" cy="21.501" fill="#8900ff" rx="3.47" ry="21.501" transform="rotate(89.009 35.419 55.202)scale(-1 1)"/></g><g filter="url(#i)"><ellipse cx="3.47" cy="21.501" fill="#8900ff" rx="3.47" ry="21.501" transform="rotate(89.009 35.419 55.202)scale(-1 1)"/></g><g filter="url(#j)"><ellipse cx="14.592" cy="9.743" fill="#8900ff" rx="4.407" ry="29.108" transform="rotate(39.51 14.592 9.743)"/></g><g filter="url(#k)"><ellipse cx="61.728" cy="-5.321" fill="#8900ff" rx="4.407" ry="29.108" transform="rotate(37.892 61.728 -5.32)"/></g><g filter="url(#l)"><ellipse cx="55.618" cy="7.104" fill="#00c2ff" rx="5.971" ry="9.665" transform="rotate(37.892 55.618 7.104)"/></g><g filter="url(#m)"><ellipse cx="12.326" cy="39.103" fill="#8900ff" rx="4.407" ry="29.108" transform="rotate(37.892 12.326 39.103)"/></g><g filter="url(#n)"><ellipse cx="12.326" cy="39.103" fill="#8900ff" rx="4.407" ry="29.108" transform="rotate(37.892 12.326 39.103)"/></g><g filter="url(#o)"><ellipse cx="49.857" cy="30.678" fill="#8900ff" rx="4.407" ry="29.108" transform="rotate(37.892 49.857 30.678)"/></g><g filter="url(#p)"><ellipse cx="52.623" cy="33.171" fill="#00c2ff" rx="5.971" ry="15.297" transform="rotate(37.892 52.623 33.17)"/></g></g><path d="M6.919 0c-9.198 13.166-9.252 33.575 0 46.789h6.215c-9.25-13.214-9.196-33.623 0-46.789zm62.424 0h-6.215c9.198 13.166 9.252 33.575 0 46.789h6.215c9.25-13.214 9.196-33.623 0-46.789" class="parenthesis"/><defs><filter id="b" width="60.045" height="41.654" x="-5.564" y="16.92" color-interpolation-filters="sRGB" filterUnits="userSpaceOnUse"><feFlood flood-opacity="0" result="BackgroundImageFix"/><feBlend in="SourceGraphic" in2="BackgroundImageFix" result="shape"/><feGaussianBlur result="effect1_foregroundBlur_2002_17286" stdDeviation="7.659"/></filter><filter id="c" width="90.34" height="51.437" x="-40.407" y="-6.762" color-interpolation-filters="sRGB" filterUnits="userSpaceOnUse"><feFlood flood-opacity="0" result="BackgroundImageFix"/><feBlend in="SourceGraphic" in2="BackgroundImageFix" result="shape"/><feGaussianBlur result="effect1_foregroundBlur_2002_17286" stdDeviation="7.659"/></filter><filter id="d" width="79.355" height="29.4" x="-35.435" y="2.801" color-interpolation-filters="sRGB" filterUnits="userSpaceOnUse"><feFlood flood-opacity="0" result="BackgroundImageFix"/><feBlend in="SourceGraphic" in2="BackgroundImageFix" result="shape"/><feGaussianBlur result="effect1_foregroundBlur_2002_17286" stdDeviation="4.596"/></filter><filter id="e" width="79.579" height="29.4" x="-30.84" y="20.8" color-interpolation-filters="sRGB" filterUnits="userSpaceOnUse"><feFlood flood-opacity="0" result="BackgroundImageFix"/><feBlend in="SourceGraphic" in2="BackgroundImageFix" result="shape"/><feGaussianBlur result="effect1_foregroundBlur_2002_17286" stdDeviation="4.596"/></filter><filter id="f" width="79.579" height="29.4" x="-29.307" y="21.949" color-interpolation-filters="sRGB" filterUnits="userSpaceOnUse"><feFlood flood-opacity="0" result="BackgroundImageFix"/><feBlend in="SourceGraphic" in2="BackgroundImageFix" result="shape"/><feGaussianBlur result="effect1_foregroundBlur_2002_17286" stdDeviation="4.596"/></filter><filter id="g" width="74.749" height="58.852" x="29.961" y="-17.13" color-interpolation-filters="sRGB" filterUnits="userSpaceOnUse"><feFlood flood-opacity="0" result="BackgroundImageFix"/><feBlend in="SourceGraphic" in2="BackgroundImageFix" result="shape"/><feGaussianBlur result="effect1_foregroundBlur_2002_17286" stdDeviation="7.659"/></filter><filter id="h" width="61.377" height="25.362" x="37.754" y="3.055" color-interpolation-filters="sRGB" filterUnits="userSpaceOnUse"><feFlood flood-opacity="0" result="BackgroundImageFix"/><feBlend in="SourceGraphic" in2="BackgroundImageFix" result="shape"/><feGaussianBlur result="effect1_foregroundBlur_2002_17286" stdDeviation="4.596"/></filter><filter id="i" width="61.377" height="25.362" x="37.754" y="3.055" color-interpolation-filters="sRGB" filterUnits="userSpaceOnUse"><feFlood flood-opacity="0" result="BackgroundImageFix"/><feBlend in="SourceGraphic" in2="BackgroundImageFix" result="shape"/><feGaussianBlur result="effect1_foregroundBlur_2002_17286" stdDeviation="4.596"/></filter><filter id="j" width="56.045" height="63.649" x="-13.43" y="-22.082" color-interpolation-filters="sRGB" filterUnits="userSpaceOnUse"><feFlood flood-opacity="0" result="BackgroundImageFix"/><feBlend in="SourceGraphic" in2="BackgroundImageFix" result="shape"/><feGaussianBlur result="effect1_foregroundBlur_2002_17286" stdDeviation="4.596"/></filter><filter id="k" width="54.814" height="64.646" x="34.321" y="-37.644" color-interpolation-filters="sRGB" filterUnits="userSpaceOnUse"><feFlood flood-opacity="0" result="BackgroundImageFix"/><feBlend in="SourceGraphic" in2="BackgroundImageFix" result="shape"/><feGaussianBlur result="effect1_foregroundBlur_2002_17286" stdDeviation="4.596"/></filter><filter id="l" width="33.541" height="35.313" x="38.847" y="-10.552" color-interpolation-filters="sRGB" filterUnits="userSpaceOnUse"><feFlood flood-opacity="0" result="BackgroundImageFix"/><feBlend in="SourceGraphic" in2="BackgroundImageFix" result="shape"/><feGaussianBlur result="effect1_foregroundBlur_2002_17286" stdDeviation="4.596"/></filter><filter id="m" width="54.814" height="64.646" x="-15.081" y="6.78" color-interpolation-filters="sRGB" filterUnits="userSpaceOnUse"><feFlood flood-opacity="0" result="BackgroundImageFix"/><feBlend in="SourceGraphic" in2="BackgroundImageFix" result="shape"/><feGaussianBlur result="effect1_foregroundBlur_2002_17286" stdDeviation="4.596"/></filter><filter id="n" width="54.814" height="64.646" x="-15.081" y="6.78" color-interpolation-filters="sRGB" filterUnits="userSpaceOnUse"><feFlood flood-opacity="0" result="BackgroundImageFix"/><feBlend in="SourceGraphic" in2="BackgroundImageFix" result="shape"/><feGaussianBlur result="effect1_foregroundBlur_2002_17286" stdDeviation="4.596"/></filter><filter id="o" width="54.814" height="64.646" x="22.45" y="-1.645" color-interpolation-filters="sRGB" filterUnits="userSpaceOnUse"><feFlood flood-opacity="0" result="BackgroundImageFix"/><feBlend in="SourceGraphic" in2="BackgroundImageFix" result="shape"/><feGaussianBlur result="effect1_foregroundBlur_2002_17286" stdDeviation="4.596"/></filter><filter id="p" width="39.409" height="43.623" x="32.919" y="11.36" color-interpolation-filters="sRGB" filterUnits="userSpaceOnUse"><feFlood flood-opacity="0" result="BackgroundImageFix"/><feBlend in="SourceGraphic" in2="BackgroundImageFix" result="shape"/><feGaussianBlur result="effect1_foregroundBlur_2002_17286" stdDeviation="4.596"/></filter></defs></svg>
````

## File: frontend/src/components/grader/sampleTests.ts
````typescript
import type { SATBVoicing } from "../../audio/synth";
⋮----
export interface GraderSampleTest {
  name: string;
  key: { tonic: string; mode: string };
  timeSignature: string;
  voicings: SATBVoicing[];
  chords: string[];
  durations: string[];
}
````

## File: frontend/src/components/ui/Input.tsx
````typescript
import React, { useId } from "react";
⋮----
export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  inputSize?: "sm" | "md";
}
⋮----
/** Token-styled text/number input with label association and error state. */
export const Input: React.FC<InputProps> = ({
  label,
  error,
  inputSize = "md",
  className = "",
  id,
  ...props
}) =>
````

## File: frontend/src/components/ui/Select.tsx
````typescript
import React, { useId } from "react";
⋮----
export interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  selectSize?: "sm" | "md";
}
⋮----
/** Token-styled native select with label association (a11y-safe option list). */
````

## File: frontend/src/components/ui/Tabs.tsx
````typescript
import React, { useRef } from "react";
⋮----
export interface TabItem {
  id: string;
  label: React.ReactNode;
  icon?: React.ReactNode;
  /** Override the active-tab visual (e.g. grader amber/rose identity). */
  activeClass?: string;
}
⋮----
/** Override the active-tab visual (e.g. grader amber/rose identity). */
⋮----
interface TabsProps {
  items: TabItem[];
  activeId: string;
  onChange: (id: string) => void;
  ariaLabel: string;
  className?: string;
}
⋮----
/**
 * Accessible tablist: role=tablist/tab, aria-selected, roving tabindex,
 * ArrowLeft/ArrowRight/Home/End keyboard navigation.
 * Renders ids `tab-<id>` / aria-controls `panel-<id>` (App panels match).
 */
export const Tabs: React.FC<TabsProps> = ({
  items,
  activeId,
  onChange,
  ariaLabel,
  className = "",
}) =>
⋮----
const focusTab = (id: string) =>
⋮----
const handleKeyDown = (e: React.KeyboardEvent, index: number) =>
⋮----
if (el) tabRefs.current.set(item.id, el);
else tabRefs.current.delete(item.id);
⋮----
onClick=
````

## File: frontend/src/hooks/useTheme.ts
````typescript
import { useState, useEffect } from "react";
⋮----
export type Theme = "dark" | "light";
⋮----
export function useTheme(): {
  theme: Theme;
  setTheme: (t: Theme) => void;
  toggleTheme: () => void;
}
⋮----
const setTheme = (newTheme: Theme) =>
⋮----
const toggleTheme = () =>
````

## File: frontend/src/types/harmony.ts
````typescript
import type { SATBVoicing } from "../audio/synth";
⋮----
export interface TabScoreState {
  musicxml: string;
  voicings: SATBVoicing[];
  chords: string[];
  asciiScore: string;
  title: string;
  problemMeasures: number[];
  durations: string[];
  key: { tonic: string; mode: string };
  timeSignature: string;
  currentPlaybackIndex: number;
}
````

## File: frontend/src/utils/durationUtils.ts
````typescript
/**
 * Utility functions and data structures for note durations, metric calculations, and downbeats.
 */
⋮----
export interface MelodyNote {
  pitch: number;
  name: string;
  duration: string; // "whole" | "dotted_half" | "half" | "dotted_quarter" | "quarter" | "dotted_eighth" | "eighth"
  is_downbeat: boolean;
}
⋮----
duration: string; // "whole" | "dotted_half" | "half" | "dotted_quarter" | "quarter" | "dotted_eighth" | "eighth"
⋮----
export interface DurationOption {
  id: string;
  label: string;
  hint: string;
  beats: number;
}
⋮----
/**
 * Recalculates downbeats according to current time signature and accumulated beat offsets.
 * Only primary measure boundaries (offset 0.0) are marked as downbeats (accented) for harmonization.
 */
export function recalculateDownbeats(
  notes: MelodyNote[],
  timeSignature: string = "4/4"
): MelodyNote[]
⋮----
// Only a measure start is a harmonization downbeat; secondary accents
// stay unaccented so passing tones can serve as NCTs.
⋮----
/**
 * Converts a MIDI pitch number (e.g. 60) to a musical note name (e.g. C4).
 */
export function midiToNoteName(pitch: number): string
````

## File: frontend/src/main.tsx
````typescript
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
⋮----
import App from './App.tsx'
````

## File: scripts/audit_harmonic_rhythm.py
````python
"""
Audit script for harmonic rhythm, chord oscillation, mediant intrusions,
and cadential preparations across diverse melodies.
Generates comprehensive BEFORE/AFTER report in .redteam/scratch/debug_rhythm/REPORT.md.
"""
⋮----
# Ensure project root is in sys.path
⋮----
@dataclass
class AuditMelody
⋮----
name: str
key: str
time_signature: str
melody: list[Any]
category: str
⋮----
# 39 diverse diatonic melodies: scales, arpeggios, motifs; C/G/F-dur, a/d/e-moll; 4/4 and 3/4; 6–16 notes
AUDIT_DATASET: list[AuditMelody] = [
⋮----
# --- Scales (Major) ---
⋮----
# --- Scales (Minor) ---
⋮----
# --- Arpeggios ---
⋮----
# --- Motifs in 4/4 and 3/4 ---
⋮----
# Quarter-note explicit durations
⋮----
# Baseline snapshot before fixes
BASELINE_SNAPSHOT = {
⋮----
def extract_pitch(item: Any) -> int
⋮----
def count_oscillations_abab(chords: list[str]) -> int
⋮----
"""Counts 4-chord sliding windows matching A-B-A-B pattern (A != B)."""
count = 0
⋮----
def run_audit(dataset: list[AuditMelody] | None = None) -> dict[str, Any]
⋮----
dataset = dataset or AUDIT_DATASET
harmonizer = Harmonizer()
⋮----
total_measures = 0
measures_gt_2_changes = 0
total_oscillations = 0
total_iii_in_major = 0
total_tt_stepwise = 0
final_pairs = Counter()
results_detail = []
⋮----
res = harmonizer.harmonize(item.melody, key=item.key, time_signature=item.time_signature)
⋮----
sol = res.best_solution
chords = [c.function for c in sol.chords]
pitches = [extract_pitch(m) for m in item.melody]
⋮----
# 1. Measures with >2 chord changes
metric_info = sol.metric_info or calculate_metric_structure(
measures_map: dict[int, list[str]] = {}
⋮----
m_num = m_info["measure"]
⋮----
item_gt2_measures = 0
⋮----
changes = sum(1 for j in range(1, len(m_chords)) if m_chords[j] != m_chords[j - 1])
⋮----
# 2. Oscillations A-B-A-B
item_oscillations = count_oscillations_abab(chords)
⋮----
# 3. III / III6 in Major
k = Key.parse(item.key)
is_major = "MAJOR" in k.mode.upper()
item_iii = 0
⋮----
# 4. (T, T) on stepwise soprano
item_tt_step = 0
⋮----
step = abs(pitches[j + 1] - pitches[j])
⋮----
# 5. Final pair
⋮----
pair = f"{chords[-2]} -> {chords[-1]}"
⋮----
rate_gt_2 = (measures_gt_2_changes / total_measures * 100.0) if total_measures > 0 else 0.0
⋮----
def generate_markdown_report(before_metrics: dict[str, Any], after_metrics: dict[str, Any]) -> str
⋮----
lines = [
⋮----
all_pairs = sorted(set(list(before_metrics["final_pairs"].keys()) + list(after_metrics["final_pairs"].keys())))
⋮----
b_cnt = before_metrics["final_pairs"].get(pair, 0)
a_cnt = after_metrics["final_pairs"].get(pair, 0)
⋮----
ch_str = " ".join(d["chords"])
⋮----
report_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".redteam", "scratch", "debug_rhythm"))
⋮----
report_path = os.path.join(report_dir, "REPORT.md")
⋮----
after_metrics = run_audit()
md = generate_markdown_report(BASELINE_SNAPSHOT, after_metrics)
````

## File: scripts/benchmark_harmonize.py
````python
"""
Benchmark CLI for SATB Harmonization pipeline.
Measures total latency and per-stage timings across various melody lengths.
"""
⋮----
# Ensure project root is in sys.path
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
⋮----
DEFAULT_MELODIES: dict[int, list[int]] = {
⋮----
"""Runs harmonization once with stage instrumentation."""
times = {
⋮----
orig_gp = HarmonicGrammar.generate_plans
def timed_gp(*args: Any, **kwargs: Any) -> Any
⋮----
t0 = time.perf_counter()
⋮----
orig_gcv = state_generator.generate_candidate_voicings
def timed_gcv(*args: Any, **kwargs: Any) -> Any
⋮----
orig_val = RuleEngine.validate
def timed_val(*args: Any, **kwargs: Any) -> Any
⋮----
orig_rep = Harmonizer._replan
def timed_rep(*args: Any, **kwargs: Any) -> Any
⋮----
# Apply temporary hooks
⋮----
harmonizer = Harmonizer()
t_start = time.perf_counter()
res = harmonizer.harmonize(
total_sec = time.perf_counter() - t_start
⋮----
results = []
⋮----
# Generate repeated base phrase to desired length
base = DEFAULT_MELODIES[8]
mel = (base * ((length // 8) + 1))[:length]
⋮----
mel = DEFAULT_MELODIES[length]
⋮----
run_records = []
⋮----
rec = benchmark_single(mel, key=key)
⋮----
# Average results over runs
avg_total = sum(r["total_ms"] for r in run_records) / runs
avg_gp = sum(r["gp_ms"] for r in run_records) / runs
avg_sg = sum(r["sg_ms"] for r in run_records) / runs
avg_val = sum(r["val_ms"] for r in run_records) / runs
avg_replan = sum(r["replan_ms"] for r in run_records) / runs
last = run_records[-1]
⋮----
summary = {
⋮----
def print_table(results: list[dict[str, Any]]) -> None
⋮----
header = (
separator = "-" * len(header)
⋮----
cost_str = f"{r['best_cost']:.2f}" if r["best_cost"] is not None else "N/A"
⋮----
def main() -> int
⋮----
parser = argparse.ArgumentParser(description="Benchmark SATB Harmonizer performance")
⋮----
args = parser.parse_args()
⋮----
lengths = [int(x.strip()) for x in args.lengths.split(",") if x.strip()]
⋮----
results = run_benchmarks(lengths=lengths, runs=args.runs, key=args.key)
````

## File: scripts/test_e2e_api.py
````python
def test_full_pipeline()
⋮----
client = TestClient(app)
⋮----
# 1. Health
r = client.get('/api/health')
⋮----
# 2. SPA index
r = client.get('/')
⋮----
# 3. Keys
r = client.get('/api/keys')
⋮----
keys = r.json()
⋮----
# 4. Harmonize
payload = {
r = client.post('/api/harmonize', json=payload)
⋮----
harm_data = r.json()
⋮----
cand0 = harm_data['candidates'][0]
⋮----
# 5. Grade
grade_payload = {
r = client.post('/api/grade', json=grade_payload)
⋮----
grade_data = r.json()
⋮----
# 6. MIDI and MusicXML export
r_midi = client.post('/api/export/midi', json={'voicings': cand0['voicings']})
⋮----
r_xml = client.post('/api/export/musicxml', json={'voicings': cand0['voicings'], 'key': {'tonic': 'C', 'mode': 'Major'}})
````

## File: src/harmony/export/__init__.py
````python
"""
Export package: MusicXML, MIDI, and ASCII score formatters.
"""
⋮----
__all__ = [
````

## File: src/harmony/export/ascii.py
````python
"""
ASCII score formatter for four-part SATB harmony.

Produces clear, human-readable terminal visualizations of chord voicings,
voice leading trajectories, and Roman numeral harmonic analyses.
"""
⋮----
"""
    Format SATB voicings and harmonic analysis into a structured ASCII score.

    Args:
        voicings: List of voicings (Voicing objects, tuples, or dicts).
        chords: Optional list of chords/functions (Chord objects or strings).
        key: Key representation (Key object, string, or dict).

    Returns:
        Formatted multi-line ASCII string representation.
    """
⋮----
chord_list = list(chords) if chords is not None else []
⋮----
parsed_rows: list[dict[str, Any]] = []
⋮----
c = chord_list[i] if i < len(chord_list) else ""
c_sym = extract_chord_symbol(c)
⋮----
spacing = classify_voicing_spacing(s, a, t)
sa_int = s - a
at_int = a - t
tb_int = t - b
⋮----
lines: list[str] = []
header_title = f"=== SATB HARMONY SCORE [{tonic_name} {mode_name}] ({len(voicings)} chords) ==="
⋮----
# 1. Vertical Detailed Table
col_idx = "#"
col_s = "Soprano (S)"
col_a = "Alto (A)"
col_t = "Tenor (T)"
col_b = "Bass (B)"
col_ch = "Function"
col_sp = "Spacing"
col_iv = "Intervals"
⋮----
fmt = "{:<4} {:<13} {:<13} {:<13} {:<13} {:<10} {:<9} {:<14}"
⋮----
# 2. Horizontal Voice-Leading Ribbon (Piano-roll / score view)
⋮----
s_line = "  [S] " + " | ".join(f"{r['s_short']:<4}" for r in parsed_rows) + " |"
a_line = "  [A] " + " | ".join(f"{r['a_short']:<4}" for r in parsed_rows) + " |"
t_line = "  [T] " + " | ".join(f"{r['t_short']:<4}" for r in parsed_rows) + " |"
b_line = "  [B] " + " | ".join(f"{r['b_short']:<4}" for r in parsed_rows) + " |"
sep    = "  --- " + "-+-".join("----" for _ in parsed_rows) + "-+"
f_line = "  [F] " + " | ".join(f"{r['chord']:<4}" for r in parsed_rows) + " |"
````

## File: src/harmony/solver/__init__.py
````python
"""
Solver package: State space generator and Viterbi dynamic programming optimizer.
"""
⋮----
__all__ = [
````

## File: src/harmony/syntax/__init__.py
````python
"""
Syntax package: Macro Period Grammar and Functional Plan Generator.
"""
⋮----
__all__ = [
````

## File: src/harmony/__init__.py
````python
"""Harmony harmonization package."""
````

## File: src/harmony/__main__.py
````python
"""
Executable module entrypoint.
Allows running `python -m src.harmony.cli` or `python -m src.harmony`.
"""
````

## File: desktop/instance.py
````python
"""
Single-instance enforcement and IPC focus mechanism for Harmony Engine Desktop.

Design note (2026-11-12): a Win32 named mutex is NOT a reliable ownership token
here. WebView2 child processes inherit handles; after a force-killed primary the
orphaned children keep the named mutex alive, so the next launch sees
ERROR_ALREADY_EXISTS and exits without ever showing a window. We therefore use an
exclusive byte-range lock on instance.lock instead: Windows releases it when the
owning process dies (even on TerminateProcess) and Python file descriptors are
non-inheritable by default, so WebView2 children never hold it.

The first process owns instance.lock, writes instance.json (pid/http/ipc ports)
and listens on a local TCP socket. A duplicate process fails to acquire the lock,
reads instance.json, sends FOCUS and exits 0.
"""
⋮----
logger = logging.getLogger("desktop.instance")
⋮----
_LOCK_FILENAME = "instance.lock"
⋮----
_lock_fd: int | None = None
_ipc_server_socket: socket.socket | None = None
_instance_file: Path | None = None
# Only the process that created instance.json may remove it on exit. A secondary
# instance must never unlink the primary's discovery file (it would break FOCUS
# delivery for every subsequent launch).
_owns_instance_file = False
⋮----
def get_instance_file_path() -> Path
⋮----
def _get_lock_path() -> Path
⋮----
def cleanup_instance() -> None
⋮----
"""Removes discovery files and releases the single-instance lock, IPC socket and mutex resources."""
⋮----
_ipc_server_socket = None
⋮----
_instance_file = None
⋮----
_lock_fd = None
lock_path = _get_lock_path()
⋮----
# Automatically clean up on interpreter exit
⋮----
def _ipc_listener_loop(sock: socket.socket, focus_callback: Callable[[], None]) -> None
⋮----
"""Daemon thread loop accepting incoming IPC commands from secondary instances."""
⋮----
data = conn.recv(1024)
⋮----
def _acquire_file_lock() -> int | None
⋮----
"""Tries to take the exclusive single-instance lock. Returns the fd or None."""
⋮----
fd = os.open(str(lock_path), os.O_CREAT | os.O_RDWR)
⋮----
"""
    Attempts to acquire the single-instance file lock.
    If another instance is already running:
        Sends FOCUS to the running instance via local IPC socket and returns False.
    If this is the primary instance:
        Starts IPC listener, records instance.json, and returns True.
    """
⋮----
_instance_file = get_instance_file_path()
⋮----
fd = _acquire_file_lock()
⋮----
# Only a real duplicate process (which does not own the file) drops the
# reference; a same-process probe must not clobber the primary state.
⋮----
_lock_fd = fd
⋮----
# We are the primary instance. Setup IPC server socket.
⋮----
_ipc_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
⋮----
ipc_port = _ipc_server_socket.getsockname()[1]
⋮----
# Write the discovery file atomically so a waiting secondary never reads half a file.
instance_data = {
tmp_path = _instance_file.with_suffix(".json.tmp")
⋮----
_owns_instance_file = True
⋮----
t = threading.Thread(
⋮----
# We still own the lock; the window will open without cross-instance focus.
⋮----
def notify_existing_instance() -> None
⋮----
"""Connects to the primary instance's IPC port and sends FOCUS command."""
instance_file = get_instance_file_path()
⋮----
data: dict | None = None
⋮----
data = json.loads(instance_file.read_text(encoding="utf-8"))
⋮----
ipc_port = int(data.get("ipc_port", 0))
⋮----
# Never raise or show tracebacks on duplicate exit
⋮----
# Backwards-compatible alias: older call sites/imports referenced this name.
def get_app_data_directory() -> Path:  # pragma: no cover - trivial alias
````

## File: frontend/src/components/grader/GraderScoreMatrix.tsx
````typescript
import React from "react";
import type { SATBVoicing } from "../../audio/synth";
import { Button } from "../ui/Button";
⋮----
interface GraderScoreMatrixProps {
  voicings: SATBVoicing[];
  onVoicePitchChange: (
    chordIdx: number,
    voice: "soprano" | "alto" | "tenor" | "bass",
    val: number
  ) => void;
  onAddChord: () => void;
  onRemoveChord: () => void;
}
⋮----
/* SATB identity colors, AA-readable in both themes. */
````

## File: frontend/src/components/grader/GraderViolationsList.tsx
````typescript
import React from "react";
import { AlertTriangle, CheckCircle, XCircle } from "lucide-react";
⋮----
export interface GraderViolationItem {
  measure: number;
  chord_index: number;
  rule_id: string;
  severity: "hard_gate" | "soft_penalty";
  message_ru: string;
  voices: string[];
  notes: string[];
}
⋮----
export interface GraderReportData {
  is_valid: boolean;
  total_violations: number;
  hard_violations_count: number;
  soft_violations_count: number;
  violations: GraderViolationItem[];
  problem_measures: number[];
  summary_verdict: string;
  grade: string;
}
⋮----
interface GraderViolationsListProps {
  report: GraderReportData;
  onHighlightMeasure: (measure: number) => void;
}
⋮----
{/* Grade banner */}
⋮----
{/* List of Rule Violations with pedagogical critique */}
⋮----
{/* No nested scrollbox: the page/panel scrolls as one. */}
⋮----
onClick=
````

## File: frontend/src/components/layout/Header.tsx
````typescript
import { Music, Award, FileMusic, Sun, Moon } from "lucide-react";
import { useTheme } from "../../hooks/useTheme";
import { Tabs } from "../ui/Tabs";
import type { TabItem } from "../ui/Tabs";
⋮----
interface HeaderProps {
  activeTab: "harmonizer" | "grader";
  onTabChange: (tab: "harmonizer" | "grader") => void;
}
⋮----
{/* Brand & Subtitle */}
⋮----
{/* Right Section: Mode Tabs + Theme Toggle */}
⋮----
{/* Theme Toggle */}
````

## File: frontend/src/components/melody/MidiInputBar.tsx
````typescript
import React, { useEffect, useRef, useState } from "react";
import { Radio, AlertCircle, Circle, Square } from "lucide-react";
import { webMidiManager } from "../../audio/midiInput";
import type { MidiDevice } from "../../audio/midiInput";
import { Button } from "../ui/Button";
⋮----
interface MidiInputBarProps {
  onNoteReceived: (pitch: number, isDownbeat: boolean) => void;
  timeSignature: string;
}
⋮----
/**
 * Web MIDI input bar built on the REAL WebMidiManager API:
 * requestAccess() → MidiDevice[], connectDevice(id), startRecording(bpm,
 * onNote(pitch, isDownbeat), onMetronomeTick, timeSignature), stopRecording().
 * Notes only arrive while recording is active (metronome-driven downbeats).
 */
⋮----
const beginRecording = (bpm: number) =>
⋮----
const handleToggleRecording = () =>
⋮----
const handleBpmChange = (value: number) =>
⋮----
const handleDeviceChange = (e: React.ChangeEvent<HTMLSelectElement>) =>
````

## File: frontend/src/components/melody/NoteList.tsx
````typescript
import React from "react";
import { Trash2, Volume2, Sparkles } from "lucide-react";
import { Button } from "../ui/Button";
import { audioEngine } from "../../audio/synth";
import { DURATIONS } from "../../utils/durationUtils";
import type { MelodyNote } from "../../utils/durationUtils";
⋮----
interface NoteListProps {
  melody: MelodyNote[];
  onChange: (newMelody: MelodyNote[]) => void;
  onClear: () => void;
  onSelectSample: () => void;
}
⋮----
const handleDurationChange = (index: number, newDur: string) =>
⋮----
const handleToggleDownbeat = (index: number) =>
⋮----
const handleDelete = (index: number) =>
⋮----
const handlePlaySingle = (pitch: number) =>
⋮----
/* No nested vertical scrollbox: the whole left panel scrolls as one. */
⋮----
{/* Note name & play button */}
⋮----
{/* Duration selector & Downbeat switch */}
````

## File: frontend/src/components/melody/PianoKeyboard.tsx
````typescript
import React, { useState } from "react";
import { audioEngine } from "../../audio/synth";
import { midiToNoteName } from "../../utils/durationUtils";
⋮----
interface PianoKeyboardProps {
  onNoteTrigger: (pitch: number, name: string) => void;
  activePitch?: number | null;
}
⋮----
/** Piano range C3–C6 (MIDI 48–84), as in the pre-redesign MelodyInput. */
⋮----
1: 14, // C#
3: 42, // D#
6: 84, // F#
8: 112, // G#
10: 140, // A#
⋮----
const handleKeyClick = (pitch: number) =>
⋮----
const focusPitch = (pitch: number) =>
⋮----
// Keyboard navigation: arrows move by semitone, Home/End jump to range edges.
const handleKeyDown = (e: React.KeyboardEvent) =>
⋮----
const whiteKeyClass = (isPressed: boolean) =>
⋮----
const blackKeyClass = (isPressed: boolean) =>
⋮----
const keyProps = (pitch: number) =>
⋮----
// Group into octaves for structured rendering (C3, C4, C5 + final C6)
⋮----
const basePitch = (octave + 1) * 12; // C3=48, C4=60, C5=72
const whiteNotes = [0, 2, 4, 5, 7, 9, 11]; // C, D, E, F, G, A, B
const blackNotes = [1, 3, 6, 8, 10]; // C#, D#, F#, G#, A#
⋮----
{/* White keys */}
⋮----
onClick={() => handleKeyClick(pitch)}
⋮----
className={whiteKeyClass(isPressed)}
⋮----
className={blackKeyClass(isPressed)}
⋮----
{/* Final C6 key */}
````

## File: frontend/src/components/ui/Badge.tsx
````typescript
import React from "react";
⋮----
export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: "default" | "brand" | "success" | "warning" | "error" | "voice";
  voice?: "soprano" | "alto" | "tenor" | "bass";
}
⋮----
export const Badge: React.FC<BadgeProps> = ({
  variant = "default",
  voice,
  children,
  className = "",
  ...props
}) =>
````

## File: frontend/src/components/ui/Button.tsx
````typescript
import React from "react";
⋮----
export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "outline" | "ghost" | "danger" | "success";
  size?: "xs" | "sm" | "md" | "lg";
  icon?: React.ReactNode;
  /** Toggle state, paired with `selectedClass` (mirrors Tabs.TabItem.activeClass). */
  selected?: boolean;
  /**
   * Color classes used instead of the variant's when `selected` is true.
   * Replaces (not merges with) the variant classes, so include `border` width
   * yourself if the selected look needs a border.
   */
  selectedClass?: string;
}
⋮----
/** Toggle state, paired with `selectedClass` (mirrors Tabs.TabItem.activeClass). */
⋮----
/**
   * Color classes used instead of the variant's when `selected` is true.
   * Replaces (not merges with) the variant classes, so include `border` width
   * yourself if the selected look needs a border.
   */
⋮----
export const Button: React.FC<ButtonProps> = ({
  variant = "secondary",
  size = "sm",
  icon,
  selected = false,
  selectedClass,
  children,
  className = "",
  disabled,
  type = "button",
  ...props
}) =>
````

## File: frontend/src/components/ui/Card.tsx
````typescript
import React from "react";
⋮----
export interface CardProps extends Omit<React.HTMLAttributes<HTMLDivElement>, "title"> {
  title?: React.ReactNode;
  subtitle?: React.ReactNode;
  headerAction?: React.ReactNode;
  badge?: React.ReactNode;
}
⋮----
export const Card: React.FC<CardProps> = ({
  title,
  subtitle,
  headerAction,
  badge,
  children,
  className = "",
  ...props
}) =>
````

## File: scripts/audit_chromatic.py
````python
"""
Audit script for chromatic melodies in Brigade Harmony Engine.
Evaluates 15 chromatic test melodies across C-dur, G-dur, and F-dur.
Tracks success rates and functional progressions.
"""
⋮----
# Add project root to sys.path
⋮----
CHROMATIC_TEST_SUITE: list[dict] = [
⋮----
# C-dur: Db, Ab, G#, D#/Eb
⋮----
# G-dur: Ab (bII), Eb (bVI)
⋮----
# F-dur: Gb (bII), Db (bVI)
⋮----
def run_audit() -> dict
⋮----
harmonizer = Harmonizer()
total = len(CHROMATIC_TEST_SUITE)
passed = 0
results = []
⋮----
name = item["name"]
key = item["key"]
melody = item["melody"]
⋮----
res = harmonizer.harmonize(melody, key=key)
success = res.is_success
⋮----
chords = [c.function for c in res.best_solution.chords]
cost = res.best_solution.cost
status = f"PASS (cost={cost:.1f}, chords={chords})"
⋮----
status = f"FAIL ({res.message})"
⋮----
pct = (passed / total) * 100.0
````

## File: scripts/generate_dataset.py
````python
"""
Synthetic SATB Harmony Dataset Generator.
Synthesizes tens of thousands of textbook-compliant 4-part harmony training pairs
(soprano melody -> SATB voicings + functional progression) using Harmonizer (Grammar + Viterbi DP).

Output format: JSON Lines (.jsonl) ready for training lightweight neural models (Bi-GRU / Transformer).
"""
⋮----
# Ensure workspace root is in sys.path
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
⋮----
ALL_KEYS = [
⋮----
# Major keys
⋮----
# Minor keys
⋮----
MAJOR_SCALE_STEPS = [0, 2, 4, 5, 7, 9, 11]
MINOR_HARMONIC_STEPS = [0, 2, 3, 5, 7, 8, 11]
⋮----
NOTE_TO_PC = {
⋮----
def get_scale_pitches(tonic: str, mode: str, min_pitch: int = 60, max_pitch: int = 77) -> list[int]
⋮----
"""Generates all admissible soprano pitches for the given key in range [C4..F5]."""
tonic_pc = NOTE_TO_PC.get(tonic, 0)
steps = MINOR_HARMONIC_STEPS if "minor" in mode.lower() else MAJOR_SCALE_STEPS
scale_pcs = {(tonic_pc + s) % 12 for s in steps}
⋮----
def generate_classical_melody(tonic: str, mode: str, length: int = 8, rng: random.Random | None = None) -> list[int]
⋮----
"""
    Synthesizes a musically coherent soprano line following classical period syntax:
    - Stepwise motion with occasional consonant leaps (3rds, 4ths, 5ths).
    - Cadence formulas ending on tonic (scale degree 1) or dominant (scale degree 5 or 2).
    """
r = rng or random.Random()
pitches = get_scale_pitches(tonic, mode)
⋮----
pitches = [60, 62, 64, 65, 67, 69, 71, 72]
⋮----
tonic_candidates = [p for p in pitches if p % 12 == tonic_pc]
mediant_candidates = [p for p in pitches if p % 12 == (tonic_pc + (3 if "minor" in mode.lower() else 4)) % 12]
dominant_candidates = [p for p in pitches if p % 12 == (tonic_pc + 7) % 12]
supertonic_candidates = [p for p in pitches if p % 12 == (tonic_pc + 2) % 12]
⋮----
# Start note: typically 1, 3, or 5 in soprano register [60..72]
start_pool = (tonic_candidates + mediant_candidates + dominant_candidates) or pitches
current = r.choice(start_pool)
melody = [current]
⋮----
# Prefer step motion (neighboring scale pitches)
curr_idx = pitches.index(current) if current in pitches else len(pitches) // 2
step_options = []
⋮----
step_options.append(pitches[curr_idx - 2])  # 3rd down
⋮----
step_options.append(pitches[curr_idx + 2])  # 3rd up
⋮----
weights = [3, 3, 1, 1][:len(step_options)]
current = r.choices(step_options, weights=weights)[0]
⋮----
# Penultimate note: supertonic (degree 2) or leading tone (degree 7)
penult_pool = supertonic_candidates or dominant_candidates or pitches
penult = r.choice(penult_pool)
⋮----
# Final note: tonic (degree 1)
final_pool = tonic_candidates or pitches
# Choose final closest to penult
final = min(final_pool, key=lambda p: abs(p - penult))
⋮----
def harmonize_single_sample(sample_id: int, tonic: str, mode: str, length: int, seed: int) -> dict[str, Any] | None
⋮----
"""Harmonizes one synthetic melody into a verified dataset record."""
rng = random.Random(seed)
melody = generate_classical_melody(tonic, mode, length=length, rng=rng)
key = Key(tonic=tonic, mode=mode)
⋮----
harmonizer = Harmonizer()
res = harmonizer.harmonize(melody=melody, key=key, max_plans=3)
⋮----
best = res.best_solution
satb_tuples = [
⋮----
def generate_batch(start_id: int, count: int, base_seed: int) -> list[dict[str, Any]]
⋮----
"""Worker task to generate a batch of samples."""
samples: list[dict[str, Any]] = []
⋮----
sid = start_id + i
seed = base_seed + sid * 31
⋮----
length = rng.choice([6, 7, 8, 9, 10])
⋮----
rec = harmonize_single_sample(sid, tonic, mode, length, seed)
⋮----
def main() -> None
⋮----
parser = argparse.ArgumentParser(description="Synthetic SATB Harmony Dataset Generator")
⋮----
args = parser.parse_args()
⋮----
out_path = Path(args.output)
⋮----
start_time = time.time()
collected: list[dict[str, Any]] = []
chunk_size = 20
next_id = 0
⋮----
active_futures = set()
⋮----
# Prime initial tasks
⋮----
# Wait for at least one future to complete
done_futures = []
⋮----
res = f.result()
⋮----
# Cancel any remaining pending futures
⋮----
# Trim to exact count
final_samples = collected[:args.count]
⋮----
# Write to JSON Lines
⋮----
elapsed = time.time() - start_time
rate = len(final_samples) / elapsed if elapsed > 0 else 0
````

## File: src/harmony/core/__init__.py
````python
"""
Core domain model for the four-part harmony engine (SATB).

Provides fundamental abstractions based on classical Russian music theory
(Бригадный учебник гармонии — Способин, Дубовский, Евсеев, Соколов):
- Pitch, PitchClass, ScaleDegree, Interval
- Key, Mode
- ChordFunction, Inversion, ChordDefinition
- Voicing, Spacing, Voice
"""
⋮----
__all__ = [
⋮----
# Pitch & scale domain
⋮----
# Key & mode domain
⋮----
# Chord & harmonic function domain
⋮----
# Voicing & texture domain
⋮----
# Modulation & tonality domain
````

## File: src/harmony/core/key.py
````python
"""
Core domain model: Key and Mode.

Defines tonality, modal scale structures, degree calculations, note membership,
and modal melodic tendencies (тяготения) in classical functional harmony
(Бригадный учебник).
"""
⋮----
class Mode(str, Enum)
⋮----
"""
    Musical modes used in classical functional harmony.

    Major (натуральный мажор)
    MinorHarmonic (гармонический минор - основной рабочий лад классической гармонии)
    MinorNatural (натуральный минор)
    MinorMelodic (мелодический минор - восходящий)
    """
⋮----
MAJOR = "Major"
MINOR_HARMONIC = "MinorHarmonic"
MINOR_NATURAL = "MinorNatural"
MINOR_MELODIC = "MinorMelodic"
⋮----
@property
    def intervals(self) -> tuple[int, ...]
⋮----
"""Semitone offsets from tonic for degrees I through VII."""
⋮----
@property
    def is_major(self) -> bool
⋮----
"""True if the mode has a major third (4 semitones)."""
⋮----
@property
    def is_minor(self) -> bool
⋮----
"""True if the mode has a minor third (3 semitones)."""
⋮----
@classmethod
    def from_str(cls, s: str) -> Mode
⋮----
"""
        Parse Mode from diverse naming conventions.

        Supports: 'Major', 'dur', 'мажор', 'MinorHarmonic', 'moll', 'minor', 'гармонический минор', etc.
        """
cleaned = s.strip().lower().replace("-", "_").replace(" ", "_")
⋮----
# In classical harmony (Бригадный), unqualified minor is harmonic minor
⋮----
@dataclass(frozen=True, slots=True)
class Key
⋮----
"""
    Tonality defined by a tonic PitchClass and a Mode.

    Provides scale degree mapping, pitch membership queries, and melodic tendencies
    (ладовые тяготения: вводный тон VII, неустойчивые ступени II, IV, VI, VII).
    """
⋮----
tonic: PitchClass
mode: Mode
⋮----
def __post_init__(self) -> None
⋮----
# Classical unstable scale degrees in Brigada harmony
UNSTABLE_DEGREES: ClassVar[tuple[ScaleDegree, ...]] = (
⋮----
# Classical stable scale degrees (tonic triad degrees)
STABLE_DEGREES: ClassVar[tuple[ScaleDegree, ...]] = (
⋮----
@classmethod
    def from_string(cls, s: str) -> Key
⋮----
"""
        Parse Key from string representations.

        Examples:
        - 'C Major', 'C:Major', 'C_Major', 'C-dur'
        - 'A MinorHarmonic', 'a-moll', 'G:Minor'
        - 'F# Major', 'Eb MinorHarmonic'
        """
cleaned = s.strip()
# Check classic German notation: 'C-dur', 'a-moll', 'c#-moll', 'Es-dur'
german_match = re.match(r"^([A-Ga-g][#b♭♯]?)[-_](dur|moll)$", cleaned, re.IGNORECASE)
⋮----
tonic = PitchClass.from_name(note_str)
mode = Mode.MAJOR if mode_str.lower() == "dur" else Mode.MINOR_HARMONIC
⋮----
# Split on whitespace, colon or underscore
parts = re.split(r"[\s:_]+", cleaned)
⋮----
# Single letter capitalized might imply major, lower might imply minor
raw = parts[0]
⋮----
tonic = PitchClass.from_name(parts[0])
mode_str = "_".join(parts[1:])
mode = Mode.from_str(mode_str)
⋮----
@property
    def name(self) -> str
⋮----
"""String representation like 'C Major' or 'A MinorHarmonic'."""
⋮----
@property
    def scale_pitch_classes(self) -> list[PitchClass]
⋮----
"""Ordered list of the 7 scale PitchClasses (I to VII)."""
⋮----
@property
    def scale_pitch_classes_set(self) -> frozenset[PitchClass]
⋮----
"""Frozenset of diatonic pitch classes in this key."""
⋮----
def get_scale_degrees(self) -> list[ScaleDegree]
⋮----
"""Returns standard scale degrees I..VII."""
⋮----
def pitch_class_for_degree(self, degree: Union[ScaleDegree, int]) -> PitchClass
⋮----
"""
        Compute the PitchClass for a given scale degree (1..7 or ScaleDegree).

        Properly applies chromatic alterations if present (e.g., VII# in minor, bII).
        """
⋮----
delta = self.mode.intervals[degree - 1]
⋮----
base_delta = self.mode.intervals[degree.degree - 1]
total_delta = base_delta + degree.alteration
⋮----
"""
        Find the ScaleDegree corresponding to a pitch class, or None if non-scale.

        prefer_flat: If True, prefer 'bII', 'bVI', 'bVII' over 'I#', 'V#', 'VI#'.
        """
target_pc = pc.pitch_class if isinstance(pc, Pitch) else (
⋮----
# 1. Check natural scale degrees first
scale_pcs = self.scale_pitch_classes
⋮----
# 2. Check standard classical chromatic alterations
# In classical harmony (Способин / Бригада):
# bII (Neapolitan), #IV (tritone), bVI (minor subdominant), bVII (natural 7), #VII (leading tone in natural minor)
⋮----
candidates = [
⋮----
ScaleDegree(2, -1),  # bII
ScaleDegree(4, 1),   # #IV
ScaleDegree(6, -1),  # bVI
ScaleDegree(7, -1),  # bVII
ScaleDegree(7, 1),   # #VII
ScaleDegree(1, 1),   # #I
ScaleDegree(2, 1),   # #II
ScaleDegree(3, -1),  # bIII
ScaleDegree(5, 1),   # #V
⋮----
def contains(self, note: Union[Pitch, PitchClass, int]) -> bool
⋮----
"""Check if pitch or pitch class is a diatonic member of this key."""
target_pc = note.pitch_class if isinstance(note, Pitch) else (
⋮----
# -------------------------------------------------------------------------
# Modal attractions & Melodic tendencies (Ладовые тяготения)
⋮----
@property
    def leading_tone(self) -> PitchClass
⋮----
"""
        The leading tone (вводный тон, VII degree).

        In Major and MinorHarmonic, this is located 1 semitone below the tonic.
        """
⋮----
@property
    def unstable_degrees(self) -> tuple[ScaleDegree, ...]
⋮----
"""Unstable scale degrees (неустойчивые ступени II, IV, VI, VII)."""
⋮----
@property
    def stable_degrees(self) -> tuple[ScaleDegree, ...]
⋮----
"""Stable scale degrees (устойчивые ступени I, III, V)."""
⋮----
@property
    def unstable_pitch_classes(self) -> tuple[PitchClass, ...]
⋮----
"""PitchClasses of unstable scale degrees (II, IV, VI, VII)."""
⋮----
@property
    def stable_pitch_classes(self) -> tuple[PitchClass, ...]
⋮----
"""PitchClasses of stable scale degrees (I, III, V)."""
⋮----
def is_stable(self, note: Union[Pitch, PitchClass, ScaleDegree, int]) -> bool
⋮----
"""Check if note corresponds to a stable degree (I, III, V)."""
⋮----
pc = note.pitch_class if isinstance(note, Pitch) else (
⋮----
def is_unstable(self, note: Union[Pitch, PitchClass, ScaleDegree, int]) -> bool
⋮----
"""Check if note corresponds to an unstable degree (II, IV, VI, VII)."""
⋮----
def is_leading_tone(self, note: Union[Pitch, PitchClass, ScaleDegree, int]) -> bool
⋮----
"""Check if note is the leading tone (вводный тон VII)."""
⋮----
def get_tendency_resolutions(self, degree: ScaleDegree) -> list[ScaleDegree]
⋮----
"""
        Return the classical melodic resolution targets for an unstable degree.

        VII -> I  (leading tone resolves up a half step to tonic)
        IV  -> III (subdominant tritone member resolves down to third)
        VI  -> V   (resolves down to fifth)
        II  -> I, III (supertonic resolves down to tonic or up to third)
        """
⋮----
def get_pitch_tendency_resolutions(self, note: Union[Pitch, PitchClass, int]) -> list[PitchClass]
⋮----
"""Return target PitchClasses for natural tendency resolution of a given note."""
sd = self.degree_for_pitch_class(note)
⋮----
target_degrees = self.get_tendency_resolutions(sd)
⋮----
def __str__(self) -> str
⋮----
def __repr__(self) -> str
````

## File: src/harmony/core/modulation.py
````python
"""
Core domain model: Modulation and Tonality Relations.

Strictly implements the theory of tonality relations, modulation, and secondary dominants
from the Brigade harmony textbook (Дубовский, Евсеев, Способин, Соколов — «Учебник гармонии»,
главы 26-28, 29, 30, 31):
- First-Degree Related Keys (Тональности первой степени родства, гл. 29)
- Common Pivot Chords and Ranking (Общие посредствующие аккорды, гл. 30)
- Canonical Modulation Plan Builder (План модуляции: завязка -> посредствующий аккорд -> K64/D7 -> D7 -> T, гл. 30, 31)
- Secondary Dominants and Tonicization (Побочные доминанты и вводные септаккорды, гл. 26-28)
"""
⋮----
@dataclass(frozen=True, slots=True)
class RelatedKeyInfo
⋮----
"""
    Metadata for a key related by the first degree of relationship (первая степень родства).

    Attributes:
        key: The related Key object.
        relation_name: Human-readable relation description (e.g. 'Dominant', 'Subdominant', 'Parallel minor').
        degree_in_source: Scale degree index (1..7) in the source key.
        is_subdominant_group: Whether this tonality belongs to the subdominant sphere (субдоминантовая группа/сфера).
        symbol: Classical harmonic degree symbol (e.g. 'V', 'VI', 'IV', 'II', 'III', 'iv', 'v', 'VII').
    """
⋮----
key: Key
relation_name: str
degree_in_source: int
is_subdominant_group: bool
symbol: str = ""
⋮----
@property
    def tonic(self) -> PitchClass
⋮----
"""Tonic pitch class of the related key."""
⋮----
@property
    def mode(self) -> Mode
⋮----
"""Mode of the related key."""
⋮----
def __str__(self) -> str
⋮----
tag = "[S-group]" if self.is_subdominant_group else "[D-group/Other]"
sym = f" ({self.symbol})" if self.symbol else ""
⋮----
@dataclass(frozen=True, slots=True)
class FirstDegreeRelations
⋮----
"""
    Container for the 6 first-degree related keys of a given source key (Бригадный учебник, гл. 29).

    Provides sequence protocol support and queries by relation, symbol, or harmonic group.
    """
⋮----
source_key: Key
relations: tuple[RelatedKeyInfo, ...]
⋮----
def __post_init__(self) -> None
⋮----
def __len__(self) -> int
⋮----
def __iter__(self)
⋮----
def __getitem__(self, index: Union[int, str]) -> RelatedKeyInfo
⋮----
res = self.by_symbol(index) or self.by_relation_name(index)
⋮----
@property
    def keys(self) -> tuple[Key, ...]
⋮----
"""Tuple of the 6 related Key objects."""
⋮----
@property
    def subdominant_group(self) -> tuple[RelatedKeyInfo, ...]
⋮----
"""Related keys belonging to the subdominant sphere."""
⋮----
@property
    def dominant_group(self) -> tuple[RelatedKeyInfo, ...]
⋮----
"""Related keys belonging to the dominant or tonic sphere."""
⋮----
def by_symbol(self, symbol: str) -> Optional[RelatedKeyInfo]
⋮----
"""Lookup related key by degree symbol ('V', 'VI', 'IV', 'II', 'III', 'iv', 'v', 'VII')."""
sym_clean = symbol.strip()
# 1. Exact case-sensitive match first (crucial to distinguish IV from iv, V from v)
⋮----
# 2. Case-insensitive fallback
⋮----
def by_relation_name(self, name: str) -> Optional[RelatedKeyInfo]
⋮----
"""Lookup related key by relation name case-insensitively."""
name_clean = name.strip().lower()
⋮----
def contains_key(self, target: Union[Key, str]) -> bool
⋮----
"""Check if target key is among the first-degree related keys."""
tgt_key = Key.from_string(target) if isinstance(target, str) else target
⋮----
def get_related_keys_first_degree(key: Union[Key, str]) -> FirstDegreeRelations
⋮----
"""
    Compute exactly 6 first-degree related keys according to Brigade Chapter 29.

    For a Major key (e.g. C Major):
    1. V  (Dominant): G Major
    2. VI (Submediant / Parallel minor): A MinorHarmonic
    3. IV (Subdominant): F Major
    4. II (Supertonic): D MinorHarmonic
    5. III (Mediant): E MinorHarmonic
    6. iv (Minor subdominant / гармоническая субдоминанта): F MinorHarmonic

    For a Minor key (e.g. A Minor):
    1. III (Parallel major): C Major
    2. iv  (Subdominant): D MinorHarmonic
    3. VI  (Submediant major): F Major
    4. v   (Natural minor dominant): E MinorNatural (or E MinorHarmonic)
    5. VII (Natural subtonic major): G Major
    6. V   (Harmonic major dominant): E Major
    """
src_key = Key.from_string(key) if isinstance(key, str) else key
⋮----
# Major key first degree relations
t = src_key.tonic.value
# 1. V Dominant (Major)
k_v = Key(tonic=PitchClass((t + 7) % 12), mode=Mode.MAJOR)
# 2. VI Parallel minor / Submediant (MinorHarmonic)
k_vi = Key(tonic=PitchClass((t + 9) % 12), mode=Mode.MINOR_HARMONIC)
# 3. IV Subdominant (Major)
k_iv = Key(tonic=PitchClass((t + 5) % 12), mode=Mode.MAJOR)
# 4. II Supertonic (MinorHarmonic)
k_ii = Key(tonic=PitchClass((t + 2) % 12), mode=Mode.MINOR_HARMONIC)
# 5. III Mediant (MinorHarmonic)
k_iii = Key(tonic=PitchClass((t + 4) % 12), mode=Mode.MINOR_HARMONIC)
# 6. iv Minor subdominant / гармоническая субдоминанта (MinorHarmonic)
k_sub_m = Key(tonic=PitchClass((t + 5) % 12), mode=Mode.MINOR_HARMONIC)
⋮----
relations = (
⋮----
# Minor key first degree relations
⋮----
# 1. III Parallel major (Major)
k_iii = Key(tonic=PitchClass((t + 3) % 12), mode=Mode.MAJOR)
# 2. iv Subdominant (MinorHarmonic)
k_iv = Key(tonic=PitchClass((t + 5) % 12), mode=Mode.MINOR_HARMONIC)
# 3. VI Submediant major (Major)
k_vi = Key(tonic=PitchClass((t + 8) % 12), mode=Mode.MAJOR)
# 4. v Natural minor dominant (MinorNatural)
k_v_nat = Key(tonic=PitchClass((t + 7) % 12), mode=Mode.MINOR_NATURAL)
# 5. VII Natural subtonic major (Major)
k_vii_nat = Key(tonic=PitchClass((t + 10) % 12), mode=Mode.MAJOR)
# 6. V Harmonic major dominant (Major)
k_v_harm = Key(tonic=PitchClass((t + 7) % 12), mode=Mode.MAJOR)
⋮----
# -----------------------------------------------------------------------------
# Pivot Chords (Посредствующие аккорды, гл. 30)
⋮----
@dataclass(frozen=True, slots=True)
class PivotChord
⋮----
"""
    Common diatonic/harmonic triad between two keys serving as pivot (посредствующий аккорд).

    Attributes:
        source_function: Function name in the source key (e.g. 'VI', 'T', 'S', 'II', 'III').
        target_function: Function name in the target key (e.g. 'II', 'IV', 'VI', 'T', 'D').
        pitch_classes: Exact 3 pitch classes of the triad (root, third, fifth).
        weight: Preference score (higher is better). Ch. 30 prioritizes subdominant functions in target.
        description: Harmonic explanation according to Brigade rules.
    """
⋮----
source_function: str
target_function: str
pitch_classes: tuple[PitchClass, PitchClass, PitchClass]
weight: float
description: str = ""
⋮----
@property
    def root(self) -> PitchClass
⋮----
"""Root pitch class of the triad."""
⋮----
@property
    def third(self) -> PitchClass
⋮----
"""Third pitch class of the triad."""
⋮----
@property
    def fifth(self) -> PitchClass
⋮----
"""Fifth pitch class of the triad."""
⋮----
@property
    def pitch_classes_set(self) -> frozenset[PitchClass]
⋮----
"""Frozenset of pitch classes for set comparisons."""
⋮----
@property
    def is_subdominant_in_target(self) -> bool
⋮----
"""True if chord functions in the subdominant group (II, IV, VI, S) in target key."""
clean = self.target_function.upper()
⋮----
pcs = "/".join(p.sharp_name for p in self.pitch_classes)
⋮----
def _get_key_triads(key: Key) -> list[tuple[str, tuple[PitchClass, PitchClass, PitchClass]]]
⋮----
"""
    Generate all primary and secondary triads (both diatonic and harmonic) in a key.

    Returns a list of (function_symbol, (root, third, fifth)).
    """
t = key.tonic.value
triads: list[tuple[str, tuple[PitchClass, PitchClass, PitchClass]]] = []
⋮----
def make_triad(r: int, third_offset: int, fifth_offset: int) -> tuple[PitchClass, PitchClass, PitchClass]
⋮----
# Natural major scale degrees
deg1 = t
deg2 = (t + 2) % 12
deg3 = (t + 4) % 12
deg4 = (t + 5) % 12
deg5 = (t + 7) % 12
deg6 = (t + 9) % 12
deg7 = (t + 11) % 12
⋮----
triads.append(("T", make_triad(deg1, 4, 7)))      # I: major (C-E-G)
triads.append(("II", make_triad(deg2, 3, 7)))     # II: minor (D-F-A)
triads.append(("III", make_triad(deg3, 3, 7)))    # III: minor (E-G-B)
triads.append(("IV", make_triad(deg4, 4, 7)))     # IV (S): major (F-A-C)
triads.append(("V", make_triad(deg5, 4, 7)))      # V (D): major (G-B-D)
triads.append(("VI", make_triad(deg6, 3, 7)))     # VI: minor (A-C-E)
triads.append(("VII", make_triad(deg7, 3, 6)))    # VII: dim (B-D-F)
⋮----
# Harmonic major (гармонический мажор: bVI = t+8)
b6 = (t + 8) % 12
triads.append(("iv", make_triad(deg4, 3, 7)))     # Minor subdominant (F-Ab-C)
triads.append(("bVI", make_triad(b6, 4, 7)))     # Major triad on bVI (Ab-C-Eb)
⋮----
# Minor key (harmonic and natural minor)
⋮----
deg3 = (t + 3) % 12
⋮----
deg6 = (t + 8) % 12
deg7_nat = (t + 10) % 12
deg7_harm = (t + 11) % 12
⋮----
triads.append(("t", make_triad(deg1, 3, 7)))          # i: minor (A-C-E)
triads.append(("II", make_triad(deg2, 3, 6)))         # ii°: dim (B-D-F)
triads.append(("III", make_triad(deg3, 4, 7)))        # III: major (C-E-G)
triads.append(("iv", make_triad(deg4, 3, 7)))         # iv (s): minor (D-F-A)
triads.append(("v", make_triad(deg5, 3, 7)))          # v (natural minor D): minor (E-G-B)
triads.append(("V", make_triad(deg5, 4, 7)))          # V (harmonic major D): major (E-G#-B)
triads.append(("VI", make_triad(deg6, 4, 7)))         # VI: major (F-A-C)
triads.append(("VII", make_triad(deg7_nat, 4, 7)))    # VII (natural subtonic): major (G-B-D)
triads.append(("vii°", make_triad(deg7_harm, 3, 6)))  # vii° (harmonic leading tone): dim (G#-B-D)
⋮----
def _calculate_pivot_weight(source_fn: str, target_fn: str, is_consonant: bool) -> float
⋮----
"""
    Score pivot chord according to Brigade Chapter 30 criteria:
    Best pivot chords are subdominant group in target key (II, IV, VI, II6),
    leading naturally into K64 or D7.
    """
target_clean = target_fn.upper()
source_clean = source_fn.upper()
⋮----
# 1. Target function score (dominant factor)
⋮----
score = 100.0  # II is the strongest subdominant bridge to K64/D7
⋮----
score = 90.0   # S is standard subdominant
⋮----
score = 80.0   # VI has strong subdominant color
⋮----
score = 40.0   # Tonic pivot is sluggish ("вяло", Ch. 30)
⋮----
score = 30.0   # Weak mediant relationship
⋮----
score = 15.0   # Dominant pivot cannot take K64 (D -> K64 forbidden)
⋮----
score = 10.0   # Diminished unstable triad
⋮----
score = 50.0
⋮----
# 2. Source function modifiers
⋮----
score += 10.0  # Natural departure directly from tonic
⋮----
score += 10.0  # Deceptive or submediant branch
⋮----
# 3. Consonance bonus
⋮----
"""
    Find all common triads between source and target keys, ranked by Brigade Chapter 30 preference.

    Returns:
        List of PivotChord objects sorted descending by weight (preferred pivot chords first).
    """
src = Key.from_string(source_key) if isinstance(source_key, str) else source_key
tgt = Key.from_string(target_key) if isinstance(target_key, str) else target_key
⋮----
src_triads = _get_key_triads(src)
tgt_triads = _get_key_triads(tgt)
⋮----
pivots: list[PivotChord] = []
seen: set[tuple[str, str, tuple[PitchClass, ...]]] = set()
⋮----
s_set = frozenset(s_pcs)
⋮----
t_set = frozenset(t_pcs)
⋮----
# Same pitch class content!
key_tuple = (s_fn, t_fn, s_pcs)
⋮----
# Check if major or minor triad (consonant) vs diminished
# In 12-TET, root to fifth is 7 semitones for major/minor
root_val = s_pcs[0].value
fifth_val = s_pcs[2].value
is_consonant = ((fifth_val - root_val) % 12) == 7
⋮----
weight = _calculate_pivot_weight(s_fn, t_fn, is_consonant)
⋮----
desc = (
⋮----
# Sort descending by weight
⋮----
# Modulation Plan Builder (План модуляции, гл. 30, 31)
⋮----
"""
    Constructs a canonical Brigade modulation sequence:
    Source cadence/progression -> Pivot chord -> Target K64 (or target D7) -> Target D7 -> Target T.

    Args:
        source_key: Initial tonality.
        target_key: Destination tonality.
        pivot_chord: Explicit pivot chord to use; if None, optimal pivot chord is selected automatically.
        include_full_cadence: If True, uses full initial cadence (T-S-D-T); if False, starts directly with T.

    Returns:
        List of (Key, chord_symbol) tuples representing the progression.
    """
⋮----
candidates = find_pivot_chords(src, tgt)
⋮----
pivot_chord = candidates[0]
⋮----
plan: list[tuple[Key, str]] = []
⋮----
# 1. Source key exposure / cadence
⋮----
# 2. Pivot chord
# If the pivot chord in source key is already T and we just played T, avoid redundant T-T
⋮----
# Re-interpreted in target key
⋮----
# 3. Target modulating cadence
# Brigade Ch. 30:
# If pivot chord is dominant group in target key (V, D), K64 cannot follow (D -> K64 forbidden).
# Otherwise (II, IV, VI, T, III), standard K64 is introduced on strong beat!
target_fn_upper = pivot_chord.target_function.upper()
⋮----
# Straight into D7 -> T
⋮----
# Secondary Dominants and Tonicization (Побочные доминанты, гл. 26-28)
⋮----
@dataclass(frozen=True, slots=True)
class SecondaryDominant
⋮----
"""
    Secondary dominant (побочная доминанта / DD) in classical functional harmony.

    Represents dominant triads, dominant seventh chords, and leading-tone seventh chords
    resolving to secondary diatonic scale degrees (Дубовский et al., гл. 26-28).

    Attributes:
        name: Common analytical symbol (e.g. 'DD', 'DD7', 'D7/II', 'D7/VI', 'VII7/V').
        key: Home tonality in which the secondary dominant operates.
        target_degree: Scale degree index in key being tonicized (e.g. 5, 2, 6, 4, 3).
        root: Root PitchClass of the secondary dominant.
        third: Third PitchClass (major third from root = leading tone to target tonic).
        fifth: Fifth PitchClass (perfect fifth from root).
        seventh: Seventh PitchClass if seventh chord, else None.
        is_seventh: Whether this chord contains a seventh factor.
        is_diminished_seventh: Whether this is a diminished leading-tone seventh chord (VII7/X).
    """
⋮----
name: str
⋮----
target_degree: int
root: PitchClass
third: PitchClass
fifth: PitchClass
seventh: Optional[PitchClass] = None
is_seventh: bool = False
is_diminished_seventh: bool = False
⋮----
@property
    def pitch_classes(self) -> tuple[PitchClass, ...]
⋮----
"""Ordered tuple of pitch classes (root, third, fifth [, seventh])."""
⋮----
"""Frozenset of pitch classes for set operations."""
⋮----
@property
    def factors(self) -> dict[str, PitchClass]
⋮----
"""Mapping from factor names to PitchClasses."""
res = {
⋮----
@property
    def target_tonic(self) -> PitchClass
⋮----
"""The pitch class of the resolution target's tonic."""
⋮----
# Minor key target degree
⋮----
# Natural subtonic VII in minor
⋮----
@classmethod
    def create(cls, key: Union[Key, str], symbol: str) -> SecondaryDominant
⋮----
"""
        Create a SecondaryDominant instance from a symbolic name in key.

        Supported notations:
        - 'DD': Double dominant triad (D to V degree)
        - 'DD7': Double dominant seventh chord (D7 to V degree)
        - 'VII7/V', 'DDVII7': Diminished leading-tone seventh to V degree
        - 'D/II', 'D7/II', 'D7/2': Secondary dominant to II degree
        - 'D/III', 'D7/III', 'D7/3': Secondary dominant to III degree
        - 'D/IV', 'D7/IV', 'D7/4': Secondary dominant to IV degree
        - 'D/V', 'D7/V': Synonym for DD / DD7
        - 'D/VI', 'D7/VI', 'D7/6': Secondary dominant to VI degree
        - 'D/VII', 'D7/VII', 'D7/7': Secondary dominant to VII natural degree (in minor)
        - 'VII7/II', 'VII7/IV', 'VII7/VI': Secondary leading-tone diminished 7th chords
        """
k = Key.from_string(key) if isinstance(key, str) else key
raw = symbol.strip()
⋮----
# 1. Double dominant special aliases
⋮----
# 2. Match patterns like 'D7/II', 'D/IV', 'VII7/VI'
m = re.match(r"^(D7|D|VII7)[/_]([0-9]+|[IViv]+)$", raw, re.IGNORECASE)
⋮----
chord_type_upper = chord_type.upper()
⋮----
degree_map = {
deg_clean = deg_str.upper()
⋮----
target_degree = degree_map[deg_clean]
is_seventh = "7" in chord_type_upper
is_leading_tone = "VII" in chord_type_upper
⋮----
"""
        Build a secondary dominant or leading-tone chord tonicizing target_degree in key.
        """
⋮----
# Find pitch class of target tonic
⋮----
target_pc = key.pitch_class_for_degree(target_degree)
⋮----
# In minor, secondary dominant targets natural VII degree (subtonic)
target_pc = PitchClass((key.tonic.value + 10) % 12)
⋮----
t_val = target_pc.value
⋮----
# Diminished seventh chord built on the leading tone to target (1 semitone below target)
root = PitchClass((t_val + 11) % 12)
third = PitchClass((root.value + 3) % 12)
fifth = PitchClass((root.value + 6) % 12)
seventh = PitchClass((root.value + 9) % 12) if is_seventh else None
chord_name = name or (f"VII7/{target_degree}" if is_seventh else f"VII/{target_degree}")
⋮----
# Standard secondary dominant (major triad or dominant 7th, root is P5 above target)
root = PitchClass((t_val + 7) % 12)
third = PitchClass((root.value + 4) % 12)  # Leading tone to target!
fifth = PitchClass((root.value + 7) % 12)
seventh = PitchClass((root.value + 10) % 12) if is_seventh else None
⋮----
default_name = f"D7/{target_degree}" if is_seventh else f"D/{target_degree}"
⋮----
default_name = "DD7" if is_seventh else "DD"
⋮----
chord_name = name or default_name
⋮----
def get_secondary_dominants(key: Union[Key, str]) -> list[SecondaryDominant]
⋮----
"""
    Enumerate all canonical secondary dominants and leading-tone seventh chords in key.
    """
⋮----
dominants: list[SecondaryDominant] = []
⋮----
# Eligible degrees in major: II, III, IV, V, VI
degrees = [2, 3, 4, 5, 6]
⋮----
# Eligible degrees in minor: III, IV, V, VI, VII
degrees = [3, 4, 5, 6, 7]
⋮----
# Dominant triad
⋮----
# Dominant seventh
⋮----
# Leading-tone seventh (VII7/deg)
````

## File: src/harmony/core/pitch.py
````python
"""
Core domain model: Pitch, PitchClass, ScaleDegree, and Interval.

Provides fundamental representations of musical pitch in 12-tone equal temperament (12-TET),
conforming to standard MIDI specifications and Russian classical music theory
(Бригадный учебник гармонии).
"""
⋮----
_SHARP_NAMES: tuple[str, ...] = (
_FLAT_NAMES: tuple[str, ...] = (
_RUSSIAN_NAMES: tuple[str, ...] = (
⋮----
class PitchClass(IntEnum)
⋮----
"""
    Pitch class representation in modulo 12 arithmetic (Z_12).

    Values range from 0 (C) through 11 (B).
    Enharmonic aliases are provided (e.g., C_SHARP == DB == 1).
    """
⋮----
C = 0
C_SHARP = 1
DB = 1
D = 2
D_SHARP = 3
EB = 3
E = 4
F = 5
F_SHARP = 6
GB = 6
G = 7
G_SHARP = 8
AB = 8
A = 9
A_SHARP = 10
BB = 10
B = 11
⋮----
@classmethod
    def from_name(cls, name: str) -> PitchClass
⋮----
"""
        Parse pitch class from note name string (e.g. 'C', 'C#', 'Db', 'F♯', 'B♭', 'H').
        """
cleaned = name.strip()
⋮----
# Normalize unicode accidentals and case
normalized = cleaned.replace("♯", "#").replace("♭", "b")
upper = normalized.upper()
⋮----
name_map = {
⋮----
@classmethod
    def from_midi(cls, midi: int) -> PitchClass
⋮----
"""Convert MIDI number to PitchClass (midi % 12)."""
⋮----
@property
    def sharp_name(self) -> str
⋮----
"""Standard sharp note name (e.g. 'C#')."""
⋮----
@property
    def flat_name(self) -> str
⋮----
"""Standard flat note name (e.g. 'Db')."""
⋮----
@property
    def russian_name(self) -> str
⋮----
"""Russian note name (e.g. 'До#')."""
⋮----
def transpose(self, semitones: int) -> PitchClass
⋮----
"""Transpose pitch class by given number of semitones."""
⋮----
def interval_to(self, other: PitchClass) -> int
⋮----
"""Number of semitones ascending from self to other modulo 12."""
⋮----
def __int__(self) -> int
⋮----
def __str__(self) -> str
⋮----
def __repr__(self) -> str
⋮----
def __add__(self, other: Union[int, Interval]) -> PitchClass
⋮----
def __sub__(self, other: Union[int, Interval, PitchClass]) -> Union[PitchClass, int]
⋮----
PitchClass.SHARP_NAMES = _SHARP_NAMES  # type: ignore[attr-defined]
PitchClass.FLAT_NAMES = _FLAT_NAMES    # type: ignore[attr-defined]
PitchClass.RUSSIAN_NAMES = _RUSSIAN_NAMES  # type: ignore[attr-defined]
⋮----
@dataclass(frozen=True, slots=True)
class Interval
⋮----
"""
    Musical interval representation with semitone distance and Russian music theory naming.

    Supports simple and compound intervals:
    0: ч1, 1: м2, 2: б2, 3: м3 (или ув2), 4: б3, 5: ч4, 6: тритон (ув4/ум5),
    7: ч5, 8: м6, 9: б6, 10: м7, 11: б7, 12: ч8, etc.
    """
⋮----
semitones: int
name: str = ""
⋮----
STANDARD_NAMES: ClassVar[dict[int, str]] = {
⋮----
NAME_TO_SEMITONES: ClassVar[dict[str, int]] = {
⋮----
def __post_init__(self) -> None
⋮----
abs_st = abs(self.semitones)
default_name = self.STANDARD_NAMES.get(abs_st, f"{abs_st}st")
⋮----
@classmethod
    def from_semitones(cls, semitones: int, name: Optional[str] = None) -> Interval
⋮----
"""Create an Interval from integer semitone count and optional custom name."""
⋮----
@classmethod
    def from_name(cls, name: str) -> Interval
⋮----
"""Create an Interval from its standard Russian name (e.g. 'ч5', 'ув2', 'м7')."""
cleaned = name.strip().lower()
# Direct check
⋮----
@classmethod
    def from_pitches(cls, lower: Pitch, upper: Pitch) -> Interval
⋮----
"""Calculate interval directed from lower pitch to upper pitch."""
diff = upper.midi_number - lower.midi_number
⋮----
@property
    def abs_semitones(self) -> int
⋮----
"""Absolute semitone distance."""
⋮----
@property
    def simple_semitones(self) -> int
⋮----
"""Interval modulo 12 (within one octave)."""
⋮----
@property
    def octaves(self) -> int
⋮----
"""Number of full octaves spanned."""
⋮----
@property
    def is_unison(self) -> bool
⋮----
"""True if interval is a perfect unison (0 semitones)."""
⋮----
@property
    def is_step(self) -> bool
⋮----
"""True if interval is stepwise motion (minor or major second, 1 or 2 semitones)."""
⋮----
@property
    def is_leap(self) -> bool
⋮----
"""True if interval is a melodic leap (>= 3 semitones)."""
⋮----
@property
    def is_tritone(self) -> bool
⋮----
"""True if interval is an augmented 4th / diminished 5th (6 semitones mod 12)."""
⋮----
@property
    def is_perfect_fifth(self) -> bool
⋮----
"""True if interval is a perfect fifth (7 semitones mod 12)."""
⋮----
@property
    def is_perfect_octave(self) -> bool
⋮----
"""True if interval is an exact multiple of an octave (> 0 semitones)."""
⋮----
@property
    def is_augmented_second(self) -> bool
⋮----
"""True if marked explicitly as an augmented second (3 semitones)."""
⋮----
@property
    def is_seventh(self) -> bool
⋮----
"""True if interval is a seventh (10 or 11 semitones mod 12)."""
⋮----
def __add__(self, other: Interval) -> Interval
⋮----
def __sub__(self, other: Interval) -> Interval
⋮----
def __neg__(self) -> Interval
⋮----
def __lt__(self, other: Union[Interval, int]) -> bool
⋮----
other_val = other.semitones if isinstance(other, Interval) else other
⋮----
def __le__(self, other: Union[Interval, int]) -> bool
⋮----
def __gt__(self, other: Union[Interval, int]) -> bool
⋮----
def __ge__(self, other: Union[Interval, int]) -> bool
⋮----
@dataclass(frozen=True, slots=True)
class ScaleDegree
⋮----
"""
    Scale degree (ступень лада) I..VII with optional chromatic alterations.

    degree: 1 to 7 (corresponds to I, II, III, IV, V, VI, VII).
    alteration: -2 (bb), -1 (b), 0 (natural), +1 (#), +2 (##).
    """
⋮----
degree: int
alteration: int = 0
⋮----
ROMAN_NUMERALS: ClassVar[tuple[str, ...]] = (
⋮----
@classmethod
    def from_str(cls, s: str) -> ScaleDegree
⋮----
"""
        Parse scale degree from roman numeral string (e.g. 'I', 'IV', 'VII#', 'bII', '#VII').
        """
raw = s.strip()
⋮----
roman_map = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6, "VII": 7}
⋮----
# Check prefix alteration (e.g. 'bII', '#VII', 'bbVI')
prefix_match = re.match(r"^(bb|b|##|#)?(VII|VI|IV|V|III|II|I)(bb|b|##|#)?$", raw, re.IGNORECASE)
⋮----
# Try numeric degree like '1', '4', '7#'
num_match = re.match(r"^(bb|b|##|#)?([1-7])(bb|b|##|#)?$", raw, re.IGNORECASE)
⋮----
deg_int = int(num_str)
⋮----
deg_int = roman_map[rom_str.upper()]
⋮----
alt_str = (pre or "") + (post or "")
alt_str = alt_str.lower().replace("♯", "#").replace("♭", "b")
⋮----
alt_val = 0
⋮----
alt_val = 1
⋮----
alt_val = 2
⋮----
alt_val = -1
⋮----
alt_val = -2
⋮----
@property
    def roman(self) -> str
⋮----
"""Roman numeral for the degree without alteration (e.g. 'VII')."""
⋮----
@property
    def alteration_symbol(self) -> str
⋮----
"""String accidental symbol ('b', '#', or empty)."""
⋮----
@property
    def name(self) -> str
⋮----
"""Full name with alteration (e.g. 'VII#', 'bII', 'I')."""
⋮----
@property
    def index(self) -> int
⋮----
"""0-based scale degree index (0..6)."""
⋮----
@property
    def is_tonic(self) -> bool
⋮----
"""True if unaltered degree I."""
⋮----
@property
    def is_subdominant(self) -> bool
⋮----
"""True if unaltered degree IV."""
⋮----
@property
    def is_dominant(self) -> bool
⋮----
"""True if unaltered degree V."""
⋮----
@property
    def is_leading_tone(self) -> bool
⋮----
"""True if degree VII (leading tone)."""
⋮----
# Predefined scale degree constants
ScaleDegree.I = ScaleDegree(1, 0)       # type: ignore[attr-defined]
ScaleDegree.II = ScaleDegree(2, 0)      # type: ignore[attr-defined]
ScaleDegree.III = ScaleDegree(3, 0)     # type: ignore[attr-defined]
ScaleDegree.IV = ScaleDegree(4, 0)      # type: ignore[attr-defined]
ScaleDegree.V = ScaleDegree(5, 0)       # type: ignore[attr-defined]
ScaleDegree.VI = ScaleDegree(6, 0)      # type: ignore[attr-defined]
ScaleDegree.VII = ScaleDegree(7, 0)     # type: ignore[attr-defined]
ScaleDegree.VII_SHARP = ScaleDegree(7, 1)  # type: ignore[attr-defined]
ScaleDegree.FLAT_II = ScaleDegree(2, -1)   # type: ignore[attr-defined]
ScaleDegree.FLAT_VI = ScaleDegree(6, -1)   # type: ignore[attr-defined]
⋮----
@dataclass(frozen=True, slots=True)
class Pitch
⋮----
"""
    Absolute musical pitch represented as a standard MIDI note number (0..127).

    Middle C (C4) is MIDI 60.
    Provides octave calculation, pitch class projection, and arithmetic.
    """
⋮----
midi_number: int
⋮----
@classmethod
    def from_midi(cls, midi: int) -> Pitch
⋮----
"""Create Pitch from raw MIDI integer."""
⋮----
@classmethod
    def from_name(cls, name: str) -> Pitch
⋮----
"""
        Parse pitch from scientific pitch notation (e.g. 'C4', 'G#3', 'Bb2', 'C-1').
        """
⋮----
match = re.match(r"^([A-Ga-gHh][#♯b♭]?)(-?\d+)$", cleaned)
⋮----
pc = PitchClass.from_name(note_part)
octave = int(oct_part)
midi = (octave + 1) * 12 + pc.value
⋮----
@property
    def octave(self) -> int
⋮----
"""Scientific octave number (e.g. 4 for C4 = 60)."""
⋮----
@property
    def pitch_class(self) -> PitchClass
⋮----
"""PitchClass in Z_12 (midi_number % 12)."""
⋮----
@property
    def note_name(self) -> str
⋮----
"""Standard scientific note name with sharp preference (e.g. 'C4', 'F#3')."""
⋮----
def get_note_name(self, prefer_flat: bool = False) -> str
⋮----
"""Get note name with preferred accidental representation."""
pc_name = self.pitch_class.flat_name if prefer_flat else self.pitch_class.sharp_name
⋮----
def transpose(self, semitones: int) -> Pitch
⋮----
"""Return a new Pitch shifted by the given semitone delta."""
⋮----
def __lt__(self, other: Union[Pitch, int]) -> bool
⋮----
other_val = other.midi_number if isinstance(other, Pitch) else other
⋮----
def __le__(self, other: Union[Pitch, int]) -> bool
⋮----
def __gt__(self, other: Union[Pitch, int]) -> bool
⋮----
def __ge__(self, other: Union[Pitch, int]) -> bool
⋮----
def __add__(self, other: Union[int, Interval]) -> Pitch
⋮----
def __sub__(self, other: Union[int, Interval, Pitch]) -> Union[Pitch, Interval]
````

## File: src/harmony/core/voicing.py
````python
"""
Core domain model: Voicing, Spacing, and Voice ranges.

Implements the 4-part SATB vertical slice (Soprano, Alto, Tenor, Bass),
voice-ordering invariants (no voice crossing), acoustic spacing rules,
voice range limits, and spacing classification (Close / Wide / Mixed)
per the Brigada harmony textbook (docs/BRIGADE_RULES.md, docs/MATH_MODEL.md).
"""
⋮----
class Voice(str, Enum)
⋮----
"""The four classical SATB choir voices."""
⋮----
SOPRANO = "Soprano"
ALTO = "Alto"
TENOR = "Tenor"
BASS = "Bass"
⋮----
class Spacing(str, Enum)
⋮----
"""
    Chord spacing (расположение аккорда):
    - CLOSE (Тесное): S-A and A-T without skipped chord tones (intervals <= 4 semitones / 3rd, 4th).
    - WIDE (Широкое / Open): S-A and A-T have exactly one chord tone skipped (intervals 5-12 / 5th, 6th, 8ve).
    - MIXED (Смешанное): mixed spacing, leaps, or irregular seventh chord arrangements.
    """
⋮----
CLOSE = "Close"
WIDE = "Wide"
MIXED = "Mixed"
⋮----
# Alias for wide
OPEN = "Wide"
⋮----
@dataclass(frozen=True, slots=True)
class Voicing
⋮----
"""
    A 4-part SATB chord voicing vertical slice: (Soprano, Alto, Tenor, Bass).

    Immutable, hashable, and equipped with verification methods for:
    - Voice ordering (S >= A >= T >= B, no voice crossing)
    - Acoustic spacing limits (S-A <= 12, A-T <= 12, T-B <= 24)
    - Standard voice range constraints
    - Spacing classification (Close / Wide / Mixed)
    """
⋮----
soprano: Pitch
alto: Pitch
tenor: Pitch
bass: Pitch
⋮----
# Standard vocal ranges from Brigada textbook (docs/BRIGADE_RULES.md)
# Soprano: C4 - A5 (60 - 81)
# Alto:    G3 - D5 (55 - 74)
# Tenor:   C3 - G4 (48 - 67)
# Bass:    E2 - C4 (40 - 60)
RANGES: ClassVar[dict[Voice, tuple[int, int]]] = {
⋮----
# Short aliases
⋮----
@property
    def S(self) -> Pitch
⋮----
"""Soprano pitch."""
⋮----
@property
    def A(self) -> Pitch
⋮----
"""Alto pitch."""
⋮----
@property
    def T(self) -> Pitch
⋮----
"""Tenor pitch."""
⋮----
@property
    def B(self) -> Pitch
⋮----
"""Bass pitch."""
⋮----
# -------------------------------------------------------------------------
# Constructors
⋮----
@classmethod
    def from_midi(cls, s: int, a: int, t: int, b: int) -> Voicing
⋮----
"""Create Voicing from 4 integer MIDI numbers (S, A, T, B)."""
⋮----
@classmethod
    def from_tuple(cls, satb: tuple[int, int, int, int]) -> Voicing
⋮----
"""Create Voicing from a 4-tuple of MIDI numbers (S, A, T, B)."""
⋮----
@classmethod
    def from_pitches(cls, s: Pitch, a: Pitch, t: Pitch, b: Pitch) -> Voicing
⋮----
"""Create Voicing from 4 Pitch instances."""
⋮----
@classmethod
    def from_names(cls, s: str, a: str, t: str, b: str) -> Voicing
⋮----
"""Create Voicing from 4 note names (e.g. 'C5', 'G4', 'E4', 'C3')."""
⋮----
# Invariant & Ordering Checks
⋮----
@property
    def is_ordered(self) -> bool
⋮----
"""
        True if voices are strictly non-crossing: S >= A >= T >= B.
        """
⋮----
@property
    def has_voice_crossing(self) -> bool
⋮----
"""True if any voice cross is present (S < A, A < T, or T < B)."""
⋮----
# Voice Intervals
⋮----
@property
    def interval_sa(self) -> Interval
⋮----
"""Interval from Alto up to Soprano (S - A)."""
diff = self.soprano.midi_number - self.alto.midi_number
⋮----
@property
    def interval_at(self) -> Interval
⋮----
"""Interval from Tenor up to Alto (A - T)."""
diff = self.alto.midi_number - self.tenor.midi_number
⋮----
@property
    def interval_tb(self) -> Interval
⋮----
"""Interval from Bass up to Tenor (T - B)."""
diff = self.tenor.midi_number - self.bass.midi_number
⋮----
@property
    def interval_st(self) -> Interval
⋮----
"""Interval from Tenor up to Soprano (S - T)."""
diff = self.soprano.midi_number - self.tenor.midi_number
⋮----
@property
    def interval_sb(self) -> Interval
⋮----
"""Interval from Bass up to Soprano (S - B)."""
diff = self.soprano.midi_number - self.bass.midi_number
⋮----
@property
    def interval_ab(self) -> Interval
⋮----
"""Interval from Bass up to Alto (A - B)."""
diff = self.alto.midi_number - self.bass.midi_number
⋮----
# Range and Spacing Constraint Checks
⋮----
def in_ranges(self) -> bool
⋮----
"""
        Check if all 4 voices reside within standard Brigada vocal limits:
        S: 60..81, A: 55..74, T: 48..67, B: 40..60.
        """
⋮----
def range_violations(self) -> list[str]
⋮----
"""Return human-readable list of range violations, empty if valid."""
violations = []
voices = [
⋮----
def is_spacing_valid(self) -> bool
⋮----
"""
        Check if acoustic spacing bounds are satisfied:
        - S - A <= 12 (no upper voice gap > 1 octave)
        - A - T <= 12 (no upper voice gap > 1 octave)
        - T - B <= 24 (bass-tenor gap <= 2 octaves)
        - No voice crossing (is_ordered)
        """
⋮----
def spacing_violations(self) -> list[str]
⋮----
"""Return list of spacing rule violations."""
⋮----
def is_statically_valid(self) -> bool
⋮----
"""Complete static validity per MATH_MODEL.md section 2.2."""
⋮----
# Spacing Classification (Close / Wide / Mixed)
⋮----
def determine_spacing(self, chord_def: Optional[ChordDefinition] = None) -> Spacing
⋮----
"""
        Determine spacing (Close, Wide, or Mixed).

        If chord_def is provided, spacing is evaluated by counting skipped chord tones:
        - Close: 0 chord tones skipped between S-A and 0 between A-T.
        - Wide: 1 chord tone skipped between S-A and 1 between A-T.
        - Mixed: any other distribution.

        If chord_def is not provided, interval thresholds are used:
        - Close: S-A <= 4 and A-T <= 4.
        - Wide: 5 <= S-A <= 12 and 5 <= A-T <= 12.
        - Mixed: otherwise.
        """
⋮----
# Count intermediate chord tones strictly between S and A
sa_chord_tones = sum(
# Count intermediate chord tones strictly between A and T
at_chord_tones = sum(
⋮----
# Heuristic interval-based spacing
sa = self.interval_sa.semitones
at = self.interval_at.semitones
⋮----
# Conversions and Sequence Interface
⋮----
def to_midi_tuple(self) -> tuple[int, int, int, int]
⋮----
"""Return 4-tuple of MIDI numbers (S, A, T, B)."""
⋮----
def to_pitches(self) -> tuple[Pitch, Pitch, Pitch, Pitch]
⋮----
"""Return 4-tuple of Pitch objects (S, A, T, B)."""
⋮----
def to_pitch_classes(self) -> tuple[PitchClass, PitchClass, PitchClass, PitchClass]
⋮----
"""Return 4-tuple of PitchClasses (S, A, T, B)."""
⋮----
def __iter__(self) -> Iterator[Pitch]
⋮----
"""Iterate over voices in order: Soprano, Alto, Tenor, Bass."""
⋮----
def __len__(self) -> int
⋮----
def __getitem__(self, idx: Union[int, Voice]) -> Pitch
⋮----
def __str__(self) -> str
⋮----
def __repr__(self) -> str
````

## File: src/harmony/export/utils.py
````python
"""
Internal normalization and pitch spelling utilities for score exporters.
"""
⋮----
# Key signature fifths offset mapping
_MAJOR_FIFTHS: dict[str, int] = {
_MINOR_FIFTHS: dict[str, int] = {
⋮----
# Standard scale spelling steps for fifths (-7 to +7)
# Pitch class 0..11 to (step, alter) for sharp and flat orientations
_SHARP_SPELLING: list[tuple[str, int]] = [
⋮----
("C", 0),   # 0
("C", 1),   # 1 C#
("D", 0),   # 2
("D", 1),   # 3 D#
("E", 0),   # 4
("F", 0),   # 5
("F", 1),   # 6 F#
("G", 0),   # 7
("G", 1),   # 8 G#
("A", 0),   # 9
("A", 1),   # 10 A#
("B", 0),   # 11
⋮----
_FLAT_SPELLING: list[tuple[str, int]] = [
⋮----
("D", -1),  # 1 Db
⋮----
("E", -1),  # 3 Eb
⋮----
("G", -1),  # 6 Gb
⋮----
("A", -1),  # 8 Ab
⋮----
("B", -1),  # 10 Bb
⋮----
def extract_satb(voicing: Any) -> tuple[int, int, int, int]
⋮----
"""
    Extracts (soprano, alto, tenor, bass) integer MIDI pitches from any voicing representation.
    Supports Voicing dataclass, NamedTuple, tuple/list, and dict.
    """
⋮----
s = voicing.get("soprano", voicing.get("S", voicing.get("s", 60)))
a = voicing.get("alto", voicing.get("A", voicing.get("a", 55)))
t = voicing.get("tenor", voicing.get("T", voicing.get("t", 48)))
b = voicing.get("bass", voicing.get("B", voicing.get("b", 40)))
⋮----
def extract_chord_symbol(chord: Any) -> str
⋮----
"""
    Normalizes chord symbol to clean Roman numeral string representation.
    """
⋮----
fn = chord.function
fn_val = fn.value if hasattr(fn, "value") else str(fn)
inv = getattr(chord, "inversion", None)
⋮----
inv_sym = getattr(inv, "symbol", "")
⋮----
def extract_key_info(key: Any) -> tuple[str, str, int, bool, int]
⋮----
"""
    Returns (tonic_name, mode_name, tonic_pc, is_minor, fifths).
    """
tonic_name = "C"
mode_name = "Major"
tonic_pc = 0
is_minor = False
⋮----
t = getattr(key, "tonic")
⋮----
tonic_name = t.sharp_name
tonic_pc = t.value
⋮----
tonic_name = str(t.name)
tonic_pc = getattr(t, "value", 0)
⋮----
tonic_name = str(t).strip()
tonic_pc = getattr(key, "tonic_pc", 0)
⋮----
m = getattr(key, "mode")
⋮----
is_minor = bool(m.is_minor)
mode_name = m.value if hasattr(m, "value") else str(m)
⋮----
mode_str = str(m).strip()
mode_name = mode_str
is_minor = "minor" in mode_str.lower() or "moll" in mode_str.lower()
⋮----
tonic_name = str(key.get("tonic", "C")).strip()
mode_str = str(key.get("mode", "Major")).strip()
⋮----
cleaned = key.strip()
⋮----
is_minor = True
mode_name = "MinorHarmonic"
⋮----
raw_tonic = cleaned.split("-")[0].split()[0].replace("moll", "").replace("dur", "").strip().rstrip("m").rstrip("M")
tonic_name = raw_tonic or "C"
⋮----
# Calculate fifths for standard key signatures
norm_tonic = tonic_name.upper().replace("♯", "#").replace("♭", "b")
⋮----
fifths = _MINOR_FIFTHS.get(norm_tonic, 0)
⋮----
fifths = _MAJOR_FIFTHS.get(norm_tonic, 0)
⋮----
def midi_to_spelled_note(midi: int, fifths: int = 0, is_minor: bool = False) -> tuple[str, int, int, str]
⋮----
"""
    Spells a MIDI pitch number (0..127) as (step, alter, octave, note_name).
    Example: 60 -> ('C', 0, 4, 'C4'), 61 with fifths=1 -> ('C', 1, 4, 'C#4').
    """
pc = midi % 12
octave = (midi // 12) - 1
⋮----
# In minor keys with harmonic minor, raised 7th degree is standard
# e.g., in A minor (fifths=0), pc 8 is G#
prefer_sharp = fifths >= 0
if is_minor and fifths == 0 and pc == 8:  # G# in A minor
⋮----
elif is_minor and fifths == -1 and pc == 1:  # C# in D minor
⋮----
elif is_minor and fifths == -2 and pc == 6:  # F# in G minor
⋮----
elif is_minor and fifths == -3 and pc == 11:  # B natural in C minor
⋮----
alter_str = "#" if alter == 1 else ("b" if alter == -1 else "")
name = f"{step}{alter_str}{octave}"
⋮----
def classify_voicing_spacing(s: int, a: int, t: int) -> str
⋮----
"""
    Classifies spacing into 'Close', 'Wide', or 'Mixed' based on SAT intervals.
    """
d_sa = s - a
d_at = a - t
````

## File: src/harmony/ml/__init__.py
````python
"""
Statistical n-gram style prior module for classical harmony (NOT a neural network) [EXPERIMENTAL].
"""
⋮----
__all__ = ["StylePriorModel"]
````

## File: backend/key_detector.py
````python
"""
Key detection and canonical keys catalog.
Provides 24 canonical keys (12 major, 12 harmonic minor) and automatic key detection.
"""
⋮----
CANONICAL_KEYS = [
⋮----
# 12 Majors
⋮----
# 12 Harmonic Minors
⋮----
# Krumhansl-Kessler key profiles (distribution over 12 semitones from tonic)
# Major profile: tonic, b2, 2, b3, 3, 4, #4, 5, b6, 6, b7, 7
KRUMHANSL_MAJOR: tuple[float, ...] = (
# Minor profile: tonic, b2, 2, b3, 3, 4, #4, 5, b6, 6, b7, 7
KRUMHANSL_MINOR: tuple[float, ...] = (
⋮----
# Standard duration weights (relative to quarter note = 1.0)
DURATION_WEIGHTS: dict[str, float] = {
⋮----
def _parse_duration(val: Any) -> float
⋮----
"""Parse duration specifier (name, numeric, or dotted) to quarter-note weight."""
⋮----
s = val.strip().lower()
⋮----
num = float(s)
⋮----
base = s[:-1]
⋮----
base = s[7:]
⋮----
def _pearson_correlation(x: Sequence[float], y: Sequence[float]) -> float
⋮----
"""Calculate Pearson correlation coefficient r between two 12-dimensional vectors."""
n = len(x)
⋮----
mx = sum(x) / n
my = sum(y) / n
num = 0.0
var_x = 0.0
var_y = 0.0
⋮----
dx = xi - mx
dy = yi - my
⋮----
denom = math.sqrt(var_x * var_y)
⋮----
def detect_key_from_melody(melody: Sequence[int | dict[str, Any]]) -> dict[str, Any]
⋮----
"""
    Auto-detects the musical key from a soprano melody sequence using a weighted
    Krumhansl-Schmuckler profile correlation algorithm.

    Scores candidates based on:
    - Pearson correlation of pitch-class distribution (weighted by note duration)
      with empirical Major and Minor key profiles (Krumhansl & Kessler).
    - Modest final tonic bonus (+12.0) to avoid hijacking half-cadence endings
      (such as C D E F G ending on G dominant or A B C D E ending on E dominant).
    - Melodic cadence bonuses for authentic (V -> I, +8.0) and deceptive/interrupted
      (V -> VI, +5.0) motions at the end of the melody.
    """
pitches: list[int] = []
durations: list[float] = []
⋮----
last_pc = pitches[-1] % 12
penult_pc = pitches[-2] % 12 if len(pitches) >= 2 else None
⋮----
# Compute duration-weighted pitch class distribution vector (12 bins)
x = [0.0] * 12
⋮----
best_key = CANONICAL_KEYS[0]
best_score = -999999.0
⋮----
k_obj = Key(tonic=cand["tonic"], mode=cand["mode"])
tonic_pc = k_obj.tonic_pc
is_minor = "minor" in cand["mode"].lower()
⋮----
prof = KRUMHANSL_MINOR if is_minor else KRUMHANSL_MAJOR
# Shift profile so that index 0 corresponds to cand tonic_pc
shifted = [prof[(i - tonic_pc) % 12] for i in range(12)]
r = _pearson_correlation(x, shifted)
⋮----
# Scale correlation to base score [-100.0, 100.0]
score = r * 100.0
⋮----
# Modest final tonic bonus (capped <= 15.0)
⋮----
# Cadence detection: V -> I or V -> VI at melody conclusion
⋮----
dom_pc = (tonic_pc + 7) % 12
vi_pc = (tonic_pc + (8 if is_minor else 9)) % 12
⋮----
best_score = score
best_key = cand
````

## File: docs/BRIGADE_RULES.md
````markdown
# Свод правил гармонизации по «Бригадному учебнику»
*(И. Дубовский, С. Евсеев, И. Способин, В. Соколов — «Учебник гармонии»)*

---

## 1. Четырехголосный склад (SATB) и диапазоны голосов

В классической четырехголосной партитуре каждый голос имеет строго очерченный рабочий диапазон:

| Голос | Обозначение | Диапазон (ноты) | MIDI pitch | Роль в фактуре |
|---|---|---|---|---|
| **Сопрано** | Soprano (S) | $C_4 - A_5$ (до 1-й — ля 2-й) | 60 – 81 | Мелодический рельеф, ведущий голос |
| **Альт** | Alto (A) | $G_3 - D_5$ (соль малой — ре 2-й) | 55 – 74 | Верхний средний подголосок |
| **Тенор** | Tenor (T) | $C_3 - G_4$ (до малой — соль 1-й) | 48 – 67 | Нижний средний подголосок |
| **Бас** | Bass (B) | $E_2 - C_4$ (ми большой — до 1-й) | 40 – 60 | Гармонический фундамент |

> [!IMPORTANT]
> **Выход за пределы диапазона:** Штрафуется как жесткое нарушение (Hard Constraint). В редких кульминациях сопрано допускается $B_5$, а в басу $D_2$, но в учебных задачах выход за границы запрещен.

---

## 2. Расположение голосов (Spacing) и фактурные интервалы

1. **Интервалы между верхними голосами ($S-A$ и $A-T$):**
   - Расстояние между соседними верхними голосами **не должно превышать октавы** ($interval \le 12$ полутонов).
   - Расстояние больше октавы между $S-A$ или $A-T$ называется **разрывом фактуры** и строго запрещено.
2. **Интервал между тенором и басом ($T-B$):**
   - Допускается расстояние **до двух октав** ($T - B \le 24$ полутона), в исключительных случаях — до дуодецимы / двух октав с терцией. Акустический разрыв между басом и гармонической триадой естественен для обертонового ряда.
3. **Виды расположения аккорда:**
   - **Тесное (Close spacing):** Между $S, A, T$ нет пропущенных аккордовых звуков (интервалы $S-A$ и $A-T$ составляют терции или кварты, редко сексту между $S$ и $A$ при пропущенной терции).
   - **Широкое (Open spacing):** Между $S, A, T$ пропущено по одному аккордовому тону (интервалы $S-A$ и $A-T$ составляют квинты, сексты, септимы или октавы).
   - **Смешанное (Mixed spacing):** Допускается при скачках, перемещениях и в септаккордах.

---

## 3. Абсолютные запреты голосоведения (Hard Gates)

Каждое из этих нарушений делает переход между двумя соседними аккордами $t_1 \to t_2$ недопустимым (штраф $= +\infty$).

### 3.1. Параллельные квинты и октавы (Parallel 5ths & 8ves)
- **Правило:** Запрещено параллельное движение чистыми квинтами (ч.5) и чистыми октавами (ч.8) между **любыми двумя голосами** из 6 пар: $(S-A, S-T, S-B, A-T, A-B, T-B)$.
- **Исключение:** Переход от чистой квинты к уменьшенной (ч.5 $\to$ ум.5) допустим при условии разрешения тритона внутрь. Переход ум.5 $\to$ ч.5 допустим только в определенных оборотах ($II_6 \to T$ при плавном шаге верхнего голоса), но в строгом стиле Бригады избегается.

### 3.2. Противоположные квинты и октавы (Contrary 5ths & 8ves)
- **Правило:** Движение двух голосов в противоположные стороны, приводящее к чистой октаве или чистой квинте (например, октава переходит в октаву через расходящееся или сходящееся движение). Запрещено так же строго, как и параллельное.

### 3.3. Скрытые (прямые) квинты и октавы в крайних голосах (Hidden 5ths/8ves)
- **Правило:** Если сопрано и бас движутся в одном направлении (прямое движение) и приходят в чистую квинту или чистую октаву:
  - Это **разрешено**, только если сопрано двигается **поступенно (на секунду)**.
  - Это **запрещено**, если сопрано делает **скачок (на терцию или шире)**.

### 3.4. Перекрещивание голосов (Voice Crossing)
- **Правило:** Нарушение вертикальной иерархии: бас выше тенора ($B > T$), альт ниже тенора ($A < T$) или сопрано ниже альта ($S < A$). Запрещено категорически во всех случаях.

### 3.5. Перекрывание голосов (Voice Overlapping)
- **Правило:** При переходе к следующему аккорду ни один голос не должен подниматься выше предыдущей ноты соседнего верхнего голоса или опускаться ниже предыдущей ноты соседнего нижнего голоса:
  - $A_{t+1} \le S_t$ и $A_{t+1} \ge T_t$
  - $T_{t+1} \le A_t$ и $T_{t+1} \ge B_t$

### 3.6. Запрещенные мелодические ходы (Melodic Leaps)
- **Увеличенные интервалы:** Запрещены ходы на увеличенную секунду (ув.2), увеличенную кварту (тритон без немедленного разрешения), увеличенную квинту. В гармоническом миноре шаг между VI и VII# ступенью строго воспрещен!
- **Септимы:** Мелодический скачок на септиму (малую или большую) в одном голосе запрещен.
- **Два скачка подряд:** Два скачка в одном направлении, образующие септиму или нону, запрещены.
- **Заполнение скачка:** Любой широкий скачок (на сексту, октаву) должен компенсироваться последующим плавным движением в противоположную сторону.

---

## 4. Правила удвоений в аккордах (Doubling Rules)

### 4.1. Главные трезвучия ($T, S, D$) в основном виде ($5/3$)
- **Норма:** Удваивается **прима (основной тон)**.
- **Запрет:** Удвоение терции строго запрещено (звучит фальшиво, утяжеляет ладовый оттенок; в доминанте терция — вводный тон, удвоение вводного тона ведет к неизбежным параллельным октавам при разрешении).
- **Исключение:** Удвоение квинты допустимо только при особых скачках в неполных оборотах.

### 4.2. Секстаккорды главных ступеней ($T_6, S_6, D_6$)
- **Норма:** Удваивается **прима** или **квинта**.
- **Бас (терцовый тон):** Удвоение баса в главных секстаккордах не рекомендуется. Допускается только в секвенциях, при соединении двух одноименных аккордов (например, $T \to T_6$ при перемещении) или в $S_6$ при особом плавном голосоведении.

### 4.3. Каденционный квартсекстаккорд ($K^6_4$)
- **Норма:** **СТРОГО удваивается бас** (V ступень лада — квинта трезвучия).
- **Метрика:** Ставится **только на сильной или относительно сильной доле** по отношению к последующему разрешающему аккорду ($D$ или $D_7$).
- **Разрешение:** Бас остается на месте (или скачет на октаву), верхние голоса идут на секунду вниз: шестая ступень идет в пятую ($6 \to 5$), четвертая ступень идет в третью ($4 \to 3$).

### 4.4. Доминантсептаккорд ($D_7$)
- **Полный $D_7$:** Содержит все 4 звука: прима, терция, квинта, септима. Все по одному разу.
- **Неполный $D_7$:** Удвоена прима, есть терция и септима; **квинта пропущена**.
- **Обращения ($D^6_5, D^4_3, D_2$):** Всегда применяются в **полном виде** (удвоения отсутствуют, все 4 звука представлены).

### 4.5. Побочные ступени: $VI$ и $II_6$
- **Прерванный оборот ($D \to VI$):** В трезвучии $VI$ ступени **СТРОГО удваивается терция** (I ступень лада!). Вводный тон доминанты идет в тонику, бас идет на секунду вверх ($V \to VI$). Удвоение примы в $VI$ при разрешении из $D$ — грубейшая ошибка.
- **Секстаккорд второй ступени ($II_6$):** Предпочтительно удваивать **терцию** (IV ступень лада — субдоминантовый центр) или приму.

---

## 5. Разрешение неустойчивых тонов и диссонансов

1. **Септима аккорда:** 
   - В $D_7, D^6_5, D^4_3, D_2, II_7, VII_7$ септима **всегда разрешается на ступень вниз**.
   - **Терцквартаккорд ($D^4_3$):** Бас аккорда — квинта доминанты (II ступень). Разрешается в $T_{5/3}$ (ход баса на секунду вниз $II \to I$) или в $T_6$ (ход баса на секунду вверх $II \to III$). Септима аккорда (IV ступень) находится в одном из верхних голосов и обязательно разрешается на секунду вниз в терцию тоники (III ступень).
2. **Секундаккорд ($D_2$):**
   - Септима аккорда лежит в басу (IV ступень). Бас **строго обязан шагнуть на секунду вниз** в терцию тоники $\implies D_2 \to T_6$. Разрешение $D_2 \to T_{5/3}$ строго запрещено.
3. **Вводный тон (VII ступень):**
   - В доминантовых аккордах при переходе в тонику вводный тон **обязан идти в тонику на полтона вверх** (в $I$ ступень), если он находится в сопрано или басу. В средних голосах при неполном $D_7$ допускается ход вводного тона на терцию вниз в квинту тоники.

---

## 6. Синтаксис гармонической формы (Macro Syntax)

1. **Функциональный круг:**
   $$T \longrightarrow S \longrightarrow D \longrightarrow T$$
   - Движение $T \to S$ и $S \to D$ естественно и гармонично.
   - Движение $D \to S$ (обратный ход) **строго запрещено**, так как разрушает ладовое тяготение к тонике.
   - Исключения: субдоминанта может появиться после слабой половинной каденции на грани предложений, либо через прерванный каданс.
2. **Каденции:**
   - **Серединная половинная каденция (конец 1-го предложения, такт 4):** Остановка на $D$ (или $K^6_4 \to D$).
   - **Заключительная совершенная каденция (конец 2-го предложения, такт 8):** Обязательный оборот:
     $$[S \text{ или } II_6] \longrightarrow K^6_4 \text{ (сильная доля)} \longrightarrow D_7 \longrightarrow T \text{ (полная тоника на сильной доле)}$$

---

## 7. Переченье (ложное хроматическое соотношение)

- **Правило:** Хроматическое видоизменение ступени (например, $F \to F\sharp$, $G \to G\sharp$, $B\flat \to B$) должно происходить **в одном и том же голосе**. Появление хроматического полутона **между разными голосами** на соседних аккордах — когда один голос звучит диатонический звук, а соседний голос берёт его хроматическую альтерацию — строго запрещено (Hard Gate, правило `FALSE_RELATION_PERECHENIE`).
- **Что не является переченьем:** Диатонические малые секунды между *разными* ступенями лада ($E-F$, $B-C$, VII–I) — это поступенное движение, а не хроматическая альтерация одной ступени.
- **Whitelist (белый список):** Диатонические полутонные пары в контексте хроматических аккордов переченьем не считаются:
   - неаполитанский аккорд $N$: между ступенями I ↔ bII;
   - пониженная VI ступень ($bVI$, а также $VII_7$): между ступенями V ↔ bVI.
- **Примечание:** Первоисточник (И. Дубовский, С. Евсеев, И. Способин, В. Соколов — «Учебник гармонии», главы 26/28) в репозитории отсутствует; формулировка раздела приведена по фактической реализации правила в `src/harmony/rules/chromatic.py`.
````

## File: docs/MATH_MODEL.md
````markdown
# Строгая математическая модель системы гармонизации

## 1. Пространство звуковысотности и ладовой структуры

### 1.1. Абсолютные и относительные высоты
Пусть $\mathbb{P} = \{0, 1, \dots, 127\}$ — пространство высот MIDI (полутоны, где $C_4 = 60$).
Определим циклическую группу классов высот:
$$\mathbb{PC} = \mathbb{Z}_{12} = \{0, 1, \dots, 11\}$$
Оператор приведения абсолютной высоты $p \in \mathbb{P}$ к классу высоты:
$$\text{pc}(p) = p \pmod{12}$$

### 1.2. Ладовая система (Key & Scale Degrees)
Тональность определяется парой $K = (t_0, M)$, где:
- $t_0 \in \mathbb{PC}$ — тоника (тоникальный класс высоты, напр. $C = 0, D = 2$).
- $M \in \{\text{Major}, \text{MinorHarmonic}, \text{MinorNatural}\}$ — ладовый вектор смещений $\Delta = (\delta_0, \delta_1, \dots, \delta_6)$:
  $$\Delta_{\text{Major}} = (0, 2, 4, 5, 7, 9, 11)$$
  $$\Delta_{\text{MinorHarmonic}} = (0, 2, 3, 5, 7, 8, 11)$$

Ступень лада $d \in \mathbb{Z}_7 = \{0, 1, \dots, 6\}$ (соответствует I, II, ..., VII).
Класс высоты ступени $d$ в тональности $K$:
$$\text{pc}_K(d) = (t_0 + \Delta[d]) \pmod{12}$$

---

## 2. Модель аккорда и вертикали SATB

### 2.1. Четырехголосный срез (SATB State)
Вертикаль в момент времени $t \in \{1, \dots, N\}$ описывается 4-мерным вектором:
$$\mathbf{v}_t = (S_t, A_t, T_t, B_t) \in \mathbb{P}^4$$

### 2.2. Геометрические ограничения вертикали (Static Validity)
Вектор $\mathbf{v}_t$ является статически допустимым ($\text{Valid}(\mathbf{v}_t) = 1$) тогда и только тогда, когда:
1. **Строгая упорядоченность по высоте (отсутствие перекрещивания):**
   $$S_t \ge A_t \ge T_t \ge B_t$$
2. **Диапазоны голосов:**
   $$S_t \in [60, 81], \quad A_t \in [55, 74], \quad T_t \in [48, 67], \quad B_t \in [40, 60]$$
3. **Акустические пределы расстояний (отсутствие разрывов фактуры):**
   $$S_t - A_t \le 12$$
   $$A_t - T_t \le 12$$
   $$T_t - B_t \le 24$$
4. **Соответствие аккордовой структуре (Pitch Class Membership):**
   Пусть $\text{ChordPC}(F_t) \subset \mathbb{PC}$ — множество разрешенных классов высот аккорда функции $F_t$:
   $$\forall X \in \{S_t, A_t, T_t, B_t\}: \quad \text{pc}(X) \in \text{ChordPC}(F_t)$$
5. **Предикат удвоений:**
   Множество кратностей классов высот в $\mathbf{v}_t$ удовлетворяет нормативам Бригады:
   $$\text{Mult}(F_t, \mathbf{v}_t) = \text{True}$$

---

## 3. Модель перехода (Voice-Leading Transition & Cost Function)

При переходе между двумя вертикалями $\mathbf{v}_{t-1} \to \mathbf{v}_t$ вычисляется стоимость ребра $C(\mathbf{v}_{t-1}, \mathbf{v}_t)$:

$$C(\mathbf{v}_{t-1}, \mathbf{v}_t) = H(\mathbf{v}_{t-1}, \mathbf{v}_t) + S(\mathbf{v}_{t-1}, \mathbf{v}_t)$$

### 3.1. Функция жестких ограничений (Hard Constraints)
$$H(\mathbf{v}_{t-1}, \mathbf{v}_t) = \begin{cases} 0, & \text{если все предикаты соблюдены} \\ +\infty, & \text{если нарушено хотя бы одно правило} \end{cases}$$

Предикаты $H$:
1. **Параллельные квинты и октавы:**
   Для любой пары голосов $(X, Y) \in \{S, A, T, B\}^2$, $X \ne Y$:
   $$\text{interval}(X_{t-1}, Y_{t-1}) \equiv 7 \pmod{12} \;\land\; \text{interval}(X_t, Y_t) \equiv 7 \pmod{12} \;\land\; \Delta X \cdot \Delta Y > 0 \implies \text{VIOLATION}$$
   $$\text{interval}(X_{t-1}, Y_{t-1}) \equiv 0 \pmod{12} \;\land\; \text{interval}(X_t, Y_t) \equiv 0 \pmod{12} \;\land\; \Delta X \cdot \Delta Y > 0 \implies \text{VIOLATION}$$
2. **Противоположные квинты и октавы:**
   Аналогично при $\Delta X \cdot \Delta Y < 0$, если результирующий интервал чистый.
3. **Скрытые квинты/октавы крайних голосов:**
   $$\Delta S \cdot \Delta B > 0 \;\land\; (S_t - B_t) \pmod{12} \in \{0, 7\} \;\land\; |\Delta S| > 2 \implies \text{VIOLATION}$$
4. **Перекрывание голосов:**
   $$A_t > S_{t-1} \lor A_t < T_{t-1} \implies \text{VIOLATION}$$
   $$T_t > A_{t-1} \lor T_t < B_{t-1} \implies \text{VIOLATION}$$
5. **Запрещенные мелодические шаги:**
   $$\forall X \in \{S, A, T, B\}: \quad |X_t - X_{t-1}| \in \{3 \text{ (ув.2 в миноре)}, 10, 11 \text{ (септимы)}\} \implies \text{VIOLATION}$$
6. **Обязательное разрешение диссонансов (D43 и D2):**
   - Для $D^4_3$: бас $B_{t-1} = \text{II}$ ступень (квинта доминанты). Разрешается в $T_{53}$ (шаг баса вниз на секунду: $B_t = B_{t-1} - 1 \lor B_t = B_{t-1} - 2$) или в $T_6$ (шаг баса вверх на секунду: $B_t = B_{t-1} + 1 \lor B_t = B_{t-1} + 2$). Септима аккорда (IV ступень) в верхних голосах обязана разрешаться на секунду вниз в III ступень.
   - Для $D_2$: бас $B_{t-1} = \text{IV}$ ступень (септима доминанты). Разрешается строго в $T_6$ (или минорное $t_6$) с обязательным шагом баса вниз на секунду ($B_t = B_{t-1} - 1 \lor B_t = B_{t-1} - 2$).
7. **Нормативы кадансового квартсекстаккорда (K64):**
   - $K^6_4$ запрещён в качестве первого аккорда фразы или построения (`CADENCE_K64_INITIAL`).
   - $K^6_4$ обязан приходиться на метрически сильное или относительно сильное время (`CADENCE_K64_STRONG_BEAT`).
   - Запрещена регрессия от доминанты к $K^6_4$ ($D \to K^6_4$, `SYNTAX_NO_D_TO_K64`).
   - $K^6_4$ обязан разрешаться в доминантовое трезвучие или септаккорд ($D$ или $D_7$, `SYNTAX_K64_MUST_RESOLVE_TO_D`).
   - В $K^6_4$ строго удваивается бас — квинта тонического трезвучия (`DOUBLING_K64_BASS`).

### 3.2. Функция мягких штрафов (Soft Cost)
Для предотвращения аномалий динамического программирования функция стоимости гарантированно неотрицательна ($S \ge 0$):

$$S(\mathbf{v}_{t-1}, \mathbf{v}_t) = w_{\text{shortest}} \cdot \text{Movement}(A, T) + P_{\text{bass\_motion}}(\Delta S, \Delta B) + P_{\text{bass\_leap}}(\Delta B) \ge 0$$

- **Закон кратчайшего пути средних голосов:**
  $$\text{Movement}(A, T) = |A_t - A_{t-1}| + |T_t - T_{t-1}|$$
- **Относительное движение баса и сопрано:**
  $$P_{\text{bass\_motion}}(\Delta S, \Delta B) = \begin{cases} +3.0, & \text{если } \Delta S \cdot \Delta B > 0 \text{ (штраф за прямое движение)} \\ 0.0, & \text{иначе (противоположное движение поощряется нулевым штрафом)} \end{cases}$$
- **Плавность басовой линии (штраф за скачки шире квинты):**
  $$P_{\text{bass\_leap}}(\Delta B) = \begin{cases} 2.0 \cdot \frac{|\Delta B| - 7}{2.0}, & \text{если } |\Delta B| > 7 \\ 0.0, & \text{иначе} \end{cases}$$
- **Гарантия неотрицательности:**
  $$\forall \mathbf{v}_{t-1}, \mathbf{v}_t: \quad S(\mathbf{v}_{t-1}, \mathbf{v}_t) \ge 0.0$$

---

## 4. Алгоритм глобальной оптимизации (Viterbi Dynamic Programming)

Пусть для каждого временного шага $t \in \{1, \dots, N\}$ сформировано множество допустимых вертикалей:
$$\mathcal{V}_t = \{\mathbf{v}_{t, 1}, \mathbf{v}_{t, 2}, \dots, \mathbf{v}_{t, K_t}\}, \quad |\mathcal{V}_t| \le K_{\max} \approx 40$$

Определим функцию оптимальной накопленной стоимости $\delta_t(j)$ для $j \in \{1, \dots, |\mathcal{V}_t|\}$:
$$\delta_1(j) = \text{InitCost}(\mathbf{v}_{1, j})$$
$$\delta_t(j) = \min_{1 \le i \le |\mathcal{V}_{t-1}|} \Big( \delta_{t-1}(i) + C(\mathbf{v}_{t-1, i}, \mathbf{v}_{t, j}) \Big)$$

Массив обратных указателей для восстановления траектории:
$$\psi_t(j) = \arg\min_{1 \le i \le |\mathcal{V}_{t-1}|} \Big( \delta_{t-1}(i) + C(\mathbf{v}_{t-1, i}, \mathbf{v}_{t, j}) \Big)$$

После достижения шага $N$:
$$j_N^* = \arg\min_{j} \delta_N(j)$$
$$j_{t-1}^* = \psi_t(j_t^*), \quad t = N, N-1, \dots, 2$$

### Теорема сложности:
- **Время работы:** $\sum_{t=2}^N |\mathcal{V}_{t-1}| \cdot |\mathcal{V}_t| \le N \cdot K_{\max}^2$. При $N=16, K_{\max} \approx 40 \implies \approx 25\,600$ парных комбинаций. С учётом глубокой валидации академических предикатов Бригадника на чистом Python реальное время инференса составляет порядка 330–350 мс для типовой 5-нотной фразы и ~1–2 с для 16-тактовой развёрнутой гармонизации.
- **Память:** $O(N \cdot K_{\max})$ — полиномиальная, в пределах 1–2 МБ.
- **Глобальная оптимальность:** В силу принципа оптимальности Беллмана алгоритм гарантированно находит путь с наименьшей суммарной стоимостью в сгенерированной решётке без риска застревания в локальных минимумах.
````

## File: frontend/src/audio/synth.ts
````typescript
/**
 * Polyphonic WebAudio Synthesizer for 4-part SATB harmony.
 * Features 3 instrument presets (Piano, Choir Pad, Church Organ),
 * individual Solo/Mute controls per voice (S, A, T, B), and timed score cursor playback.
 */
⋮----
export type InstrumentPreset = "piano" | "choir" | "organ";
⋮----
export interface SATBVoicing {
  soprano: number;
  alto: number;
  tenor: number;
  bass: number;
  measure?: number;
  is_downbeat?: boolean;
  duration?: string;
}
⋮----
export class AudioEngine {
⋮----
constructor()
⋮----
// Lazy initialized on first user gesture
⋮----
private initCtx()
⋮----
public setPreset(preset: InstrumentPreset)
⋮----
public setMute(voiceIdx: number, muted: boolean)
⋮----
public setSolo(voiceIdx: number, soloed: boolean)
⋮----
private updateGains()
⋮----
private midiToFreq(midi: number): number
⋮----
/**
   * Triggers a single voice note according to the selected instrument preset.
   */
public playNote(voiceIdx: number, midiPitch: number, durationSec: number = 1.0)
⋮----
// Piano: warm percussive attack, rich harmonics
⋮----
// Attack / Decay envelope
⋮----
// Choir Pad: lush detuned triangle/saw with slow vocal formant envelope
⋮----
// Church Organ: additive drawbars (8', 4', 2 2/3', 2')
⋮----
/**
   * Plays full SATB vertical chord slice.
   */
public playChord(voicing: SATBVoicing, durationSec: number = 1.2)
⋮----
/**
   * Sequentially plays through voicings with cursor synchronization.
   */
public playSequence(
    voicings: SATBVoicing[],
    bpm: number,
    onStep: (index: number) => void,
    onFinish: () => void
  )
⋮----
// Each chord in Brigade textbook is default half note = 2 beats
⋮----
const playNext = () =>
⋮----
public stop()
⋮----
// Silence already-scheduled oscillators: clearing the timer alone leaves
// the current chord ringing until its scheduled stop time.
⋮----
// already stopped
⋮----
public getIsPlaying(): boolean
````

## File: frontend/src/components/melody/MelodyFileUpload.tsx
````typescript
import React, { useState, useRef } from "react";
import { Upload, FileCode, Check, AlertCircle } from "lucide-react";
import { Button } from "../ui/Button";
import type { MelodyNote } from "../../utils/durationUtils";
⋮----
interface MelodyFileUploadProps {
  onMelodyLoaded: (melody: MelodyNote[], timeSignature?: string, key?: { tonic: string; mode: string }) => void;
  /** Current UI meter — sent to /api/parse-text (backend contract m1). */
  timeSignature: string;
}
⋮----
/** Current UI meter — sent to /api/parse-text (backend contract m1). */
⋮----
const handleParseText = async () =>
⋮----
// Backend contract: /api/parse-text returns a bare list of notes;
// accept both shapes (array or {melody: [...]}) defensively.
⋮----
const handleFileUpload = async (file: File) =>
⋮----
// Backend contract: /api/import-file returns soprano_melody (api.py);
// keep data.melody as a defensive fallback.
⋮----
{/* Text string input */}
⋮----
onChange=
⋮----
{/* File Upload / Dropzone */}
````

## File: frontend/src/components/AudioControls.tsx
````typescript
import React, { useEffect, useState } from "react";
import {
  Play,
  Square,
  Volume2,
  VolumeX,
  Headphones,
  SlidersHorizontal,
  SkipBack,
  SkipForward,
} from "lucide-react";
import { audioEngine } from "../audio/synth";
import type { InstrumentPreset, SATBVoicing } from "../audio/synth";
import { Button } from "./ui/Button";
import { Input } from "./ui/Input";
⋮----
interface AudioControlsProps {
  voicings: SATBVoicing[];
  currentChordIndex: number;
  onStepChange: (index: number) => void;
}
⋮----
/* SATB voice identity colors (kept recognizable in both themes). */
⋮----
// Unmount (tab switch) must silence playback: the engine is a module singleton.
⋮----
const handlePlayToggle = () =>
⋮----
// Manual transport: step back/forward through chord slices with cursor sync.
const handleStep = (dir: -1 | 1) =>
⋮----
const handleBpmChange = (value: number) =>
⋮----
const handlePresetChange = (newPreset: InstrumentPreset) =>
⋮----
const toggleMute = (idx: number) =>
⋮----
const toggleSolo = (idx: number) =>
⋮----
{/* Playback & Instrument bar */}
⋮----
{/* Play/Stop + Step transport + BPM */}
⋮----
{/* BPM 40–200 */}
⋮----
onChange={(e) =>
⋮----
{/* Preset Selector */}
⋮----
onClick=
⋮----
{/* Voice Strips: Solo / Mute per Voice */}
````

## File: frontend/src/hooks/useHarmonizer.ts
````typescript
import { useState, useEffect, useRef, useCallback } from "react";
import { recalculateDownbeats } from "../utils/durationUtils";
import type { MelodyNote } from "../utils/durationUtils";
import type { CandidateSolution } from "../components/ControlPanel";
import type { TabScoreState } from "../types/harmony";
⋮----
export interface CanonicalKey {
  tonic: string;
  mode: string;
  fifths: number;
  title?: string;
  name?: string;
}
⋮----
export function useHarmonizer(initialMelody: MelodyNote[])
⋮----
// Event-driven meter change: recalculate downbeats here (not in an effect),
// keeping the auto-strong-beats feature without setState-in-effect.
⋮----
// Opt-in relaxed modes (backend api.py: allow_adjacent_unisons / relax_hard_gates).
// Defaults are strict (false) — the flags are never sent implicitly enabled.
⋮----
// Load canonical keys on mount
⋮----
// Harmonize function
⋮----
// Same race guard as the success path: a clear during body read must
// not resurrect a stale error message.
⋮----
// Guard against the race where clearHarmonizationResult() aborted the
// request after fetch resolved but before state was applied.
⋮----
// Clears the harmonization result (right panel) — used when the melody is
// emptied so a stale score is not shown for an empty input.
⋮----
// An in-flight /api/harmonize response would otherwise repopulate the panel
// with a score for the melody that has just been cleared.
⋮----
// Key Auto-detection
⋮----
const handleSelectCandidate = (cand: CandidateSolution) =>
````

## File: frontend/src/index.css
````css
@import "tailwindcss";
⋮----
@custom-variant dark (&:where([data-theme="dark"], [data-theme="dark"] *));
⋮----
/* Raw theme variables — runtime-switchable via [data-theme] on <html>. */
⋮----
[data-theme="light"] {
⋮----
/* Register design tokens as Tailwind v4 theme values. `inline` keeps the
   var() references in utilities so [data-theme] switches apply live. */
@theme inline {
⋮----
body {
⋮----
#root {
⋮----
/* Custom scrollbars in the artifact's own visual language */
::-webkit-scrollbar {
⋮----
::-webkit-scrollbar-track {
⋮----
::-webkit-scrollbar-thumb {
⋮----
::-webkit-scrollbar-thumb:hover {
⋮----
/* Firefox: scrollbar-color / scrollbar-width are inherited and they override
   the ::-webkit-* rules there, so declaring them on <html> styles every
   scroller. Declared on the same element as the [data-theme] palette, so the
   var() tokens re-resolve live on theme switch. No hover analogue exists in
   Firefox (thumb stays at --app-border-default). */
:root {
⋮----
/* High-contrast focus visible utility */
.focus-ring {
.focus-ring:focus-visible {
````

## File: scripts/grammar_metrics.py
````python
"""
Grammar Metrics Benchmark: Before vs After Soprano Filter Removal.
Measures total plans, solved plans, plan survival rate, NO_FEASIBLE rate,
beam starvations, and end-to-end harmonization status.
"""
⋮----
# Ensure workspace root is in sys.path
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
⋮----
def load_grammar_before() -> type
⋮----
"""Loads previous grammar before soprano filter removal from scratch dir."""
before_path = _PROJECT_ROOT / ".redteam" / "scratch" / "grammar_metrics" / "grammar_before.py"
⋮----
spec = importlib.util.spec_from_file_location("grammar_before", str(before_path))
⋮----
mod = importlib.util.module_from_spec(spec)
⋮----
BENCHMARK_MELODIES: list[tuple[str, list[int], str]] = [
⋮----
ADDITIONAL_MELODIES: list[tuple[str, list[int], str]] = [
⋮----
k = Key.parse(key_str)
ts = TimeSignature.parse("4/4")
metric_info = calculate_metric_structure(melody, default_time_signature=ts)
proc_mel = [
⋮----
grammar = grammar_cls(k)
t0 = time.perf_counter()
plans = grammar.generate_plans(proc_mel, key=k, max_plans=60)
gen_time = time.perf_counter() - t0
⋮----
total_plans = len(plans)
starvations = getattr(grammar, "beam_starvations", 0)
⋮----
solved_plans = 0
⋮----
res = solver.solve(proc_mel, p, k)
⋮----
survival_pct = (solved_plans / total_plans * 100.0) if total_plans > 0 else 0.0
no_feasible_pct = ((total_plans - solved_plans) / total_plans * 100.0) if total_plans > 0 else 0.0
⋮----
harmonizer = Harmonizer(grammar=grammar)
h_res = harmonizer.harmonize(melody, key=key_str)
harmonize_ok = h_res.is_success
⋮----
def run_benchmark() -> str
⋮----
grammar_before_cls = load_grammar_before()
grammar_after_cls = HarmonicGrammarCurrent
solver = ViterbiSolver()
⋮----
lines: list[str] = []
⋮----
all_melodies = BENCHMARK_MELODIES + ADDITIONAL_MELODIES
⋮----
header = (
sep = "|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|"
⋮----
res_before = evaluate_melody(name, mel, key_str, grammar_before_cls, solver)
res_after = evaluate_melody(name, mel, key_str, grammar_after_cls, solver)
⋮----
plans_str = f"{res_before['total_plans']} -> {res_after['total_plans']}"
solved_str = f"{res_before['solved_plans']} -> {res_after['solved_plans']}"
surv_str = f"{res_before['survival_pct']:.1f}% -> {res_after['survival_pct']:.1f}%"
nofeas_str = f"{res_before['no_feasible_pct']:.1f}% -> {res_after['no_feasible_pct']:.1f}%"
starv_str = f"{res_before['beam_starvations']} -> {res_after['beam_starvations']}"
harm_str = f"{'PASSED' if res_after['harmonize_ok'] else 'FAILED'}"
⋮----
row = (
⋮----
report_text = "\n".join(lines) + "\n"
⋮----
# Save to .redteam/scratch/grammar_metrics/REPORT.md
out_dir = _PROJECT_ROOT / ".redteam" / "scratch" / "grammar_metrics"
⋮----
report_file = out_dir / "REPORT.md"
⋮----
out = run_benchmark()
````

## File: src/harmony/core/metric.py
````python
"""
Unified Metric Grid Engine for Brigade Classical Harmony.
Provides deterministic, authoritative metric coordinates across 4/4, 3/4, 2/4, 6/8, and 3/8 meters.
"""
⋮----
"""
    Evaluates metric accent per Brigade textbook rules:
    - 4/4: downbeats on beats 0 and 2 (in quarters)
    - 3/4: downbeat on beat 0
    - 2/4: downbeat on beat 0
    - 6/8: downbeats on beats 0 and 3 (in eighths)
    - 3/8: downbeat on beat 0
    Syncopated notes starting off-beat are never downbeats.
    """
# Verify the note starts exactly on a beat boundary (within tolerance)
expected_offset = beat * quarter_per_beat
⋮----
b = time_sig.beats
bt = time_sig.beat_type
⋮----
# General fallback: measure start is always a downbeat
⋮----
# Compound / duple / quadruple meters fallback
⋮----
class MetricGrid
⋮----
"""
    Authoritative Metric Grid representation for melody note sequences and chord slices.
    Yields for each note:
    {measure: int, beat: int, offset: float, is_downbeat: bool, duration: str}
    """
⋮----
curr_time_sig = self.time_signature
curr_measure = 1
curr_offset = 0.0
prev_time_sig = None
⋮----
raw_items: list[dict[str, Any]] = []
⋮----
p_list = list(pitches) if pitches is not None else [60] * len(durations)
⋮----
note_ts = None
⋮----
note_ts = TimeSignature.parse(item["time_signature"])
dur_raw = item.get("duration", "half")
pitch = item.get("pitch", 60)
explicit_db = item.get("is_downbeat")
⋮----
curr_time_sig = note_ts
⋮----
dur_q = parse_duration_quarters(dur_raw)
measure_duration = curr_time_sig.measure_duration_quarters
quarter_per_beat = 4.0 / curr_time_sig.beat_type
⋮----
# Defensive: a degenerate meter (0/4, 4/0) must never spin the
# measure-advance loop forever. Fall back to 4/4.
curr_time_sig = TimeSignature(4, 4)
⋮----
# Advance measure if offset exceeds measure length
⋮----
time_sig_changed = (curr_time_sig != prev_time_sig)
prev_time_sig = curr_time_sig
⋮----
beat = int(round(curr_offset / quarter_per_beat, 4))
⋮----
is_db = bool(explicit_db)
⋮----
is_db = _is_metric_downbeat(
⋮----
norm_dur_name = f"dotted_{xml_type}" if dots > 0 else xml_type
⋮----
# Advance offset by duration; notes crossing barline keep measure at their start
⋮----
def __len__(self) -> int
⋮----
def __iter__(self)
⋮----
def __getitem__(self, idx: int) -> dict[str, Any]
⋮----
def to_list(self) -> list[dict[str, Any]]
⋮----
"""Factory helper to construct a MetricGrid instance."""
````

## File: src/harmony/ml/model.py
````python
"""
n-gram statistical style prior (NOT a neural network) [EXPERIMENTAL].
Pure Python (zero external C-dependencies).

Learns empirical transition frequency distributions (interval movements, bass leaps)
from classical datasets with Laplace smoothing and computes negative log-likelihood
transition costs for Viterbi DP soft guidance.
"""
⋮----
class StylePriorModel
⋮----
"""
    n-gram statistical style prior (NOT a neural network) [EXPERIMENTAL].
    Scores SATB voice leading smoothness based on empirical transition frequencies.
    """
⋮----
def __init__(self, weight: float = 1.0)
⋮----
# Interval transition frequencies: (ds, da, dt, db) -> count
⋮----
# Relative spacing transitions: (prev_spacing, curr_spacing) -> count
⋮----
# Bass leap distributions
⋮----
# Pre-seed with textbook classical preferences (Laplace prior)
⋮----
def _initialize_classical_priors(self) -> None
⋮----
"""Seeds classical Brigade voice leading priors."""
# Preference for contrary motion (ds * db < 0) and small middle movements (da <= 2, dt <= 2)
prototypes = [
⋮----
# (ds, da, dt, db, weight)
⋮----
k = f"{ds},{da},{dt},{db}"
⋮----
def train_on_dataset(self, dataset_path: str | Path) -> int
⋮----
"""
        Learns transition priors from a JSON Lines (.jsonl) dataset generated by generate_dataset.py.
        Returns number of transitions processed.
        """
p = Path(dataset_path)
⋮----
count = 0
⋮----
line = line.strip()
⋮----
data = json.loads(line)
satb_list = data.get("satb", [])
⋮----
prev_v = satb_list[i - 1]
curr_v = satb_list[i]
⋮----
ds = cs - ps
da = ca - pa
dt = ct - pt
db = cb - pb
⋮----
def score_transition(self, prev_satb: Sequence[int] | Voicing, curr_satb: Sequence[int] | Voicing) -> float
⋮----
"""
        Computes negative log-likelihood soft penalty for transition:
        Cost = -log P(transition) * weight
        Lower cost means more idiomatic/classical.
        """
p_satb = to_satb(prev_satb)
c_satb = to_satb(curr_satb)
⋮----
ds = c_satb[0] - p_satb[0]
da = c_satb[1] - p_satb[1]
dt = c_satb[2] - p_satb[2]
db = c_satb[3] - p_satb[3]
⋮----
count = self.motion_counts.get(k, 0)
⋮----
# Laplace smoothing: (count + 1) / (total + vocab_size)
prob = (count + 1.0) / (self.total_transitions + self.vocab_size)
nll = -math.log(prob)
⋮----
# Additional penalty for excessive middle voice jumps
jump_penalty = max(0, abs(da) - 4) * 2.0 + max(0, abs(dt) - 4) * 2.0
⋮----
def save_weights(self, path: str | Path) -> None
⋮----
"""Saves model priors to JSON."""
p = Path(path)
⋮----
data = {
⋮----
@classmethod
    def load_weights(cls, path: str | Path) -> "StylePriorModel"
⋮----
"""Loads model priors from JSON."""
⋮----
model = cls()
⋮----
data = json.loads(p.read_text(encoding="utf-8"))
````

## File: src/harmony/rules/chromatic.py
````python
"""
Chromatic Voice Leading, Secondary Dominants, and False Relation (Переченье) Validator.
Strictly implements Brigade textbook rules (Способин, Дубовский et al., Глава 26, 28):
1. Переченье (Cross-relation / False relation):
   Хроматическое видоизменение ступени (например, F -> F# или Bb -> B) должно происходить
   в одном и том же голосе. Появление хроматического полутона в разных голосах
   при одновременном звучании или непосредственном следовании строго запрещено (hard_gate).
   ВАЖНО: Диатонические малые секунды (например, E-F, B-C, или VII-I ступени) НЕ являются переченьем!
"""
⋮----
VOICE_NAMES = ["Soprano", "Alto", "Tenor", "Bass"]
⋮----
MAJOR_SCALE_STEPS = {0, 2, 4, 5, 7, 9, 11}
MINOR_HARMONIC_STEPS = {0, 2, 3, 5, 7, 8, 11}
⋮----
def get_diatonic_pcs(key: Any) -> set[int]
⋮----
"""Returns set of diatonic pitch classes for the key."""
⋮----
steps = MINOR_HARMONIC_STEPS if "minor" in mode.lower() else MAJOR_SCALE_STEPS
⋮----
"""
    Detects False Relation (Переченье):
    Occurs when a chromatic alteration of a diatonic scale step appears in a DIFFERENT voice
    than the original voice that sounded the diatonic step in the previous chord.

    Brigade harmony (Ch. 28, 31):
    Diatonic minor seconds between distinct scale degrees (degree I <-> bII in Neapolitan
    harmonies, degree V <-> bVI in chromatic submediant) are diatonic steps, NOT false relations.
    However, cross-voice chromatic semitones (e.g. C <-> C#, F <-> F#, G <-> G#) must strictly be flagged.
    """
violations: list[RuleViolation] = []
p_satb = to_satb(prev_voicing)
c_satb = to_satb(curr_voicing)
⋮----
diatonic_pcs = get_diatonic_pcs(key)
⋮----
p_pcs = [(i, p % 12, p) for i, p in enumerate(p_satb)]
c_pcs = [(j, c % 12, c) for j, c in enumerate(c_satb)]
p_set = {p for _, p, _ in p_pcs}
c_set = {c for _, c, _ in c_pcs}
⋮----
p_sym_raw = parse_chord_symbol(prev_chord).strip() if prev_chord is not None else ""
c_sym_raw = parse_chord_symbol(curr_chord).strip() if curr_chord is not None else ""
p_sym = p_sym_raw.upper().replace("/", "")
c_sym = c_sym_raw.upper().replace("/", "")
⋮----
# Neapolitan presence: N / N6 / bII, or voicing containing both bII and 4th degree (Db and F in C)
is_neapolitan = (
⋮----
# Lowered 6th degree presence (harmonic major s/s6, bVI, vii7, or Neapolitan fifth)
# Pitch classes must contain lowered 6th (Ab in C) AND either tonic (C) or subdominant 4th (F)
has_lowered_sixth = (
⋮----
diatonic_pairs: set[tuple[int, int]] = set()
⋮----
# If both pitch classes are diatonic in the current key, this is a diatonic interval (e.g. E-F, B-C),
# NOT a chromatic alteration / false relation!
⋮----
# Legitimate diatonic steps in Neapolitan / bVI contexts are not false relation
⋮----
# Check for chromatic semitone relationship (|p_pc - c_pc| == 1 or 11)
diff = abs(c_pc - p_pc)
is_chromatic_semitone = (diff == 1 or diff == 11)
⋮----
# Voice i had the diatonic note, but voice j introduced the chromatic alteration!
voice_i_moved_to_chromatic = (c_satb[i] % 12 == c_pc)
voice_j_came_from_diatonic = (p_satb[j] % 12 == p_pc)
⋮----
"""Master validator for chromatic voice leading and false relation."""
````

## File: src/harmony/rules/non_chord_tones.py
````python
"""
Non-Chord Tones (Неаккордовые звуки) and Melodic Embellishments Validator.
Implements Brigade Textbook rules for:
- Задержания (Suspensions): приготовление, задержание на сильной доле, разрешение на ступень вниз/вверх.
- Проходящие звуки (Passing tones): поступенное заполнение терций на слабой доле.
- Вспомогательные звуки (Neighbor/Auxiliary tones): шаг на секунду от аккордового тона и возврат обратно.
- Предъёмы (Anticipations): взятие аккордового тона следующей гармонии на слабой доле.
"""
⋮----
class NonChordToneType(str, Enum)
⋮----
NONE = "none"
PASSING = "passing"           # Проходящий
NEIGHBOR = "neighbor"         # Вспомогательный
SUSPENSION = "suspension"     # Задержание
ANTICIPATION = "anticipation" # Предъём
⋮----
@dataclass
class NonChordToneAnalysis
⋮----
tone_type: NonChordToneType
voice_index: int              # 0: S, 1: A, 2: T, 3: B
pitch: int
is_valid: bool
violations: list[RuleViolation]
⋮----
"""
    Classifies a soprano melodic pitch relative to chord pitch classes.
    Returns: 'passing' | 'neighbor' | 'suspension' | 'chord_tone' | None

    Rules:
    - chord_tone: curr_pitch % 12 is in chord_pcs.
    - suspension: tone held from previous pitch (d1 == 0), on downbeat (is_downbeat == True),
                  resolves down by step (d2 in (-1, -2)).
    - passing: moves in the same direction by step (abs(d1) in (1, 2), abs(d2) in (1, 2), d1 * d2 > 0)
               between surrounding pitches.
    - neighbor: moves by step (abs(d1) in (1, 2)) and returns back to the same pitch (next_pitch == prev_pitch).
    """
norm_pcs = {pc % 12 for pc in chord_pcs}
⋮----
d1 = curr_pitch - prev_pitch
d2 = next_pitch - curr_pitch
⋮----
# Suspension: held note on downbeat resolving down by step
⋮----
# Passing tone: stepwise motion in the same direction
⋮----
# Neighbor tone: step and return
⋮----
"""
    Classifies a pitch between two surrounding pitches (prev -> curr -> next).
    Returns (NonChordToneType, violations).
    """
⋮----
violations: list[RuleViolation] = []
⋮----
# 1. Задержание (Suspension):
# Tone held from previous chord (d1 == 0), appears on downbeat, resolves down by step (d2 == -1 or -2)
⋮----
# Upward suspension (задержание снизу) - permitted in Brigade, but rarer
⋮----
# 2. Проходящий звук (Passing tone):
# Must move in the same direction by step: prev -> curr (step) -> next (step)
⋮----
# Downbeat passing tone is permitted (тяжелый проходящий), but soft-penalized in classical vocal style
⋮----
# 3. Вспомогательный звук (Neighbor / Auxiliary tone):
# Moves by step and returns back: prev -> curr (step) -> prev (step back)
⋮----
# 4. Предъём (Anticipation):
# Steps into tone on weak beat, next chord holds same tone (d2 == 0)
⋮----
# If it is not a chord tone and fits none of the classical NCT patterns -> illegal leap to non-chord tone!
⋮----
"""
    Validates all 4 voices across a 3-chord window (prev -> curr -> next)
    for strict classical handling of non-chord embellishments.
    """
⋮----
p_satb = to_satb(prev_voicing)
c_satb = to_satb(curr_voicing)
n_satb = to_satb(next_voicing)
⋮----
p_pitch = p_satb[v_idx]
c_pitch = c_satb[v_idx]
n_pitch = n_satb[v_idx]
⋮----
is_chord_tone = (c_pitch % 12) in {t % 12 for t in curr_chord_tones}
````

## File: src/harmony/rules/spacing.py
````python
"""
Voice ranges, crossing, and texture spacing rules according to Brigade Harmony textbook.
"""
⋮----
_UNISONS_CONTEXT = threading.local()
⋮----
def set_unisons_allowed(allowed: bool) -> None
⋮----
"""Thread-local context setter for allowing voice unisons."""
⋮----
def is_unisons_allowed() -> bool
⋮----
"""Thread-local context getter for allowing voice unisons."""
⋮----
VOICE_NAMES = ("Soprano", "Alto", "Tenor", "Bass")
⋮----
# Standard Brigade textbook ranges (MIDI pitch)
STANDARD_VOICE_RANGES: dict[int, tuple[int, int]] = {
⋮----
0: (60, 81),  # Soprano: C4 - A5
1: (55, 74),  # Alto: G3 - D5
2: (48, 67),  # Tenor: C3 - G4
3: (40, 60),  # Bass: E2 - C4
⋮----
# Extended ranges permitted in exceptional climaxes / cadences
EXTENDED_VOICE_RANGES: dict[int, tuple[int, int]] = {
⋮----
0: (59, 83),  # B3 - B5
1: (53, 75),  # F3 - Eb5
2: (46, 69),  # Bb2 - A4
3: (36, 60),  # C2 - C4 (final cadential bass reaches C2 = 36)
⋮----
"""
    Checks whether all four voices fall within their strictly designated vocal compass.
    """
satb = to_satb(voicing)
active_ranges = ranges or (EXTENDED_VOICE_RANGES if allow_extended else STANDARD_VOICE_RANGES)
⋮----
violations: list[RuleViolation] = []
⋮----
def check_voice_crossing(voicing: Any) -> list[RuleViolation]
⋮----
"""
    Checks for voice crossing: Soprano >= Alto >= Tenor >= Bass.
    """
⋮----
def check_voice_unison(voicing: Any) -> list[RuleViolation]
⋮----
"""
    Checks for adjacent voice unisons: strict descending order Soprano > Alto > Tenor > Bass.
    Equality between adjacent voices is strictly prohibited in 4-part classical harmony.
    """
⋮----
def check_texture_spacing(voicing: Any) -> list[RuleViolation]
⋮----
"""
    Checks for acoustic texture gaps (spacing limits):
    - Soprano - Alto <= 12 semitones (pure octave)
    - Alto - Tenor <= 12 semitones (pure octave)
    - Tenor - Bass <= 24 semitones (two octaves)
    """
⋮----
"""
    Runs full static texture checks on a single voicing vertical slice.
    """
effective_allow_unisons = allow_unisons or is_unisons_allowed()
⋮----
violations = []
````

## File: backend/exporters.py
````python
"""
Exporters service wrapping core exporters and enriching MusicXML for OSMD rendering.
Adds voice-specific color attributes and places Sposobin functional analysis under the bass.
"""
⋮----
VOICE_COLORS = {
⋮----
"1": "#2563eb",  # Soprano - Blue
"2": "#16a34a",  # Alto - Green
"3": "#ea580c",  # Tenor - Orange
"4": "#dc2626",  # Bass - Red
⋮----
"""
    Generates standard MusicXML 3.1 partwise score and enriches it with:
    1. Color attributes per voice:
       - Voice 1 (Soprano): #2563eb (blue)
       - Voice 2 (Alto): #16a34a (green)
       - Voice 3 (Tenor): #ea580c (orange)
       - Voice 4 (Bass): #dc2626 (red)
    2. Relocates harmonic functional analysis (T, S, D, K64...) from soprano to Bass
       so OSMD renders Sposobin markings directly under the bass staff.
    3. Respects time signatures, meter changes, and dotted durations.
    """
raw_xml = export_to_musicxml(
⋮----
root = ET.fromstring(raw_xml)
⋮----
def _is_tie_continuation(note: ET.Element) -> bool
⋮----
"""True when this <note> is the continuation slice of a note tied over a barline."""
tie_types = [t.get("type") for t in note.findall("tie")]
⋮----
tied_types = [t.get("type") for t in note.findall(".//tied")]
⋮----
# Process each measure
measures = root.findall(".//measure")
chord_idx = 0
⋮----
notes = measure.findall("note")
⋮----
# Collect chords lyrics from voice 1 to transfer to voice 4 (Bass)
measure_chords: list[str] = []
⋮----
voice_el = note.find("voice")
v_val = voice_el.text.strip() if voice_el is not None and voice_el.text else "1"
⋮----
# Remove lyric from voice 1 if present
⋮----
lyric_el = note.find("lyric")
⋮----
txt_el = lyric_el.find("text")
⋮----
# Apply voice colors and attach lyric to bass notes
bass_note_counter = 0
⋮----
staff_el = note.find("staff")
⋮----
staff_val = staff_el.text.strip() if staff_el is not None and staff_el.text else "1"
⋮----
# Color note
color = VOICE_COLORS.get(v_val, "#000000")
⋮----
# If note is Bass (staff 2, voice 4), add lyric under bass
⋮----
# Same harmony carried over the barline: no duplicate lyric.
⋮----
chord_text = measure_chords[bass_note_counter]
lyric = ET.SubElement(note, "lyric", number="1")
ltext = ET.SubElement(lyric, "text")
⋮----
c = chords[chord_idx]
sym = c.function if hasattr(c, "function") else str(c)
⋮----
rough_string = ET.tostring(root, encoding="utf-8")
⋮----
reparsed = minidom.parseString(rough_string)
⋮----
"""Generates standard MIDI file in-memory and returns raw bytes."""
⋮----
tmp_path = Path(tmp.name)
````

## File: backend/importers.py
````python
"""
File importers for MusicXML and MIDI formats.
Extracts soprano melodies or full SATB voicings without altering core modules.
"""
⋮----
STEP_TO_PC = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
PC_TO_STEP = {0: "C", 2: "D", 4: "E", 5: "F", 7: "G", 9: "A", 11: "B"}
⋮----
def midi_to_note_name(pitch: int) -> str
⋮----
"""Converts MIDI pitch to readable note name like C4, F#3, Bb4."""
names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
octave = (pitch // 12) - 1
pc = pitch % 12
⋮----
def normalize_duration_str(dur_str: str | None) -> str
⋮----
s = dur_str.strip().lower()
⋮----
"""
    Parses melody from text string.
    Supports:
    1. Note names with octave: 'C4 E4 F4 G4 E4 D4 C4' or comma-separated 'C4, E4, F4, G4'
    2. Note names with duration and dots: 'C4:dotted_quarter D4:eighth E4:dotted_half' or 'C4:quarter.'
    3. Inline time signature tags: '[3/4] C4:quarter E4:quarter G4:quarter'
    4. Scale degrees for theorists: '1 3 4 5 3 2 1' (maps relative to key_tonic in octave 4)
    5. Comma-separated MIDI pitch numbers: '60, 64, 65, 67, 64, 62, 60'
    """
cleaned = text.strip()
⋮----
# Check for inline meter like [3/4] or leading 3/4
ts_bracket = re.search(r"\[(\d+/\d+)\]", cleaned)
⋮----
time_signature = ts_bracket.group(1)
cleaned = cleaned.replace(ts_bracket.group(0), " ").strip()
⋮----
m_lead = re.match(r"^(\d+/\d+)\b", cleaned)
⋮----
time_signature = m_lead.group(1)
cleaned = cleaned[m_lead.end():].strip()
⋮----
tokens = [t.strip().rstrip(",") for t in re.split(r"[\s,]+", cleaned) if t.strip().rstrip(",")]
⋮----
# Check if tokens are all scale degrees (e.g. '1', '3', '4', '5')
all_degrees = all(t.isdigit() and 1 <= int(t) <= 8 for t in tokens)
# Check if tokens are MIDI numbers (>= 36 and <= 96)
all_midi = all(t.isdigit() and int(t) >= 36 for t in tokens)
⋮----
parsed_key = Key(tonic=key_tonic, mode=key_mode)
scale_pcs = parsed_key.scale_pcs
⋮----
raw_items: list[dict[str, Any]] = []
⋮----
deg = int(tok)
deg_idx = (deg - 1) % 7
pc = scale_pcs[deg_idx]
pitch = 60 + pc
⋮----
p = int(tok)
⋮----
# Parse note names like C4, D#4, Eb4, G5:quarter., C4:dotted_half
note_pattern = re.compile(r"^([A-Ga-g])([#bB]?)(-?\d+)?(?::([A-Za-z0-9_./]+))?$")
⋮----
m = note_pattern.match(tok)
⋮----
step = m.group(1).upper()
acc = m.group(2)
oct_str = m.group(3)
dur_str = normalize_duration_str(m.group(4))
⋮----
octave = int(oct_str) if oct_str is not None else 4
pc = STEP_TO_PC.get(step, 0)
⋮----
pc = (pc + 1) % 12
⋮----
pc = (pc - 1) % 12
⋮----
pitch = (octave + 1) * 12 + pc
⋮----
# Calculate exact metric coordinates and downbeats
metric_info = calculate_metric_structure(raw_items, default_time_signature=time_signature)
⋮----
def parse_musicxml_content(xml_text: str) -> dict[str, Any]
⋮----
"""
    Parses MusicXML string to extract:
    - soprano melody (highest line / Voice 1)
    - full SATB voicings if available (for the Grader)
    - key signature (fifths, mode)
    - time signature
    """
root = ET.fromstring(xml_text)
⋮----
# 1. Detect key attributes
fifths = 0
mode = "major"
time_beats = 4
time_beat_type = 4
⋮----
key_elem = root.find(".//key")
⋮----
f_elem = key_elem.find("fifths")
⋮----
fifths = int(f_elem.text.strip())
⋮----
m_elem = key_elem.find("mode")
⋮----
mode = m_elem.text.strip().lower()
⋮----
time_elem = root.find(".//time")
⋮----
b_elem = time_elem.find("beats")
⋮----
time_beats = int(b_elem.text.strip())
⋮----
bt_elem = time_elem.find("beat-type")
⋮----
time_beat_type = int(bt_elem.text.strip())
⋮----
# Extract all notes grouped by measure and voice/staff
def _extract_note(note: ET.Element) -> dict[str, Any] | None
⋮----
pitch_elem = note.find("pitch")
⋮----
step_elem = pitch_elem.find("step")
alter_elem = pitch_elem.find("alter")
octave_elem = pitch_elem.find("octave")
⋮----
step = step_elem.text.strip().upper()
octave = int(octave_elem.text.strip())
alter = int(alter_elem.text.strip()) if alter_elem is not None and alter_elem.text else 0
pc = (STEP_TO_PC.get(step, 0) + alter) % 12
⋮----
voice_elem = note.find("voice")
staff_elem = note.find("staff")
voice_val = voice_elem.text.strip() if voice_elem is not None and voice_elem.text else "1"
staff_val = staff_elem.text.strip() if staff_elem is not None and staff_elem.text else "1"
type_elem = note.find("type")
duration_name = type_elem.text.strip().lower() if type_elem is not None and type_elem.text else "half"
⋮----
duration_name = f"dotted_{duration_name}"
lyric_elem = note.find(".//lyric/text")
lyric_text = lyric_elem.text.strip() if lyric_elem is not None and lyric_elem.text else ""
⋮----
parts = root.findall(".//part")
satb_voicings: list[dict[str, Any]] = []
chords_extracted: list[str] = []
soprano_melody: list[dict[str, Any]] = []
parts_have_measures = [p for p in parts if p.findall("measure")]
⋮----
# Choral SATB export (MuseScore/Sibelius): one <part> per voice,
# ordered Soprano, Alto, Tenor, Bass. Staff/voice tags are then useless.
voice_notes: list[list[dict[str, Any]]] = [[] for _ in range(4)]
⋮----
info = _extract_note(note)
⋮----
min_len = min(len(s_notes), len(a_notes), len(t_notes), len(b_notes))
⋮----
# Two-staff or single-staff layout: classify by (staff, voice) tags.
⋮----
min_len = (
⋮----
# Fifth to Key Tonic mapping
FIFTHS_TO_MAJOR = {
FIFTHS_TO_MINOR = {
is_min = "min" in mode
detected_tonic = (FIFTHS_TO_MINOR if is_min else FIFTHS_TO_MAJOR).get(fifths, "C")
detected_mode = "MinorHarmonic" if is_min else "Major"
⋮----
def parse_midi_file(data: bytes) -> dict[str, Any]
⋮----
"""
    Parses binary MIDI file data using mido.
    Extracts soprano melody from the top melodic line and SATB voicings.
    Calculates exact durations and metric downbeats from delta_time and MetricGrid.
    """
⋮----
mid = mido.MidiFile(file=io.BytesIO(data))
ticks_per_beat = mid.ticks_per_beat if mid.ticks_per_beat and mid.ticks_per_beat > 0 else 480
⋮----
# Collect note-on and note-off events with timestamp and detect time signature
events: list[dict[str, Any]] = []
note_ends: dict[tuple[int, int], list[int]] = {}
detected_ts = {"beats": 4, "beat_type": 4}
⋮----
current_time = 0
⋮----
detected_ts = {"beats": msg.numerator, "beat_type": msg.denominator}
⋮----
ch = getattr(msg, "channel", 0)
⋮----
# Sort events by time
⋮----
# Group notes that occur at roughly the same time (within 30 ticks)
time_clusters: list[list[dict[str, Any]]] = []
⋮----
last_time = time_clusters[-1][0]["time"]
⋮----
# Calculate real duration for each cluster from delta_time or note_off
cluster_durations_q: list[float] = []
⋮----
t_start = cluster[0]["time"]
⋮----
delta_ticks = time_clusters[i + 1][0]["time"] - t_start
⋮----
# For the last chord, search matching note_off times
matching_offs = []
⋮----
key = (ev["channel"], ev["pitch"])
⋮----
offs = [o for o in note_ends[key] if o > t_start]
⋮----
delta_ticks = max(matching_offs)
⋮----
delta_ticks = int(round(cluster_durations_q[-1] * ticks_per_beat))
⋮----
delta_ticks = ticks_per_beat * 2  # default 2 beats (half)
⋮----
dur_q = max(0.25, delta_ticks / ticks_per_beat)
⋮----
# Convert durations to canonical duration strings
cluster_dur_names: list[str] = []
⋮----
dur_name = f"dotted_{xml_type}" if dots > 0 else xml_type
⋮----
# Build raw items for metric grid analysis
raw_items = []
⋮----
sorted_notes = sorted(cluster, key=lambda x: x["pitch"], reverse=True)
⋮----
# Authoritative metric coordinates and downbeats from MetricGrid
ts_str = f"{detected_ts['beats']}/{detected_ts['beat_type']}"
metric_info = calculate_metric_structure(raw_items, default_time_signature=ts_str)
⋮----
extracted_durations: list[str] = []
⋮----
soprano_note = sorted_notes[0]
m_info = metric_info[i]
````

## File: frontend/src/audio/midiInput.ts
````typescript
/**
 * Web MIDI API Manager with live metronome recording for soprano melody input.
 */
⋮----
export interface MidiDevice {
  id: string;
  name: string;
  manufacturer: string;
}
⋮----
export type MidiNoteCallback = (pitch: number, isDownbeat: boolean) => void;
⋮----
interface LocalMidiMessageEvent {
  data: Uint8Array | number[];
}
⋮----
interface LocalMidiInput {
  id: string;
  name?: string;
  manufacturer?: string;
  onmidimessage: ((event: LocalMidiMessageEvent) => void) | null;
}
⋮----
interface LocalMidiAccess {
  inputs: {
    forEach: (callback: (input: LocalMidiInput) => void) => void;
    get: (id: string) => LocalMidiInput | undefined;
  };
}
⋮----
export class WebMidiManager {
⋮----
/** Minimal adapter: Web MIDI support probe (no access request). */
public isSupported(): boolean
⋮----
public async requestAccess(): Promise<MidiDevice[]>
⋮----
public getAvailableDevices(): MidiDevice[]
⋮----
public connectDevice(deviceId: string)
⋮----
public disconnectDevice()
⋮----
public cleanup()
⋮----
public startRecording(
    bpm: number,
    onNote: MidiNoteCallback,
    onMetronomeTick?: (beat: number) => void,
    timeSignature: string = "4/4"
  )
⋮----
// Start metronome click
const playTick = () =>
⋮----
public stopRecording()
⋮----
private getBeatsPerMeasure(): number
⋮----
private handleMidiMessage(event: LocalMidiMessageEvent)
⋮----
// Note On with velocity > 0
⋮----
private getAudioContext(): AudioContext | null
⋮----
private playClick(isDownbeat: boolean)
⋮----
// Ignore audio click error
````

## File: frontend/src/components/ExportBar.tsx
````typescript
import React, { useState } from "react";
import { Download, FileText, Check, Music } from "lucide-react";
import { Button } from "./ui/Button";
import type { SATBVoicing } from "../audio/synth";
⋮----
interface ExportBarProps {
  voicings: SATBVoicing[];
  chords?: string[];
  keyObj: { tonic: string; mode: string };
  timeSignature?: string;
  asciiScore?: string;
  durations?: string[];
}
⋮----
const handleDownloadMidi = async () =>
⋮----
const handleDownloadMusicXml = async () =>
⋮----
const handleCopyAscii = async () =>
⋮----
// Fallback
````

## File: scripts/stress_test_harness.py
````python
"""
Automated Stress-Test Harness for Brigade Harmony Engine.
Executes 24-key iterations across escalating difficulty levels.
Target: 5 consecutive iterations of 24/24 successful, rule-compliant harmonizations without bugfixes.
"""
⋮----
# Ensure project root is on sys.path
⋮----
# The canonical 24 classical keys
TWENTY_FOUR_KEYS = [
⋮----
# 12 Majors
⋮----
# 12 Harmonic Minors
⋮----
def generate_level_melody(tonic: str, mode: str, level: int, seed: int) -> list[int]
⋮----
"""
    Synthesizes a textbook soprano cantus firmus adhering to Brigade rules across difficulty levels:
    - L1/L2: Length 6, stepwise motion with consonant 3rds.
    - L3: Length 8, 3rds and 4ths.
    - L4/L5: Length 8, 3rds, 4ths, and 5ths with classical contrary motion balance.
    """
r = random.Random(seed)
pitches = get_scale_pitches(tonic, mode)
⋮----
pitches = [60, 62, 64, 65, 67, 69, 71, 72]
⋮----
tonic_pc = NOTE_TO_PC.get(tonic, 0)
is_minor = "minor" in mode.lower()
deg7_pc = (tonic_pc + 11) % 12
deg2_pc = (tonic_pc + 2) % 12
deg6_pc = (tonic_pc + 8) % 12
⋮----
length = 6 if level <= 2 else 8
max_leap = 4 if level <= 2 else (5 if level == 3 else 7)
⋮----
def is_step_ok(p1: int, p2: int) -> bool
⋮----
d = p2 - p1
ad = abs(d)
if ad > max_leap or ad == 6:  # No excessive leap or tritone
⋮----
return False  # No augmented second leap
⋮----
return False  # Leading tone must step up to tonic
⋮----
return False  # Scale degree 6 in harmonic minor resolves downward
⋮----
start_pcs = [tonic_pc, (tonic_pc + (3 if is_minor else 4)) % 12, (tonic_pc + 7) % 12]
starts = [p for p in pitches if p % 12 in start_pcs and 60 <= p <= 74]
path = [r.choice(starts or pitches)]
⋮----
success = True
⋮----
curr = path[-1]
⋮----
# Cadence: resolve to tonic
⋮----
cand = curr + 1
⋮----
cand = curr - 2
⋮----
success = False
⋮----
# Penultimate cadence preparation: must be scale degree 2 or 7
cands = [p for p in pitches if p % 12 in (deg2_pc, deg7_pc) and is_step_ok(curr, p)]
⋮----
# Melodic continuation
cands = [p for p in pitches if is_step_ok(curr, p) and 60 <= p <= 78]
# Classical rule: avoid more than 2 consecutive identical notes in vocal cantus
⋮----
cands = [p for p in cands if p != curr]
⋮----
weights = [4 if 1 <= abs(p - curr) <= 2 else 1 for p in cands]
⋮----
def test_single_key(tonic: str, mode: str, level: int, seed: int, harmonizer: Harmonizer, engine: RuleEngine) -> tuple[bool, str, list[int], list[str]]
⋮----
"""Harmonizes and strictly verifies one key."""
melody = generate_level_melody(tonic, mode, level, seed)
key = Key(tonic=tonic, mode=mode)
⋮----
res = harmonizer.harmonize(melody=melody, key=key, max_plans=30)
⋮----
best = res.best_solution
funcs = [c.function for c in best.chords]
⋮----
# Verify every single transition through RuleEngine
prev_v = None
prev_c = None
metric_grid = MetricGrid(
⋮----
is_downbeat = metric_grid[idx]["is_downbeat"] if idx < len(metric_grid) else False
vres = engine.validate(
⋮----
errs = [f"{vi.rule_id}: {vi.description}" for vi in vres.hard_violations]
⋮----
prev_v = v
prev_c = c
⋮----
def run_iteration(iteration_num: int, level: int, base_seed: int) -> tuple[int, list[dict[str, Any]]]
⋮----
"""Runs one full 24-key iteration."""
harmonizer = Harmonizer()
engine = RuleEngine()
passed = 0
failures = []
⋮----
key_seed = base_seed + iteration_num * 1000 + idx * 37
⋮----
key_name = f"{tonic} {mode}"
⋮----
parser = argparse.ArgumentParser()
⋮----
args = parser.parse_args()
⋮----
mode_str = f"на фиксированном уровне {args.level}" if args.fixed_level else "с эскалацией сложности"
⋮----
consecutive_passed = 0
current_iter = 1
⋮----
lvl = args.level if args.fixed_level else min(consecutive_passed + 1, 5)
````

## File: src/harmony/export/midi.py
````python
"""
Standard MIDI file exporter for four-part SATB voicings.
Pure Python implementation (no external dependencies required).
Supports Format 1 (4 tracks, channels 0..3, Program Change 52 Choir Aahs),
variable durations, dotted notes, and time signature changes.
"""
⋮----
VOICE_NAMES = ("Soprano", "Alto", "Tenor", "Bass")
PROGRAM_CHOIR_AAHS = 52  # General MIDI 53 (0-indexed 52)
⋮----
def _encode_variable_length(value: int) -> bytes
⋮----
"""Encodes an integer into MIDI variable-length quantity bytes."""
buffer = bytearray()
⋮----
def _encode_time_signature_event(time_sig: TimeSignature) -> bytes
⋮----
"""Encodes MIDI Time Signature Meta Event (FF 58 04 nn dd cc bb)."""
dd = int(math.log2(time_sig.beat_type)) if time_sig.beat_type > 0 else 2
⋮----
"""
    Exports a sequence of SATB voicings to a standard MIDI file.
    Default: Format 1 with 4 tracks (channels 0..3, Program Change 52 Choir Aahs).
    Supports variable chord durations from durations parameter, dotted rhythms, and time signatures.
    """
out_p = Path(output_path)
⋮----
# Default contract: SMF Format 1 — one track per SATB voice.
midi_format = 1
⋮----
melody_items = []
⋮----
dur = durations[i] if durations and i < len(durations) else "half"
⋮----
metric_info = calculate_metric_structure(melody_items, default_time_signature=time_signature)
tempo_us = int(60_000_000 / bpm)
init_ts = metric_info[0]["time_signature"] if metric_info else TimeSignature.parse(time_signature)
velocity = 80
⋮----
# Format 0: Single combined track (legacy compatibility)
track_events = bytearray()
⋮----
# Meta: Set Tempo
⋮----
# Initial Time Signature
⋮----
# Program Change: Choir Aahs
⋮----
satb = to_satb(v)
info = metric_info[i]
dur_quarters = info["duration_quarters"]
chord_ticks = int(round(dur_quarters * ticks_per_beat))
⋮----
delta = 0
⋮----
delta = chord_ticks if voice_idx == 0 else 0
⋮----
header_chunk = b"MThd" + struct.pack(">IHHH", 6, 0, 1, ticks_per_beat)
track_chunk = b"MTrk" + struct.pack(">I", len(track_events)) + bytes(track_events)
⋮----
# Format 1: 4 separate tracks (Soprano, Alto, Tenor, Bass) on channels 0..3
track_chunks = bytearray()
⋮----
channel = voice_idx
⋮----
# Track 0 gets tempo and initial time signature
⋮----
# Track Name meta event
v_name = VOICE_NAMES[voice_idx].encode("ascii")
⋮----
# Program Change: 52 (Choir Aahs) on channel
⋮----
pitch = satb[voice_idx]
⋮----
# Note On (delta = 0)
⋮----
# Note Off (delta = chord_ticks)
⋮----
# End of Track
⋮----
# Track chunk
⋮----
header_chunk = b"MThd" + struct.pack(">IHHH", 6, 1, 4, ticks_per_beat)
````

## File: src/harmony/rules/__init__.py
````python
"""
Validation rules and engine for four-part harmony following the Brigade textbook.
"""
⋮----
__all__ = [
⋮----
# Core types
⋮----
# Spacing
⋮----
# Voice leading
⋮----
# Doubling
⋮----
# Resolutions
⋮----
# Engine
⋮----
# Non-chord tones
````

## File: src/harmony/cli.py
````python
"""
CLI entrypoint for the Brigade Harmony Engine.
Allows command-line harmonization of melodies with MusicXML, MIDI, and ASCII outputs.
"""
⋮----
def parse_melody(melody_arg: str) -> list[dict]
⋮----
"""
    Parses comma-separated MIDI pitch numbers into melody note dicts.
    Example: '64,65,67,62,60' -> [{'pitch': 64, 'is_downbeat': True}, ...]
    """
pitches = [int(p.strip()) for p in melody_arg.split(",") if p.strip()]
⋮----
# Simple metric heuristic: alternate downbeat / upbeat
⋮----
def main(argv: list[str] | None = None) -> int
⋮----
parser = argparse.ArgumentParser(
⋮----
args = parser.parse_args(argv)
⋮----
melody = parse_melody(args.melody)
key = Key(args.tonic, args.mode)
⋮----
harmonizer = Harmonizer()
result = harmonizer.harmonize(
⋮----
solution = result.best_solution
⋮----
out_xml = solution.save_musicxml(args.musicxml, title=args.title)
⋮----
out_mid = solution.save_midi(args.midi)
````

## File: backend/main.py
````python
"""
Main FastAPI server application for Brigade Harmony Engine.
Serves REST API and compiled SPA static assets.
"""
⋮----
# Configure centralized structured logging
⋮----
logger = logging.getLogger("backend.main")
⋮----
app = FastAPI(
⋮----
MAX_REQUEST_BYTES = 2 * 1024 * 1024  # 2 MB body limit (ReDoS / slowloris guard)
⋮----
@app.middleware("http")
async def request_context_middleware(request: Request, call_next)
⋮----
"""Attaches a request id to every response and rejects oversized bodies."""
request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
⋮----
content_length = request.headers.get("content-length")
⋮----
response = await call_next(request)
⋮----
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError)
⋮----
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception)
⋮----
"""
    Global unhandled exception handler.
    Logs full traceback with unique error_id and returns structured JSON 500.
    Preserves Starlette / FastAPI HTTPException status codes and payloads.
    """
⋮----
error_id = str(uuid.uuid4())
request_id = getattr(request.state, "request_id", None) or error_id
⋮----
# CORS configuration
⋮----
# Register API routes first
⋮----
@app.get("/api/health")
def health_check()
⋮----
# Fallback for any unknown /api/* endpoints to ensure JSON 404 response
⋮----
@app.api_route("/api/{full_path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
async def api_unknown_fallback(full_path: str)
⋮----
# Static files setup (serving frontend/dist)
def resolve_frontend_dist() -> Path | None
⋮----
"""Robust resolution of frontend/dist for dev and PyInstaller onedir/onefile."""
# 1. Explicit override via environment variable
env_dir = os.environ.get("FRONTEND_DIST_DIR")
⋮----
p = Path(env_dir).resolve()
⋮----
# 2. PyInstaller bundle path (_MEIPASS / internal bundle)
⋮----
meipass_p = Path(sys._MEIPASS) / "frontend" / "dist"
⋮----
# 3. Development / source tree path
dev_p = Path(__file__).resolve().parents[1] / "frontend" / "dist"
⋮----
DIST_DIR = resolve_frontend_dist()
⋮----
assets_dir = DIST_DIR / "assets"
⋮----
@app.get("/{full_path:path}")
    async def serve_spa(full_path: str)
⋮----
# Don't intercept API routes: return JSON 404
⋮----
file_path = DIST_DIR / full_path
⋮----
index_file = DIST_DIR / "index.html"
⋮----
@app.get("/")
    def serve_placeholder()
````

## File: docs/brigade_rules.json
````json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "version": "1.0.0",
  "description": "Машиночитаемый каталог правил гармонизации по Бригадному учебнику (Способин, Дубовский, Евсеев, Соколов)",
  "rules": [
    {
      "id": "VOICE_RANGE_BOUNDS",
      "category": "spacing",
      "severity": "hard_gate",
      "penalty": 100000.0,
      "description": "Выход голоса за пределы допустимого диапазона (S: 60-81, A: 55-74, T: 48-67, B: 40-60 MIDI)."
    },
    {
      "id": "VOICE_UNISON",
      "category": "spacing",
      "severity": "hard_gate",
      "penalty": 100000.0,
      "description": "Унисон между соседними голосами в тесном или широком расположении разрушает четырехголосную фактуру."
    },
    {
      "id": "VOICE_CROSSING",
      "category": "spacing",
      "severity": "hard_gate",
      "penalty": 100000.0,
      "description": "Перекрещивание голосов: нарушение вертикального порядка S >= A >= T >= B."
    },
    {
      "id": "UPPER_VOICE_SPACING_LIMIT",
      "category": "spacing",
      "severity": "hard_gate",
      "penalty": 100000.0,
      "description": "Разрыв фактуры: расстояние между S и A или между A и T превышает чистую октаву (12 полутонов)."
    },
    {
      "id": "BASS_TENOR_SPACING_LIMIT",
      "category": "spacing",
      "severity": "hard_gate",
      "penalty": 100000.0,
      "description": "Расстояние между тенором и басом превышает две октавы (24 полутона)."
    },
    {
      "id": "PARALLEL_FIFTHS",
      "category": "voice_leading",
      "severity": "hard_gate",
      "penalty": 100000.0,
      "description": "Параллельные чистые квинты между любой парой голосов в прямом движении."
    },
    {
      "id": "PARALLEL_DIM5_P5",
      "category": "voice_leading",
      "severity": "hard_gate",
      "penalty": 100000.0,
      "description": "Переход с уменьшенной квинты на чистую квинту в прямом движении воспрещается."
    },
    {
      "id": "PARALLEL_OCTAVES",
      "category": "voice_leading",
      "severity": "hard_gate",
      "penalty": 100000.0,
      "description": "Параллельные чистые октавы или унисоны между любой парой голосов в прямом движении."
    },
    {
      "id": "CONTRARY_FIFTHS",
      "category": "voice_leading",
      "severity": "hard_gate",
      "penalty": 100000.0,
      "description": "Противоположные чистые квинты между любой парой голосов."
    },
    {
      "id": "CONTRARY_OCTAVES",
      "category": "voice_leading",
      "severity": "hard_gate",
      "penalty": 100000.0,
      "description": "Противоположные чистые октавы между любой парой голосов."
    },
    {
      "id": "HIDDEN_FIFTHS_OCTAVES",
      "category": "voice_leading",
      "severity": "hard_gate",
      "penalty": 100000.0,
      "description": "Скрытые квинты/октавы в крайних голосах: S и B идут в одном направлении в 5 или 8 без поступенного шага в S."
    },
    {
      "id": "VOICE_OVERLAPPING",
      "category": "voice_leading",
      "severity": "hard_gate",
      "penalty": 100000.0,
      "description": "Перекрывание голосов: голос идет выше предыдущей ноты верхнего соседа или ниже предыдущей ноты нижнего соседа."
    },
    {
      "id": "DIRECT_UNISON",
      "category": "voice_leading",
      "severity": "hard_gate",
      "penalty": 100000.0,
      "description": "Взятие или оставление унисона прямым движением голосов воспрещается."
    },
    {
      "id": "MELODIC_AUGMENTED_INTERVAL",
      "category": "voice_leading",
      "severity": "hard_gate",
      "penalty": 100000.0,
      "description": "Мелодический ход на увеличенный интервал (ув.2, ув.4) в любом голосе без разрешения."
    },
    {
      "id": "MELODIC_SEVENTH_LEAP",
      "category": "voice_leading",
      "severity": "hard_gate",
      "penalty": 100000.0,
      "description": "Мелодический ход на септиму в любом голосе."
    },
    {
      "id": "DOUBLING_MAIN_TRIAD_ROOT",
      "category": "doubling",
      "severity": "hard_gate",
      "penalty": 100000.0,
      "description": "В главных трезвучиях (T, S, D) удваивается строго прима. Удвоение терции запрещено."
    },
    {
      "id": "DOUBLING_SEXTACCORD",
      "category": "doubling",
      "severity": "hard_gate",
      "penalty": 100000.0,
      "description": "В секстаккордах удваивается прима или квинта. Удвоение терции в T6 запрещено."
    },
    {
      "id": "DOUBLING_D6_LEADING_TONE",
      "category": "doubling",
      "severity": "hard_gate",
      "penalty": 100000.0,
      "description": "В секстаккорде D6 удвоение вводного тона (терции) категорически запрещено."
    },
    {
      "id": "DOUBLING_K64_BASS_ONLY",
      "category": "doubling",
      "severity": "hard_gate",
      "penalty": 100000.0,
      "description": "В каденционном квартсекстаккорде (K64) строго удваивается бас (квинта аккорда)."
    },
    {
      "id": "DOUBLING_DECEPTIVE_VI_THIRD",
      "category": "doubling",
      "severity": "hard_gate",
      "penalty": 100000.0,
      "description": "В трезвучии VI ступени при прерванном обороте (D -> VI) строго удваивается терция (I ступень тоники)."
    },
    {
      "id": "DOUBLING_VII_LEADING_TONE",
      "category": "doubling",
      "severity": "hard_gate",
      "penalty": 100000.0,
      "description": "В уменьшённом трезвучии VII ступени (VII 5/3) категорически запрещено удвоение примы (вводного тона), а также пропуск квинты (неполный аккорд)."
    },
    {
      "id": "DOUBLING_PASSING_64",
      "category": "doubling",
      "severity": "hard_gate",
      "penalty": 100000.0,
      "description": "В проходящих и вспомогательных квартсекстаккордах (T64, S64) строго удваивается бас (квинта трезвучия); удвоение терции запрещено."
    },
    {
      "id": "RESOLUTION_SEVENTH_DOWN",
      "category": "resolution",
      "severity": "hard_gate",
      "penalty": 100000.0,
      "description": "Септима доминантсептаккорда (D7 и обращений) обязана разрешаться на ступень вниз."
    },
    {
      "id": "RESOLUTION_D43_TO_T6",
      "category": "resolution",
      "severity": "hard_gate",
      "penalty": 100000.0,
      "description": "D43 разрешается в T или T6; септима в верхних голосах идет на ступень вниз (в басу D43 квинта доминанты — II ступень лада, идущая в I или III)."
    },
    {
      "id": "RESOLUTION_II7_SEVENTH_DOWN",
      "category": "resolution",
      "severity": "hard_gate",
      "penalty": 100000.0,
      "description": "Септима септаккорда II ступени (II7 и обращений, I ступень лада) обязана разрешаться на ступень вниз (-1 или -2 полутона) или удерживаться на месте при переходе в K64."
    },
    {
      "id": "RESOLUTION_II7_TO_DOMINANT",
      "category": "resolution",
      "severity": "hard_gate",
      "penalty": 100000.0,
      "description": "Септаккорд II ступени (II7, II65, II43, II2) обязан разрешаться в доминантовую группу (D, D6, D7, D65, D43, D2, K64)."
    },
    {
      "id": "RESOLUTION_D2_TO_T6",
      "category": "resolution",
      "severity": "hard_gate",
      "penalty": 100000.0,
      "description": "D2 обязан разрешаться в T6, так как септима в басу обязана шагнуть на секунду вниз в терцию тоники."
    },
    {
      "id": "RESOLUTION_VII7_LEADING_TONE_UP",
      "category": "resolution",
      "severity": "hard_gate",
      "penalty": 100000.0,
      "description": "Вводный тон (VII) в аккорде VII7 обязан разрешаться на полутон вверх в тонику."
    },
    {
      "id": "RESOLUTION_DD_TARGET",
      "category": "resolution",
      "severity": "hard_gate",
      "penalty": 100000.0,
      "description": "Двойная доминанта обязана разрешаться в K64, D или D7."
    },
    {
      "id": "RESOLUTION_LEADING_TONE_UP",
      "category": "resolution",
      "severity": "hard_gate",
      "penalty": 100000.0,
      "description": "Вводный тон (VII) в крайних голосах при автентическом обороте обязан идти в тонику (I)."
    },
    {
      "id": "CADENCE_K64_STRONG_BEAT",
      "category": "syntax",
      "severity": "hard_gate",
      "penalty": 100000.0,
      "description": "K64 обязан стоять на сильной или относительно сильной доле по сравнению с последующим D/D7."
    },
    {
      "id": "SYNTAX_NO_D_TO_S",
      "category": "syntax",
      "severity": "hard_gate",
      "penalty": 100000.0,
      "description": "Запрещен функциональный откат из доминантовой группы в субдоминантовую (D -> S, D -> II)."
    },
    {
      "id": "SOFT_SHORTEST_PATH_LAW",
      "category": "voice_leading",
      "severity": "soft_penalty",
      "penalty": 1.0,
      "description": "Закон кратчайшего пути: штраф пропорционален сумме смещений средних голосов |dA| + |dT|."
    },
    {
      "id": "SOFT_CONTRARY_BASS_MOTION",
      "category": "voice_leading",
      "severity": "soft_penalty",
      "penalty": 0.0,
      "description": "Поощрение (бонус): противоположное движение баса относительно сопрано."
    },
    {
      "id": "SOFT_SMOOTH_BASS_LINE",
      "category": "voice_leading",
      "severity": "soft_penalty",
      "penalty": 2.0,
      "description": "Штраф за избыточные скачки баса шире кварты/квинты без необходимости."
    },
    {
      "id": "FALSE_RELATION_PERECHENIE",
      "category": "chromatic",
      "severity": "hard_gate",
      "penalty": 100000.0,
      "description": "Переченье (ложное хроматическое соотношение): хроматическая альтерация ступени появляется в другом голосе, а не в том, где прозвучал диатонический звук предыдущего аккорда; хроматический полутон между разными голосами на соседних аккордах строго запрещён. Whitelist: диатонические секунды в контексте неаполитанского аккорда N (I ↔ bII) и пониженной VI ступени bVI/VII7 (V ↔ bVI) переченьем не считаются; диатонические малые секунды (E–F, B–C) не являются переченьем."
    },
    {
      "id": "CADENCE_K64_INITIAL",
      "category": "syntax",
      "severity": "hard_gate",
      "penalty": 100000.0,
      "description": "K64 запрещён в качестве начального аккорда произведения; кадансовый квартсекстаккорд появляется только внутри каденционного оборота перед D/D7."
    },
    {
      "id": "SYNTAX_NO_D_TO_K64",
      "category": "syntax",
      "severity": "hard_gate",
      "penalty": 100000.0,
      "description": "Запрещённый функциональный откат из доминантовой группы (D, D7, D6, D65, D43, D2) в кадансовый квартсекстаккорд K64."
    },
    {
      "id": "SYNTAX_K64_MUST_RESOLVE_TO_D",
      "category": "syntax",
      "severity": "hard_gate",
      "penalty": 100000.0,
      "description": "K64 обязан разрешаться в доминанту D или D7; любое другое продолжение запрещено."
    },
    {
      "id": "SYNTAX_NO_CONSECUTIVE_III6",
      "category": "syntax",
      "severity": "hard_gate",
      "penalty": 100000.0,
      "description": "Подряд идущие медиантовые трезвучия (III → III, III6 → III6 и т.п.) строго запрещены."
    },
    {
      "id": "CADENCE_K64_FINAL",
      "category": "syntax",
      "severity": "hard_gate",
      "penalty": 100000.0,
      "description": "K64 не может быть финальным аккордом: он обязан разрешаться в D/D7."
    },
    {
      "id": "CADENCE_FINAL_SEVENTH_FORBIDDEN",
      "category": "syntax",
      "severity": "hard_gate",
      "penalty": 100000.0,
      "description": "Финальный аккорд не может быть септаккордом (D7, II65, D43 и т.п.): каденция закрывается трезвучием T, D или VI."
    },
    {
      "id": "CADENCE_FINAL_INVERSION_FORBIDDEN",
      "category": "syntax",
      "severity": "hard_gate",
      "penalty": 100000.0,
      "description": "Финальный аккорд не может быть обращением или некаденсовым аккордом (T6, D6, D65, D43, D2, VII6, VII, S6, II6, III6): допустимы только основные виды T, D или VI."
    },
    {
      "id": "CADENCE_FINAL_VI_REQUIRES_DOMINANT",
      "category": "syntax",
      "severity": "hard_gate",
      "penalty": 100000.0,
      "description": "Финальный VI (прерванная каденция) обязан следовать за доминантовой группой (D, D7, VII7, III); после тоники или субдоминанты (включая bVI) запрещён."
    },
    {
      "id": "CADENCE_FINAL_T6_FORBIDDEN",
      "category": "syntax",
      "severity": "hard_gate",
      "penalty": 100000.0,
      "description": "T6 не может предшествовать финальной основной тонике T: требуется доминантовый или плаговый субдоминантовый подход."
    },
    {
      "id": "CADENCE_FINAL_NON_CADENTIAL_FORBIDDEN",
      "category": "syntax",
      "severity": "hard_gate",
      "penalty": 100000.0,
      "description": "Финальный аккорд не может быть основной субдоминантой (S/II), если высота сопрано принадлежит T, D или VI: требуется автентическая или половинная каденция."
    },
    {
      "id": "MELODIC_TWO_LEAPS_SAME_DIRECTION",
      "category": "voice_leading",
      "severity": "hard_gate",
      "penalty": 100000.0,
      "description": "Два подряд идущих скачка в одном направлении в одном голосе (каждый шире большой терции, > 4 полутонов) запрещены."
    },
    {
      "id": "MELODIC_DIMINISHED_SEVENTH",
      "category": "voice_leading",
      "severity": "hard_gate",
      "penalty": 100000.0,
      "description": "Мелодический скачок на уменьшенную септиму (9 полутонов, между VI и VII# ступенями гармонического минора/мажора) запрещён."
    },
    {
      "id": "MELODIC_DIMINISHED_FOURTH_SOFT",
      "category": "voice_leading",
      "severity": "soft",
      "penalty": 5.0,
      "description": "Скачок на уменьшённую кварту (4 полутона, между VII# и III ступенями): мягкий штраф; допускается при разрешении внутрь."
    },
    {
      "id": "NCT_SUSPENSION_UNRESOLVED",
      "category": "non_chord_tones",
      "severity": "hard_gate",
      "penalty": 100000.0,
      "description": "Задержание на сильной доле обязано разрешаться поступенно; скачок вместо поступенного разрешения запрещён."
    },
    {
      "id": "NCT_PASSING_ON_DOWNBEAT",
      "category": "non_chord_tones",
      "severity": "soft_penalty",
      "penalty": 3.0,
      "description": "Акцентированный (на сильной доле) проходящий звук: допускается, но штрафуется в строгом классическом вокальном стиле."
    },
    {
      "id": "NCT_ILLEGAL_LEAP_NON_CHORD_TONE",
      "category": "non_chord_tones",
      "severity": "hard_gate",
      "penalty": 100000.0,
      "description": "Незаконный неаккордовый тон: нота не подходит ни под один классический паттерн проходящего, вспомогательного, предъёма или задержания (скачок к неаккордовому звуку и/или скачок с него)."
    },
    {
      "id": "RESOLUTION_DD2_TO_D6",
      "category": "resolution",
      "severity": "hard_gate",
      "penalty": 100000.0,
      "description": "DD2 (секундаккорд двойной доминанты) обязан разрешаться в доминантовую группу (D6, D, D7, D65) или K64, а не в тонику; бас идёт на секунду вниз."
    },
    {
      "id": "RESOLUTION_VII7_SEVENTH_DOWN",
      "category": "resolution",
      "severity": "hard_gate",
      "penalty": 100000.0,
      "description": "Септима вводного септаккорда VII7 (VI ступень) обязана разрешаться на ступень вниз."
    },
    {
      "id": "RESOLUTION_VII7_FIFTH_DOWN",
      "category": "resolution",
      "severity": "hard_gate",
      "penalty": 100000.0,
      "description": "Квинта вводного септаккорда VII7 (IV ступень) обязана разрешаться вниз в терцию тоники."
    },
    {
      "id": "RESOLUTION_VII7_DOUBLED_THIRD",
      "category": "resolution",
      "severity": "hard_gate",
      "penalty": 100000.0,
      "description": "При разрешении VII7 в тонику терция тонического трезвучия обязана удваиваться во избежание параллельных квинт."
    },
    {
      "id": "RESOLUTION_SECONDARY_DOMINANT",
      "category": "resolution",
      "severity": "hard_gate",
      "penalty": 100000.0,
      "description": "Голосоведение побочной доминанты: альтерированный вводный тон разрешается на полутон вверх (или хроматически на полутон вниз), септима — на ступень вниз (или удерживается в K64)."
    },
    {
      "id": "DOUBLING_SECONDARY_DOMINANT",
      "category": "doubling",
      "severity": "hard_gate",
      "penalty": 100000.0,
      "description": "В трезвучии побочной доминанты (DD) удваивается прима; удвоение терции (альтерированного вводного тона) строго запрещено."
    },
    {
      "id": "DOUBLING_VII6_LEADING_TONE",
      "category": "doubling",
      "severity": "hard_gate",
      "penalty": 100000.0,
      "description": "В вводном секстаккорде VII6 удвоение примы (вводного тона) строго запрещено; удваивается терция (бас) или квинта."
    },
    {
      "id": "SEVENTH_CHORD_INVERSION_INCOMPLETE",
      "category": "doubling",
      "severity": "hard_gate",
      "penalty": 100000.0,
      "description": "Обращения септаккордов (65, 43, 2) применяются только в полном виде: прима, терция, квинта и септима присутствуют по одному разу."
    },
    {
      "id": "SEVENTH_CHORD_DISTRIBUTION",
      "category": "doubling",
      "severity": "hard_gate",
      "penalty": 100000.0,
      "description": "Септаккорд основного вида должен быть полным (все четыре тона по разу) или неполным (удвоенная прима, терция, септима, пропущенная квинта); для VII7 неполный вид строго запрещён."
    },
    {
      "id": "CHORD_ROOT_MISSING",
      "category": "doubling",
      "severity": "hard_gate",
      "penalty": 100000.0,
      "description": "В аккорде отсутствует прима (обязательна в септаккордах, неаполитанском аккорде N и хроматической субмедианте bVI)."
    },
    {
      "id": "CHORD_THIRD_MISSING",
      "category": "doubling",
      "severity": "hard_gate",
      "penalty": 100000.0,
      "description": "В аккорде отсутствует терция: терцовый тон обязателен в каждом аккорде и каждом обращении, включая финальный."
    },
    {
      "id": "CHORD_FIFTH_MISSING",
      "category": "doubling",
      "severity": "hard_gate",
      "penalty": 100000.0,
      "description": "В аккорде отсутствует квинта. Пропуск допустим только в неуменьшённом секстаккорде без удвоенного баса, в неполной финальной тонике с утроенной примой и в VI при прерванном обороте."
    },
    {
      "id": "CHORD_SEVENTH_MISSING",
      "category": "doubling",
      "severity": "hard_gate",
      "penalty": 100000.0,
      "description": "В септаккорде отсутствует септима."
    },
    {
      "id": "DOUBLING_NEAPOLITAN_THIRD",
      "category": "doubling",
      "severity": "hard_gate",
      "penalty": 100000.0,
      "description": "В неаполитанском секстаккорде N6 терция (бас, тоническая ступень) обязана удваиваться."
    },
    {
      "id": "DOUBLING_NEAPOLITAN_ROOT_FORBIDDEN",
      "category": "doubling",
      "severity": "hard_gate",
      "penalty": 100000.0,
      "description": "В неаполитанском секстаккорде N6 удвоение примы (ступени bII) строго запрещено."
    },
    {
      "id": "DOUBLING_NEAPOLITAN_ROOT",
      "category": "doubling",
      "severity": "hard_gate",
      "penalty": 100000.0,
      "description": "В неаполитанском аккорде N основного вида прима обязана удваиваться."
    },
    {
      "id": "DOUBLING_BVI",
      "category": "doubling",
      "severity": "hard_gate",
      "penalty": 100000.0,
      "description": "В хроматической субмедианте bVI обязана удваиваться прима или терция; неполное трезвучие bVI запрещено."
    }
  ]
}
````

## File: frontend/src/components/GraderPanel.tsx
````typescript
import React, { useState } from "react";
import { Award, Upload, BookOpen, Sparkles } from "lucide-react";
import type { SATBVoicing } from "../audio/synth";
import { Button } from "./ui/Button";
import { Input } from "./ui/Input";
import { GraderScoreMatrix } from "./grader/GraderScoreMatrix";
import { GraderViolationsList } from "./grader/GraderViolationsList";
import type { GraderReportData, GraderViolationItem } from "./grader/GraderViolationsList";
import { SAMPLE_TESTS } from "./grader/sampleTests";
import type { GraderSampleTest } from "./grader/sampleTests";
⋮----
export interface GraderMeta {
  key: { tonic: string; mode: string };
  timeSignature: string;
  chords: string[];
  durations: string[];
  asciiScore?: string;
}
⋮----
interface GraderPanelProps {
  selectedKey: { tonic: string; mode: string };
  timeSignature?: string;
  allowExtendedRanges: boolean;
  onGradeComplete: (
    report: GraderReportData,
    musicxml: string,
    voicings: SATBVoicing[],
    meta?: GraderMeta
  ) => void;
  onHighlightMeasure: (measure: number) => void;
}
⋮----
const runGrading = async (
    targetVoicings = voicings,
    targetChordsInput = chordsInput,
    targetKey = currentKey,
    targetTimeSig = currentTimeSignature,
    targetDurations = currentDurations
  ) =>
⋮----
const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) =>
⋮----
const loadSample = (sample: GraderSampleTest) =>
⋮----
const updateVoicePitch = (
    chordIdx: number,
    voice: "soprano" | "alto" | "tenor" | "bass",
    val: number
  ) =>
⋮----
{/* Header */}
⋮----
{/* Preset Pickers */}
⋮----
onClick=
⋮----
{/* Harmonic Functions */}
⋮----
{/* SATB Matrix */}
⋮----
onRemoveChord={() =>
⋮----
{/* Submit button */}
⋮----
{/* Violations report */}
````

## File: frontend/src/components/ScoreDisplay.tsx
````typescript
import React, { useEffect, useRef, useState, useCallback } from "react";
import { OpenSheetMusicDisplay } from "opensheetmusicdisplay";
⋮----
interface ScoreDisplayProps {
  musicxml: string;
  currentChordIndex?: number;
  problemMeasures?: number[];
  title?: string;
}
⋮----
// Initialize OSMD and load/render MusicXML with race condition guard
⋮----
// Empty musicxml clears score
⋮----
// ignore
⋮----
// Bump after every render so measure highlights re-apply even when
// musicxml and problemMeasures change in the same commit.
⋮----
// Apply red measure highlights matching ONLY problemMeasures
⋮----
// 1. Clear any existing measure highlights
⋮----
// 2. Try highlighting via OSMD GraphicSheet if available
⋮----
// 3. Highlight via SVG element IDs / classes matching specific measure number
⋮----
// Dedicated effect for problem measure highlights
⋮----
// Cursor playback effect
⋮----
// Cursor might not be supported if empty
⋮----
{/* Legend & Indicators */}
⋮----
{/* Voice color legend */}
⋮----
{/* Sheet Music Rendering Target: warm matte manuscript paper in a themed
          frame (token-driven). NO blanket SVG invert/hue-rotate: OSMD draws on
          the paper, error markers keep their #ef4444 identity in both themes. */}
````

## File: src/harmony/core/chord.py
````python
"""
Core domain model: ChordFunction, Inversion, and ChordDefinition.

Implements harmonic functions, inversions, chord tone factor composition,
and voice doubling constraints according to the Brigada harmony textbook
(Дубовский, Евсеев, Способин, Соколов — «Учебник гармонии»).
"""
⋮----
class ChordFunction(str, Enum)
⋮----
"""
    Classical harmonic functions:
    - T: Tonic (I degree)
    - S: Subdominant (IV degree)
    - D: Dominant (V degree)
    - II: Supertonic (II degree)
    - VI: Submediant (VI degree)
    - VII: Leading-tone triad / chord (VII degree)
    - III: Mediant triad / chord (III degree)
    - K64: Cadential Six-Four chord (каденционный квартсекстаккорд)
    """
⋮----
T = "T"
S = "S"
D = "D"
II = "II"
VI = "VI"
VII = "VII"
III = "III"
K64 = "K64"
DD = "DD"
N = "N"
BVI = "bVI"
⋮----
@classmethod
    def from_str(cls, s: str) -> ChordFunction
⋮----
"""Parse ChordFunction case-insensitively, supporting 't', 's', 'd', 'k64', etc."""
cleaned = s.strip().upper()
⋮----
@property
    def root_scale_degree(self) -> ScaleDegree
⋮----
"""The fundamental scale degree associated with this function."""
⋮----
@property
    def is_tonic_group(self) -> bool
⋮----
"""True if belonging to the tonic harmonic group (T, VI, bVI)."""
⋮----
@property
    def is_subdominant_group(self) -> bool
⋮----
"""True if belonging to the subdominant harmonic group (S, II, N)."""
⋮----
@property
    def is_dominant_group(self) -> bool
⋮----
"""True if belonging to the dominant harmonic group (D, VII, K64)."""
⋮----
class Inversion(str, Enum)
⋮----
"""
    Chord inversions in classical figured bass:
    - ROOT / 53: Трезвучие в основном виде (5/3)
    - SEXTA / 6: Секстаккорд (6)
    - QUARTSEXTA / 64: Квартсекстаккорд (6/4)
    - SEPTIMA / 7: Септаккорд в основном виде (7)
    - QUINTSEXTA / 65: Квинтсекстаккорд (6/5, 1-е обращение септаккорда)
    - TERZQUART / 43: Терцквартаккорд (4/3, 2-е обращение септаккорда)
    - SECUNDA / 2: Секундаккорд (2, 3-е обращение септаккорда)
    """
⋮----
ROOT = "53"
SEXTA = "6"
QUARTSEXTA = "64"
SEPTIMA = "7"
QUINTSEXTA = "65"
TERZQUART = "43"
SECUNDA = "2"
⋮----
@classmethod
    def from_str(cls, s: str) -> Inversion
⋮----
"""
        Parse Inversion from various notation strings:
        '53', '5/3', 'root', '6', '64', '6/4', '7', '65', '6/5', '43', '4/3', '2'.
        """
cleaned = s.strip().lower().replace("/", "")
mapping = {
⋮----
@property
    def is_seventh(self) -> bool
⋮----
"""True if the inversion represents a 4-note seventh chord."""
⋮----
@property
    def is_triad(self) -> bool
⋮----
"""True if the inversion represents a 3-note triad."""
⋮----
@property
    def bass_factor(self) -> str
⋮----
"""The default chord factor positioned in the bass."""
⋮----
@property
    def symbol(self) -> str
⋮----
"""Standard figured bass symbol."""
⋮----
@dataclass(frozen=True, slots=True)
class ChordDefinition
⋮----
"""
    Concrete chord definition in a specific key.

    Contains:
    - function: harmonic function (T, S, D, II, VI, VII, K64)
    - inversion: inversion (53, 6, 64, 7, 65, 43, 2)
    - key: tonality
    - is_seventh: whether chord is a 7th chord
    - bass_factor: chord factor present in the bass ('root', 'third', 'fifth', 'seventh')

    Provides factor pitch classes, bass pitch class, allowed doublings, and
    validation against Brigada textbook rules (docs/BRIGADE_RULES.md).
    """
⋮----
function: ChordFunction
inversion: Inversion
key: Key
is_seventh: bool = False
bass_factor: Optional[str] = None
⋮----
def __post_init__(self) -> None
⋮----
# Determine is_seventh if inversion implies it
⋮----
# Set default bass factor if not explicitly given
⋮----
# K64 always has scale degree V (the fifth of tonic) in bass
⋮----
@classmethod
    def from_string(cls, name: str, key: Key) -> ChordDefinition
⋮----
"""
        Parse ChordDefinition from notation like 'T', 'T6', 'K64', 'D7', 'D43', 's6', 'VI', 'DD', 'DD7', 'CAD64'.
        """
raw = name.strip()
⋮----
upper_raw = raw.upper()
# K64 / CAD64 special case
⋮----
cleaned = raw.replace("-", "").replace("/", "")
upper_clean = cleaned.upper()
⋮----
pattern = r"^(T|S|D|II|VI|VII|III|DD|N|BVI|bVI|t|s|d|ii|vi|vii|iii|dd|n|bvi)(53|64|65|43|6|7|2)?$"
match = re.match(pattern, cleaned, re.IGNORECASE)
⋮----
fn = ChordFunction.from_str(fn_str)
⋮----
inv = Inversion.from_str(inv_str)
⋮----
inv = Inversion.ROOT
⋮----
is_seventh = inv.is_seventh or (inv_str == "7")
⋮----
@property
    def root(self) -> PitchClass
⋮----
"""Root pitch class of the chord."""
⋮----
@property
    def third(self) -> PitchClass
⋮----
"""
        Third pitch class of the chord.

        In D (Dominant) in minor keys, the third is always raised to the leading tone
        (гармонический вид — мажорная доминанта!).
        """
⋮----
# Secondary leading tone: raised IV degree (+6 semitones from tonic)
⋮----
@property
    def fifth(self) -> PitchClass
⋮----
"""Fifth pitch class of the chord."""
⋮----
# VI scale degree (+9 semitones from tonic)
⋮----
@property
    def seventh(self) -> Optional[PitchClass]
⋮----
"""Seventh pitch class of the chord, if a seventh chord."""
⋮----
@property
    def factors(self) -> dict[str, PitchClass]
⋮----
"""Mapping from factor name ('root', 'third', 'fifth', 'seventh') to PitchClass."""
result = {
⋮----
@property
    def pitch_classes(self) -> frozenset[PitchClass]
⋮----
"""Frozenset of all pitch classes comprising this chord."""
⋮----
@property
    def bass_pitch_class(self) -> PitchClass
⋮----
"""The exact PitchClass required in the bass voice."""
⋮----
@property
    def allowed_doublings(self) -> tuple[str, ...]
⋮----
"""
        Allowed voice doubling factors according to Brigada rules:
        - Main triads (T, S, D) in 5/3: double ROOT ('root', rarely 'fifth'). Third STRICTLY forbidden.
        - Sextachords (T6, S6, D6): double ROOT or FIFTH ('root', 'fifth').
        - K64: STRICTLY double BASS (fifth of triad: 'fifth').
        - D7 root position: full (no doubling) or incomplete (double root: 'root').
        - D7 inversions (65, 43, 2): ALWAYS complete, no doublings allowed ('none').
        - VI triad: double THIRD ('third') in deceptive cadence (D -> VI), or ROOT ('root').
        - II6: double THIRD ('third' - IV scale degree) or ROOT ('root').
        """
# K64
⋮----
# Seventh chords
⋮----
# Full D7 (no doubling) or incomplete D7 (doubled root, fifth omitted)
⋮----
# Inversions of 7th chords must be complete in Brigada style
⋮----
# Deceptive cadence VI
⋮----
# II6
⋮----
# VII6 (leading tone root cannot be doubled; double third or fifth)
⋮----
# III / III6
⋮----
# DD triad
⋮----
# N triad and N6
⋮----
# bVI
⋮----
# Main triads in root position (T, S, D)
⋮----
# Sextachords (T6, S6, D6)
⋮----
# Quartsextachords (passing / auxiliary)
⋮----
def factor_of(self, pc: Union[Pitch, PitchClass, int]) -> Optional[str]
⋮----
"""Identify which chord factor ('root', 'third', 'fifth', 'seventh') corresponds to pc."""
target_pc = pc.pitch_class if isinstance(pc, Pitch) else (
⋮----
"""
        Validate whether the 4 voices in pitches (S, A, T, B) satisfy chord tones,
        bass requirement, and Brigada doubling rules.

        Returns (is_valid: bool, reason: str).
        """
⋮----
pcs = [
⋮----
# 1. Check all pitch classes belong to the chord
⋮----
# 2. Check bass note matches required bass factor
⋮----
# 3. Factor distribution
factor_counts: Counter[str] = Counter()
⋮----
factor = self.factor_of(pc)
⋮----
# Check special doubling rules
# 3.1. K64 strictly doubles fifth (the bass)
⋮----
# 3.2. Deceptive VI triad
⋮----
# 3.2b. Neapolitan chord doubling check
⋮----
# 3.2c. Chromatic submediant (bVI) doubling check
⋮----
# 3.3. Main triads in root position (T, S, D in 5/3): doubling third is forbidden!
⋮----
# 3.4. Dominant seventh inversions (65, 43, 2): must be complete (all 4 factors once)
⋮----
# 3.5. Dominant seventh root position (D7): complete or incomplete (doubled root, no fifth)
⋮----
is_complete = all(factor_counts[f] == 1 for f in ("root", "third", "fifth", "seventh"))
is_incomplete = (
⋮----
# 3.6. General triad doubling check
doubled_factors = [f for f, count in factor_counts.items() if count >= 2]
⋮----
primary_doubled = doubled_factors[0]
⋮----
def __str__(self) -> str
⋮----
fn_str = self.function.value
inv_str = "" if self.inversion == Inversion.ROOT else self.inversion.symbol
⋮----
def __repr__(self) -> str
⋮----
def normalize_roman(symbol: str) -> str
⋮----
"""
    Normalizes Roman numeral chord notation to harmonic function symbol:
    I -> T, IV -> S, V -> D (lowercase to minor variants: i -> t, iv -> s, v -> d).
    Preserves II, III, VI, VII and existing function symbols (T, S, D, K64, etc.),
    as well as figured bass inversion suffixes (e.g. V7 -> D7, i6 -> t6, IV6 -> S6).
    """
s = symbol.strip()
````

## File: src/harmony/rules/voice_leading.py
````python
"""
Horizontal voice leading rules according to Brigade Harmony textbook.
Detects parallel/contrary 5ths and 8ves, hidden 5ths/8ves, overlapping, and forbidden melodic leaps.
"""
⋮----
# Намеренный реэкспорт spacing-проверок: историческая публичная поверхность модуля
# (redundant alias — явный re-export, F401 не применяется).
⋮----
VOICE_NAMES = ("Soprano", "Alto", "Tenor", "Bass")
VOICE_PAIRS = (
⋮----
(0, 1),  # S - A
(0, 2),  # S - T
(0, 3),  # S - B
(1, 2),  # A - T
(1, 3),  # A - B
(2, 3),  # T - B
⋮----
"""
    Checks for parallel pure fifths and pure octaves/unisons across all 6 voice pairs.
    Direct motion into the same pure interval between the same pair of voices is strictly forbidden.
    Catches diminished 5th -> perfect 5th in similar motion (PARALLEL_DIM5_P5).
    Does not apply to pure octave shifts within the same chord (prev_chord == curr_chord).
    """
prev_satb = to_satb(prev_voicing)
curr_satb = to_satb(curr_voicing)
violations: list[RuleViolation] = []
⋮----
is_same_chord = False
⋮----
p_sym = parse_chord_symbol(prev_chord)
c_sym = parse_chord_symbol(curr_chord)
⋮----
is_same_chord = True
⋮----
d1 = c1 - p1
d2 = c2 - p2
⋮----
# Motion must be in the same direction and non-zero
⋮----
raw_prev = abs(p1 - p2)
raw_curr = abs(c1 - c2)
int_prev = raw_prev % 12
int_curr = raw_curr % 12
⋮----
# Catch dim 5th -> perfect 5th in similar motion
⋮----
# Skip parallel checks on pure octave repositioning within the same chord
⋮----
"""
    Checks for contrary fifths and octaves: voices moving in opposite directions
    retaining or arriving from a pure 5th/8ve into another pure 5th/8ve.
    Checks exact pure intervals (5th: 7, 19; 8ve: 12, 24, 36).
    Does not apply to voice exchanges or repositioning within the same chord (prev_chord == curr_chord).
    """
⋮----
# Contrary motion: opposite directions
⋮----
# Pure fifths: 7 or 19 or 31 semitones (modulo 12 == 7)
⋮----
# Pure octaves / unison: modulo 12 == 0
⋮----
description = (
⋮----
"""
    Checks for hidden (direct) fifths and octaves between outer voices (Soprano and Bass).
    If Soprano and Bass move in the same direction into a pure 5th or 8ve,
    Soprano MUST move by step (|dS| <= 2). A leap in soprano (|dS| > 2) is forbidden.
    Does not duplicate violation if parallel violation is already recorded for outer voices.
    """
⋮----
ds = curr_satb[0] - prev_satb[0]
db = curr_satb[3] - prev_satb[3]
⋮----
# Direct motion between outer voices
⋮----
raw_curr = abs(curr_satb[0] - curr_satb[3])
⋮----
# If soprano leaps by more than a step (> 2 semitones)
⋮----
interval_type = "fifth"
⋮----
interval_type = "unison"
⋮----
interval_type = "octave"
⋮----
"""
    Checks for voice overlapping (перекрывание голосов):
    A voice must not move higher than the previous pitch of its upper neighbor,
    or lower than the previous pitch of its lower neighbor.
    """
⋮----
# Upper movements crossing previous upper neighbor
⋮----
# Downward movements crossing previous lower neighbor
⋮----
"""
    Checks for forbidden melodic intervals in any single voice:
    - Melodic leaps of a seventh (10 or 11 semitones) or wider than an octave (> 12 semitones)
    - Tritone melodic leaps (augmented 4th / diminished 5th, 6 semitones), with exception:
      diminished 5th DOWN (-6) resolving inwards by step up (+1 or +2) is permitted.
    - Augmented second leaps (3 semitones between scale degrees VI and VII# in harmonic minor)
    - Augmented fifth leaps (8 semitones, e.g. III -> VII# in harmonic minor)
    - Diminished seventh leaps (9 semitones, e.g. VII# -> VI in harmonic minor)
    - Diminished fourth leaps (4 semitones, e.g. VII# -> III in harmonic minor)
    - Two consecutive leaps in the same direction (|d1| > 2 and |d2| > 2, d1*d2 > 0)
    """
⋮----
# Check two leaps in same direction if history provided
⋮----
p2_satb = to_satb(prev2_voicing)
⋮----
d_prev = prev_satb[idx] - p2_satb[idx]
d_curr = curr_satb[idx] - prev_satb[idx]
⋮----
p = prev_satb[idx]
c = curr_satb[idx]
delta = c - p
step = abs(delta)
⋮----
# Seventh leaps or excessive leaps (> 12)
⋮----
# Tritone leap (6 semitones: aug 4th or dim 5th)
⋮----
# Diminished 5th DOWN (-6 semitones): permitted if resolving inwards
⋮----
is_permitted = False
⋮----
d_prev = prev_satb[idx] - to_satb(prev2_voicing)[idx]
⋮----
is_permitted = True
⋮----
next_pitch = to_satb(next_voicing)[idx]
next_delta = next_pitch - c
⋮----
# If prev2 is not provided and next_voicing is None, allow as before
⋮----
# Tritone leap (+6) is strictly forbidden
⋮----
# Augmented 2nd leap (3 semitones between VI and VII# in harmonic minor/major)
⋮----
deg6_pc = (tonic_pc + 8) % 12
deg7_pc = (tonic_pc + 11) % 12
pcs = {p % 12, c % 12}
⋮----
# Diminished 7th leap (9 semitones between VII# and VI in minor/harmonic major)
⋮----
# Augmented 5th leap (8 semitones, e.g. III -> VII# in harmonic minor, III -> VIb in harmonic major)
⋮----
deg3_min_pc = (tonic_pc + 3) % 12
⋮----
deg3_maj_pc = (tonic_pc + 4) % 12
⋮----
# Diminished 4th leap (4 semitones between VII# and III in harmonic minor/major)
⋮----
"""
    Checks for illegal motion into or out of unisons:
    In classical harmony, a unison between any pair of voices can only be approached
    or left by contrary motion or oblique motion (one voice stationary).
    Approaching or leaving a unison in direct (similar) motion is strictly forbidden.
    """
⋮----
# Direct motion: both voices move in the same non-zero direction
⋮----
# 1. Direct motion INTO unison
⋮----
# 2. Direct motion OUT OF unison
⋮----
"""
    Runs full suite of horizontal voice-leading transition checks.
    """
violations = []
````

## File: pyproject.toml
````toml
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "harmony"
version = "0.1.0"
description = "Classical four-part harmony solver based on the Brigada textbook."
readme = "README.md"
requires-python = ">=3.10"
dependencies = [
    "fastapi>=0.110.0",
    "uvicorn[standard]>=0.28.0",
    "pydantic>=2.0.0",
    "python-multipart>=0.0.9",
    "mido>=1.3.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "ruff>=0.4.0",
    "httpx>=0.27.0",
]
desktop = [
    "pywebview>=5.0.0",
    "pyinstaller>=6.0.0",
]

[tool.setuptools.packages.find]
where = ["src"]

[tool.ruff]
line-length = 120
target-version = "py310"
# .redteam/scratch — исторические redteam-скрипты (одноразовые охоты/зонды),
# вне скоупа продуктовой гигиены кода.
extend-exclude = [".redteam/scratch"]

[tool.ruff.lint]
select = ["E", "F", "W"]
ignore = ["E501"]

[tool.ruff.lint.per-file-ignores]
# E402 намеренный: скрипты бутстрапят sys.path (корень проекта) ДО импортов src.harmony.*,
# чтобы работать без установленного пакета. Перестановка ломает запуск.
"scripts/*" = ["E402"]

[tool.pytest.ini_options]
pythonpath = [".", "src"]
testpaths = ["tests"]
addopts = "-ra -q"
filterwarnings = [
    "ignore::DeprecationWarning",
    "ignore::pytest.PytestDeprecationWarning",
]
````

## File: README.md
````markdown
# 🎼 Brigade Classical 4-Part Harmony Engine (Бригадный учебник)

[![Tests](https://img.shields.io/badge/pytest-848%20passed-brightgreen.svg)](tests/)
[![Python](https://img.shields.io/badge/python-3.10%2B%20%7C%203.14%2B-blue.svg)](pyproject.toml)
[![Architecture](https://img.shields.io/badge/architecture-Viterbi%20DP%20%2B%20CFG-orange.svg)](docs/MATH_MODEL.md)
[![FastAPI](https://img.shields.io/badge/backend-FastAPI-009688.svg)](backend/)
[![React](https://img.shields.io/badge/frontend-React%2019%20%2B%20OSMD-61DAFB.svg)](frontend/)

Высокоточный, алгоритмически строгий движок классической четырёхголосной гармонизации (SATB) на базе динамического программирования (Viterbi DP) и синтаксической грамматики макро-плана по правилам канонического Бригадного учебника гармонии (И. Дубовский, С. Евсеев, И. Способин, В. Соколов).

Включает в себя:
- **Алгоритмическое символическое ядро** на чистом Python без внешних C-зависимостей (Viterbi DP + CFG грамматика макро-синтаксиса).
- **Консерваторский инспектор («Grader»)**: автоматическая проверка студенческих задач с диагностикой нарушений вплоть до такта, пары голосов и ноты.
- **REST API микросервер** на базе FastAPI / Uvicorn с полной поддержкой импорта/экспорта MusicXML/MIDI.
- **Интерактивный Web GUI** на React 19 + TypeScript + OpenSheetMusicDisplay (OSMD) для мгновенной визуализации партитур.
- **One-click запуск**: скрипт [`run_app.py`](run_app.py) поднимает бэкенд и сразу открывает браузер.

---

## 🏛️ Архитектура системы

В отличие от наивных бэктрекинг-солверов или непрозрачных нейросеток (галлюцинирующих параллельными квинтами и недопустимыми оборотами $D \to S$), движок реализует строгую иерархическую модель:

```
                            [Входная мелодия / Soprano]
                                         │
                   ┌─────────────────────┴─────────────────────┐
                   ▼                                           ▼
          [Анализ и парсинг]                           [Автодетект тональности]
      (Ноты / Ступени / MIDI / XML)                    (24 канонических лада)
                   │                                           │
                   └─────────────────────┬─────────────────────┘
                                         ▼
                   ┌───────────────────────────────────────────┐
                   │        Macro Syntax Engine (CFG)          │  <-- Грамматика функций, кадансов
                   └─────────────────────┬─────────────────────┘      и прерванных оборотов
                                         │ Допустимые планы (T, S, D, K64, D7, DD...)
                                         ▼
                   ┌───────────────────────────────────────────┐
                   │       State Lattice & Rule Pruning        │  <-- Генерация срезов SATB
                   └─────────────────────┬─────────────────────┘
                                         │
                          ┌──────────────┴──────────────┐
                          ▼                             ▼
              ┌───────────────────────┐   ┌───────────────────────────┐
              │ Hard Gates (правила)  │   │ Soft Cost / Style Priors  │  <-- Неотрицательные эвристики
              │ - Параллельные 5 и 8  │   │ - Закон кратчайшего пути  │      и n-gram prior стиля
              │ - Скрытые 5 и 8       │   │ - Противодвижение баса    │      (models/style_weights.json)
              │ - Удвоения и септимы  │   │ - Тесситурный комфорт     │
              │ - Скачки и альтерации │   │ - Штрафы за скачки баса   │
              └───────────┬───────────┘   └─────────────┬─────────────┘
                          │                             │
                          └──────────────┬──────────────┘
                                         ▼
                   ┌───────────────────────────────────────────┐
                   │          Viterbi DP Optimizer             │  <-- O(N * K^2) глобальный оптимум
                   └─────────────────────┬─────────────────────┘
                                         │
                    ┌────────────────────┼────────────────────┐
                    ▼                    ▼                    ▼
          ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
          │  Colored MusicXML│ │  Multi-Track MIDI│ │   ASCII Score    │
          │  (OSMD + цвета)  │ │  (Формат 0 / 1)  │ │  (Терминал/Логи) │
          └──────────────────┘ └──────────────────┘ └──────────────────┘
```

---

## 🛠️ Установка и окружение

> [!WARNING]
> Каталог `.venv` в репозитории не является источником истины и может быть несовместим с вашей системой или версией Python. Всегда создавайте собственное виртуальное окружение.

### 1. Создание и активация окружения (Python 3.10+ / 3.14):
```bash
python -m venv .venv

# Windows (PowerShell):
.venv\Scripts\Activate.ps1

# Linux / macOS:
source .venv/bin/activate
```

### 2. Установка зависимостей проекта и dev-инструментов:

Проект ведётся на [uv](https://docs.astral.sh/uv/) (`uv.lock` лежит в репозитории) — это рекомендуемый путь:
```bash
uv sync --extra dev --extra desktop
```

Альтернатива без uv:
```bash
pip install -e .[dev]
```

### 3. Запуск веб-сервера и интерфейса:
```bash
python run_app.py
```

---

## 🚀 Быстрый старт

### 0. Зависимости и самопроверка

```bash
# зависимости (проект на uv)
uv sync --extra dev --extra desktop

# прогон тестового сьюта (Windows, PowerShell)
.venv\Scripts\python.exe -m pytest -q
```

### 1. Запуск Web GUI в один клик

Запуск единого веб-сервиса (FastAPI + собранный SPA на React):

```bash
python run_app.py
```
Скрипт автоматически поднимает Uvicorn на `http://127.0.0.1:8000` и распахивает окно в вашем браузере.

---

### 2. Запуск нативного Windows Desktop Shell

Для работы в режиме настольного приложения без браузера и терминала:

```bash
# Запуск из исходников
python -m desktop

# Сборка портативного бинарника (.exe)
pip install -e ".[desktop]"
python -m PyInstaller desktop.spec --noconfirm
```

Собранное портативное приложение доступно по пути `dist/HarmonyEngine/HarmonyEngine.exe`.

**Особенности и ограничения Desktop-версии:**
- **Движок отображения**: Microsoft Edge WebView2 Evergreen Runtime. В Windows 10 (20H2+) и Windows 11 встроен по умолчанию.
- **Single-instance**: при повторном запуске приложение автоматически разворачивает существующее окно.
- **Логи**: сохраняются с ротацией в `%LOCALAPPDATA%\HarmonyEngine\logs\desktop.log`.
- **SmartScreen**: при первом запуске неподписанного бинарника Windows может запросить подтверждение ("Подробнее" → "Выполнить в любом случае").

---

### 3. Запуск через консольный CLI

Гармонизация мелодии одной командой без графического интерфейса:

```bash
python -m src.harmony.cli --melody "64,65,67,62,60" --tonic C --mode Major --musicxml output/result.musicxml --midi output/result.mid
```

**Параметры CLI:**
- `--melody`: Номера высот в стандарте MIDI через запятую (`64,65,67,62,60` соответствует `E4, F4, G4, D4, C4`).
- `--tonic`: Тоника (`C`, `G`, `F#`, `Bb`, `A` и т.д., по умолчанию `C`).
- `--mode`: Лад (`Major` или `Minor`, по умолчанию `Major`).
- `--musicxml`: Путь для сохранения партитуры MusicXML (открывается в MuseScore, Sibelius, Dorico, Finale).
- `--midi`: Путь для экспорта полифонического файла MIDI.

---

### 3. Использование через Python API

```python
from src.harmony.pipeline import Harmonizer
from src.harmony.core.types import Key

harmonizer = Harmonizer()
key = Key("C", "Major")

# Мелодия сопрано с метрическими акцентами
melody = [
    {"pitch": 64, "is_downbeat": True},   # E4
    {"pitch": 65, "is_downbeat": False},  # F4
    {"pitch": 67, "is_downbeat": True},   # G4
    {"pitch": 62, "is_downbeat": False},  # D4
    {"pitch": 60, "is_downbeat": True},   # C4
]

result = harmonizer.harmonize(melody=melody, key=key)

if result.is_success:
    solution = result.best_solution
    print(solution.ascii_score)
    solution.save_musicxml("output/solution.musicxml", title="Гармонизация Способина")
    solution.save_midi("output/solution.mid")
```

---

## 🌐 REST API Gateway (`backend/`)

Сервер построен на FastAPI и предоставляет полный набор сервисов для интеграции с мобильными клиентами, DAW или веб-интерфейсами.

| Метод | Эндпоинт | Описание |
|---|---|---|
| `GET` | `/api/health` | Проверка жизнеспособности сервиса |
| `GET` | `/api/keys` | Список 24 канонических тональностей (12 мажоров, 12 гармонических миноров) |
| `POST` | `/api/detect-key` | Автоматическое определение тональности по входной мелодии |
| `POST` | `/api/parse-text` | Парсинг нотного текста (названия `C4 E4`, ступени `1 3 4 5`, MIDI `60, 64`) |
| `POST` | `/api/harmonize` | Полный цикл гармонизации: возвращает топ-3 решения, функциональный план, Viterbi-стоимость и цветной MusicXML |
| `POST` | `/api/grade` | **Консерваторский инспектор**: аудит студенческого голосоведения с выставлением оценки (5, 4, 3, 2) |
| `POST` | `/api/import-file` | Загрузка файлов `.musicxml`, `.xml`, `.mid`, `.midi` |
| `POST` | `/api/export/midi` | Генерация и стриминг бинарного MIDI файла |
| `POST` | `/api/export/musicxml`| Генерация и отдача 4-голосного MusicXML с цветовой разметкой голосов |

---

## 🎓 Консерваторский инспектор («Student Grader»)

Движок умеет не только решать задачи, но и проверять чужие решения как строгий профессор консерватории. 

Через метод `grade_satb_solution` (или эндпоинт `POST /api/grade`) выполняется полный прогон по всем 12 правилам голосоведения с выдачей подробнейшего вердикта:

```json
{
  "grade": "2 (Не зачтено)",
  "is_valid": false,
  "hard_violations_count": 2,
  "problem_measures": [3, 5],
  "violations": [
    {
      "measure": 3,
      "rule_id": "PARALLEL_FIFTHS",
      "severity": "hard_gate",
      "message_ru": "Такт 3: Параллельные квинты между басом и альтом (D2-A3 → E2-B3)",
      "voices": ["бас", "альт"],
      "notes": ["бас: D2 -> E2", "альт: A3 -> B3"]
    },
    {
      "measure": 5,
      "rule_id": "DOUBLING_K64_BASS",
      "severity": "hard_gate",
      "message_ru": "Такт 5: В квартсекстаккорде K64 удвоена терция вместо баса (квинты)",
      "voices": ["сопрано", "тенор"]
    }
  ]
}
```

---

## 📋 Реализованные правила Бригадника

Все правила формализованы в машинном каталоге [`docs/brigade_rules.json`](docs/brigade_rules.json) и спецификациях [`docs/BRIGADE_RULES.md`](docs/BRIGADE_RULES.md) и [`docs/MATH_MODEL.md`](docs/MATH_MODEL.md):

| Категория | Правило | Реализация |
|---|---|---|
| **Диапазоны** | S (C4–A5), A (G3–D5), T (C3–G4), B (E2–C4) | Hard Gate |
| **Расположение** | Тесное ($\le 4^{ta}$), широкое ($5^{ta}-8^{va}$), смешанное | Hard Gate / Soft Penalty |
| **Интервалы голосов** | Расстояние между S–A и A–T строго $\le 8^{va}$ | Hard Gate |
| **Перекрещивание** | Перекрещивание и переплывание голосов категорически запрещены | Hard Gate |
| **Параллелизмы** | Параллельные и противоположные квинты и октавы | Hard Gate |
| **Скрытые 5 и 8** | Прямое движение крайних голосов к чистой квинте / октаве | Hard Gate |
| **Мелодика** | Запрет ходов на тритоны, увеличенные интервалы и септимы | Hard Gate |
| **Удвоения** | В трезвучиях строго прима; в $K^6_4$ строго бас (квинта трезвучия) | Hard Gate |
| **Прерванный оборот** | В трезвучии $VI$ ступени после $D$ строго удваивается терция (тоника) | Hard Gate |
| **Разрешения** | Септима $D_7$, $VII_7$, $II_7$ разрешается только на ступень вниз; $D^4_3 \to T_6$ | Hard Gate |
| **Синтаксис** | Запрет регрессии $D \to S$; $K^6_4$ только на сильном времени | Hard Gate |
| **Стиль и плавность**| Противодвижение баса, минимальные перемещения средних голосов | Soft Cost (Heuristics / n-gram prior) |

---

## 📂 Структура проекта

```
aitraining/
├── backend/                   # FastAPI REST шлюз
│   ├── api.py                 # Маршруты и схемы валидации Pydantic
│   ├── exporters.py           # Форматирование цветного MusicXML (OSMD)
│   ├── grader.py              # Консерваторский инспектор студенческих работ
│   ├── importers.py           # Парсеры MusicXML и бинарного MIDI
│   ├── key_detector.py        # Тональный анализатор (24 тональности)
│   └── main.py                # Точка входа FastAPI приложения
├── docs/                      # Математическая и музыковедческая спецификация
│   ├── BRIGADE_RULES.md       # Подробный свод правил Бригадника
│   ├── brigade_rules.json     # Машиночитаемый реестр правил
│   └── MATH_MODEL.md          # Математическая модель решётки и Витерби
├── frontend/                  # Веб-интерфейс (SPA)
│   ├── src/                   # React 19 + TypeScript + Tailwind/CSS
│   ├── dist/                  # Собранный production бандл
│   └── package.json           # Зависимости: OpenSheetMusicDisplay, Lucide
├── models/                    # Веса и калибровки моделей
│   └── style_weights.json     # Прототипы голосоведения и n-gram априорные веса
├── scripts/                   # Служебные скрипты и утилиты
│   ├── generate_dataset.py    # Многопроцессорный синтез датасета (50 000+ пар)
│   └── stress_test_harness.py # 24-тональный стресс-тест солвера
├── src/harmony/               # Алгоритмическое ядро солвера
│   ├── core/                  # Базовые типы: Pitch, Chord, Key, Voicing
│   ├── export/                # Экспортёры в MusicXML, MIDI, ASCII
│   ├── ml/                    # n-gram статистический скорер стиля (экспериментальный)
│   ├── rules/                 # Реализация Hard Gates правил голосоведения
│   ├── solver/                # Генератор состояний и Viterbi DP
│   ├── syntax/                # CFG гармоническая грамматика Способина
│   ├── cli.py                 # Консольный интерфейс CLI
│   └── pipeline.py            # Высокоуровневый оркестратор Harmonizer
├── tests/                     # Сьют автоматических тестов (848 тестов)
├── pyproject.toml             # Конфигурация сборки, ruff и pytest
└── run_app.py                 # One-click скрипт запуска Web-приложения
```

---

## 🧪 Тестирование и производительность

Тестовый сьют покрывает критические пути движка: юнит-тесты правил, аккордовых типов, тональностей, разрешений, модуляций, синтаксиса, экспорта, а также интеграционные тесты эталонных консерваторских задач из задачника Способина и REST API.

Запуск тестов:
```bash
# в активированном окружении
pytest -q

# без активации (Windows, PowerShell)
.venv\Scripts\python.exe -m pytest -q
```

Фактический статус на ветке `master` (ветка `redteam-p2` влита fast-forward и удалена):
```
848 passed, 0 failed, 0 skipped
```

### Реальная производительность

Гармонизация типовой 5-нотной мелодии методом Viterbi DP с полной валидацией академических предикатов на чистом Python (CPython 3.14):
- **Время одного прогона:** ~330–350 мс
- **Развёрнутая 16-тактовая задача:** ~1–2 с
- **Память:** единицы мегабайт (полиномиальная сложность $O(N \cdot K_{\max})$)

### Стресс-тестирование по 24 тональностям

Для проверки надёжности алгоритма на случайных мелодиях предусмотрен автономный харнесс:

```bash
python scripts/stress_test_harness.py
```
В текущей версии алгоритм стабильно гармонизует подавляющее большинство тональностей (20–22 из 24). В сложных последовательностях гармонического минора тупики решётки разрешаются динамическим репланнингом.

---

## ⚠️ Ограничения системы

1. **Жёсткие правила голосоведения (Hard Gates):**
   Движок бескомпромиссно отсекает параллельные и противоположные квинты/октавы, перекрещивания, переплывания голосов и ходы на запрещённые интервалы (тритоны, септимы, увеличенные секунды). Если мелодический контур не допускает ни одного строго корректного голосоведения в рамках сгенерированной решётки, солвер не выдаёт компромиссную халтуру, а возвращает ошибку неразрешимости пути.

2. **Неаккордовые звуки (NCT):**
   Поддерживаются только проходящие и вспомогательные звуки на слабых долях такта. Задержания (suspensions), синкопы, камбиаты и брошенные ноты в текущей модели не рассчитываются.

3. **Минорные лады и тупики решётки:**
   В гармоническом миноре наличие увеличенной секунды между VI и VII# ступенями сильно сужает коридоры допустимого движения средних голосов. Возникающие тупики решётки требуют механизма репланнинга (replanning) синтаксического макро-плана.

4. **Хроматика и отклонения:**
   Поддержаны канонические альтерации и отклонения Бригадного учебника (K64, D7, DD/D43/D2, прерванный оборот VI). Сложные альтерированные аккорды позднего романтизма и далёкие модуляции поддержаны лишь частично.
````

## File: frontend/src/components/ControlPanel.tsx
````typescript
import React from "react";
import {
  Wand2,
  Sparkles,
  Sliders,
  CheckCircle2,
  Layers,
  Clock,
  ArrowRight,
} from "lucide-react";
import { Button } from "./ui/Button";
import { Select } from "./ui/Select";
⋮----
export interface CandidateSolution {
  id: string;
  rank: number;
  cost: number;
  chords: string[];
  progression_preview: string;
  description: string;
  voicings: Array<{ soprano: number; alto: number; tenor: number; bass: number }>;
  musicxml: string;
  ascii_score: string;
}
⋮----
interface ControlPanelProps {
  keys: Array<{ tonic: string; mode: string; fifths: number; title?: string; name?: string }>;
  selectedKey: { tonic: string; mode: string };
  onKeyChange: (key: { tonic: string; mode: string }) => void;
  onAutoDetectKey: () => void;
  timeSignature: string;
  onTimeSignatureChange: (val: string) => void;
  allowExtendedRanges: boolean;
  onToggleExtendedRanges: (val: boolean) => void;
  allowSecondaryDominants: boolean;
  onToggleSecondaryDominants: (val: boolean) => void;
  allowAdjacentUnisons: boolean;
  onToggleAdjacentUnisons: (val: boolean) => void;
  relaxHardGates: boolean;
  onToggleRelaxHardGates: (val: boolean) => void;
  onHarmonize: () => void;
  isHarmonizing: boolean;
  isMelodyEmpty?: boolean;
  latencyMs: number | null;
  candidates: CandidateSolution[];
  selectedCandidateId: string | null;
  onSelectCandidate: (candidate: CandidateSolution) => void;
}
⋮----
{/* Row 1: Key selection + Auto detect */}
⋮----
onChange={(e) =>
⋮----
{/* Time Signature (Meter) Selector */}
⋮----
{/* Row 2: Strictness Toggles */}
⋮----
{/* Candidate Selector (Top-3 pool) */}
⋮----
{/* Chord progression preview */}
````

## File: src/harmony/export/musicxml.py
````python
"""
MusicXML exporter for classical four-part harmony (SATB).
Produces valid MusicXML 3.1 / 4.0 partwise score files readable by MuseScore, Sibelius, Dorico, and Finale.
Supports variable durations, dotted notes, and time signature changes across measures.
"""
⋮----
SHARP_SPELLING = (
⋮----
("C", 0),  # 0: C
("C", 1),  # 1: C#
("D", 0),  # 2: D
("D", 1),  # 3: D#
("E", 0),  # 4: E
("F", 0),  # 5: F
("F", 1),  # 6: F#
("G", 0),  # 7: G
("G", 1),  # 8: G#
("A", 0),  # 9: A
("A", 1),  # 10: A#
("B", 0),  # 11: B
⋮----
FLAT_SPELLING = (
⋮----
("C", 0),   # 0: C
("D", -1),  # 1: Db
("D", 0),   # 2: D
("E", -1),  # 3: Eb
("E", 0),   # 4: E
("F", 0),   # 5: F
("G", -1),  # 6: Gb
("G", 0),   # 7: G
("A", -1),  # 8: Ab
("A", 0),   # 9: A
("B", -1),  # 10: Bb
("B", 0),   # 11: B
⋮----
STEP_NAMES = tuple(s[0] for s in SHARP_SPELLING)
ALTERS = tuple(s[1] for s in SHARP_SPELLING)
⋮----
FIFTHS_TABLE = {
⋮----
# Major
⋮----
# Minor
⋮----
def get_fifths(tonic: str, mode: str) -> int
⋮----
t_clean = tonic.strip().upper().replace("H", "B")
m_clean = "MINOR" if "MINOR" in mode.upper() else "MAJOR"
⋮----
pitch_elem = ET.Element("pitch")
pc = midi_pitch % 12
octave = (midi_pitch // 12) - 1
⋮----
use_flats = True
⋮----
use_flats = False
⋮----
spelling = FLAT_SPELLING if use_flats else SHARP_SPELLING
⋮----
step_elem = ET.SubElement(pitch_elem, "step")
⋮----
alter_elem = ET.SubElement(pitch_elem, "alter")
⋮----
octave_elem = ET.SubElement(pitch_elem, "octave")
⋮----
@dataclass
class NoteSlice
⋮----
satb: tuple[int, int, int, int]
dur_divs: int
xml_type: str
dots: int
chord_sym: str | None
tie_start: bool
tie_stop: bool
is_rest: bool = False
⋮----
@dataclass
class MeasureSliceData
⋮----
measure_num: int
time_signature: TimeSignature
time_sig_changed: bool
slices: list[NoteSlice]
total_divisions: int
⋮----
note = ET.Element("note")
⋮----
dur_elem = ET.SubElement(note, "duration")
⋮----
voice_elem = ET.SubElement(note, "voice")
⋮----
ntype = ET.SubElement(note, "type")
⋮----
staff_elem = ET.SubElement(note, "staff")
⋮----
notations = ET.SubElement(note, "notations")
⋮----
lyric = ET.SubElement(note, "lyric", number="1")
ltext = ET.SubElement(lyric, "text")
⋮----
"""
    Exports a sequence of SATB voicings to a standard MusicXML 3.1 Partwise document.
    Properly formats:
    - Custom time signatures (e.g. 3/4, 2/4, 6/8, 4/4) and meter changes
    - Dotted notes (<type> + <dot/> elements)
    - Dynamic measure grouping based on exact time signature beats and divisions
    - Note splitting across barlines with <tie> and <notations><tied> elements
    - Constant measure duration sums without overflow or underflow
    - 4 independent polyphonic SATB voices across two staves with safe <backup> boundaries
    """
root = ET.Element("score-partwise", version="3.1")
⋮----
# Header: Work / Identification
⋮----
work = ET.SubElement(root, "work")
work_title = ET.SubElement(work, "work-title")
⋮----
identification = ET.SubElement(root, "identification")
creator = ET.SubElement(identification, "creator", type="composer")
⋮----
# Part-list
part_list = ET.SubElement(root, "part-list")
score_part = ET.SubElement(part_list, "score-part", id="P1")
part_name = ET.SubElement(score_part, "part-name")
⋮----
# Part
part = ET.SubElement(root, "part", id="P1")
⋮----
rough_string = ET.tostring(root, encoding="utf-8")
reparsed = minidom.parseString(rough_string)
⋮----
# Key signature
tonic_str = "C"
mode_str = "Major"
⋮----
tonic_str = key.tonic
mode_str = key.mode
⋮----
tonic_str = key.get("tonic", "C")
mode_str = key.get("mode", "Major")
⋮----
parts = key.split()
tonic_str = parts[0] if parts else "C"
mode_str = parts[1] if len(parts) > 1 else "Major"
⋮----
fifths_val = get_fifths(tonic_str, mode_str)
⋮----
divisions_per_quarter = 4
default_ts = TimeSignature.parse(time_signature)
⋮----
curr_ts = default_ts
prev_ts = None
curr_measure_num = 1
offset_in_measure_q = 0.0
⋮----
current_slices: list[NoteSlice] = []
measures_data: list[MeasureSliceData] = []
⋮----
STANDARD_REST_DURS = [
⋮----
def close_current_measure()
⋮----
rem_space = curr_ts.measure_duration_quarters - offset_in_measure_q
⋮----
found = False
⋮----
divs = int(round(q_val * divisions_per_quarter))
⋮----
found = True
⋮----
m_total_divs = int(round(curr_ts.measure_duration_quarters * divisions_per_quarter))
time_changed = (curr_ts != prev_ts)
⋮----
prev_ts = curr_ts
⋮----
current_slices = []
⋮----
dur_raw = durations[i] if durations and i < len(durations) else "half"
⋮----
dur_name = dur_raw.get("duration", "half")
⋮----
note_ts = TimeSignature.parse(dur_raw["time_signature"])
⋮----
curr_ts = note_ts
⋮----
dur_name = dur_raw
⋮----
dur_q = parse_duration_quarters(dur_name)
chord_sym = (
⋮----
rem_q = dur_q
is_first_slice = True
⋮----
space_q = curr_ts.measure_duration_quarters - offset_in_measure_q
⋮----
space_q = curr_ts.measure_duration_quarters
⋮----
slice_q = min(rem_q, space_q)
will_continue = (slice_q < rem_q - 1e-4)
is_continuation = not is_first_slice
⋮----
slice_divs = int(round(slice_q * divisions_per_quarter))
⋮----
is_first_slice = False
⋮----
m_num = m_data.measure_num
m_time_sig = m_data.time_signature
time_changed = m_data.time_sig_changed
m_total_divisions = m_data.total_divisions
⋮----
measure = ET.SubElement(part, "measure", number=str(m_num))
⋮----
# Attributes on measure 1 or upon meter change
⋮----
attrs = ET.SubElement(measure, "attributes")
⋮----
divs = ET.SubElement(attrs, "divisions")
⋮----
key_elem = ET.SubElement(attrs, "key")
fifths_elem = ET.SubElement(key_elem, "fifths")
⋮----
mode_elem = ET.SubElement(key_elem, "mode")
⋮----
time_elem = ET.SubElement(attrs, "time")
beats = ET.SubElement(time_elem, "beats")
⋮----
beat_type = ET.SubElement(time_elem, "beat-type")
⋮----
staves = ET.SubElement(attrs, "staves")
⋮----
clef1 = ET.SubElement(attrs, "clef", number="1")
sign1 = ET.SubElement(clef1, "sign")
⋮----
line1 = ET.SubElement(clef1, "line")
⋮----
clef2 = ET.SubElement(attrs, "clef", number="2")
sign2 = ET.SubElement(clef2, "sign")
⋮----
line2 = ET.SubElement(clef2, "line")
⋮----
# Voice 1 (Soprano) - Staff 1
⋮----
note = make_note_element(
⋮----
# Voice 2 (Alto) - Staff 1
backup = ET.SubElement(measure, "backup")
b_dur = ET.SubElement(backup, "duration")
⋮----
# Voice 3 (Tenor) - Staff 2
backup2 = ET.SubElement(measure, "backup")
b_dur2 = ET.SubElement(backup2, "duration")
⋮----
# Voice 4 (Bass) - Staff 2
backup3 = ET.SubElement(measure, "backup")
b_dur3 = ET.SubElement(backup3, "duration")
````

## File: frontend/src/components/MelodyInput.tsx
````typescript
import React, { useState } from "react";
import { Piano, Clock } from "lucide-react";
import { Card } from "./ui/Card";
import { PianoKeyboard } from "./melody/PianoKeyboard";
import { MidiInputBar } from "./melody/MidiInputBar";
import { NoteList } from "./melody/NoteList";
import { MelodyFileUpload } from "./melody/MelodyFileUpload";
import {
  DURATIONS,
  recalculateDownbeats,
  midiToNoteName,
} from "../utils/durationUtils";
import type { MelodyNote } from "../utils/durationUtils";
⋮----
interface MelodyInputProps {
  melody: MelodyNote[];
  onChange: (newMelody: MelodyNote[]) => void;
  onAutoDetectKey: () => void;
  timeSignature?: string;
}
⋮----
// Downbeat recalculation on meter change lives in useHarmonizer.setTimeSignature
// (event-driven, no setState-in-effect).
⋮----
const handleAddNote = (pitch: number, name?: string) =>
⋮----
is_downbeat: false, // will be recalculated
⋮----
const handleLoadSample = () =>
⋮----
const handleClear = () =>
⋮----
const handleLoadedFromFile = (
    loadedNotes: MelodyNote[],
    loadedTs?: string
  ) =>
⋮----
{/* WebMIDI device status + metronome recording */}
⋮----
onNoteReceived=
⋮----
{/* Visual Piano Keyboard */}
⋮----
{/* Note List / Chips */}
⋮----
{/* File and text upload options */}
````

## File: backend/grader.py
````python
"""
Student Homework Grader ("Консерваторский инспектор").
Validates student SATB solutions using RuleEngine and generates precise,
pedagogical Russian diagnostic reports with measure numbers and note names.
"""
⋮----
VOICE_NAMES_RU = ("сопрано", "альт", "тенор", "бас")
VOICE_NAMES_EN = ("Soprano", "Alto", "Tenor", "Bass")
⋮----
@dataclass
class GraderViolation
⋮----
measure: int
chord_index: int
rule_id: str
severity: str  # "hard_gate" | "soft_penalty"
message_ru: str
voices: list[str]
notes: list[str]
⋮----
@dataclass
class GraderReport
⋮----
is_valid: bool
total_violations: int
hard_violations_count: int
soft_violations_count: int
violations: list[dict[str, Any]]
problem_measures: list[int]
summary_verdict: str
grade: str  # "5 (Отлично)", "4 (Хорошо)", "3 (Удовлетворительно)", "2 (Не зачтено)"
⋮----
"""Generates precise Russian critique with exact note names and voice names."""
curr_satb = to_satb(v_curr)
prev_satb = to_satb(v_prev) if v_prev is not None else None
⋮----
involved_voices: list[str] = []
involved_notes: list[str] = []
⋮----
involved_voices = [VOICE_NAMES_RU[v] for v in voices_tuple]
⋮----
p_name = midi_to_note_name(prev_satb[v])
c_name = midi_to_note_name(curr_satb[v])
⋮----
# Specific formatting per rule
⋮----
# Defect #6: for rule ids without a dedicated Russian formatting branch,
# prefer the Russian catalog description (docs/brigade_rules.json) before
# falling back to the raw validator description / bare rule id.
⋮----
# Fallback to description
⋮----
"""
    Grades an entire 4-part SATB progression using the Brigade RuleEngine.
    Returns structured diagnostic feedback with problem measures, severity,
    and a final pedagogical grade according to the Moscow Conservatory standards.
    Supports variable meters (3/4, 2/4, 6/8, 4/4) and dotted durations.
    """
⋮----
parsed_key = key if isinstance(key, Key) else Key(tonic=parse_key(key)[0], mode=parse_key(key)[1])
engine = RuleEngine(allow_extended_ranges=allow_extended_ranges)
⋮----
# Calculate metric structure and exact measure indices
melody_items = []
⋮----
dur = durations[i] if durations and i < len(durations) else "half"
⋮----
metric_info = calculate_metric_structure(melody_items, default_time_signature=time_signature)
⋮----
violations_list: list[GraderViolation] = []
problem_measures_set: set[int] = set()
⋮----
chord_list = list(chords) if chords else []
seen_violations: set[tuple[int, int, str, tuple[str, ...]]] = set()
⋮----
def _record_violation(viol: Any, measure_num: int, chord_idx: int, v_prev: Any | None, v_curr: Any) -> None
⋮----
dedup_key = (measure_num, chord_idx, viol.rule_id, tuple(voices))
⋮----
# 1. Validate the initial vertical slice (chord 0)
m0 = metric_info[0]["measure"]
db0 = metric_info[0]["is_downbeat"]
c0 = chord_list[0] if chord_list else None
is_single = (len(voicings) == 1)
res_first = engine.validate_voicing(
⋮----
# 2. Validate all transitions and subsequent slices (chords 1..N-1)
# Note: engine.validate() evaluates both slice i (spacing, doubling with prev_chord context,
# and metric syntax) as well as transition i-1 -> i (voice leading, resolutions, chromatic).
⋮----
measure_num = metric_info[i]["measure"]
is_downbeat = metric_info[i]["is_downbeat"]
prev_v = voicings[i - 1]
curr_v = voicings[i]
prev_chord = chord_list[i - 1] if (i - 1) < len(chord_list) else None
curr_chord = chord_list[i] if i < len(chord_list) else None
is_final = (i == len(voicings) - 1)
⋮----
res_trans = engine.validate(
⋮----
# Skip non-rule heuristic costs
⋮----
hard_count = sum(1 for v in violations_list if v.severity == "hard_gate")
soft_count = sum(1 for v in violations_list if v.severity != "hard_gate")
is_clean = (hard_count == 0)
⋮----
# Determine grade
⋮----
grade = "5 (Отлично / Без замечаний)"
verdict = "Безупречное голосоведение! Все каноны Бригадного учебника строго соблюдены."
⋮----
grade = "3 (Удовлетворительно)"
verdict = f"Обнаружена 1 грубая ошибка правил голосоведения в такте {list(problem_measures_set)[0]}."
⋮----
grade = "2 (Не зачтено)"
verdict = f"Обнаружено {hard_count} грубых нарушений правил Способина. Требуется исправление."
⋮----
grade = "2 (Не зачтено / Полный разнос)"
verdict = f"Грубейшие нарушения ({hard_count} ошибок)! Параллелизмы или запрещенные удвоения ломают фактуру."
````

## File: src/harmony/solver/state_generator.py
````python
"""
Fast combinatorial state generator for four-part SATB voicings.
Generates all statically admissible voicings for a given soprano melody note and chord,
pruning forbidden doublings and textural gaps before passing states to the DP graph.
"""
⋮----
# Thread-safe global memoization caches for candidate voicings and static doubling checks
_CANDIDATE_VOICINGS_CACHE: dict[tuple, list[Voicing]] = {}
_STATIC_DOUBLING_CACHE: dict[tuple, list[Any]] = {}
⋮----
def clear_candidate_cache() -> None
⋮----
"""Clears candidate voicings and static doubling caches."""
⋮----
"""
    Generates all statically valid SATB voicings for a given soprano pitch and chord.

    Constraints enforced during generation:
    1. Pitch ranges:
       - S: 60..81 (extended 59..83)
       - A: 55..74 (extended 53..75)
       - T: 48..67 (extended 46..69)
       - B: 40..60 (extended 36..60)
    2. Voice ordering (no voice crossing):
       S >= A >= T >= B
    3. Textural spacing limits:
       S - A <= 12
       A - T <= 12
       T - B <= 24
    4. Chord tone membership:
       Every voice pitch must be one of the permitted pitch classes for the chord.
    5. Doubling and distribution rules:
       - Main triads (T, S, D in 5/3): root doubled, third doubling strictly forbidden.
       - K64: bass (fifth of chord) strictly doubled.
       - VI (in deceptive cadence): third strictly doubled.
       - Seventh chords: complete (1-3-5-7) or incomplete (doubled root, 3, 7).
       - Inversions: bass note strictly matches required factor (5/3: root; 6: 3rd; 6/4: 5th; 6/5: 3rd; 4/3 & 2: 7th).
    """
chord_sym = chord.function if hasattr(chord, "function") else str(chord)
chord_bpc = getattr(chord, "bass_pitch_class", None)
⋮----
chord_bpc = chord_bpc.value
chord_is_7th = getattr(chord, "is_seventh", None)
chord_key = (chord_sym, chord_bpc, chord_is_7th)
⋮----
key_key = (key.tonic, key.mode) if hasattr(key, "tonic") and hasattr(key, "mode") else (str(key) if key is not None else None)
prev_chord_sym = (prev_chord.function if hasattr(prev_chord, "function") else str(prev_chord)) if prev_chord is not None else None
⋮----
cache_key = (
⋮----
ranges = EXTENDED_VOICE_RANGES if allow_extended_ranges else STANDARD_VOICE_RANGES
⋮----
# Get allowed pitch classes and chord factors
⋮----
allowed_pcs = {root_pc, third_pc, fifth_pc}
⋮----
sym_clean = chord_sym.strip().upper().replace("/", "")
is_seventh = (
⋮----
seventh_pc = tonic_pc % 12
⋮----
# diminished 7th in minor/harmonic major (deg 6 = +8), or natural major (+9)
seventh_pc = (tonic_pc + 8 if ("MINOR" in mode or sym_clean.islower()) else tonic_pc + 9) % 12
⋮----
seventh_pc = (tonic_pc + 7) % 12
⋮----
seventh_pc = (tonic_pc + 3 if ("MINOR" in mode or sym_clean.islower()) else tonic_pc + 4) % 12
⋮----
seventh_pc = (tonic_pc + 5) % 12
⋮----
# Check that soprano belongs to chord, or qualify as melodic non-chord tone (NCT)
is_nct = False
⋮----
nct_type = classify_nct(
⋮----
is_nct = True
⋮----
# Inversion bass pitch class requirement
# 5/3: root; 6: third; 6/4: fifth; 7: root; 6/5: third; 4/3: fifth/seventh; 2: seventh
required_bass_pc = None
⋮----
b_val = chord.bass_pitch_class
required_bass_pc = int(b_val.value if hasattr(b_val, "value") else b_val) % 12
⋮----
required_bass_pc = fifth_pc
⋮----
required_bass_pc = third_pc
⋮----
required_bass_pc = seventh_pc
⋮----
# Root position (5/3, 7): bass MUST be the root of the chord
required_bass_pc = root_pc
⋮----
candidates: list[Voicing] = []
⋮----
# Find valid Alto pitches:
alto_low = max(a_min, soprano_pitch - 12)
alto_high = min(a_max, soprano_pitch if allow_adjacent_unisons else (soprano_pitch - 1))
⋮----
# Find valid Tenor pitches:
tenor_low = max(t_min, a - 12)
tenor_high = min(t_max, a if allow_adjacent_unisons else (a - 1))
⋮----
# Find valid Bass pitches:
bass_low = max(b_min, t - 24)
bass_high = min(b_max, t if allow_adjacent_unisons else (t - 1))
⋮----
# Soprano is excluded from chord tones.
# Lower 3 voices (A, T, B) must provide triad completeness (root, third, fifth).
lower_pcs = {a % 12, t % 12, b % 12}
⋮----
v = Voicing(soprano=soprano_pitch, alto=a, tenor=t, bass=b)
⋮----
# Check doublings via doubling validator (cache static checks without context)
⋮----
static_key = (v, chord_key, key_key, bool(is_final_chord))
⋮----
doubling_violations = _STATIC_DOUBLING_CACHE[static_key]
⋮----
doubling_violations = check_doubling(
⋮----
# Contextual check: DO NOT CACHE
````

## File: backend/service.py
````python
"""
Service layer for Brigade Classical Harmony harmonization requests.
Encapsulates plan generation, DD filtering, Viterbi optimization, candidate selection,
scoring, MusicXML/ASCII formatting, and structured error reporting.
"""
⋮----
logger = logging.getLogger(__name__)
⋮----
# Request-level cache for idempotent repeated requests.
# Bounded LRU + TTL: the service runs inside a long-lived desktop process, so an
# unbounded cache of full MusicXML payloads is a memory leak (audit M2).
CACHE_MAX_ENTRIES = 128
CACHE_TTL_SEC = 300.0
⋮----
# Hard time budget for the fast-path plan evaluation loop. NOT client-configurable:
# HarmonizeRequest has no timeout field (pydantic drops unknown keys), and the old
# data.get("timeout_sec", 4.0) was dead code always yielding 4.0 (audit finding).
# Per-request tuning belongs to the separate performance wave.
HARMONIZE_TIMEOUT_SEC = 4.0
⋮----
# Entries are (stored_at_monotonic, payload); OrderedDict gives O(1) LRU order.
_SERVICE_REQUEST_CACHE: OrderedDict[tuple, tuple[float, dict[str, Any]]] = OrderedDict()
_SERVICE_CACHE_LOCK = threading.Lock()
⋮----
def _cache_lookup(key: tuple) -> dict[str, Any] | None
⋮----
"""Returns a deep copy of a live cache entry; None on miss or TTL expiry."""
⋮----
item = _SERVICE_REQUEST_CACHE.get(key)
⋮----
def _cache_store(key: tuple, payload: dict[str, Any]) -> None
⋮----
"""Stores a deep copy of the payload, evicting the LRU tail beyond capacity."""
⋮----
def clear_service_cache() -> None
⋮----
"""Flushes the service-level request cache."""
⋮----
def select_top_candidates(solutions: list[dict[str, Any]], k: int = 3) -> list[dict[str, Any]]
⋮----
"""
    Stably selects the top-k candidate solutions with the lowest total cost.
    Updates the 1-based rank on each selected candidate.
    """
sorted_solutions = sorted(solutions, key=lambda s: s.get("cost", 0.0))[:k]
⋮----
class HarmonizationService
⋮----
"""
    Authoritative Harmonization Application Service.
    Orchestrates macro syntax synthesis and micro voice-leading search.
    """
⋮----
"""Bounded-replanning fallback.

        The fast path walks pre-generated plans one by one; the core engine owns
        macro/micro replanning and can synthesize plans itself when the grammar
        produced none (chromatic NCT lines, minor-key S6 dead ends, ...).

        Note: the raw melody is forwarded unchanged (is_downbeat=None when the
        client omitted the flag) so the core can decide metric placement itself.
        """
⋮----
fallback = self.harmonizer.harmonize(
⋮----
candidates: list[dict[str, Any]] = []
⋮----
chords_list = [c.function for c in sol.chords]
voicings_list = [
ascii_text = format_ascii_score(
colored_xml = build_colored_musicxml(
cand_dict = {
⋮----
def harmonize(self, req: dict[str, Any] | Any) -> dict[str, Any]
⋮----
"""
        Executes complete harmonization workflow on request parameters.
        Returns unified JSON payload compliant with REST API schema.
        """
t_start = time.perf_counter()
⋮----
# Handle pydantic model or plain dict
⋮----
data = req.model_dump()
⋮----
data = req.dict()
⋮----
data = req
⋮----
data = dict(req)
⋮----
# Private marker (defect #8, log hygiene): a failing strict pass inside a
# relax_hard_gates request is expected and will be followed by a relaxed
# retry — its abort logs are demoted from WARNING to debug.
is_strict_retry_of_relaxed = bool(data.get("_strict_retry_of_relaxed"))
⋮----
# relax_hard_gates is a last resort: a strictly legal plan always wins.
# The fast path evaluates plans with the solver directly, so the strict
# retry has to happen here as well (mirrors Harmonizer.harmonize).
⋮----
strict_request = dict(data)
⋮----
strict_result = self.harmonize(strict_request)
⋮----
melody_raw = data.get("melody", [])
⋮----
key_data = data.get("key", {})
⋮----
tonic = key_data.get("tonic", "C")
mode = key_data.get("mode", "Major")
⋮----
tonic = getattr(key_data, "tonic", "C")
mode = getattr(key_data, "mode", "Major")
⋮----
parsed_key = Key(tonic=tonic, mode=mode)
time_sig_raw = data.get("time_signature", "4/4")
time_sig = TimeSignature.parse(time_sig_raw)
allow_extended_ranges = bool(data.get("allow_extended_ranges", False))
allow_secondary_dominants = bool(data.get("allow_secondary_dominants", True))
max_plans = int(data.get("max_plans", 50))
allow_adjacent_unisons = bool(data.get("allow_adjacent_unisons", False))
relax_hard_gates = bool(data.get("relax_hard_gates", False))
⋮----
# Normalize melody items through unified MetricGrid
norm_melody_input = []
⋮----
metric_grid = MetricGrid(time_signature=time_sig, notes=norm_melody_input)
melody_dicts = [
durations_list = [item["duration"] for item in metric_grid]
⋮----
# Request-level cache lookup for identical parameters
cache_key = (
cached_resp = _cache_lookup(cache_key)
⋮----
# 1. Synthesize candidate functional plans
grammar = HarmonicGrammar(key=parsed_key)
all_plans = grammar.generate_plans(melody=melody_dicts, key=parsed_key, max_plans=max_plans)
⋮----
# Filter secondary dominants if disallowed
⋮----
filtered_plans = []
⋮----
fns = [c.function for c in plan]
⋮----
plans_to_try = filtered_plans
⋮----
latency = round((time.perf_counter() - t_start) * 1000, 2)
⋮----
plans_to_try = all_plans
⋮----
# The grammar may legitimately produce no plans (e.g. a chromatic NCT
# line with an awkward cadence); the replanning engine can still
# synthesize a functional plan from scratch.
⋮----
replanned = self._replanning_candidates(
⋮----
replanned = select_top_candidates(replanned, k=3)
⋮----
resp = {
⋮----
# Demoted to debug inside a strict retry of a relaxed request (defect #8):
# the failure is expected there and a relaxed retry follows immediately.
log_abort = logger.debug if is_strict_retry_of_relaxed else logger.warning
⋮----
# 2. Solve candidate plans via Viterbi
solutions: list[dict[str, Any]] = []
collected_diagnostics: list[dict[str, Any]] = []
⋮----
best_cost_seen = float("inf")
stagnant_count = 0
early_stop_threshold = 15 if len(norm_melody_input) >= 16 else 0
timeout_sec = HARMONIZE_TIMEOUT_SEC
⋮----
res = self.solver.solve(
⋮----
best_cost_seen = res.total_cost
⋮----
chords_list = [c.function for c in plan]
⋮----
progression_str = " → ".join(chords_list)
cadence_type = "Полная каденция" if "K64" in chords_list else "Автентический оборот"
⋮----
# 2b. Bounded replanning fallback: the fast path above walks plans one by
# one; the core engine owns macro/micro replanning for melodies whose
# plans are all micro-infeasible (e.g. minor-key scales with S6 dead ends).
⋮----
solutions = select_top_candidates(solutions, k=3)
⋮----
# Demoted to debug inside a strict retry of a relaxed request (defect #8).
⋮----
# Defect #8 (additive): aggregate per-step blocking hard-rule ids from the
# solver diagnostics into a dominant-blocker histogram (count descending,
# rule_id as tie-break). blocking_rules entries only ever come from
# hard-gate prunes in the solver, so a non-empty histogram means hard
# blockers dominate the failure.
blocker_histogram: dict[str, int] = {}
⋮----
blocking_rules = diag.get("blocking_rules") if isinstance(diag, dict) else None
⋮----
dominant_blockers = dict(
error_payload: dict[str, Any] = {
⋮----
err_resp = {
⋮----
final_response = {
````

## File: frontend/src/App.tsx
````typescript
import { useState, useRef, useEffect, lazy, Suspense } from "react";
import { AlertCircle } from "lucide-react";
import { Header } from "./components/layout/Header";
import { MelodyInput } from "./components/MelodyInput";
import { ControlPanel } from "./components/ControlPanel";
import { AudioControls } from "./components/AudioControls";
import { GraderPanel } from "./components/GraderPanel";
import type { GraderReportData, GraderMeta } from "./components/GraderPanel";
import { ExportBar } from "./components/ExportBar";
import { useHarmonizer } from "./hooks/useHarmonizer";
import type { TabScoreState } from "./types/harmony";
import type { MelodyNote } from "./utils/durationUtils";
import type { SATBVoicing } from "./audio/synth";
⋮----
// Clearing the melody must also clear the stale score/candidates in the right panel.
const handleMelodyChange = (next: MelodyNote[]) =>
⋮----
// Capture the ref value in the effect body (react-hooks/exhaustive-deps):
// handleHarmonize sets abortControllerRef.current synchronously before its
// first await, so this snapshot is the in-flight request to abort on cleanup.
⋮----
const handleGradeComplete = (
    report: GraderReportData,
    musicxml: string,
    voicings: SATBVoicing[],
    meta?: GraderMeta
  ) =>
⋮----
const handleHighlightMeasure = (m: number) =>
⋮----
setHarmonizerScore((prev) => (
````

## File: src/harmony/core/types.py
````python
"""
Core domain types for Brigade Harmony Engine.
"""
⋮----
class Voicing(NamedTuple)
⋮----
"""
    Four-part vocal vertical slice (SATB).
    Immutable and hashable for DP state space.
    """
soprano: int
alto: int
tenor: int
bass: int
⋮----
@property
    def s(self) -> int
⋮----
@property
    def a(self) -> int
⋮----
@property
    def t(self) -> int
⋮----
@property
    def b(self) -> int
⋮----
def pitch_classes(self) -> tuple[int, int, int, int]
⋮----
PITCH_CLASS_NAMES: dict[str, int] = {
⋮----
SCALE_INTERVALS: dict[str, tuple[int, ...]] = {
⋮----
"MINOR": (0, 2, 3, 5, 7, 8, 11),           # default harmonic minor in Brigade
⋮----
@dataclass(frozen=True)
class Key
⋮----
"""
    Key definition: tonic name or pitch class and harmonic mode.
    """
tonic: str = "C"
mode: str = "Major"
⋮----
@classmethod
    def parse(cls, val: Any) -> "Key"
⋮----
"""
        Parses Key from string, dict, or Key instance.
        Supports 'C Major', 'A minor', 'c-moll', 'G-dur', 'F# minor', 'Bb Major', etc.
        """
⋮----
t = val.tonic
t_str = t.sharp_name if hasattr(t, "sharp_name") else str(t)
m = val.mode
m_str = m.value if hasattr(m, "value") else str(m)
⋮----
cleaned = val.strip()
german_match = re.match(r"^([A-Ga-g][#bB♭♯]?)[-_](dur|moll)$", cleaned, re.IGNORECASE)
⋮----
is_min = mode_str.lower() == "moll"
⋮----
parts = re.split(r"[\s:_]+", cleaned)
⋮----
note_str = parts[0]
mode_str = "_".join(parts[1:]).lower()
is_min = "minor" in mode_str or "moll" in mode_str
⋮----
raw = parts[0]
is_min = raw[0].islower() or (len(raw) > 1 and raw.endswith("m") and not raw.endswith("b"))
note_str = raw.rstrip("m").rstrip("M")
⋮----
@property
    def tonic_pc(self) -> int
⋮----
t = self.tonic.strip().upper()
⋮----
@property
    def normalized_mode(self) -> str
⋮----
m = self.mode.strip().upper().replace(" ", "").replace("_", "").replace("-", "")
⋮----
@property
    def scale_pcs(self) -> tuple[int, ...]
⋮----
intervals = SCALE_INTERVALS.get(self.normalized_mode, SCALE_INTERVALS["MAJOR"])
t0 = self.tonic_pc
⋮----
@property
    def name(self) -> str
⋮----
def __str__(self) -> str
⋮----
def degree_to_pc(self, degree_1_indexed: int) -> int
⋮----
idx = (degree_1_indexed - 1) % 7
⋮----
@dataclass(frozen=True)
class Chord
⋮----
"""
    Harmonic functional representation.
    """
function: str
inversion: int = 0
is_seventh: bool = False
is_downbeat: bool = False
⋮----
@property
    def symbol(self) -> str
⋮----
@dataclass(frozen=True)
class RuleViolation
⋮----
"""
    Record of a rule violation with metadata and severity.
    """
rule_id: str
severity: str = "hard_gate"  # "hard_gate" | "soft_penalty"
penalty: float = 100000.0
description: str = ""
voices: tuple[int, ...] | None = None
⋮----
@property
    def is_hard(self) -> bool
⋮----
@dataclass
class ValidationResult
⋮----
"""
    Result of validating a vertical state or transition.
    """
is_valid: bool
violations: list[RuleViolation] = field(default_factory=list)
cost: float = 0.0
⋮----
@property
    def has_hard_violations(self) -> bool
⋮----
@property
    def hard_violations(self) -> list[RuleViolation]
⋮----
@property
    def soft_violations(self) -> list[RuleViolation]
⋮----
def to_satb(voicing: Any) -> tuple[int, int, int, int]
⋮----
"""
    Converts any compatible voicing structure to a 4-tuple (S, A, T, B).
    """
⋮----
# Support dict format e.g. {"soprano": 60, ...} or {"S": 60, ...}
s = voicing.get("soprano", voicing.get("S", voicing.get("s")))
a = voicing.get("alto", voicing.get("A", voicing.get("a")))
t = voicing.get("tenor", voicing.get("T", voicing.get("t")))
b = voicing.get("bass", voicing.get("B", voicing.get("b")))
⋮----
def parse_key(key: Any) -> tuple[int, str]
⋮----
"""
    Extracts (tonic_pc, normalized_mode) from Key object, dict, or string.
    Supports both core.types.Key and core.key.Key seamlessly.
    """
⋮----
t = key.tonic
if hasattr(t, "value"):  # PitchClass enum/class
t_pc = int(t.value) % 12
⋮----
t_pc = t % 12
⋮----
t_str = t.strip().upper()
t_pc = PITCH_CLASS_NAMES.get(t_str, 0)
⋮----
t_pc = 0
⋮----
m = key.mode
⋮----
m_clean = m_str.strip().upper().replace(" ", "").replace("_", "").replace("-", "")
⋮----
norm_mode = "MINORHARMONIC"
⋮----
norm_mode = "MINORNATURAL"
⋮----
norm_mode = "MAJOR"
⋮----
k = Key.parse(key)
⋮----
# E.g. "C", "Am", "c-moll", "G-dur", "C Major", "A Minor"
⋮----
def parse_chord_symbol(chord: Any) -> str
⋮----
"""
    Normalizes a chord symbol to standard uppercase string representation.
    """
⋮----
sym = chord
⋮----
# Preserve the inversion of the core Chord model: Chord("T", inversion=1)
# is T6, not a root-position T. Seventh chords use 65/43/2.
sym = chord.function
inv = int(getattr(chord, "inversion", 0) or 0)
⋮----
seventh_suffix = {1: "65", 2: "43", 3: "2"}.get(inv)
⋮----
sym = f"{sym}{seventh_suffix}"
⋮----
triad_suffix = {1: "6", 2: "64"}.get(inv)
⋮----
sym = f"{sym}{triad_suffix}"
⋮----
fn = chord.function
fn_val = fn.value if hasattr(fn, "value") else str(fn)
⋮----
inv = chord.inversion
inv_val = inv.value if hasattr(inv, "value") else str(inv)
⋮----
sym = "K64"
⋮----
sym = fn_val
⋮----
sym = f"{fn_val}{inv_val}"
⋮----
sym = str(chord.value)
⋮----
sym = str(chord.symbol)
⋮----
sym = str(chord)
⋮----
# Normalize accents / slashes / spaces
cleaned = sym.strip().replace("^", "").replace("/", "")
⋮----
# Normalize hyphenated chord symbols: VII-6 -> VII6, II-6 -> II6, T-6 -> T6,
# D-7 -> D7, D-65 -> D65, D-43 -> D43, D-2 -> D2, T-53 -> T53, etc.
cleaned = re.sub(
⋮----
# Check common synonyms (T64 is deliberately excluded from K64 per Brigade rules)
upper_c = cleaned.upper()
⋮----
@dataclass(frozen=True)
class TimeSignature
⋮----
"""
    Musical time signature (meter), e.g. 4/4, 3/4, 6/8, 2/4.
    """
beats: int = 4
beat_type: int = 4
⋮----
@property
    def measure_duration_quarters(self) -> float
⋮----
"""Total duration of one complete measure in quarter notes."""
# Degenerate meters (0 beats, 0 denominator) used to yield 0 and spin
# the measure-advance loop forever; clamp to one quarter note instead.
⋮----
@classmethod
    def parse(cls, val: Any) -> "TimeSignature"
⋮----
s = val.strip().lower()
⋮----
parts = s.split("/")
⋮----
beats_val = int(parts[0])
beat_type_val = int(parts[1])
⋮----
# Reject nonsense meters (0/0, 7/0, negative) before they reach
# any division: they used to crash with ZeroDivisionError.
⋮----
def is_downbeat(self, beat_offset_quarters: float) -> bool
⋮----
"""
        Determines whether a quarter-note offset from measure start is a metric downbeat/accent.
        """
offset = round(beat_offset_quarters, 4)
⋮----
# Secondary downbeat in 4/4 or 2/2 (the 3rd quarter note)
⋮----
# In 6/8, the 4th eighth note (offset 1.5 quarters) is the secondary accent
⋮----
DURATION_TO_QUARTERS: dict[str, float] = {
⋮----
#: Duration spellings accepted by the public API (numeric strings are validated separately).
VALID_DURATIONS: frozenset[str] = frozenset(DURATION_TO_QUARTERS)
⋮----
def parse_duration_quarters(dur: Any) -> float
⋮----
"""Converts a duration string, float, or int to quarter-note units."""
⋮----
key = dur.strip().lower()
⋮----
def quarters_to_xml_type_and_dots(quarters: float) -> tuple[str, int]
⋮----
"""
    Returns (xml_type_name, dot_count) for a given duration in quarter units.
    """
q = round(quarters, 4)
⋮----
"""
    Calculates exact metric coordinates for a sequence of melody notes or chord slices.
    Delegates to MetricGrid while strictly preserving backward compatibility.
    Explicit is_downbeat (True/False) is always respected; None is taken from MetricGrid.
    """
⋮----
grid = MetricGrid(time_signature=default_time_signature, notes=notes)
````

## File: src/harmony/rules/resolutions.py
````python
"""
Dissonance and tendency tone resolution rules according to Brigade Harmony textbook.
Enforces 7th resolution downward by step, mandatory D43 -> T6 progression,
and leading tone resolution upward to the tonic in outer voices.
"""
⋮----
VOICE_NAMES = ("Soprano", "Alto", "Tenor", "Bass")
DOMINANT_SEVENTH_CHORDS = {"D7", "D65", "D43", "D2"}
DOMINANT_GROUP = {"D", "D7", "D6", "D65", "D43", "D2"}
TONIC_GROUP = {"T", "T6", "T64", "t", "t6", "VI", "vi"}
⋮----
"""
    In dominant seventh chords (D7, D65, D43, D2), the seventh (scale degree IV)
    must resolve down by step (1 or 2 semitones down).
    If curr_chord is in DOMINANT_GROUP (intra-dominant repositioning or inversion change, e.g. D7 -> D65),
    the seventh may be sustained on the same pitch (delta == 0) or transferred to another voice.
    """
⋮----
prev_sym = parse_chord_symbol(prev_chord)
⋮----
curr_sym = parse_chord_symbol(curr_chord) if curr_chord is not None else ""
is_curr_dominant = curr_sym in DOMINANT_GROUP
⋮----
seventh_pc = (tonic_pc + 5) % 12  # Scale degree IV is the 7th of the dominant
⋮----
prev_satb = to_satb(prev_voicing)
curr_satb = to_satb(curr_voicing)
⋮----
seventh_present_in_curr = any(curr_satb[v] % 12 == seventh_pc for v in range(4))
⋮----
violations: list[RuleViolation] = []
⋮----
delta = curr_satb[idx] - prev_satb[idx]
# If transitioning within DOMINANT_GROUP: allow sustained 7th (delta 0) or transfer
⋮----
# Standard authentic resolution: must step down (-1 or -2 semitones)
⋮----
"""
    D43 has the fifth of dominant in the bass (scale degree II).
    It resolves canonically to T/T53 (bass steps down II -> I by 1 or 2 semitones)
    or to T6 (bass steps up II -> III by 1 or 2 semitones).
    The seventh (scale degree IV) in upper voices must resolve down by step.
    """
⋮----
prev_sym = parse_chord_symbol(prev_chord).strip().upper().replace("/", "")
⋮----
curr_sym = parse_chord_symbol(curr_chord).strip().upper().replace("/", "")
⋮----
# Target chord must be T, T53, T6 (or minor t, t53, t6)
⋮----
# Bass motion check:
# If resolving to T / T53: bass must step down 1 or 2 semitones (II -> I)
# If resolving to T6: bass must step up 1 or 2 semitones (II -> III)
⋮----
delta_b = curr_satb[3] - prev_satb[3]
⋮----
# Seventh resolution in upper voices (scale degree IV)
⋮----
seventh_pc = (tonic_pc + 5) % 12  # Scale degree IV
for idx in range(3):  # S, A, T
⋮----
"""
    D2 has the seventh in the bass (scale degree IV).
    It MUST resolve strictly to T6 (or t6), with the bass stepping down
    by 1 or 2 semitones into the third of the tonic.
    """
⋮----
# D2 (V4/2) resolves to T6; DD2 (V4/2 of V) resolves to the dominant
# (D6/D/D7/D65) or K64 — it must NOT be forced into the tonic.
is_dd2 = prev_sym == "DD2"
allowed_targets = ("D6", "D", "D7", "D65", "K64") if is_dd2 else ("T6", "T-6", "t6", "t-6")
⋮----
"""
    When progressing from Dominant to Tonic in an authentic cadence,
    the leading tone (scale degree VII) in outer voices (Soprano and Bass)
    must resolve upward to the tonic (scale degree I) by half-step (+1 semitone).
    """
⋮----
curr_sym = parse_chord_symbol(curr_chord)
⋮----
leading_tone_pc = (tonic_pc + 11) % 12  # Scale degree VII
⋮----
# Check outer voices: Soprano (0) and Bass (3)
⋮----
# Must step up by half-step (+1)
⋮----
"""
    In leading-tone seventh chords (VII7, VII65, VII43, VII2) resolving to T/t:
    - The seventh (scale degree VI) must resolve down by step into degree V.
    - The fifth (scale degree IV) must resolve down by step into degree III.
    - The leading tone (scale degree VII) must resolve up by half-step into degree I.
    - The resulting tonic triad T strictly requires a doubled third!
    """
⋮----
vii7_family = {"VII7", "vii7", "VII65", "vii65", "VII43", "vii43", "VII2", "vii2"}
⋮----
leading_pc = (tonic_pc + 11) % 12
fifth_pc = (tonic_pc + 5) % 12    # Scale degree IV is 5th of VII7
seventh_pc = (tonic_pc + 9) % 12  # Scale degree VI (or 8 in minor)
seventh_pc_alt = (tonic_pc + 8) % 12
⋮----
p = prev_satb[idx] % 12
⋮----
# Seventh must resolve down by step (-1 or -2)
⋮----
# Fifth of VII7 must resolve down by step (-1 or -2) into 3rd of T
⋮----
# Leading tone of VII7 must resolve up by half-step (+1) into tonic
⋮----
# Resulting tonic triad must strictly double the third to avoid parallel fifths
⋮----
curr_counts = Counter([p % 12 for p in curr_satb])
⋮----
is_minor = "MINOR" in mode or curr_sym.islower()
tonic_third_pc = (tonic_pc + 3 if is_minor else tonic_pc + 4) % 12
⋮----
"""
    Validates resolution of Secondary Dominant chords (DD, DD7, D7/V, D7/II, D7/VI, D7/IV):
    - Secondary leading tone (e.g. F# in C-dur for DD) must resolve up by semitone (+1)
      into target root (e.g. G in D, D7, or K64), OR step down chromatically (-1).
    - Secondary seventh (e.g. C in DD7) must resolve down by step (-1 or -2)
      into the third of the target chord (e.g. B in G).
    """
⋮----
# Determine secondary leading tone and secondary seventh
sec_leading_pc = None
sec_seventh_pc = None
⋮----
sec_leading_pc = (tonic_pc + 6) % 12
⋮----
sec_seventh_pc = tonic_pc % 12
⋮----
sec_leading_pc = (tonic_pc + 1) % 12
⋮----
sec_seventh_pc = (tonic_pc + 7) % 12
⋮----
sec_leading_pc = (tonic_pc + 8) % 12
⋮----
sec_seventh_pc = (tonic_pc + 2) % 12
⋮----
sec_leading_pc = (tonic_pc + 4) % 12
⋮----
sec_seventh_pc = (tonic_pc + 10) % 12
⋮----
# Validate target chord for secondary dominant
⋮----
allowed_targets = {"D", "D7", "D6", "D65", "D43", "D2", "K64", "VII", "VII7", "VII65", "VII43", "VII2"}
⋮----
# Check secondary leading tone resolution
⋮----
# Must step up by semitone (+1) or step down chromatically (-1)
⋮----
# Check secondary seventh resolution
⋮----
# Must resolve down by step (-1 or -2), or be held as common tone in K64 (delta == 0)
is_k64_held = (curr_sym == "K64" and delta == 0)
⋮----
II7_CHORDS = {"II7", "II65", "II43", "II2"}
II7_DOMINANT_TARGETS = {"D", "D53", "D6", "D7", "D65", "D43", "D2", "K64"}
⋮----
"""
    Validates resolution of supertonic seventh chords (II7, II65, II43, II2):
    - Target chord must belong to dominant group (D, D6, D7, D65, D43, D2, K64),
      otherwise hard RESOLUTION_II7_TO_DOMINANT.
    - Seventh of II7 (scale degree I / tonic_pc) must resolve down by step
      (-1 or -2 semitones), or be held as a common tone in K64 (delta == 0),
      otherwise hard RESOLUTION_II7_SEVENTH_DOWN.
    """
⋮----
prev_sym = parse_chord_symbol(prev_chord).strip().upper().replace("/", "").replace("-", "")
⋮----
curr_sym = parse_chord_symbol(curr_chord).strip().upper().replace("/", "").replace("-", "")
⋮----
# 1. Target function check: must belong to dominant group
⋮----
# 2. Seventh resolution check: seventh (tonic PC) must step down by 1-2 semitones (or held in K64)
⋮----
seventh_pc = tonic_pc % 12
⋮----
"""
    Runs all dissonance and tendency tone resolution checks.
    """
violations = []
````

## File: backend/api.py
````python
"""
FastAPI REST router for Brigade Harmony Engine.
Exposes harmonization, student grading, file imports, exports, and key detection.
"""
⋮----
logger = logging.getLogger(__name__)
⋮----
router = APIRouter(prefix="/api")
harmonization_service = HarmonizationService()
⋮----
VALID_TONICS = set(PITCH_CLASS_NAMES.keys())
VALID_MODES = {
⋮----
def _check_time_signature(value: str) -> str
⋮----
"""Validates a meter spelling; malformed meters are rejected with 422."""
text = str(value).strip()
parts = text.split("/")
⋮----
beats = int(parts[0])
beat_type = int(parts[1])
⋮----
TimeSignatureStr = Annotated[str, AfterValidator(_check_time_signature)]
⋮----
def _check_duration(value: str) -> str
⋮----
"""Validates a note duration spelling; unknown strings are rejected with 422."""
text = str(value).strip().lower()
⋮----
# Historical aliases accepted by grade/export endpoints (case variants, figured-bass
# spellings like "D6/5", "K6/4", lowercase minor functions, secondary-dominant shorthands).
# Kept for backwards compatibility; the grammar itself never generates them.
_LEGACY_CHORD_FUNCTION_ALIASES = {
⋮----
# Tonic
⋮----
# Subdominant
⋮----
# Dominant
⋮----
# Cadential 6/4
⋮----
# II degree
⋮----
# VI degree
⋮----
# III degree
⋮----
# VII degree
⋮----
# Double Dominant
⋮----
# Secondary dominants
⋮----
# Neapolitan chord (bII)
⋮----
# Chromatic submediant (bVI)
⋮----
# Single source of truth (audit M-whitelist): everything the grammar can generate,
# unioned with the historical aliases so no previously accepted symbol starts 422-ing.
VALID_CHORD_FUNCTIONS = frozenset(ALL_FUNCTIONS) | _LEGACY_CHORD_FUNCTION_ALIASES
⋮----
def select_top_candidates(solutions: list[dict[str, Any]], k: int = 3) -> list[dict[str, Any]]
⋮----
"""
    Stably selects the top-k candidate solutions with the lowest total cost.
    Updates the 1-based rank on each selected candidate.
    """
sorted_solutions = sorted(solutions, key=lambda s: s.get("cost", 0.0))[:k]
⋮----
class KeyRequest(BaseModel)
⋮----
tonic: str = "C"
mode: str = "Major"
⋮----
@field_validator("tonic")
@classmethod
    def validate_tonic(cls, v: str) -> str
⋮----
@field_validator("mode")
@classmethod
    def validate_mode(cls, v: str) -> str
⋮----
class MelodyNoteItem(BaseModel)
⋮----
pitch: int = Field(..., ge=0, le=127)
is_downbeat: bool | None = None
duration: str = "half"
name: str | None = None
⋮----
@field_validator("duration")
@classmethod
    def validate_duration(cls, v: str) -> str
⋮----
class HarmonizeRequest(BaseModel)
⋮----
melody: list[MelodyNoteItem] = Field(..., min_length=1, max_length=128)
key: KeyRequest = Field(default_factory=KeyRequest)
time_signature: TimeSignatureStr = "4/4"
allow_extended_ranges: bool = False
allow_secondary_dominants: bool = True
max_plans: int = Field(default=50, ge=1, le=100)
allow_adjacent_unisons: bool = False
relax_hard_gates: bool = False
⋮----
class VoicingItem(BaseModel)
⋮----
soprano: int
alto: int
tenor: int
bass: int
measure: int | None = None
is_downbeat: bool = False
duration: str | None = None
⋮----
@field_validator("duration")
@classmethod
    def validate_duration(cls, v: str | None) -> str | None
⋮----
class GradeRequest(BaseModel)
⋮----
voicings: list[VoicingItem] = Field(..., min_length=1)
chords: list[str] = Field(..., min_length=1)
⋮----
durations: list[str] | None = None
⋮----
@field_validator("durations")
@classmethod
    def validate_durations(cls, v: list[str] | None) -> list[str] | None
⋮----
@field_validator("chords")
@classmethod
    def validate_chords(cls, chords: list[str]) -> list[str]
⋮----
@model_validator(mode="after")
    def validate_lengths(self) -> Self
⋮----
class ParseTextRequest(BaseModel)
⋮----
text: str
⋮----
class ExportMidiRequest(BaseModel)
⋮----
voicings: list[VoicingItem]
bpm: int = 80
⋮----
class ExportMusicXmlRequest(BaseModel)
⋮----
chords: list[str] | None = None
⋮----
title: str = "Harmonization Exercise"
⋮----
@router.get("/keys")
def get_canonical_keys() -> list[dict[str, Any]]
⋮----
"""Returns 24 canonical keys (12 major, 12 harmonic minor)."""
⋮----
@router.post("/detect-key")
def api_detect_key(melody: list[MelodyNoteItem]) -> dict[str, Any]
⋮----
"""Auto-detects the most probable key from a soprano melody."""
⋮----
@router.post("/parse-text")
def api_parse_text(req: ParseTextRequest) -> list[dict[str, Any]]
⋮----
"""Parses text notation (note names, MIDI numbers, or scale degrees)."""
⋮----
@router.post("/harmonize")
async def api_harmonize(req: HarmonizeRequest) -> dict[str, Any]
⋮----
"""
    Harmonizes a given soprano melody.
    Returns candidate pool (top-3 solutions) with Viterbi costs, colored MusicXML,
    and Sposobin functional analysis.
    """
⋮----
@router.post("/grade")
def api_grade(req: GradeRequest) -> dict[str, Any]
⋮----
"""
    Grades student SATB solution using RuleEngine.
    Returns comprehensive diagnostic report and highlighted score.
    """
voicings = [
parsed_key = Key(tonic=req.key.tonic, mode=req.key.mode)
⋮----
durs = req.durations or ([v.duration or "half" for v in req.voicings] if any(v.duration for v in req.voicings) else None)
report = grade_satb_solution(
⋮----
colored_xml = build_colored_musicxml(
ascii_score = format_ascii_score(
⋮----
@router.post("/import-file")
async def api_import_file(request: Request) -> dict[str, Any]
⋮----
"""
    Imports MusicXML (.musicxml, .xml) or MIDI (.mid, .midi) file.

    Two content paths are supported (the raw request is parsed manually, so no
    body parameters are declared in the OpenAPI schema):
    - multipart/form-data with a `file` field;
    - application/json body: {"filename": ..., "content_base64": ...} or
      {"filename": ..., "xml_content": ...}.

    Malformed payloads (invalid JSON, invalid base64, unparsable MusicXML/MIDI)
    are rejected with 400 and a structured detail message — never 500.
    """
⋮----
filename = ""
content = b""
⋮----
content_type = request.headers.get("content-type", "")
⋮----
body = await request.json()
⋮----
filename = str(body.get("filename") or "")
⋮----
content = body["xml_content"].encode("utf-8")
⋮----
content = base64.b64decode(body["content_base64"])
⋮----
# Multipart form upload. Non-form content types (e.g. text/plain) can
# make Starlette raise here — reject with 400 instead of leaking a 500.
⋮----
form = await request.form()
⋮----
uploaded_file = form.get("file")
⋮----
filename = getattr(uploaded_file, "filename", "upload") or "upload"
content = await uploaded_file.read()
⋮----
xml_text = content.decode("utf-8", errors="ignore")
⋮----
res = parse_musicxml_content(xml_text)
⋮----
ts_info = res.get("time_signature") or {}
ts_str = f"{ts_info.get('beats', 4)}/{ts_info.get('beat_type', 4)}"
durations = [note.get("duration", "half") for note in res["soprano_melody"]]
⋮----
res = parse_midi_file(content)
⋮----
# Auto detect key from soprano
detected_key = detect_key_from_melody(res["soprano_melody"]) if res["soprano_melody"] else CANONICAL_KEYS[0]
⋮----
@router.post("/export/midi")
def api_export_midi(req: ExportMidiRequest)
⋮----
"""Exports SATB voicings to binary MIDI file download."""
⋮----
data = generate_midi_bytes(
⋮----
@router.post("/export/musicxml")
def api_export_musicxml(req: ExportMusicXmlRequest)
⋮----
"""Exports SATB voicings to MusicXML file download."""
⋮----
xml_str = build_colored_musicxml(
````

## File: src/harmony/rules/doubling.py
````python
"""
Chord tone doubling rules according to Brigade Harmony textbook.
Enforces root doubling in main triads (T, S, D), bass doubling in K64,
and third doubling in deceptive cadence (VI after D/D7).
"""
⋮----
# Triad symbols (root position, first inversion '6', second inversion '64') and
# seventh-chord symbols (7, 65, 43, 2). Completeness rules must cover ALL of
# them, not just root-position triads: a dominant without its leading tone is
# not a dominant, and a seventh chord without its third is not a chord at all.
_TRIAD_RE = re.compile(
_SEVENTH_RE = re.compile(
⋮----
def _seventh_pcs(symbol: str, tonic_pc: int, mode: str) -> set[int]
⋮----
"""Pitch classes allowed for the chord seventh of a seventh-chord symbol."""
sym = symbol.strip().upper()
is_minor = "MINOR" in mode.upper() or symbol.strip().islower()
⋮----
# The leading-tone seventh is a half-diminished VII7 in minor and a
# diminished VII7 (harmonic mixture) in major; the engine accepts both
# spellings of the seventh (Ab and A in C).
⋮----
def get_triad_tones(symbol: str, tonic_pc: int, mode: str) -> tuple[int, int, int]
⋮----
"""
    Returns (root_pc, third_pc, fifth_pc) for the given chord function.
    Supports all standard inversions and extensions (D7, D43, K64, S6, T6, II6, VI, etc.).
    """
is_minor = "MINOR" in mode.upper() or symbol.islower()
sym_upper = symbol.strip().upper()
⋮----
# Double Dominant (D of V): Root = II degree, Third = raised IV (secondary leading tone), Fifth = VI degree
root = (tonic_pc + 2) % 12
third = (tonic_pc + 6) % 12
fifth = (tonic_pc + 9) % 12
⋮----
# Dominant to II: Root = VI degree, Third = raised I degree, Fifth = III degree
root = (tonic_pc + 9) % 12
third = (tonic_pc + 1) % 12
fifth = (tonic_pc + 4) % 12
⋮----
# Dominant to VI: Root = III degree in major, Third = raised V degree, Fifth = VII degree
root = (tonic_pc + 4) % 12
third = (tonic_pc + 8) % 12
fifth = (tonic_pc + 11) % 12
⋮----
# Dominant to IV: Root = I degree, Third = III degree, Fifth = V degree
root = tonic_pc
third = (tonic_pc + 4) % 12
fifth = (tonic_pc + 7) % 12
⋮----
# Cadential 6/4 is tonic chord tones over fifth degree (dominant bass)
⋮----
third = (tonic_pc + 3 if is_minor else tonic_pc + 4) % 12
⋮----
root = (tonic_pc + 5) % 12
third = (tonic_pc + 8 if is_minor else tonic_pc + 9) % 12
fifth = tonic_pc
⋮----
root = (tonic_pc + 7) % 12
# Dominant in both major and harmonic minor has major third (leading tone)
third = (tonic_pc + 11) % 12
fifth = (tonic_pc + 2) % 12
⋮----
root = (tonic_pc + 3 if is_minor else tonic_pc + 4) % 12
third = (tonic_pc + 7) % 12
fifth = (tonic_pc + 10 if is_minor else tonic_pc + 11) % 12
⋮----
third = (tonic_pc + 5) % 12
fifth = (tonic_pc + 8 if is_minor else tonic_pc + 9) % 12
⋮----
root = (tonic_pc + 11) % 12
third = (tonic_pc + 2) % 12
fifth = (tonic_pc + 5) % 12
⋮----
# Neapolitan triad (bII): Root = tonic+1, Third = tonic+5, Fifth = tonic+8
root = (tonic_pc + 1) % 12
⋮----
fifth = (tonic_pc + 8) % 12
⋮----
# Chromatic submediant (bVI): Root = tonic+8, Third = tonic+0, Fifth = tonic+3
root = (tonic_pc + 8) % 12
third = tonic_pc % 12
fifth = (tonic_pc + 3) % 12
⋮----
root = (tonic_pc + 8 if is_minor else tonic_pc + 9) % 12
third = tonic_pc  # Third of VI is always the tonic!
fifth = (tonic_pc + 3 if is_minor else tonic_pc + 4) % 12
⋮----
# Fallback to tonic
⋮----
TRIAD_SYMBOLS = {
⋮----
"""
    Chord-tone completeness for triads (all inversions, DD, K64) and seventh chords:
    - Third is strictly required everywhere (CHORD_THIRD_MISSING).
    - Triads: fifth is required, except a first inversion of a non-diminished triad
      (canon: the 5th may be omitted, but not in 2nd inversion or diminished chords),
      the canonical incomplete final tonic (tripled root + third),
      and deceptive cadence VI with doubled third after dominant (root position VI53).
    - Seventh chords: fifth may be omitted (incomplete V7 doubles the root), but
      root, third and seventh are mandatory.
    """
sym = parse_chord_symbol(chord).strip().replace("/", "")
triad_match = _TRIAD_RE.match(sym)
seventh_match = _SEVENTH_RE.match(sym)
⋮----
satb = to_satb(voicing)
pcs = [p % 12 for p in satb]
counts = Counter(pcs)
⋮----
violations: list[RuleViolation] = []
⋮----
def _add(rule_id: str, description: str) -> None
⋮----
# 1. Third is mandatory in every chord, every inversion, including the final one.
⋮----
# 2. Seventh chords: root, third and seventh are mandatory; fifth optional.
seventh_pcs = _seventh_pcs(sym, tonic_pc, mode)
⋮----
# 3. Triads: fifth rules.
⋮----
group = triad_match.group(1)
inversion = triad_match.group(2) or "53"
is_diminished = ((third - root) % 12 == 3) and ((fifth - root) % 12 == 6)
allowed = False
⋮----
# canon: 5th may be omitted in a non-diminished first inversion,
# but not while the bass (third) is doubled: that hollows the chord.
allowed = True
⋮----
allowed = True  # canonical incomplete final tonic (tripled root)
⋮----
prev_s = parse_chord_symbol(prev_chord).strip()
deceptive_dom_group = (
⋮----
"""
    In root-position main triads (T, S, D, t, s), the root (prima) must be doubled.
    Doubling the third is strictly forbidden, EXCEPT when resolving directly from VII7,
    where doubling the third in T is mandatory by Brigade rules to avoid parallel fifths.
    """
sym = parse_chord_symbol(chord)
⋮----
sym = sym.replace("53", "")
⋮----
# Check if coming from VII7 resolution: in VII7 -> T, doubling the third of T is mandatory!
prev_sym = parse_chord_symbol(prev_chord) if prev_chord is not None else ""
VII7_FAMILY = {"VII7", "vii7", "VII65", "vii65", "VII43", "vii43", "VII2", "vii2"}
⋮----
# Hard prohibition: never double the third in main root-position triads
⋮----
v_idx = tuple(i for i, p in enumerate(satb) if p % 12 == third)
⋮----
# If soprano is a non-chord tone (NCT), the lower 3 voices form a complete triad
# (1 root, 1 third, 1 fifth), so doubling of the root in 4 voices is not possible.
soprano_pc = satb[0] % 12
⋮----
# Standard requirement: root must be doubled (multiplicity >= 2)
⋮----
v_idx = tuple(i for i, p in enumerate(satb) if p % 12 == root)
⋮----
"""
    In cadential six-four chord (K64):
    - The bass must strictly be scale degree V (fifth of the key / dominant pitch class).
    - The bass note (scale degree V) must strictly be doubled.
    - Other tones (root I, third III) may not be doubled.
    """
⋮----
bass_pc = satb[3] % 12
⋮----
degree_v_pc = (tonic_pc + 7) % 12
⋮----
# 1. Bass MUST be scale degree V (PC 7 in C-dur)
⋮----
# 2. Bass (scale degree V) MUST be doubled
⋮----
v_idx = tuple(i for i, p in enumerate(satb) if p % 12 == degree_v_pc)
⋮----
# 3. Third of tonic (scale degree III) must NOT be doubled
is_minor = "MINOR" in mode
third_pc = (tonic_pc + 3 if is_minor else tonic_pc + 4) % 12
⋮----
"""
    In deceptive cadence (D -> VI or D7 -> VI), the third of the VI triad
    (which is scale degree I / tonic pitch class) must strictly be doubled.
    """
⋮----
prev_sym = parse_chord_symbol(prev_chord)
curr_sym = parse_chord_symbol(curr_chord)
⋮----
is_dominant = prev_sym in ("D", "D7", "D65", "D43", "D2", "D6")
is_vi = curr_sym in ("VI", "vi")
⋮----
satb = to_satb(curr_voicing)
⋮----
v_idx = tuple(i for i, p in enumerate(satb) if p % 12 == tonic_pc)
⋮----
"""
    In Secondary Dominant triads (e.g. DD 5/3):
    The root (prima) must be doubled.
    Doubling the third (secondary leading tone) is strictly forbidden!
    """
sym = parse_chord_symbol(chord).strip().upper().replace("/", "")
⋮----
# Third (secondary leading tone) NEVER doubled
⋮----
# Root must be doubled
⋮----
"""
    Validates doubling rules for sextaccords (first inversion triads: T6, S6, D6, t6, s6, d6):
    - In T6 and S6 (t6, s6): the root (prima) or fifth must be doubled.
      Doubling the third (bass) is forbidden in standard harmonic texture,
      EXCEPT in specific voice leading situations (e.g. resolution from D43 or D2 into T6,
      or voice exchanges in S6).
    - In D6: the third is the leading tone (scale degree VII).
      Doubling the leading tone in D6 is STRICTLY FORBIDDEN!
      Either the root (V) or fifth (II) must be doubled.
    """
⋮----
# If soprano is a non-chord tone (NCT), skip doubling requirement
⋮----
# VII6 / vii6: Leading tone (root) NEVER doubled; double third (bass) or fifth
⋮----
# II6 / ii6: double third (bass, IV degree) or root (II degree)
⋮----
# D6 / d6: Leading tone (third) NEVER doubled
⋮----
# T6, S6, t6, s6:
# Standard rule: root or fifth must be doubled
⋮----
# Check exceptions:
# 1. T6 / t6 resolving from D43, D2, DD43, DD2 where 7th resolves to 3rd in bass
is_d_inversion_res = (sym in ("T6", "t6") and prev_sym in ("D43", "D2", "DD43", "DD2"))
# 2. S6 / s6 where smooth voice leading requires doubled third
is_s6_smooth = (sym in ("S6", "s6") and counts[third] == 2)
⋮----
"""
    Validates factor completeness and doublings for seventh chords (D7, D65, D43, D2, VII7, II7, DD7, etc.):
    - Inversions (65, 43, 2): must be complete (1 root, 1 third, 1 fifth, 1 seventh).
    - Root position (7): complete (1, 1, 1, 1) or incomplete (2 roots, 1 third, 1 seventh, 0 fifths).
    """
⋮----
is_seventh = (
⋮----
seventh = tonic_pc % 12
seventh_alt = seventh
⋮----
seventh = (tonic_pc + 8 if ("MINOR" in mode or sym.islower()) else tonic_pc + 9) % 12
seventh_alt = (tonic_pc + 8) % 12
⋮----
seventh = (tonic_pc + 7) % 12
⋮----
seventh = (tonic_pc + 3 if ("MINOR" in mode or sym.islower()) else tonic_pc + 4) % 12
⋮----
seventh = (tonic_pc + 5) % 12
⋮----
is_inversion = any(inv in sym for inv in ("65", "43")) or sym.endswith("2") or sym in ("D2", "DD2", "II2", "VII2")
has_seventh = counts[seventh] >= 1 or counts[seventh_alt] >= 1
⋮----
is_complete = counts[root] == 1 and counts[third] == 1 and counts[fifth] == 1 and has_seventh
# Leading-tone seventh chord VII7 MUST strictly be complete; doubling leading tone (root) in incomplete VII7 is forbidden
is_vii = sym.startswith("VII")
is_incomplete = (not is_vii) and (counts[root] == 2 and counts[third] == 1 and has_seventh and counts[fifth] == 0)
⋮----
"""
    In root-position diminished triad VII (VII 5/3, vii 5/3):
    - The root (leading tone) must NEVER be doubled (rule_id: DOUBLING_VII_LEADING_TONE).
    - Omitting the fifth (incomplete VII 5/3) is forbidden (rule_id: DOUBLING_VII_LEADING_TONE).
    """
⋮----
# 1. Root (leading tone) NEVER doubled
⋮----
# 2. Incomplete VII53 without fifth is forbidden
⋮----
"""
    In passing and auxiliary six-four chords (T64, S64, t64, s64):
    - The bass (fifth of the triad) must be doubled.
    - Doubling the third is strictly forbidden.
    Otherwise raises DOUBLING_PASSING_64.
    """
⋮----
# 1. Bass (fifth of the triad) MUST be doubled
⋮----
# 2. Third must NOT be doubled
⋮----
"""
    Validates doubling rules for Neapolitan (N, N6) and Chromatic Submediant (bVI, bVI6):
    - N in root position: root must strictly be doubled (counts[root] >= 2).
    - N6: third (bass, tonic degree) must strictly be doubled (counts[third] >= 2).
      Doubling the root (bII degree) is strictly forbidden.
    - Incomplete N/N6 without third or fifth is strictly forbidden.
    - bVI / bVI6: complete triad (counts[root] >= 1, counts[third] >= 1, counts[fifth] >= 1).
      Doubling of either root or third is allowed. Incomplete bVI is strictly forbidden.
    """
sym = parse_chord_symbol(chord).strip()
sym_clean = sym.upper().replace("-", "").replace("/", "")
⋮----
is_n = sym_clean.startswith("N")
is_bvi = sym_clean.startswith("BVI")
⋮----
def _add(rule_id: str, description: str, voices: tuple[int, ...] = ()) -> None
⋮----
is_sexta = ("6" in sym_clean and "64" not in sym_clean)
# Completeness
⋮----
# N6: third must be doubled (bass)
⋮----
# N6: doubling root (bII) is forbidden
⋮----
# N root position: root must be doubled
⋮----
# Completeness: complete triad required
⋮----
# Doubling of either root or third is required
⋮----
"""
    Runs all doubling validation checks relevant to the given chord and context.
    """
violations = []
````

## File: .redteam/HANDOFF.md
````markdown
# HANDOFF — «Бригадное Ядро Гармонизации» (D:\aitraining)

> Точка входа для следующей сессии. Обновлено 2026-11-14 после волны 4 (дефекты ядра #8/#6).
> Полный план рефакторинга и статусы волн — [REMEDIATION_PLAN.md](REMEDIATION_PLAN.md).
> Независимый аудит критика — [scratch/critic/AUDIT.md](scratch/critic/AUDIT.md).
> Свежий аудит оркестратора + план починки волнами — [AUDIT_2026-11-13.md](AUDIT_2026-11-13.md).
> Метрики выживаемости планов: старый снапшот — [scratch/grammar_metrics/REPORT.md](scratch/grammar_metrics/REPORT.md),
> актуальные после P2-фиксов — [scratch/grammar_metrics/REPORT_P2_FIX.md](scratch/grammar_metrics/REPORT_P2_FIX.md).

> ⚠️ История: этот файл уже дважды врал (последний коммит `c6ef64d` вместо фактического, счёт тестов,
> статусы дефектов). Сверяйтесь с `git log -1` и реальным прогоном, а не с таблицами ниже, если расходятся.

> ✅ **ТЕКУЩАЯ ТОЧКА (2026-11-14, оркестратор build):** `master` = `eac4ebd` (волна 4: дефекты ядра #8/#6) зелёный:
> **886 passed** (879 + 7 новых, живой прогон QA), **ruff check . → 0 ошибок**, **hunt_lead.py → PROBLEMS: 0**,
> grammar_metrics survival идентичен базлайну (21.3%), exe пересобран и смоукнут (health 200, SPA 200, NO_ORPHANS).
> **Волна 1 (Wave 2 UI) ЗАВЕРШЕНА** (merge `078114a`): критик APPROVE, 5 minor закрыты.
> **Волна 2 (гигиена) ЗАВЕРШЕНА** (`57ec318`): ruff 472→0, мусор удалён, README актуализирован.
> **Волна 3 (надёжность backend) ЗАВЕРШЕНА** (`7888455`): import-file 400, LRU+TTL кэш, whitelist из грамматики,
> monkey-patch guard удалён, контракт-фиксы parse-text/import-file, «Очистить»+abort, relaxed-флаги в UI.
> **Волна 4 (дефекты ядра) ЗАВЕРШЕНА** (`eac4ebd`, 9 файлов, +504/−26): пайплайн APPROVE с 1-й итерации,
> независимый QA-гейт 9/9. Дефекты #8 и #6 CLOSED (резолюции ниже).
> **#8:** root-cause проверен живыми зондами — правило check_false_relation КОРРЕКТНО (ложных срабатываний нет,
> guard одного голоса работает); мелодия C–Eb–E–D–C в C-dur структурно неразрешима строго (T/T6 на шаге 0
> обязаны содержать E♮; Eb4 только в bVI; все продолжения блокируются FALSE_RELATION_PERECHENIE ×4 +
> VOICE_OVERLAPPING ×2). Закрыто БЕЗ ослабления правила: сквозная диагностика отказа (blocking_rules в
> solver-диагностике → HarmonizationResult.diagnostics → error.dominant_blockers + relax_suggestion),
> relaxed-путь спасает (T→bVI→K64→D→T, маркер relaxed_rule_ids, 3 решения — проверено вживую),
> раздел «Переченье» в BRIGADE_RULES.md, +4 теста.
> **#6:** удалён мёртвый код (get_rule_severity, contrary_bass_bonus, no-op elif, мёртвый протокол
> rule_engine.allow_unisons — thread-local сохранён), сбой загрузки каталога → logger.warning,
> brigade_rules.json дополнен всеми статически эмитируемыми id (+238 строк, severity/penalty 1:1 из кода),
> grader fallback на каталожные описания для незамапленных id. severity/penalty валидаторов НЕ тронуты —
> поведение идентично (метрики before=after). +3 теста.
> Осознанные minor критика (не блокеры): маркер _strict_retry_of_relaxed теоретически передаваем извне
> (влияет только на уровень лога); гистограмма blocking_rules приближённая (cost-pruning до validate);
> ветка optimal_cost==inf без blocking_rules (практически недостижима).
> Дальше — §8: **перф-волна (начинать отсюда)**: 64-нотные мелодии (timeout 4 с), MIDI round-trip 6 vs 7 нот,
> затем K-best/диверсификация (survival 21.3%), survival-метрики в CI, P3.
> Не блокеры: PyInstaller non-fatal warnings `uvicorn.lifespans[.on]` hidden import (сборку не ломают).

## 1. Снимок состояния (проверено)

| Параметр | Значение |
|---|---|
| Рабочая папка | `D:\aitraining` |
| Ветка | `master`; `wip/wave2-ui-redesign` влита (merge `078114a`), ветка сохранена; `redteam-p0/p1/p2` удалены |
| Remote | `https://github.com/nolekek/harmony-engine.git` |
| Последний коммит | `eac4ebd` — волна 4 дефекты ядра #8/#6 (+7 тестов); ранее `7888455` надёжность backend, `57ec318` гигиена, `078114a` merge Wave 2 UI |
| Тесты | **886 passed, 0 failed**, подтверждено живым прогоном 14.11 (QA, exit 0, ~103 с) |
| Линт | **ruff check . → 0 ошибок** (гейт с 13.11; extend-exclude `.redteam/scratch`; per-file-ignores: `scripts/*` E402; pipeline.py E402 убран в волне 3) |
| Python | `.venv\Scripts\python.exe` (3.14.0; `.venv` восстановлен 13.11 через `uv sync --extra dev --extra desktop`); системный `pythoncore-3.14-64` — fallback |
| Node/фронт | `frontend/` React 19 + Vite; прод-сборка в `frontend/dist` (в .gitignore) |

## 2. Быстрый старт

```powershell
cd D:\aitraining

# тесты (обязательный гейт перед коммитом); .venv восстановлен 13.11 (uv sync --extra dev --extra desktop)
.venv\Scripts\python.exe -m pytest -q

# линт (обязательный гейт с волны 2, 13.11)
.venv\Scripts\python.exe -m ruff check .

# скрипты из .redteam/scratch запускать с PYTHONPATH
$env:PYTHONPATH='D:\aitraining'
$env:PYTHONIOENCODING='utf-8'

# нативное Windows-приложение (без браузера/терминала)
python -m desktop                      # dev-запуск из исходников
python -m PyInstaller desktop.spec --noconfirm
# готовый exe: dist\HarmonyEngine\HarmonyEngine.exe (onedir, ~14.4 МБ)
# логи: %LOCALAPPDATA%\HarmonyEngine\logs\desktop.log

# метрики грамматики (13 мелодий, before/after)
python scripts/grammar_metrics.py
# перф-бенчмарк
python scripts/benchmark_harmonize.py

# приёмка волн (exit 0 = ок)
python .redteam/scratch/lead/verify_p0.py
python .redteam/scratch/lead/verify_p1.py
python .redteam/scratch/lead/verify_p2.py

# перезапуск сервиса (порт занят старым процессом — убить по PID)
Get-CimInstance Win32_Process -Filter "Name like '%python%'" |
  Where-Object { $_.CommandLine -like '*run_app.py*' } |
  ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
Start-Process -FilePath 'C:\Users\Admin\AppData\Local\Python\pythoncore-3.14-64\python.exe' `
  -ArgumentList 'run_app.py','--port','8000','--no-browser' -WorkingDirectory 'D:\aitraining' `
  -WindowStyle Hidden -RedirectStandardOutput '.redteam\scratch\lead\server.out.log' `
  -RedirectStandardError '.redteam\scratch\lead\server.err.log'
# проверка: Invoke-WebRequest http://127.0.0.1:8000/api/health
```

`run_app.py` форсит UTF-8 на stdout — без этого cp1251 ломает логи с русским.

## 3. Что сделано (сжато)

**Волна 1 починки — Wave 2 UI (merge `078114a`, фича `d9c5294`, 13.11):** редизайн завершён,
приёмка и детали — [WAVE2_WIP.md](WAVE2_WIP.md) (баннер ✅ ЗАВЕРШЕНО).
**Волна 2 починки — гигиена (`57ec318`, 13.11):** ruff 472→0, мусор, README; критик APPROVE,
4 minor — осознанные решения перечислены в текущей точке выше.
**Волна 3 починки — надёжность backend (`7888455`, 14.11):** import-file 400-валидация, LRU+TTL кэш,
whitelist из грамматики, удаление monkey-patch guard, контракт-фиксы parse-text/import-file,
«Очистить»+abort, relaxed-флаги в UI; +31 тест (879), критик APPROVE (2 итерации фикса), exe пересобран.
**Волна 4 починки — дефекты ядра (`eac4ebd`, 14.11):** #8 диагностика отказа (blocking_rules →
diagnostics → dominant_blockers/relax_suggestion) + verified relaxed-escape без ослабления правила;
#6 чистка мёртвого кода RuleEngine + каталог дополнен + grader fallback; +7 тестов (886),
пайплайн APPROVE с 1-й итерации, независимый QA 9/9 (hunt PROBLEMS: 0, метрики unchanged), exe пересобран.
Детали — в текущей точке выше.

Волны P0/P1/P2 закрыты: унисоны/неполные трезвучия, канонический D43/D2/K64, честный топ-3,
структурные ошибки API (`error.code`, 422/400/413), NCT, MetricGrid, словарь III/VII6/VII7/II7,
Krumhansl-Schmuckler, единый `RuleEngine`, `HarmonizationService`, изоляция вкладок фронта,
MIDI Format 1, MusicXML с бемолями по `fifths`, OSMD в lazy-чанке.

**Волна P2 (коммит `814ca5f`):**
1. **Плагальный last-resort финал** для нетонической сопрано. Раньше `harmonize([60,64,62,65])`
   (финал F4, IV ступень) отбивался в трёх слоях: `grammar.get_compatible_chords_for_pitch:122-128`
   → дубль фильтра в `generate_plans` → `engine.py` (финальный аккорд только root T/D/VI).
   Теперь: при пустом пуле разрешены root `S/s/II/ii`; `engine.py` даёт hard-gate только если
   pc сопрано покрывается T/D/VI, иначе soft-штраф (50 для S/s, 70 для II/ii); финальный `S/s`
   получает +12.0 в beam-скоринге, чтобы консонантный F-A-C выигрывал у уменьшённого ii (D-F-Ab).
2. **Та же мина в replanning:** `pipeline._replan` хардкодил финальные альтернативы ("D","d","VI","vi")
   в двух местах — синхронизировано с плагальным fallback.
3. **B3 / суб-C4 сопрано:** вместо ломки `STANDARD_VOICE_RANGES` (роняет `tests/unit/test_spacing.py`)
   в `pipeline.harmonize` автоматически включается `allow_extended_ranges`, когда мелодия выходит
   за `[60,81]`; в результате выставлен `auto_extended_ranges=True`.
4. **Две замены soprano-`continue` на штрафы −6.0** и починка `Fallback 3` (не сустейнит аккорд,
   не содержащий финальную ноту сопрано).
5. **Тесты:** `tests/test_plagal_final_and_ranges.py` (6 шт.). **Метрики:** корпус
   `scripts/grammar_metrics.py` расширен двумя мелодиями, отчёт `scratch/grammar_metrics/REPORT_P2_FIX.md`.

**Волна P1 (коммит `06c4437`, two-stage gate Lead+Coder+Critic, оба на Gemini 3.8 Flash/agy):**
1. **Настоящая первопричина T→VI** (не soft+15, а голодание генератора): `D→VI` при приме VI
   в сопрано требует баса на приме и удвоения терции → 4 голоса A,A,C,C без квинты, а
   `check_triad_completeness` разрешал неполное трезвучие только финальной тонике → hard
   `CHORD_FIFTH_MISSING` → 0 кандидатов → Viterbi падает → `_replan` лепит `T→VI`.
   Фикс: `doubling.check_triad_completeness(prev_chord=...)` разрешает неполное root-position VI
   (удвоенная терция) ТОЛЬКО после доминантовой группы; правило применяется в прерванном кадансе.
2. **`engine.py`: hard-gate `CADENCE_FINAL_VI_REQUIRES_DOMINANT`** — финальный VI только после
   D/d/D7/D6/D65/D43/D2/VII7 (и III/iii со штрафом +15 ради легального rescue-плана); после
   T/T6/T53/S/II/bVI — hard. Правило действует только при наличии предшественника (n=1 не ломается).
3. **`pipeline._replan`:** финальный VI фильтруется по предшественнику (без предшественника — не фильтруется).
4. **Monkey-patch выпилен:** `doubling.py` больше не перезаписывает `chromatic.check_false_relation` /
   `validate_chromatic_rules` на импорте. Вся логика перенесена в `chromatic.py` и стала mode-aware.
5. **Хроматика:** `check_false_relation`/`validate_chromatic_rules` принимают `prev_chord/curr_chord`;
   диатонические полутоны I↔bII (неаполитанский) и V↔bVI (понижённая VI) больше не «переченье»,
   а cross-voice C↔C#, F↔F#, G↔G# — hard `FALSE_RELATION_PERECHENIE` (раньше молча пропускались).
   `engine.py` пробрасывает аккорды в валидатор (раньше вызов был слепой).
6. **Grader:** русская педагогическая диагностика для `CADENCE_FINAL_VI_REQUIRES_DOMINANT`
   (студент за `T→VI` получает «2 (Не зачтено)»).
7. **Тесты:** `tests/test_final_vi_and_false_relation.py` (11 шт.): репро `[60,62,64,65,67,69]` больше
   не даёт `T→VI` (теперь `T,II6,T,S6,III,VI`); `[69]` → `['VI']`; `[60,69]/[64,69]/[67,69]` →
   `is_success=False` (осознанно, строгая каденция); `[72,71,69]` → `['T','III','VI']`; cross-voice
   переченья; отсутствие monkey-patch. `test_long_lines.py`: докстринги синхронизированы (пороги не тронуты).

**Волна Desktop (коммит `29b5a5f`):**
1. **`desktop/`** — нативное окно pywebview (EdgeChromium) в главном потоке, uvicorn в daemon-треде,
   свободный порт, ожидание `/api/health`, логи `%LOCALAPPDATA%\HarmonyEngine\logs` (10 МБ × 3),
   DPI-awareness V2, сохранение геометрии окна, проверка WebView2 с нативным MessageBox.
2. **Single-instance — НЕ мьютекс.** Win32 named mutex обосрался в реальной жизни: WebView2-дети
   наследуют хэндл, после force-kill родителя мьютекс остаётся занят, и следующий запуск навсегда
   выходит как «второй». Заменено на эксклюзивный byte-range file-lock (`instance.lock`,
   `msvcrt.locking`): ОС снимает лок при смерти процесса, Python-fd не наследуется. `instance.json`
   пишется атомарно (tmp + os.replace); дубликат шлёт FOCUS по loopback-TCP и выходит.
3. **FOCUS — только Win32** (`FindWindowW` + `ShowWindow(SW_RESTORE)` + `SetForegroundWindow`).
   Кросс-поточные `window.restore()/show()` из IPC-треда убивали окно pywebview (лог «Window closed»).
4. **`backend/main.py`: `resolve_frontend_dist()`** — env `FRONTEND_DIST_DIR` → `sys._MEIPASS` →
   dev-путь; иначе в PyInstaller onedir/onefile exe показывал заглушку вместо SPA.
5. **`desktop.spec`** — onedir COLLECT, `upx=False` (Defender), `console=False`,
   `datas=frontend/dist`, hidden imports uvicorn/fastapi/pywebview/pythonnet/mido.
6. **Тесты:** `tests/test_desktop_lifecycle.py` (7) — порт, health-wait, graceful shutdown, IPC focus,
   и два регресса на найденные баги (дубликат не удаляет `instance.json`; лок освобождается и stale
   discovery перезаписывается).
7. **Сборка:** `python -m PyInstaller desktop.spec --noconfirm` → `dist/HarmonyEngine/HarmonyEngine.exe`
   (onedir, ~14.4 МБ). Проверено на живой Windows: окно видимо, health ok, SPA отдаётся, второй
   инстанс выходит, первый жив, минимизированное окно восстанавливается по FOCUS.

## 4. Метрики выживаемости планов (после P2-фиксов, P1 не изменил)

Полная таблица — [scratch/grammar_metrics/REPORT_P2_FIX.md](scratch/grammar_metrics/REPORT_P2_FIX.md).
Ключевое (замер после P1 идентичен):

| Мелодия | Survival (Before -> After) | Starvations | Harmonize |
|---|---|---:|---|
| default (6) | 21.3% -> 21.3% | 0 | PASSED |
| a-moll desc (8) | 0.0% -> 0.0% | 0 | PASSED (replanning) |
| 16-note scale | 45.0% -> 45.0% | 0 | PASSED |
| 32-note arch | 0.0% -> 0.0% | **1 -> 0** | PASSED (replanning) |
| chromatic 1..4 | 0–8.3% без изменений | 0 | PASSED |
| **final F4 plagal** | **0.0% -> 40.0%** | 0 | PASSED |
| **soprano B3 extended** | 0% (артефакт метрики*) | 0 | PASSED |
| same_triad / s_to_d_leap | 41.7→39.3% / 25.0→26.1% | 0 | PASSED |

\* `evaluate_melody()` дергает `ViterbiSolver.solve()` напрямую, без pipeline-авто-расширения диапазона,
поэтому колонка survival для B3 остаётся 0 — сквозной `harmonize()` при этом PASSED.

**Вывод неизменен:** план-генератор сам по себе выдаёт жизнеспособный план редко; UI держится на
bounded replanning. Главный архитектурный долг — диверсификация планов / K-best Viterbi.

## 5. Статусы дефектов (после 06c4437)

| # | Дефект | Статус |
|---|---|---|
| 1 | Финальный аккорд жёстко T/VI/D при нетонической сопрано → 0 решений | **CLOSED** (P2) — плагальный last-resort S, финал F-A-C-F |
| 2 | Финальный `T -> VI` как «прерванная каденция» | **CLOSED** (P1) — hard-gate `CADENCE_FINAL_VI_REQUIRES_DOMINANT`; первопричина (голодание `D→VI` из-за `CHORD_FIFTH_MISSING`) тоже устранена |
| 3 | Monkey-patching: `doubling.py` перезаписывает `chromatic.check_false_relation`/`validate_chromatic_rules` | **CLOSED** (P1) — логика перенесена в `chromatic.py`, патч удалён, добавлен регресс-тест на отсутствие патча |
| 4 | Сопрано B3 (59) вне диапазона → неаполитанский оборот падал | **CLOSED** (P2) — авто-включение extended, `auto_extended_ranges=True` |
| 5 | Перф-пороги тестов подняты (16 нот 2500 мс, 32/длинные 6000 мс) | **ОТКЛОНЕНО как дефект** — 1200/3000 недостижимы без перф-волны (замер: 16 нот ~0.4–1.5 с, 32 ноты ~1.5–3.0 с в зависимости от условий; под нагрузкой полного сьюта старые пороги флакуют). Пороги не трогаем; докстринги синхронизированы (P1). Перф-оптимизация — отдельная волна |
| 6 | Мёртвый/декоративный код в `RuleEngine` | **CLOSED** (волна 4, `eac4ebd`) — удалены get_rule_severity/contrary_bass_bonus/no-op-elif/мёртвый allow_unisons-протокол; сбой каталога → logger.warning; каталог дополнен всеми эмитируемыми id; grader fallback на описания каталога; severity/penalty валидаторов не тронуты (поведение идентично) |
| 7 | Незастаженный хак в рабочей копии | **CLOSED** — дерево чистое, всё в коммитах |
| 8 | `chromatic 5` `[60,63,64,62,60]` → FAILED (`FALSE_RELATION_PERECHENIE`, тенор E3 vs альтерированное сопрано Eb4) | **CLOSED** (волна 4, `eac4ebd`) — правило корректно (проверено вживую), мелодия структурно неразрешима строго; закрыто диагностикой отказа (dominant_blockers + relax_suggestion) + verified relaxed-путём (T→bVI→K64→D→T с маркером); правило НЕ ослаблялось |

Новое поведение, которое нужно считать осознанным (не баг): короткие мелодии с финалом на VI после
T/T6/S/II (`[60,69]`, `[64,69]`, `[67,69]`) теперь возвращают `is_success=False` — легальной строгой
каденции для них нет. Одиночная нота (`[69]`) по-прежнему даёт `['VI']` (каденционного перехода нет).

## 5.1 Статус фиче-флагов (проверено в `06c4437`)

| Флаг | Дефолт | Где реализован | Семантика |
|---|---|---|---|
| `allow_adjacent_unisons` | `False` | `viterbi.py:72`, `pipeline.py:115,279`, `backend/service.py:68`, `backend/api.py:178` | thread-local `set_unisons_allowed`, снимает hard-`VOICE_UNISON` в state_generator; в API — opt-in |
| `relax_hard_gates` | `False` | `viterbi.py:73`, `pipeline.py:116,280`, `backend/service.py:69`, `backend/api.py:179` | last-resort escape hatch: hard-нарушение получает штраф 10000, метаданные `relaxed_rule_ids` / `had_relaxed_violations`; **строгий план всегда предпочтительнее релаксации** — повторный strict-прогон в `Harmonizer.harmonize` и `HarmonizationService` (`service.py:160` принудительно ставит `relax_hard_gates=False` для strict-прохода) |

Оба флага прокинуты до API и не включаются молча; `allow_extended_ranges` тоже `False` по умолчанию,
но автоматически включается для мелодий вне `[60,81]` (факт виден в `auto_extended_ranges`).

## 6. Известные ограничения (не блокеры)

- Хроматика (N/bVI/альтерации) абсорбируется не полностью: `[60,63,64,62,60]` → строгий отказ,
  но теперь объяснимый (`error.dominant_blockers` + `relax_suggestion`); relaxed-путь даёт решение с маркером.
- `brigade_rules.json` дополнен всеми эмитируемыми id и используется grader для описаний;
  severity/penalty в валидаторах захардкожены ОСОЗНАННО (каталог — не гейт, поведение не зависит от файла).
- Grader API принимает только канонические символы функций.
- UI-каталог тональностей: 12 мажоров и 12 гармонических миноров (natural/melodic — P3).
- K-best/CP-SAT и «объяснение неразрешимости» — P3 (см. план, T24).
- Плагальный финал `S/s` — только last-resort и только для ступеней, физически не покрываемых
  T/D/VI. Финальный VI после III/iii — легален со штрафом (компромисс ради rescue-теста), после
  T/T6/S/II/bVI — запрещён.
- Mode-aware эвристики в `chromatic.py` (N/bVI контекст) основаны на символах аккордов и
  характеристических диадах; при отсутствии контекста падают в безопасный режим.

## 7. Грабли окружения и агентов (личный опыт, не повторять)

- **Диагностика pytest:** смотреть хвост `pytest -q` и опираться на exit code; `--co -q` для числа тестов.
- **Параллельные агенты ломают прогон:** правка `.py` во время `pytest` даёт ложные фейлы.
  Two-stage gate держит Coder и Critic последовательно.
- **Тимпейты в этом DSH по умолчанию рождаются на модели родителя (deepseek).** Чтобы они были на
  Gemini/agy, харнесс пропатчен (2026-11-12): `dsh-experimental-agent-team/lib/index.js` — поддержка
  `memberLlmProvider/memberModel/memberReasoningEffort` и проброс `agentOptions` в `startActivation`;
  профиль `~/.dsh/profiles/web/cordis.patch.yml` — строка с id **`agent-team`** (не `agent-teams`!).
  Бэкапы: `index.js.bak-20261112`, `cordis.patch.yml.bak-20261112`. Патч слетит при `npm update` dsh.
- **agy-тимпейты:** `send_message(recipient="lead")` у их нативного тула падает (`recipient "lead" not found`) —
  отчёт приходит в closing message сессии. Lead видит его как уведомление.
- **`agy_ask(mode="plan")`** в этой сборке моста падает с `unknown error`; model slug — `gemini-3.8-flash`.
- **`git status` после работы тимпейта проверять обязательно** — иначе пропустишь регрессию (так была
  поймана регрессия n=1: `[69]` → падение вместо `['VI']`).
- Windows: `$env:PYTHONIOENCODING='utf-8'` для скриптов с русским выводом, иначе `UnicodeEncodeError`.
- `run_app.py` убивать строго по PID из `Win32_Process` (иначе плодятся сервисы на 8000).
- Много «мёртвых» тимпейтов в roster чистить нельзя: API удаления нет, имена immutable, лимит 8;
  чистый roster — только в новой сессии.
- **Пайплайн (опыт 13.11):** кодер flash склонен к ролевой инверсии — пытается делегировать через
  `pipeline_run` изнутри прогона (гарантированный BUSY, ноль правок) или зависает до дедлайна
  (тогда fallback devstral делает работу). Лечение: ролевая блокировка в начале ТЗ («ты исполнитель,
  делегирование запрещено») + явные QA-критерии в ТЗ («нулевой diff = FAILED», иначе QA проверяет
  что попало и даёт false-green). Критик на большом diff (~90 файлов) падает по таймауту 15 мин →
  ревью напрямую саб-агентом critic с ограниченным скоупом (полный diff только рисковых файлов,
  остальное — выборка + косвенные гейты ruff/pytest).
- **Волна 3 (опыт 14.11):** на большом ТЗ (8 пунктов) ОБА кодера пайплайна таймаутнулись, оставив
  частичные правки в дереве (`files_changed=[]` в отчёте плагина НЕ означает отсутствие правок —
  всегда проверяй `git status`). Восстановление: ручной цикл — кодер-доделчик оценивает partial diff
  и завершает → QA → критик. One-shot саб-агентам ЗАПРЕЩАТЬ background-команды (кодер ушёл ждать
  уведомление от фонового pytest и потерял ход); продолжение сессии по sessionID может не работать
  (ID обрезается) → ТЗ всегда самодостаточное. QA-смоук должен покрывать ВАЛИДНЫЕ пути, не только
  негативные (критик поймал сломанный импорт валидного файла, который QA пропустил, проверяя только 400).
- **Волна 4 (опыт 14.11):** связка «живой QA-зонд ДО ТЗ → точное ТЗ с ролевой блокировкой и
  foreground-only → pipeline_run» дала APPROVE с 1-й итерации (flash снова пустой ответ → devstral-fallback
  отработал). Разведчик без shell не может верифицировать репро — закрывай это быстрым QA-зондом до
  написания ТЗ (зонд подтвердил: relaxed спасает chromatic5, правило не баг → фикс стал хирургическим).
  ТЗ с запретом трогать валидаторы + гейт «метрики before=after» защитил от ослабления правил.

## 8. Что дальше (рекомендуемый порядок)

**Волны 1–4 починки ЗАВЕРШЕНЫ 13–14.11** (UI, гигиена, надёжность backend, дефекты ядра #8/#6).
Дальнейшее — исследовательские/перф-волны, выше риск, отдельные сессии:

1. **Перф-волна (НАЧИНАТЬ ОТСЮДА):** профилирование генератора планов / `parse_chord_symbol`, 64-нотные
   мелодии (сейчас `success=False`, timeout 4 с), затем возврат порогов тестов к 1200/3000 мс.
   Сюда же MIDI round-trip теряет ноту (`parse_midi_file`, 6 vs 7).
2. **K-best / диверсификация луча** — главный драйвер survival (сейчас 21.3%, UI на replanning).
3. **Survival-метрики в CI** (`scripts/grammar_metrics.py` уже готов, нужен job).
4. **P3:** хроматический словарь (N/bVI/альтерации), natural/melodic minor в UI-каталоге, маппинг римских
   I/IV/V в grader.
````

## File: src/harmony/solver/viterbi.py
````python
"""
Global Viterbi Dynamic Programming Optimizer for four-part harmony.
Computes the globally optimal SATB voice leading trajectory over the admissible state lattice,
minimizing total voice leading cost subject to zero Brigade hard rule violations.
"""
⋮----
# Thread-safe global cache for static slice validations (no transition context)
_STATIC_STEP0_CACHE: dict[tuple, tuple[float, list[str]]] = {}
⋮----
def clear_solver_cache() -> None
⋮----
"""Clears static Step 0 validation cache."""
⋮----
def _sorted_rule_histogram(counts: dict[str, int]) -> dict[str, int]
⋮----
"""Deterministic {rule_id: count} view: count descending, rule_id as tie-break."""
⋮----
@dataclass
class SolverStepDiagnostic
⋮----
step_index: int
chord: str
soprano_pitch: int
candidates_count: int
reachable_candidates_count: int
⋮----
@dataclass
class SolverResult
⋮----
is_success: bool
voicings: list[Voicing] | None
total_cost: float
diagnostics: list[dict[str, Any]]
message: str = ""
step_diagnostics: list[SolverStepDiagnostic] | None = None
had_relaxed_violations: bool = False
relaxed_rule_ids: list[str] = field(default_factory=list)
⋮----
class ViterbiSolver
⋮----
"""
    Viterbi dynamic programming solver for classical four-part harmony.
    Complexity: O(N * K^2), where N is number of chords, K is max candidates per step.
    Runs in under 10ms for typical 8-16 bar exercises.
    """
⋮----
def __init__(self, rule_engine: RuleEngine | None = None, early_stopping_k: int = 0)
⋮----
"""
        Finds the globally optimal sequence of Voicings for the given melody and chord progression.
        """
n = len(chords)
⋮----
msg = f"Length mismatch: melody ({len(melody)}) vs chords ({n})"
⋮----
# Parse melody and chords
melody_pitches: list[int] = []
downbeats: list[bool] = []
phrase_boundaries: list[bool] = []
⋮----
metric_structure = calculate_metric_structure(melody)
has_explicit_downbeats = any(
⋮----
explicit_pb = m.get("phrase_boundary") if "phrase_boundary" in m else m.get("is_phrase_boundary")
⋮----
measure = metric.get("measure", 1)
is_pb = (measure % 4 == 0 and metric.get("is_downbeat", False)) or (i > 0 and (i % 4 == 0 or i == n // 2))
⋮----
parsed_chords: list[Chord] = []
⋮----
# Parse key
parsed_key = Key.parse(key) if key is not None else Key("C", "Major")
⋮----
# Session tracking for early stopping on long melodies with multiple candidate plans
session_key = (
⋮----
# Configure rule engine extended ranges and unisons.
# Unisons are governed exclusively by the thread-local set_unisons_allowed
# protocol consumed by spacing.validate_spacing; RuleEngine has no
# allow_unisons attribute (former assignments were dead code, defect #6).
orig_extended = getattr(self.rule_engine, "allow_extended_ranges", False)
⋮----
# 1. Generate state lattice V[t]
lattice: list[list[Voicing]] = []
step_diag: list[SolverStepDiagnostic] = []
⋮----
prev_s = melody_pitches[t - 1] if t > 0 else None
next_s = melody_pitches[t + 1] if t + 1 < n else None
is_db = downbeats[t]
candidates = generate_candidate_voicings(
⋮----
msg = f"Step {t} ({parsed_chords[t].function}): no candidate voicings found for soprano pitch {melody_pitches[t]}"
⋮----
# 2. Viterbi forward DP
# delta[t][j] = min cost to reach candidate j at step t
# psi[t][j] = index of best predecessor in lattice[t-1]
delta: list[list[float]] = []
psi: list[list[int]] = []
⋮----
# Step 0: Initial cost based on static spacing (cached without context)
init_delta: list[float] = []
step0_violations: list[list[str]] = []
chord_sym_0 = parsed_chords[0].function if hasattr(parsed_chords[0], "function") else str(parsed_chords[0])
⋮----
cache_key_0 = (
⋮----
res = self.rule_engine.validate(
hard_viols = [
n_hard = len(hard_viols)
⋮----
cost = res.cost if res.cost < float("inf") else self.rule_engine.compute_initial_cost(v, chord=parsed_chords[0], key=parsed_key)
viol_ids = []
⋮----
cost = float("inf")
⋮----
base_cost = self.rule_engine.compute_initial_cost(v, chord=parsed_chords[0], key=parsed_key)
cost = base_cost + 10000.0 * n_hard
viol_ids = [viol.rule_id for viol in hard_viols]
⋮----
msg = "Initial step 0 has no valid voicings under rule engine constraints."
⋮----
# Steps 1 to N-1
trans_violations: list[list[list[str]]] = [[]]
# Defect #8 (additive diagnostics): per-step histogram of hard rule ids
# that pruned transitions. prev_step_blocking holds the histogram of the
# previous step for the "all predecessors unreachable" failure branch.
prev_step_blocking: dict[str, int] = {}
⋮----
curr_candidates = lattice[t]
prev_candidates = lattice[t - 1]
curr_chord = parsed_chords[t]
prev_chord = parsed_chords[t - 1]
is_downbeat = downbeats[t]
⋮----
step_delta: list[float] = [float("inf")] * len(curr_candidates)
step_psi: list[int] = [-1] * len(curr_candidates)
step_trans_violations: list[list[str]] = [[] for _ in range(len(curr_candidates))]
blocking_counter: dict[str, int] = {}
⋮----
# Pre-filter reachable predecessors and sort by accumulated cost for branch pruning
reachable_prev = [
⋮----
msg = f"Step {t} ({curr_chord.function}): all {len(curr_candidates)} candidates blocked by hard-rule violations from step {t-1}."
⋮----
best_cost = float("inf")
best_prev_idx = -1
best_viols: list[str] = []
⋮----
# Non-negative transition cost guarantee: if prev_cost >= best_cost,
# no subsequent predecessor can improve best_cost. Prune safely.
⋮----
prev2_v = None
⋮----
prev2_idx = psi[t - 1][i]
⋮----
prev2_v = lattice[t - 2][prev2_idx]
⋮----
# In SATB harmonization of a given cantus firmus, soprano melodic intervals
# are immutable input constraints of the melody itself (such as degree 6 <-> 7
# in harmonic minor scales). Hard violations strictly confined to voice 0
# (soprano) melodic intervals must not prune the lattice for accompanying voices.
hard_violations = [
⋮----
hard_violations = [v for v in hard_violations if v.rule_id != "VOICE_UNISON"]
⋮----
# Defect #8: aggregate blocking rule ids from the
# already-computed validate() result (no re-validation).
⋮----
n_hard = len(hard_violations)
base_cost = res.cost if res.cost < float("inf") else self.rule_engine.compute_soft_cost(prev_v, curr_v)
⋮----
trans_cost = base_cost + 10000.0 * n_hard
cur_viols = [v.rule_id for v in hard_violations]
⋮----
trans_cost = res.cost if res.cost < float("inf") else self.rule_engine.compute_soft_cost(prev_v, curr_v)
cur_viols = []
⋮----
total_cost = prev_cost + trans_cost
⋮----
best_cost = total_cost
best_prev_idx = i
best_viols = cur_viols
⋮----
reachable = sum(1 for c in step_delta if c < float("inf"))
⋮----
prev_step_blocking = blocking_counter
⋮----
# 3. Backtrack optimal trajectory
last_step_costs = delta[n - 1]
best_last_idx = min(range(len(last_step_costs)), key=lambda idx: last_step_costs[idx])
optimal_cost = last_step_costs[best_last_idx]
⋮----
msg = f"Step {n - 1} ({parsed_chords[-1].function}): final cadence unreachable or no valid path across lattice."
⋮----
optimal_path: list[Voicing] = [lattice[n - 1][best_last_idx]]
curr_idx = best_last_idx
all_relaxed_ids: list[str] = []
⋮----
prev_idx = psi[t][curr_idx]
⋮----
curr_idx = prev_idx
⋮----
unique_relaxed_ids = list(dict.fromkeys(all_relaxed_ids))
had_relaxed = len(unique_relaxed_ids) > 0
````

## File: src/harmony/pipeline.py
````python
"""
End-to-End Orchestrator Pipeline for four-part harmony.
Unifies Macro Syntax Generation, State Lattice Pruning, Viterbi Optimization,
and Multi-Format Score Exporting.
"""
⋮----
@dataclass
class HarmonizationSolution
⋮----
chords: list[Chord]
voicings: list[Voicing]
cost: float
ascii_score: str
durations: list[str] = field(default_factory=list)
time_signature: str = "4/4"
metric_info: list[dict[str, Any]] = field(default_factory=list)
had_relaxed_violations: bool = False
relaxed_rule_ids: list[str] = field(default_factory=list)
⋮----
def to_musicxml(self, title: str = "Harmonization Exercise") -> str
⋮----
def save_musicxml(self, output_path: str | Path, title: str = "Harmonization Exercise") -> Path
⋮----
p = Path(output_path)
⋮----
def save_midi(self, output_path: str | Path, bpm: int = 80) -> Path
⋮----
@dataclass
class HarmonizationResult
⋮----
is_success: bool
solutions: list[HarmonizationSolution]
best_solution: HarmonizationSolution | None
message: str = ""
⋮----
auto_extended_ranges: bool = False
# Defect #8 (additive): solver diagnostics of failed plans on failure; empty on success.
diagnostics: list[dict[str, Any]] = field(default_factory=list)
⋮----
class Harmonizer
⋮----
"""
    Complete end-to-end Classical Harmony Engine.
    Harmonizes any given soprano melody according to the Brigade textbook rules.
    """
⋮----
"""
        Harmonizes a soprano melody.
        If 'chords' is provided, uses that functional plan directly.
        Otherwise, uses the HarmonicGrammar to synthesize valid plans.
        Supports custom time signatures (3/4, 2/4, 6/8, 4/4) and dotted durations.

        ``relax_hard_gates`` is a last-resort escape hatch: a strictly legal plan is
        always preferred, and relaxation is attempted only when the strict pass (or
        its bounded replanning) produced nothing at all. Accepting a 10000-point
        penalty while a clean plan exists is never the desirable outcome.
        """
⋮----
strict = self.harmonize(
⋮----
parsed_key = Key.parse(key)
parsed_ts = TimeSignature.parse(time_signature)
⋮----
# Pre-process melody with exact metric structure and durations
metric_info = calculate_metric_structure(melody, default_time_signature=parsed_ts)
processed_melody = []
⋮----
raw_item = melody[i]
explicit_db = None
⋮----
explicit_db = raw_item.get("is_downbeat")
⋮----
# The client declared the metric flag explicitly: respect it.
db = bool(explicit_db)
⋮----
# Auto mode (int notes, missing flag or explicit None): measure
# start (offset 0.0) defines the primary downbeat; secondary
# accents (offset > 0.0) are unaccented for NCT classification.
db = (info["offset_in_measure"] == 0.0)
⋮----
durations_list = [info["duration"] for info in metric_info]
melody_pitches = [m["pitch"] for m in processed_melody]
auto_extended = (not allow_extended_ranges) and any(p < 60 or p > 81 for p in melody_pitches)
effective_extended = allow_extended_ranges or auto_extended
⋮----
# 1. Determine functional plans to try
plans_to_try: list[list[Chord]] = []
⋮----
parsed_chords = [c if isinstance(c, Chord) else Chord(function=str(c)) for c in chords]
⋮----
grammar = self.grammar or HarmonicGrammar(key=parsed_key)
⋮----
plans_to_try = grammar.generate_plans(melody=processed_melody, key=parsed_key, max_plans=max_plans)
⋮----
solutions: list[HarmonizationSolution] = []
failed_plans: list[tuple[list[Chord], SolverResult]] = []
⋮----
# 2. Run Viterbi optimization on candidate plans
⋮----
res: SolverResult = self.solver.solve(
⋮----
ascii_view = format_ascii_score(
⋮----
# 3. Replanning pass if initial plans all failed and replanning is allowed
⋮----
replan_res = self._replan(
⋮----
# Defect #8: surface WHY plans failed — pass through the blocking-rule
# diagnostics of the first few rejected plans (additive, failure-only).
failure_diagnostics: list[dict[str, Any]] = []
⋮----
# Sort solutions by ascending cost and take top-3
⋮----
top_solutions = solutions[:3]
⋮----
"""
        Bounded replanning engine: analyzes diagnostic failures from Viterbi,
        identifies the first blocked step/chord, iterates over deterministic
        alternative functions from ALL_FUNCTIONS, and reassembles valid syntax tails.
        """
start_time = time.perf_counter()
n = len(melody)
⋮----
effective_extended = allow_extended_ranges
grammar = self.grammar or HarmonicGrammar(key=key)
⋮----
seen_plans: set[tuple[str, ...]] = {tuple(c.function for c in p) for p, _ in failed_plans}
⋮----
attempts = 0
⋮----
# Try alternative chords for the first blocked step in each failed plan
⋮----
blocked_t = None
⋮----
blocked_t = int(d["step"])
⋮----
blocked_t = sd.step_index
⋮----
blocked_t = 0
⋮----
# Steps to reconsider: the blocked step itself, and predecessor if blocked by dead-end context
steps_to_try = [blocked_t]
⋮----
target_pitch = melody[target_step]["pitch"]
is_db = melody[target_step]["is_downbeat"]
is_final = (target_step == n - 1)
is_penult = (target_step == n - 2)
next_p = melody[target_step + 1]["pitch"] if target_step < n - 1 else None
prev_fn = plan[target_step - 1].function if target_step > 0 else None
⋮----
cand_alts = grammar.get_compatible_chords_for_pitch(
all_compat = [
⋮----
cand_alts = [fn for fn in cand_alts if fn != plan[target_step].function]
⋮----
cand_alts = [
⋮----
is_minor_0 = "MINOR" in str(mode_0).upper()
tonic_tones_0 = {
⋮----
cand_alts = [fn for fn in cand_alts if fn in ("T", "t", "T6", "t6", "VI", "vi")]
⋮----
# Deterministic ordering
# The final chord must be a legal cadence ending, never a
# dominant inversion (D6/D65/D43) or a passing chord.
⋮----
is_minor_r = "MINOR" in str(mode_r).upper()
tonic_tones = {
⋮----
cand_alts = [fn for fn in cand_alts if fn in ("T", "t")]
⋮----
cand_alts = [fn for fn in cand_alts if fn in ("T", "t", "D", "d", "VI", "vi")]
⋮----
base = [fn for fn in cand_alts if fn in ("D", "d", "VI", "vi")]
sub = [fn for fn in cand_alts if fn in ("S", "s", "II", "ii")]
⋮----
cand_alts = base + sub
⋮----
cand_alts = sub
⋮----
pred_fn = plan[target_step - 1].function if target_step > 0 else ""
allowed_deceptive_preds = (
⋮----
cand_alts = [fn for fn in cand_alts if fn not in ("VI", "vi")]
⋮----
prefix = [c.function for c in plan[:target_step]] + [alt_fn]
⋮----
full_plans = [prefix]
⋮----
beams = [(0.0, prefix)]
⋮----
k_p = melody[k]["pitch"]
k_db = melody[k]["is_downbeat"]
k_final = (k == n - 1)
k_penult = (k == n - 2)
k_next_p = melody[k + 1]["pitch"] if k < n - 1 else None
⋮----
k_cands = grammar.get_compatible_chords_for_pitch(
⋮----
# The final chord of the rebuilt tail must also be a
# legal cadence ending (T-family, or D/VI for a
# half/deceptive cadence) — never a dominant inversion.
⋮----
is_minor_k = "MINOR" in str(mode_k).upper()
tonic_tones_k = {
⋮----
k_cands = [fn for fn in k_cands if fn in ("T", "t")]
⋮----
k_cands = [fn for fn in k_cands if fn in ("T", "t", "D", "d", "VI", "vi")]
⋮----
base_k = [fn for fn in k_cands if fn in ("D", "d", "VI", "vi")]
sub_k = [fn for fn in k_cands if fn in ("S", "s", "II", "ii")]
⋮----
k_cands = base_k + sub_k
⋮----
k_cands = sub_k
k_cands = [
⋮----
next_pitch_k = melody[n - 1]["pitch"]
⋮----
dom_tones_k = {(tonic_pc_k + 7) % 12, (tonic_pc_k + 11) % 12, (tonic_pc_k + 2) % 12, (tonic_pc_k + 5) % 12}
⋮----
d_cands_k = [fn for fn in k_cands if fn in ("D", "d", "D7", "d7", "D65", "d65", "D43", "d43", "D2", "d2", "D6", "d6")]
⋮----
k_cands = d_cands_k + [fn for fn in k_cands if fn not in d_cands_k]
⋮----
new_beams = []
⋮----
last_c = path[-1]
⋮----
b_score = 0.0
⋮----
# Penalize identical chord repetition on moving soprano
⋮----
# Penalize III6 / VI chains
⋮----
beams = []
⋮----
beams = new_beams[:16]
⋮----
full_plans = [path for _, path in beams if len(path) == n]
⋮----
t_fp = tuple(fp)
⋮----
candidate_chord_plan = [Chord(function=c_fn) for c_fn in fp]
sol_res = self.solver.solve(
⋮----
# Also fallback: if no solutions yet from failed plans, re-try top plans from failed_plans with relax_soprano_intervals=True
````

## File: src/harmony/rules/engine.py
````python
"""
Central Brigade Rule Engine for four-part voice leading and texture validation.
Executes hard-gate rule checks and computes soft heuristic costs for dynamic programming.
"""
⋮----
logger = logging.getLogger(__name__)
⋮----
DOMINANT_GROUP = {"D", "D7", "D6", "D65", "D43", "D2"}
SUBDOMINANT_GROUP = {"S", "S6", "S64", "s", "s6", "s64", "II", "II6", "II65"}
⋮----
"""
    Core Brigade syntax rules for harmonic functional progressions:
    - K64 cannot appear as initial chord of piece
    - K64 must be placed on a strong/downbeat
    - D -> S prohibition: strictly forbidden inside phrases, permitted only at phrase boundaries
    - Dominant cannot regress to K64
    - K64 must resolve to Dominant (D or D7)
    """
violations: list[RuleViolation] = []
curr_sym = parse_chord_symbol(curr_chord) if curr_chord is not None else ""
prev_sym = parse_chord_symbol(prev_chord) if prev_chord is not None else ""
⋮----
# K64 is strictly forbidden as initial chord of a progression
⋮----
# K64 must be on a downbeat
⋮----
# Functional regression prohibition: D -> S (forbidden inside phrase, allowed on phrase boundary)
⋮----
# Dominant cannot move to K64 (D -> K64 regression)
⋮----
# K64 must resolve to dominant (D or D7)
⋮----
# Consecutive mediant chords (III6 -> III6, etc.) strictly forbidden
⋮----
class RuleEngine
⋮----
"""
    Central validation engine implementing Brigade Textbook (Способин et al.) rules.
    """
⋮----
def get_rule_description(self, rule_id: str) -> str | None
⋮----
"""Returns the human-readable description of a rule from the catalog if loaded."""
rule = self.rules_registry.get(rule_id)
⋮----
def _load_catalog(self, path: str | Path | None) -> None
⋮----
catalog_path = None
⋮----
p = Path(path)
⋮----
catalog_path = p
⋮----
default_p = Path(__file__).resolve().parents[3] / "docs" / "brigade_rules.json"
⋮----
catalog_path = default_p
⋮----
data = json.loads(catalog_path.read_text(encoding="utf-8"))
⋮----
rid = r.get("id")
⋮----
"""
        Validates macro harmonic syntax using the unified check_syntax_rules predicate.
        """
⋮----
_OPENING_PENALTY: dict[str, float] = {
⋮----
"""
        Computes heuristic cost for the starting state (step 0).
        Penalizes extreme vocal registers, wide spacing gaps, and adjacent unisons,
        and prefers a tonic opening (T > T6 > VI...). Guarantees step 0 cost >= 0.0.
        """
satb = to_satb(voicing)
cost = 1.0
⋮----
# Functional opening preference: classical exercises open on the tonic,
# not on a mediant/submediant wandering chord.
⋮----
sym = parse_chord_symbol(chord)
⋮----
is_minor = "MINOR" in str(mode).upper()
tonic_tones = {tonic_pc, (tonic_pc + 3 if is_minor else tonic_pc + 4) % 12, (tonic_pc + 7) % 12}
⋮----
# Distance from center of comfortable vocal tessitura:
# S ~ 69 (A4), A ~ 62 (D4), T ~ 55 (G3), B ~ 47 (B2)
⋮----
# Penalize adjacent voice unisons (S==A, A==T, T==B)
⋮----
# Penalize upper voice spacing gaps > 8 semitones
gap_sa = satb[0] - satb[1]
gap_at = satb[1] - satb[2]
gap_tb = satb[2] - satb[3]
⋮----
"""
        Computes non-negative heuristic transition cost (REPORT #53):
        - Movement cost of middle voices (Alto + Tenor)
        - Direct motion penalty between Soprano and Bass
        - Smooth bass line preference
        Guarantees cost >= 0.0.
        """
prev_satb = to_satb(prev_voicing)
curr_satb = to_satb(curr_voicing)
⋮----
cost = 0.0
⋮----
# Law of shortest path: |dA| + |dT|
da = abs(curr_satb[1] - prev_satb[1])
dt = abs(curr_satb[2] - prev_satb[2])
movement_cost = (da + dt) * self.weights.get("shortest_path", 1.0)
⋮----
# Bass vs Soprano relative motion: non-negative scheme
# (contrary motion ds*db < 0 simply earns no penalty — former no-op branch removed)
ds = curr_satb[0] - prev_satb[0]
db = curr_satb[3] - prev_satb[3]
⋮----
# Smooth bass line: penalty for leaps wider than a fifth (> 7 semitones)
abs_db = abs(db)
⋮----
# Neuro-symbolic style prior scorer (if provided)
⋮----
_DOMINANT_FAMILY = {
⋮----
"""Non-negative harmonic-quality cost.

        Cadences must be prepared by a dominant (authentic cadence); wandering
        mediant/submediant chords outside a deceptive resolution are penalized.
        """
⋮----
prev_sym = parse_chord_symbol(prev_chord)
curr_sym = parse_chord_symbol(curr_chord)
⋮----
cost += 0.8  # weaker inversions of the dominant
⋮----
cost += 8.0  # deceptive cadence as the final is weak
⋮----
cost += 10.0  # K64 directly to T without D resolution
⋮----
cost += 50.0  # T6 in final approach is unacceptable
⋮----
cost += 4.0  # plagal cadence (allowed when dominant impossible)
⋮----
cost += 4.0  # stasis on final tonic
⋮----
cost += 10.0  # unprepared final tonic
⋮----
cost += 50.0  # T6 in final is unacceptable
⋮----
cost += 0.5  # half cadence is legitimate but less conclusive
⋮----
cost += 1.0  # deceptive cadence
⋮----
is_minor = False
⋮----
# Chains of III6/VI as patches
⋮----
"""
        Validates transition from prev_voicing to curr_voicing or evaluates
        a single starting vertical slice if prev_voicing is None.
        """
⋮----
# 1. Static checks on current vertical slice
⋮----
# 2. Macro syntax checks (metric placement & regression)
⋮----
# 3. Transition checks (if previous voicing is present)
soft_cost = 0.0
⋮----
soft_cost = self.compute_soft_cost(prev_voicing, curr_voicing)
⋮----
# Penalize repeating identical chord on moving soprano note
⋮----
prev_s = to_satb(prev_voicing)[0]
curr_s = to_satb(curr_voicing)[0]
⋮----
# Requirement 3: Final T,T with different soprano notes soft penalty (+6)
⋮----
soft_cost = self.compute_initial_cost(curr_voicing, chord=curr_chord, key=key)
⋮----
# Cadential final chord validation:
⋮----
# Requirement 2: Final VI permitted only after dominant (deceptive cadence) or mediant III/iii
# Final VI after T/T6, subdominant (S, II, bVI) is hard-gate.
# Only enforced when a predecessor chord exists (not applicable to n=1 melodies).
⋮----
forbidden_preds = (
allowed_deceptive_preds = (
⋮----
# Requirement 1: Final root T cannot be preceded by T6
⋮----
soprano_pc = to_satb(curr_voicing)[0] % 12
t_tones = set(get_triad_tones("T", tonic_pc, mode))
d_tones = set(get_triad_tones("D", tonic_pc, mode))
vi_tones = set(get_triad_tones("VI", tonic_pc, mode))
⋮----
# Outer voice direct motion (HIDDEN_FIFTHS_OCTAVES) is permitted in cadences as soft penalty
adjusted: list[RuleViolation] = []
⋮----
violations = adjusted
⋮----
# 4. Determine validity and final cost
has_hard = any(v.is_hard for v in violations)
⋮----
"""
        Convenience method to validate a single isolated vertical slice.
        """
````

## File: src/harmony/syntax/grammar.py
````python
"""
Macro Harmonic Syntax Engine and Period Grammar.
Generates structurally sound functional chord progressions (T, S, D, K64, etc.)
for a given soprano melody according to classical period form and Brigade syntax rules.
"""
⋮----
# All standard classical functions considered by the grammar
ALL_FUNCTIONS = [
⋮----
DOMINANT_GROUP = {"D", "D7", "D6", "D65", "D43", "D2", "VII", "VII6", "VII7"}
PRIMARY_DOMINANT_GROUP = {"D", "D7", "D6", "D65", "D43", "D2"}
LEADING_TONE_GROUP = {"VII", "VII6", "VII7"}
SUBDOMINANT_GROUP = {"S", "S6", "S64", "II", "II6", "II65", "II7"}
SECONDARY_DOMINANT_GROUP = {"DD", "DD7", "DD65", "DD43", "DD2"}
NEAPOLITAN_GROUP = {"N", "N6"}
CHROMATIC_SUBMEDIANT_GROUP = {"bVI", "bVI6"}
⋮----
@dataclass
class MelodyNote
⋮----
pitch: int
duration: int = 4
is_downbeat: bool = False
is_cadence_point: bool = False
phrase_boundary: bool = False
⋮----
class HarmonicGrammar
⋮----
"""
    Formal Grammar and Plan Generator for classical four-part harmony.
    Enforces macro syntax:
    - Period structure (middle cadence -> D, final cadence -> K64 - D7 - T)
    - Functional circle (T -> S -> D -> T)
    - Strict prohibition of D -> S regression
    - Mandatory D43 -> T6 resolution
    - K64 on downbeat only
    """
⋮----
def __init__(self, key: Key | None = None)
⋮----
@property
    def beam_starvation_count(self) -> int
⋮----
@beam_starvation_count.setter
    def beam_starvation_count(self, value: int) -> None
⋮----
def get_chord_pitch_classes(self, fn: str, key: Key | None = None) -> set[int]
⋮----
"""Returns the set of pitch classes belonging to the chord function."""
k = key or self.key
⋮----
pcs = {root, third, fifth}
fn_upper = fn.strip().upper()
⋮----
is_minor = "MINOR" in mode.upper() or fn.islower()
⋮----
"""
        Returns all chord functions that can harmonically accommodate the soprano pitch.
        If next_pitch is provided, ensures that unstable tendency tones (like 7ths in soprano)
        can actually resolve smoothly without illegal leaps.
        """
⋮----
pc = pitch % 12
compatible: list[str] = []
⋮----
is_minor = "MINOR" in mode.upper()
tonic_tones = {tonic_pc, (tonic_pc + 3 if is_minor else tonic_pc + 4) % 12, (tonic_pc + 7) % 12}
can_step_down = (next_pitch is not None) and ((next_pitch - pitch) in (-1, -2))
⋮----
# Metric rule: K64 cannot be on weak beat
⋮----
# Position rule: Final cadence ending chord
# If pitch matches tonic triad, authentic cadence ending must be root T.
# If pitch does not match tonic (e.g. degrees 2, 7), half cadence D or deceptive VI are allowed.
# Inversions (T6, D6, etc.) and dissonant 7ths (D7) are strictly forbidden in final cadence.
⋮----
# Position rule: Penultimate chord in authentic cadence is typically D, D7, etc.
# K64 CANNOT be penultimate immediately before final T, because K64 must resolve to D!
⋮----
next_in_tonic = (next_pitch is None) or ((next_pitch % 12) in tonic_tones)
⋮----
# Dissonance resolution rule: If a 7th chord is chosen and the soprano note IS the 7th,
# the soprano MUST step down (-1 or -2) into the next note. Leaps from the 7th are forbidden!
⋮----
allowed_pcs = {root, third, fifth}
⋮----
# Inversion doubling rules:
# In D6 and D65, the bass has the leading tone (third).
# Doubling the leading tone in the soprano is strictly forbidden!
⋮----
# In D2 and D43, the bass has the 7th.
# Doubling the 7th in soprano is strictly forbidden!
⋮----
# Add 7th for seventh chords
⋮----
seventh = (tonic_pc + 5) % 12
⋮----
seventh = tonic_pc % 12
⋮----
# Cadential preference: before the final tonic the textbook wants a
# dominant preparation (D/D7/D65/D43/D2/D6), not a plagal S/II.
# Requirement 1: Before final root T, penultimate chord is strictly dominant group
# (D, D6, D7, D65, D43, D2, K64) if melodic note allows it;
# if dominant physically impossible, S/II is allowed, but NOT T6/VI/T.
# Exception: when the final two melody notes repeat the tonic pitch (e.g. C4 -> C4),
# T, T is valid cadential prolongation.
⋮----
t_cands = [fn for fn in compatible if fn in ("T", "t")]
⋮----
compatible = t_cands
⋮----
cadential = [
⋮----
compatible = cadential
⋮----
subdominant = [
⋮----
compatible = subdominant
⋮----
compatible = [fn for fn in compatible if fn not in ("T6", "t6", "VI", "vi")]
⋮----
compatible = [fn for fn in ("S", "s", "II", "ii") if pc in set(get_triad_tones(fn, tonic_pc, mode))]
⋮----
"""
        Validates syntactic progression rules using unified RuleEngine check_syntax_rules:
        - No D -> S or D -> II regression (unless phrase_boundary=True)
        - D43 must go to T6 or T
        - D2 must go to T6
        - K64 must be followed by D or D7
        - Dominants cannot move to K64
        - Dominants cannot move to secondary dominants (D -> DD)
        - Secondary dominant (DD) must resolve to Dominant or K64, not S, II, T, or VI
        - D6 and D65 have leading tone in bass; cannot leap to T6 or VI
        - D7 cannot resolve to T6
        """
# Unified check with RuleEngine syntax rules
syntax_violations = check_syntax_rules(
⋮----
prev_upper = prev_fn.strip().upper()
curr_upper = curr_fn.strip().upper()
⋮----
# D -> S and D -> II regression forbidden inside phrase (allowed at phrase boundary)
⋮----
# Dominants cannot move to K64 (D -> K64, D6 -> K64 is strictly forbidden; K64 resolves TO dominant)
⋮----
# Dominant 7th chords cannot un-resolve back into dominant triad (D or D6)
⋮----
# Secondary dominant (DD) cannot resolve to subdominant, tonic, or VI
⋮----
# Dominant cannot regress to secondary dominant (D -> DD)
⋮----
# Dominant cannot regress to mediant (D -> III, D -> III6)
⋮----
# Mediant cannot move to K64, DD, or VII
⋮----
# Consecutive mediant chords (III6 -> III6, etc.) strictly forbidden
⋮----
# Root-position diminished VII triad (VII, VII53) is strictly forbidden in classical harmony
⋮----
# Supertonic seventh chords (II7, II65) can only resolve to Dominant group, K64, or T64
⋮----
# Leading-tone chords (VII6, VII7) can only resolve to Tonic, intra-functionally to Dominant, or deceptively to VI
⋮----
# VII6 is a passing chord between tonic inversions (T-VII6-T6, T6-VII6-T); cannot follow subdominant
⋮----
# D43 must resolve to T6 or T (and T53)
⋮----
# D2 must resolve strictly to T6
⋮----
# K64 must resolve to dominant triad or D7
⋮----
# Inversions with leading tone in bass (D6, D65) cannot leap to T6 or VI
⋮----
# Root position D7 cannot resolve to T6
⋮----
# Neapolitan chord transitions:
# N/N6 -> K64/D/D7/D6/T/T6 (and intra-functional N, N6, or chromatic bVI, bVI6)
# N -> S is strictly forbidden
⋮----
# Approach to N/N6: can be approached from S, II, T, T6, VI, bVI, N, N6
# D -> N is a forbidden regression inside a phrase
⋮----
# Transition between natural submediant VI and chromatic submediant bVI is forbidden
⋮----
# Chromatic submediant transitions:
# bVI/bVI6 -> D/D7/S/T (and VI-zone)
# Cannot move to mediant III, secondary dominant DD, or leading tone VII
⋮----
_CADENCE_TEMPLATES: tuple[tuple[str, ...], ...] = (
⋮----
_HALF_CADENCE_TEMPLATES: tuple[tuple[str, ...], ...] = (
⋮----
"""
        Generates candidate functional plans for the entire melody.
        Backtracks through the compatible function lattice with beam search pruning.
        Uses adaptive beam width widening if beam starves or produces empty plans.
        """
⋮----
n = len(melody)
⋮----
# Parse notes
notes: list[MelodyNote] = []
⋮----
p = int(m["pitch"])
db = bool(m.get("is_downbeat", False))
pb = bool(m.get("phrase_boundary", m.get("is_phrase_boundary", False)))
⋮----
p = int(m)
db = (i % 2 == 0)
pb = False
is_final = (i == n - 1)
⋮----
# Adaptive strategy: retry with widened beam if beam starves or yields zero plans
⋮----
results: list[list[Chord]] = []
⋮----
results = self._generate_plans_pass(notes=notes, key=k, max_plans=max_plans, multiplier=multiplier)
⋮----
k = key
⋮----
n = len(notes)
⋮----
scale_pcs = set(k.scale_pcs)
⋮----
scale_pcs.add((tonic_pc + 10) % 12)  # Natural 7th
scale_pcs.add((tonic_pc + 9) % 12)   # Melodic 6th
⋮----
# Build candidate options per step
step_candidates: list[list[str]] = []
⋮----
is_penult = (i == n - 2)
next_p = notes[i + 1].pitch if i < n - 1 else None
cands = self.get_compatible_chords_for_pitch(
⋮----
# Fallback to any functions in ALL_FUNCTIONS whose tones contain note pitch
cands = [
⋮----
cands = [fn for fn in ("S", "s", "II", "ii") if (note.pitch % 12) in self.get_chord_pitch_classes(fn, k)]
lead_pc = (tonic_pc + 11) % 12
⋮----
cands = [fn for fn in cands if fn != "VII7"]
⋮----
# Canon requirement: Initial chord must be T or T6 if soprano is in tonic tones
⋮----
t_cands = [fn for fn in cands if fn in ("T", "t", "T6", "t6")]
⋮----
cands = t_cands
⋮----
# Canon requirement: Final chord must be T in root position if soprano is in tonic tones
⋮----
t_cands = [fn for fn in cands if fn in ("T", "t")]
⋮----
# Inversions and 7th chords strictly forbidden in final cadence (must be root D or VI, or fallback S/s/II/ii)
final_d_vi = [
⋮----
cands = final_d_vi
⋮----
# Canon requirement: Penultimate chord before final tonic prioritizes dominant if soprano allows
⋮----
dom_tones = {(tonic_pc + 7) % 12, (tonic_pc + 11) % 12, (tonic_pc + 2) % 12, (tonic_pc + 5) % 12}
⋮----
d_cands = [fn for fn in cands if fn in ("D", "d", "D7", "d7", "D65", "d65", "D43", "d43", "D2", "d2", "D6", "d6")]
⋮----
cands = d_cands + [fn for fn in cands if fn not in d_cands]
⋮----
# Beam search for top functional progressions
# State: (score, [chord_symbols])
beams: list[tuple[float, list[str]]] = [(0.0, [])]
⋮----
def _final_fallback_chords(target_pitch: int, prev_fn_chord: str | None = None) -> tuple[str, ...]
⋮----
target_pc = target_pitch % 12
d_vi = []
⋮----
new_beams: list[tuple[float, list[str]]] = []
is_downbeat = notes[i].is_downbeat
is_pb = bool(notes[i].phrase_boundary)
⋮----
local_cands = cands
⋮----
prev_fn_nct = path[-1]
⋮----
local_cands = cands + [prev_fn_nct]
⋮----
prev_fn = path[-1]
⋮----
trans_score = 0.0
⋮----
vi_root_pc = (tonic_pc + (8 if is_minor else 9)) % 12
⋮----
root_triads = {"T", "S", "D", "II", "VI", "III", "t", "s", "d"}
⋮----
same_triad_inversion = (
⋮----
p_mel = notes[i - 1].pitch % 12
c_mel = notes[i].pitch % 12
⋮----
soprano_step = abs(notes[i].pitch - notes[i - 1].pitch) in (1, 2)
⋮----
# Штраф за осцилляцию T, S6, T, S6 (только при линейном движении мелодии)
⋮----
is_t_s6_abab = (
⋮----
melody_oscillating = (
⋮----
is_descending_leading = (
⋮----
is_next_bvi = (
⋮----
is_chromatic_note = (notes[i].pitch % 12) == (tonic_pc + 6) % 12
is_db_pc = (notes[i].pitch % 12) == (tonic_pc + 1) % 12
is_ab_pc = (notes[i].pitch % 12) == (tonic_pc + 8) % 12
is_eb_pc = (notes[i].pitch % 12) == (tonic_pc + 3) % 12
is_chromatic_cand = cand in ("N", "N6", "bVI", "bVI6")
has_chromatic_context = (
⋮----
dom_pcs = {(tonic_pc + 7) % 12, (tonic_pc + 11) % 12, (tonic_pc + 2) % 12, (tonic_pc + 5) % 12}
⋮----
trans_score = 6.0
⋮----
trans_score = 4.0
⋮----
trans_score = -50.0
⋮----
trans_score = 2.0
⋮----
trans_score = 1.0
⋮----
trans_score = 0.5
⋮----
# Fallback 1: Relax voice leading heuristics with penalty, but strictly enforce is_valid_syntax_transition
⋮----
is_final_step = (i == n - 1)
⋮----
prev_fn_for_cand = path[-1] if path else None
allowed_finals = _final_fallback_chords(notes[i].pitch, prev_fn_for_cand)
⋮----
# Fallback 2: Check all functions containing the pitch that are valid transitions
⋮----
allowed_finals = _final_fallback_chords(notes[i].pitch, prev_fn) if is_final_step else ()
⋮----
allowed_finals = _final_fallback_chords(notes[i].pitch, None) if is_final_step else ()
⋮----
# Fallback 3: Sustain previous harmony across passing tone if valid
⋮----
# Keep top beams with diversity preservation: avoid a single local chord monopolizing all slots
⋮----
_beam_width = min(max(max_plans * 4, 32) * multiplier, 2048)
⋮----
_beam_width = min(max(max_plans * 8, 256) * multiplier, 2048)
⋮----
_beam_width = min(max(max_plans * 6, 128) * multiplier, 1024)
⋮----
chord_counts: dict[str, int] = {}
filtered_beams: list[tuple[float, list[str]]] = []
max_per_chord = max(_beam_width // 4, 16)
⋮----
ch = item[1][-1]
cnt = chord_counts.get(ch, 0)
⋮----
beams = filtered_beams
⋮----
# Extract top plans with deduplication
⋮----
seen_paths: set[tuple[str, ...]] = set()
⋮----
t_path = tuple(path)
⋮----
# Inject textbook cadence templates (authentic and half cadences)
⋮----
"""Builds plans whose final cadence follows a textbook template.

        Template chords occupy positions n-1-Len .. n-2, the final tonic stays at
        n-1. The prefix is beam-searched with the regular compatibility rules, so
        the resulting plan is always syntactically valid end to end.
        """
⋮----
tonic_tones = {
is_half_cadence = (notes[-1].pitch % 12) not in tonic_tones
final_fn = ("D" if not is_minor else "d") if is_half_cadence else ("T" if not is_minor else "t")
⋮----
templates = self._HALF_CADENCE_TEMPLATES if is_half_cadence else self._CADENCE_TEMPLATES
plans: list[list[str]] = []
seen: set[tuple[str, ...]] = set()
⋮----
length = len(template)
⋮----
prefix_len = n - 1 - length
⋮----
compatible = True
⋮----
idx = prefix_len + j
pc = notes[idx].pitch % 12
⋮----
compatible = False
⋮----
# Verify transition from last template chord to final cadence chord
⋮----
nxt = notes[i + 1].pitch if i + 1 < n else None
⋮----
step: list[tuple[float, list[str]]] = []
⋮----
bonus = 4.0 if cand in ("T", "t") else (2.0 if cand in ("T6", "t6") else 0.0)
⋮----
# Penalize consecutive III6/VI in templates
⋮----
bonus = -8.0
⋮----
bonus = -6.0
⋮----
bonus = 1.0 if cand in ("S", "S6", "II", "II6") else 0.0
⋮----
beams = []
⋮----
beams = step[:64]
⋮----
full = path + list(template) + [final_fn]
⋮----
valid = True
⋮----
valid = False
⋮----
signature = tuple(full)
````
