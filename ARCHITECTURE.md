# ARCHITECTURE.md — Brigade Harmony Engine

**Проект:** `harmony` 0.1.0  
**Ветка / HEAD на момент проверки:** `master` / `fe8f94285c48385ec6ff93cb3567652e44066f71`  
**Дата проверки:** 2026-11-16  
**Живые гейты:** 901 pytest-тестов пройдено, `ruff` — 0 ошибок, frontend build — успех.

Канонические источники: [`docs/BRIGADE_RULES.md`](docs/BRIGADE_RULES.md), [`docs/MATH_MODEL.md`](docs/MATH_MODEL.md), [`docs/brigade_rules.json`](docs/brigade_rules.json), [`SPECIFICATION.md`](SPECIFICATION.md), [.redteam/HANDOFF.md](.redteam/HANDOFF.md).

---

## 1. Назначение системы

Система выполняет четырёхголосную SATB-гармонизацию сопрано-мелодии по правилам brigade учебника гармонии (Дубовский, Евсеев, Способин, Соколов). Основной алгоритм — детерминированный symbolic solver: генерация гармонических планов и поиск Витерби по решётке допустимых вертикалей.

Система также:

- определяет тональность мелодии;
- импортирует MusicXML, MIDI и текст;
- экспортирует MusicXML, MIDI и ASCII;
- проверяет готовое студенческое решение и выдаёт оценку;
- предоставляет Web UI, REST API, CLI и desktop-оболочку.

Нейросетевая гармонизация в основном пути отсутствует. `src/harmony/ml` — экспериментальный n-gram prior, не подключённый к production-пайплайну.

---

## 2. Архитектурный стиль

Модульный монолит с чёткими слоями:

```text
Desktop / Browser / CLI
          │
          ▼
Frontend React SPA ──► REST Backend ──► HarmonizationService
                                            │
                                            ▼
                                     Pipeline / Harmonizer
                                            │
              ┌───────────────┬─────────────┴──────────────┐
              ▼               ▼                            ▼
        HarmonicGrammar   State Generator           Export layer
              │               │                            │
              └────────► Viterbi Solver ◄────── RuleEngine ┘
                                 │
                                 ▼
                    Candidate ranking / diagnostics
```

Слои:

1. **Domain layer** — `src/harmony/core`: высоты, лады, аккорды, voice spacing, метрика, модуляция.
2. **Syntax layer** — `src/harmony/syntax`: макроплан, функции, cadence templates, whitelist.
3. **Solver layer** — `src/harmony/solver`: candidate states и Витерби DP.
4. **Rule layer** — `src/harmony/rules`: hard gates, soft penalties, удвоения, хроматика, неаккордовые звуки.
5. **Export/Import layer** — MusicXML, MIDI, ASCII, text parsing.
6. **Pipeline layer** — оркестрация strict/relaxed, replanning, top-k.
7. **Interface layer** — REST API, React, CLI, desktop wrapper.

---

## 3. Границы модулей

| Модуль | Ответственность | Основные артефакты |
|---|---|---|
| `src/harmony/core` | базовые типы и музыкальная арифметика | `Pitch`, `Key`, `ChordDefinition`, `Voicing`, `MetricGrid` |
| `src/harmony/syntax` | грамматика последовательностей функций | `ALL_FUNCTIONS`, cadence templates, beam search |
| `src/harmony/solver` | построение решётки и глобальный поиск | `state_generator`, `ViterbiSolver` |
| `src/harmony/rules` | проверка правил и стоимости переходов | `RuleEngine`, voice leading, chromatic, doubling |
| `src/harmony/export` | сериализация решений | MusicXML, MIDI, ASCII |
| `src/harmony/pipeline.py` | сквозной контракт гармонизатора | `Harmonizer.harmonize` |
| `backend/` | HTTP-контракты, кэш, импорт/оценка | `api.py`, `service.py`, `grader.py`, `importers.py` |
| `frontend/` | UI и вызовы API | `App.tsx`, `useHarmonizer.ts`, OSMD viewer |
| `desktop/` | локальный single-window wrapper | `app.py`, `instance.py`, `logging_config.py` |
| `docs/` | формализованная музыкальная спецификация | `BRIGADE_RULES.md`, `MATH_MODEL.md`, `brigade_rules.json` |
| `scripts/` | аудит, бенчмарки, датасеты, e2e | metrics, stress, benchmark |

---

## 4. Точки входа

