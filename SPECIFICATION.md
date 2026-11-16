# SPECIFICATION.md — Brigade Harmony Engine

**Версия документа:** 2026-11-16  
**Основание:** `docs/BRIGADE_RULES.md`, `docs/MATH_MODEL.md`, `docs/brigade_rules.json`, `backend/api.py`, `src/harmony/pipeline.py`, [.redteam/HANDOFF.md](.redteam/HANDOFF.md)

---

## 1. Scope

Система обязана:

1. Принимать мелодию сопрано или готовую SATB-партитуру.
2. Определять или принимать тональность и метр.
3. Строить гармонический план по каноническим функциям.
4. Генерировать SATB-вертикали и выбирать оптимальные решения Витерби.
5. Валидировать правила Brigade как hard constraints и soft costs.
6. Возвращать top-3 решения, diagnostics, MusicXML, MIDI и ASCII.
7. Оценивать студенческое решение и выдавать `5/3/2`; оценка `4` в текущей реализации не возвращается.
8. Работать как REST API, Web UI, CLI и desktop-приложение.

Вне scope:

- нейросетевая генерация;
- полная поддержка всех хроматических аккордов позднего романтизма;
- natural/melodic minor в UI-каталоге без явного расширения;
- сохранение пользовательских проектов в БД;
- публикация партитур как music notation editor.

---

## 2. Functional requirements

### FR-1: Ввод мелодии

Система должна принимать мелодию как:

- MIDI pitches: `0..127`;
- names (`C4`, `Eb4` и т.п.);
- scale degrees (`1 3 4 5`);
- JSON array of `MelodyNoteItem`;
- `is_downbeat` boolean/null;
- `duration` string/number;
- file upload для `.musicxml`, `.xml`, `.mid`, `.midi`.

Допустимая длина `/api/harmonize`: 1..128 notes.

### FR-2: Тональность и лад

Система должна поддерживать:

- 12 pitch classes как тоники; `PITCH_CLASS_NAMES` содержит 22 spelling'а для этих классов;
- modes: `Major`, `MinorHarmonic`, `MinorNatural` и совместимые алиасы `Minor`, `dur`, `moll`;
- канонический каталог `/api/keys`: 12 major + 12 harmonic minor;
- автодетект тональности для `/api/detect-key` и MIDI import.

### FR-3: Метр

Поддерживается формат `<beats>/<beat_type>`:

- `beats`: 1..32;
- `beat_type`: 1, 2, 4, 8, 16, 32;
- значение возвращается нормализованным (`4/4`, `3/4`).

### FR-4: Harmonization

`POST /api/harmonize` должен:

1. Принять `HarmonizeRequest`.
2. Вычислить гармонические планы через grammar.
3. Для плана построить допустимые voicings.
4. Выполнить Viterbi DP.
5. Вернуть candidates top-3.
6. Вернуть MusicXML/ASCII/functional plan/costs/diagnostics.
7. Сохранять deterministic ranking по минимальной стоимости.

### FR-5: Grading

`POST /api/grade` должен:

- принимать voicings и chords одинаковой длины;
- валидировать chord functions через grammar-derived whitelist + historical aliases;
- возвращать violations по тактам;
- назначать оценку:
  - 0 hard violations → `5`;
  - 1 hard violation → `3`;
  - 2+ hard violations → `2 (Не зачтено)`.

### FR-6: Export

Система должна экспортировать:

- `POST /api/export/midi`: binary MIDI `audio/midi`;
- `POST /api/export/musicxml`: MusicXML `application/vnd.recordare.musicxml+xml`;
- ASCII score для CLI и backend diagnostics.

Экспорт принимает voicings; при наличии chords — валидирует функции.

### FR-7: Flags

`HarmonizeRequest` поддерживает:

| Флаг | По умолчанию | Семантика |
|---|---:|---|
| `allow_extended_ranges` | `False` | расширяет допустимый voice range; auto-enable вне `[60,81]` для сопрано |
| `allow_secondary_dominants` | `True` | разрешает второстепенные доминанты |
| `max_plans` | `50` | лимит генерируемых планов, диапазон `1..100` |
| `allow_adjacent_unisons` | `False` | снимает hard `VOICE_UNISON` в opt-in режиме |
| `relax_hard_gates` | `False` | escape-hatch: hard violation становится штрафом, результат маркируется |

---

## 3. Domain requirements

### DR-1: SATB вертикаль

Для каждого аккорда обязательно:

```text
S ≥ A ≥ T ≥ B
S ∈ [60, 81]
A ∈ [55, 74]
T ∈ [48, 67]
B ∈ [40, 60]
S - A ≤ 12
A - T ≤ 12
T - B ≤ 24
```

### DR-2: Hard constraints

Следующие правила считаются недопустимыми переходами (`+∞`) в strict mode:

- параллельные чистые квинты и октавы между любой парой голосов;
- противоположные чистые квинты и октавы;
- hidden/direct 5ths/8ves в крайних голосах при скачке сопрано;
- voice crossing;
- voice overlapping;
- запрещённые мелодические ходы: септимы, увеличенные интервалы, два скачка подряд;
- удвоение не того тона в K64: в квартсекстаккорде удваивается бас;
- нарушение resolution seventh в D7/D65/D43/D2/II7/VII7;
- syntax regression D→S без разрешённого исключения;
- K64 initial, K64 без strong beat, K64 не разрешённый в D/D7;
- final chord gate CADENCE_FINAL_VI_REQUIRES_DOMINANT;
- false relation / переченье между разными голосами, кроме whitelist контекстов.