| Способ | Команда | Точка входа |
|---|---|---|
| Web | `python run_app.py` | backend `backend.main:app` + собранный `frontend/dist` |
| Backend dev | Uvicorn вручную | `backend/main.py` |
| Frontend dev | `pnpm dev` / `npm run dev` | `frontend/src/main.tsx`, Vite proxy `/api → :8000` |
| CLI | `python -m src.harmony.cli` | `src/harmony/cli.py` |
| Desktop | `python -m desktop` | `desktop/app.py` |
| Desktop exe | PyInstaller `desktop.spec` | `dist/HarmonyEngine/HarmonyEngine.exe` |
| Python API | `from src.harmony.pipeline import Harmonizer` | `pipeline.Harmonizer.harmonize` |

---

## 5. Основной runtime flow

### 5.1 Гармонизация

1. Клиент отправляет мелодию, тональность, метр и флаги.
2. `backend/api.py` валидирует Pydantic-схему.
3. `backend/api.py` вызывает `HarmonizationService.harmonize` в threadpool; сервис проверяет кэш и запускает основной перебор планов.
4. `HarmonicGrammar` генерирует план функций.
5. Для каждого плана `state_generator` строит множество допустимых SATB-вертикалей.
6. `ViterbiSolver` находит минимальную траекторию по hard/soft стоимости.
7. `RuleEngine` и специализированные валидаторы вычисляют переходные штрафы.
8. Если основной перебор планов не дал решения, сервис выполняет ограниченный `Harmonizer.harmonize` как replanning-fallback.
9. Top-3 кандидата ранжируются по стоимости.
10. Экспортеры формируют MusicXML/MIDI/ASCII и функциональный анализ.

### 5.2 Оценка готового решения

1. `POST /api/grade` принимает voicings, chords, key, time signature.
2. `backend/grader.py` прогоняет правила и собирает violations.
3. Оценка: 0 hard → 5; 1 hard → 3; 2 и более → 2.
4. Возвращаются report, colored MusicXML и ASCII score.

### 5.3 Импорт

MusicXML/MIDI/text парсятся в мелодию, тональность, voicings и длительности. Ошибки парсинга возвращаются как 400, без внутреннего стека.

---

## 6. Domain model

### Вертикаль SATB

```text
v = (S, A, T, B), где высоты expressed as MIDI pitches
```

Инварианты статической валидности:

```text
S ≥ A ≥ T ≥ B
S ∈ [60, 81]
A ∈ [55, 74]
T ∈ [48, 67]
B ∈ [40, 60]
S - A ≤ 12
A - T ≤ 12
T - B ≤ 24
pc(S), pc(A), pc(T), pc(B) ∈ allowed PitchClasses(chord)
```

### Ключевые контракты

- `Key` задаёт тонику и лад.
- `ChordDefinition` задаёт функцию, inversion, состав и предикат допустимости.
- `Voicing` — аккордовая вертикаль.
- `MetricGrid` — единый источник сильных/слабых долей.
- `ALL_FUNCTIONS` — единый grammar-derived whitelist функций.
- `RuleViolation` — rule_id, measure, severity, голос, сообщение.

---

## 7. Solver и стоимость

### Viterbi DP

Для шагов `t = 1..N`, состояний `v_{t,j}`:

```text
delta_1(j) = InitCost(v_1j)
delta_t(j) = min_i(delta_{t-1}(i) + C(v_{t-1,i}, v_{t,j}))
```

Сложность: `O(N * Kmax^2)` в пределах сгенерированной решётки.

### Стоимость перехода

```text
C(prev, next) = H(prev, next) + S(prev, next)
```

- `H` — hard constraint, 0 или `+∞`.
- `S` — мягкая неотрицательная стоимость: движение средних голосов, относительное движение баса/сопрано, скачки баса.

### Relaxation

`relax_hard_gates` позволяет escape-hatch только по явному запросу: hard violation получает большой штраф, результат помечается diagnostics/`relaxed_rule_ids`. Strict-путь остаётся приоритетным и не меняет правила ядра.

---

## 8. Backend и кэш

- FastAPI приложение: `backend/main.py`.
- Router `/api`: `backend/api.py`.
- Сервисный кэш: `backend/service.py`.
  - `CACHE_MAX_ENTRIES = 128`
  - `CACHE_TTL_SEC = 300.0`
  - timeout: `HARMONIZE_TIMEOUT_SEC = 4.0`
- Кэш LRU+TTL хранит полный JSON-response гармонизации: candidates, costs, ASCII и MusicXML. Он не является персистентным хранилищем.
- Middleware: X-Request-ID, лимит тела ~2 МБ, CORS для dev/localhost, SPA fallback, global JSON 500 с `error_id`.

---

## 9. API boundaries

REST маршруты:

| Маршрут | Метод | Назначение |
|---|---:|---|
| `/api/health` | GET | health probe |
| `/api/keys` | GET | канонические тональности |
| `/api/detect-key` | POST | автодетект тональности |
| `/api/parse-text` | POST | парсинг текста |
| `/api/harmonize` | POST | полный цикл гармонизации, top-3 |
| `/api/grade` | POST | проверка студенческого SATB |
| `/api/import-file` | POST | MusicXML/MIDI import |
| `/api/export/midi` | POST | binary MIDI export |
| `/api/export/musicxml` | POST | MusicXML export |

Полные контракты и acceptance criteria: [`SPECIFICATION.md`](SPECIFICATION.md).

---

## 10. Frontend architecture

React 19 + TypeScript + Vite:

- `App.tsx` — состояние страницы и tabs.
- `hooks/useHarmonizer.ts` — REST client, AbortController, error state.
- `hooks/useTheme.ts` — dark/light.
- `components/melody` — piano, file upload, MIDI input, note list.
- `components/ui` — Button/Card/Input/Select/Tabs атомы.
- `components/grader` — violations list, score matrix.
- `components/ScoreDisplay` — OpenSheetMusicDisplay viewer.
- `audio/` — WebMIDI playback/input.

Frontend не содержит правил гармонизации; он оркестрирует вызовы REST API.

---

## 11. Desktop architecture

`desktop/` оборачивает тот же backend/Frontend bundle:

- Uvicorn запускается в daemon thread.
- Порт выбирается ephemeral.
- `/api/health` опрашивается перед открытием окна.
- Single instance реализован эксклюзивным byte-range file lock, а не named mutex: это защищает от stale mutex после force-kill.
- Повторный запуск активирует существующее окно Win32 calls (`FindWindowW`, `ShowWindow`, `SetForegroundWindow`).
- Логи пишутся в `%LOCALAPPDATA%\HarmonyEngine\logs` с ротацией.
- PyInstaller собирает onedir exe с `frontend/dist` как data.

---

## 12. Persistence и внешние интеграции

Приложение не имеет базы данных.

Данные существуют только как:

- запросы в памяти;
- service cache с TTL;
- экспортируемые файлы MusicXML/MIDI;
- локальные логи desktop;
- тестовые корпусы/датасеты в репозитории.

Внешние интеграции ограничены браузером, DAW-совместимым MusicXML/MIDI и локальным API.

---

## 13. Security and operational boundaries

- Система локальная/учебная; аутентификация и авторизация не входят в scope.
- CORS настроен для localhost dev/production ports.
- Ограничение тела запроса предотвращает случайные большие uploads.
- Ошибки парсинга не должны возвращать 500 с внутренним стеком.
- Секретов в коде нет; конфигурация не содержит credentials.

---

## 14. Observability

- Backend logger и X-Request-ID.
- FastAPI global exception handler возвращает JSON с `error_id`.
- Desktop logs: `%LOCALAPPDATA%\HarmonyEngine\logs\desktop.log`.
- Scripts provide grammar survival, performance benchmark, e2e API checks.

---

## 15. Known architectural debt

- План-генератор имеет низкую выживаемость (survival 21.3% по корпусу); надёжность частично обеспечивается bounded replanning.
- Хроматические корпуса и 64-нотные мелодии остаются слабыми местами производительности и полноты.
- ML `StylePriorModel` не подключён и не должен восприниматься как production-компонент.
- Domain types частично дублируются между `core/types.py`, `core/key.py`, `core/voicing.py`.
- Packaging mismatch: дистрибутив описывает пакет `harmony`, а код/README используют импорт `src.harmony.*`.
- `PROJECT_MAP.md` остаётся Repomix-снимком; governance-статус актуализируется, но машинный дамп не является canonical source.

---

## 16. Non-goals

- Нейросетевой генеративный solver.
- Формальный music notation editor.
- База данных пользовательских партитур.
- Публичное SaaS, аутентификация, multi-tenancy.
- Автоматическая запись сложной полифонии вне SATB учебного scope.
- Изменение музыкальных правил без явного подтверждения учебником и пользователем.