### DR-3: Soft costs

Мягкая стоимость обязана быть неотрицательной:

```text
S(prev,next) ≥ 0
```

Включает:

- движение альтов и теноров;
- штраф за прямое движение баса/сопрано;
- штраф за скачки баса шире квинты.

### DR-4: Doubling truth source

Canonical bass doubling rule для BASS_INVERSION_MISMATCH и FOREIGN_TONE использует single source of truth:

```text
src/harmony/rules/doubling.py::required_bass_pc_for
```

Этот же контракт применяется state generator и engine.

### DR-5: False relation

Правило `FALSE_RELATION_PERECHENIE` должно быть mode-aware.

Whitelist не-перечений:

- неаполитанский аккорд: I ↔ bII;
- пониженная VI / VII7-контекст: V ↔ bVI;
- диатонические полутонные шаги разных ступеней.

### DR-6: Chord whitelist

Backend accepts chord symbols только из:

```text
grammar.ALL_FUNCTIONS ∪ _LEGACY_CHORD_FUNCTION_ALIASES
```

Grammar не генерирует legacy aliases; они нужны только для совместимости API.

---

## 4. REST contracts

### `/api/keys`

Response: list of 24 canonical keys.

### `/api/detect-key`

Request body: `MelodyNoteItem[]`.

Response: detected key object. Если пустой ввод — fallback first canonical key.

### `/api/parse-text`

Request:

```json
{
  "text": "C4 E4 G4",
  "key": {"tonic": "C", "mode": "Major"},
  "time_signature": "4/4"
}
```

Response: parsed melody notes.

### `/api/harmonize`

Request example:

```json
{
  "melody": [{"pitch": 64}, {"pitch": 65}],
  "key": {"tonic": "C", "mode": "Major"},
  "time_signature": "4/4",
  "max_plans": 50,
  "relax_hard_gates": false
}
```

Response contains:

- candidates top-3;
- cost;
- MusicXML;
- ASCII;
- chords/plan;
- diagnostics;
- relaxed rule markers.

### `/api/grade`

Request:

```json
{
  "voicings": [{"soprano": 64, "alto": 60, "tenor": 55, "bass": 48}],
  "chords": ["T"],
  "key": {"tonic": "C", "mode": "Major"},
  "time_signature": "4/4"
}
```

Response:

```json
{
  "report": {},
  "musicxml": "...",
  "ascii_score": "..."
}
```

### `/api/import-file`

Принимает multipart `file` или JSON body:

```json
{"filename": "score.xml", "xml_content": "..."}
{"filename": "score.mid", "content_base64": "..."}
```

Ожидаемые ошибки:

- bad JSON → 400;
- bad base64 → 400;
- bad XML/MIDI → 400;
- unsupported filename → 400.

### `/api/export/midi`

Request: voicings, bpm, time_signature, optional durations.

Response: binary MIDI.

### `/api/export/musicxml`

Request: voicings, optional chords, key, title, time_signature, optional durations.

Response: MusicXML string with attachment header.

---

## 5. CLI and desktop requirements

### CLI

`python -m src.harmony.cli` должен принимать мелодию, тонику, лад, пути сохранения MusicXML/MIDI и возвращать exit code 0 при успехе.

### Desktop

Должны выполняться:

- single instance;
- повторный запуск активирует существующее окно;
- backend health wait;
- frontend SPA load;
- logs в `%LOCALAPPDATA%\HarmonyEngine\logs`;
- PyInstaller exe запускается без терминала.

---

## 6. Non-functional requirements

### NFR-1: Determinism

При одинаковом входе строгий путь возвращает тот же top-k ranking.

### NFR-2: Performance

Документированный baseline:

- 5-note phrase: примерно 330–350 ms;
- 16-measure phrase: примерно 1–2 s.

64-note phrase currently not guaranteed; known issue.

### NFR-3: Memory

Service cache ограничен 128 entries и 300 seconds TTL.

### NFR-4: Testability

Every public API contract должен покрываться существующими тестами: core, rules, syntax, solver, export, backend, desktop lifecycle.

### NFR-5: Documentation

Требуемые документы по AGENTS.md: `PROJECT_MAP.md`, `ARCHITECTURE.md`, `SPECIFICATION.md`, `DECISIONS.md`, `KNOWN_ISSUES.md`, `TASK_LOG.md`.

---

## 7. Acceptance criteria

Решение принимается, если:

1. `.venv\Scripts\python.exe -m pytest -q` завершается exit 0.
2. `.venv\Scripts\python.exe -m ruff check .` завершается exit 0.
3. `npm run build` в `frontend/` завершается exit 0.
4. REST endpoints не возвращают 500 для malformed import payloads.
5. Strict path не ослабляет hard rules без явного `relax_hard_gates`.
6. Grammar-derived whitelist не расходится с backend accepted chord symbols.
7. Grading assignment корректно по числу hard violations.
8. Documentation не содержит заведомо устаревших live-гейтов.

---

## 8. Verification commands

```powershell
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\python.exe -m ruff check .
npm run build
python scripts/grammar_metrics.py
python scripts/benchmark_harmonize.py
python scripts/stress_test_harness.py
```
