# 🔴 Red Team Report — «Бригадное Ядро Гармонизации»

**Объект:** `D:\aitraining` (FastAPI + `src/harmony` + React/OSMD), живой сервис `http://127.0.0.1:8000`
**Дата:** 2026-11-10
**Режим:** red team, read-only аудит кода и поведения; приложение не менялось.
**Методика:** лид + 7 параллельных агентов (solver, rules, backend/grammar, frontend, theory, fuzz, architecture).
**Исходный симптом:** скриншот с `alert` «Все кандидаты отклонены жесткими правилами голосоведения», при этом на экране остаются старые кандидаты (#1 `T → S6 → D → T → D → T`, cost −7), кнопка висит в состоянии «Математический синтез (Viterbi)...».

---

## 0. TL;DR — если читать только один абзац

Это не «строгий Бригадный движок», а **генератор пустых квинт и унисонов**, который сам себе ставит «5 (Отлично)». Топ-1 «оптимум» содержит унисон тенора и баса `C3` (первый аккорд) и унисон сопрано/альта `C4` без терции (последний аккорд). Собственный `grader` на этом ставит **5/5, 0 нарушений**. Обычная нисходящая диатоника `C5-B4-A4-G4` и даже `C5…C4` получают «все кандидаты отклонены». Причина не в «сложной мелодии», а в архитектуре: нет слоя неаккордовых звуков, нет обязательной терции, нет честного K-best, нет единой модели метра, а правила в грамматике и в `RuleEngine` противоречат друг другу. 515 зелёных тестов проверяют в том числе то, что унисон — это «ок» (`tests/unit/test_spacing.py:62`). README врёт про 127 тестов, 24/24 и «Bi-GRU». Python API/CLI с дефолтным `max_plans=30` не гармонизуют даже дефолтную мелодию фронтенда — успех включается только на `max_plans=50`. Ниже — доказательства, теория и план лечения.

---

## 1. Как воспроизвести (без магии)

Все команды — из `D:\aitraining`, Python с установленными `fastapi/uvicorn/pytest` (системный `python`, не пустой `.venv`).

### 1.1. Дефолтная мелодия проходит (контроль)
```powershell
$body = @{
  melody = @(
    @{pitch=64; duration="half"; is_downbeat=$true},
    @{pitch=65; duration="half"; is_downbeat=$false},
    @{pitch=67; duration="half"; is_downbeat=$true},
    @{pitch=64; duration="half"; is_downbeat=$false},
    @{pitch=62; duration="half"; is_downbeat=$true},
    @{pitch=60; duration="whole"; is_downbeat=$false}
  )
  key=@{tonic="C";mode="Major"}; time_signature="4/4"; max_plans=50
} | ConvertTo-Json -Depth 6
Invoke-RestMethod -Uri 'http://127.0.0.1:8000/api/harmonize' -Method Post -ContentType 'application/json' -Body $body
```
Результат: `is_success=true`, 3 кандидата, ~405 мс. Значит баг не «всегда», а **input-dependent**.

### 1.2. Легальная 4-нотная мелодия — отказ
`C5 B4 A4 G4` (72,71,69,67), C-dur, 4/4:
```text
POST /api/harmonize → success=False, n=0
message="Все кандидаты отклонены жесткими правилами голосоведения."
```
Воспроизводится и ядром (`Harmonizer.harmonize`), и API. Минимальный отказ — всего три ноты: `C5-B4-A4` (72,71,69). Это ровно тот `alert`, что на скриншоте.
Причина: `B` — вводный тон; в сопрано он идёт вниз в `A`, а доминанта (единственная функция с `B` в словаре) обязана вести вводный тон вверх. В классике `B` гармонизуют `III` (E-moll) или `VII6`; в `grammar.ALL_FUNCTIONS` (`grammar.py:13-21`) **нет ни `III`, ни `VII6`, ни `VII`**. Это не «сложная мелодия» — это отсутствующий аккорд.

### 1.3. Ещё отказы на нормальной диатонике
| Мелодия (C-dur) | Результат |
|---|---|
| `C5 B4 A4 G4` | FAIL |
| `C5 B4 A4 G4 F4 E4 D4 C4` | FAIL |
| `C5 E4 F4 G4 C5` | FAIL |
| `A natural minor: A4 B4 C5 D5 E5 F5 G5 A5` | FAIL |
| `A melodic minor down: A5 G5 F5 E5 D5 C5 B4 A4` | FAIL |
| 16-нотная диатоника | FAIL (1.1 с) |
| `A melodic minor up` | OK (единственный спасшийся минорный сценарий) |

### 1.4. Топ-1 и его «оценка»
`POST /api/harmonize` (дефолт) → `best.voicings`:
```text
1: S=64 A=60 T=48 B=48   ← T=B унисон C3; квинты G нет
2: S=65 A=60 T=48 B=45
3: S=67 A=59 T=55 B=43
4: S=64 A=60 T=55 B=48
5: S=62 A=59 T=55 B=43
6: S=60 A=60 T=55 B=48   ← S=A унисон C4; терции E нет
```
`POST /api/grade` с этими voicings и chords:
```text
GRADE: 5 (Отлично / Без замечаний), hard=0, violations=[]
```
То есть **инспектор не видит ни унисонов, ни отсутствия терции**.

### 1.5. K64 в начале и снова «5»
Мелодия `C5 G4 E4 C4`:
```text
best.chords = ["K64","D","T","T"]
voicings = [(72,60,55,43),(67,59,55,43),(64,60,55,48),(60,60,55,48)]
grade = 5 (Отлично / Без замечаний)
```
Кадансовый квартсекстаккорд стоит **первым аккордом**, в нём нет терции, а в финале — S/A унисон. Для «консерваторского инспектора» это приговор.

### 1.6. «Топ-3» — не топ-3
Мелодия `[64,65,62,67]` (E-F-D-G), C-dur:
```text
first 3 successes: cost -2.0, -6.0, -6.0
global min among all 16 successful plans: -10.0  ["VI","II","II6","T"]
```
`backend/api.py:229` обрывает цикл после 3 успешных планов и только потом сортирует. Глобальный минимум не возвращается никогда.

### 1.7. API и ядро дают разные ответы на один и тот же вход
`C4 E4 G4 C5` (60,64,67,72):
```text
pipeline: OK, ["T","VI","T6","T"]
API:      FAIL, "Все кандидаты отклонены..."
```
Причина — `backend/api.py:142`:
```python
"is_downbeat": m.is_downbeat if m.is_downbeat else None
```
Явный `false` превращается в `None`, и `calculate_metric_structure` «додумывает» сильную долю. В ядре `false` уважается. Один и тот же JSON даёт разные планы.

### 1.8. Метр — декорация
`4/4`, `3/4`, `2/4`, `6/8`, `3/8` для одной и той же UI-мелодии дают **одинаковые** аккорды и **одинаковые** durations (`half,…,whole`). Причина не в `calculate_metric_structure` (он умеет 3/4/6/8), а в сквозной передаче: `MelodyInput` считает downbeats по 4/4 (`totalBeats % 4`), API превращает `false` в `None`, а `is_downbeat` дальше жёстко влияет на K64/грамматику. Итог: выбранный размер меняет только `<time>` в XML, а для 3/4 целая нота в конце даёт такт на 6 четвертей. Это баг **UI-контракта**, а не метрического калькулятора.

### 1.9. MusicXML: такт переполнен
Дефолтный результат, `measure` 3:
```text
voice1 total divisions = 24 (норма 16 для 4/4), backups = [24,24,24]
```
`src/harmony/export/musicxml.py` группирует ноты по накопленной длительности, но **не режет ноту на границе такта**. Итог: невалидный ритм в MusicXML.

### 1.10. Graded-байпас
`POST /api/grade` без `chords`:
```text
voicing (64,64,60,48), chords=["T"]  → grade 3, hard=1 (удвоена терция)
то же, chords omitted               → grade 5, hard=0
```
А chord `"V"` (стандартная римская цифра) вообще не распознаётся: C-dur аккорд с подписью `V` получает **5**, потому что `get_triad_tones("V")` молча возвращает тонику.

---

### 1.11. Что произошло на скриншоте (реконструкция)
Карточки `#1 T→S6→D→T→D→T (cost −7)` и `#2 … D6 … (cost −5)` — это **результат предыдущего успешного запуска** (дефолтная мелодия; API отдаёт ровно эти cost). Затем пользователь изменил мелодию/настройки (панель ввода выше кадра обрезана) и нажал «Гармонизовать». Новый запрос упал, `alert()` заблокировал поток, `finally` не успел снять `isHarmonizing`, поэтому кнопка осталась «Математический синтез (Viterbi)...», а старые кандидаты и партитура — на экране. Это не косметика: UI **не отличает «нет решения» от «старое решение»** и не показывает причину. Точная мелодия в кадр не попала, но любой из отказов §1.2–1.3 воспроизводит тот же сценарий.

### 1.12. Галка «Побочные доминанты» игнорируется
Мелодия `E4 F#4 G4 E4 D4 C4` (F# — хроматика), `allow_secondary_dominants=false`:
```text
POST /api/harmonize → 200, is_success=true
candidates[0].chords = ["T","DD7","D","T","D","T"]
```
`DD7` — это и есть побочная доминанта, которую пользователь только что запретил. Причина — `backend/api.py:159-167`:
```python
if not req.allow_secondary_dominants:
    ...
    plans_to_try = filtered_plans or all_plans   # если фильтр пуст — молча берём всё
```
Фильтр отсёк все планы (без DD эту мелодию движок не умеет), и настройка была тихо проигнорирована. Это не «edge case», это нарушение контракта API.

### 1.13. Тесты
```text
python -m pytest -q → 515 passed in 3.45s
```
README: «127 passed». Тесты **закрепляют** дефект:
- `tests/unit/test_spacing.py:62-63` считает `(60,60,48,48)` валидным;
- `tests/test_solver.py:20-34` проверяет только `>=`, `<=` и «прима удвоена», но не терцию/унисоны;
- «эталонный» корпус `tests/corpus/benchmark_tasks.py:32` содержит финальный аккорд `(60,60,55,48)` (S=A унисон, без терции), а `:57` — `(67,67,59,43)` (снова S=A). То есть тесты сверяются с эталоном, в котором уже есть тот самый дефект.

### 1.14. «Авто»-тональность уезжает на половинной каденции
`/api/detect-key` для `C D E F G` (C-dur, половинная каденция на V):
```text
→ G Major
```
`backend/key_detector.py:76-78` даёт +60 за последнюю ноту-тонику; для мелодии, кончающейся на доминанту, это перевешивает. Пользователь нажимает «Авто» — и гармонизация уходит в G-dur. Синтетический тест 24/24 это не ловит, потому что там все мелодии кончаются на тонике.

### 1.15. Дефолтный `Harmonizer` не гармонизует дефолтную мелодию
`Harmonizer.harmonize` по умолчанию `max_plans=30` (`pipeline.py:91`). Для мелодии из `frontend/src/App.tsx` (E-F-G-E-D-C, 6 нот):
```text
max_plans=30 → FAIL "All candidate plans were rejected by hard voice-leading constraints."
max_plans=40 → FAIL
max_plans=50 → OK ["T","S6","D","T","D","T"]
```
Первые **39** планов (все с `S` в основном виде) неразрешимы: на шаге `F4 → G4` бас `F → G` даёт железные параллельные октавы с сопрано, а альтернативный бас — запрещённый скачок. Живой план — `S6` (бас `A → G`) — стоит на позиции 40.
То есть Python API и CLI (`cli.py:87-88`, без `max_plans`) не могут гармонизовать **ровно ту мелодию, которую фронтенд показывает по умолчанию**. Фронт спасает только `max_plans: 50` (`App.tsx:95`). Это не «настройка качества», это скрытая зависимость успеха от количества эвристических планов: нужные планы (`S6`) стоят под номерами 40–43, а не в начале.

### 1.16. Стресс-харнесс
```text
python scripts/stress_test_harness.py --iter 1 --level 1 --seed 100
→ 20/24 (FAIL: D-dur, As-dur, cis-moll, es-moll; K64 на слабой доле)
```
README обещает 5 подряд 24/24. Харнесс сам использует `is_downbeat = idx % 2 == 0` (`scripts/stress_test_harness.py:148-150`) — ещё одно, шестое определение сильной доли.

---

### 1.17. Фаззинг: масштаб бедствия
Агентский фазз (`max_plans=30`, seed 42; `.redteam/evidence/category_stats.json`):
| Категория | Passed / Total | Fail % |
|---|---:|---:|
| control (дефолт) | 0/1 | 100% (из-за `max_plans=30`) |
| 24 major keys (scale/arpeggio/figure) | 22/42 | 47.6% |
| 24 minor keys | 22/42 | 47.6% |
| random diatonic (120) | 70/120 | 41.7% |
| NCT (8) | 7/8 | 12.5% (но «успех» — смена аккорда на каждой ноте) |
| chromatic (5) | 1/5 | 80% |
Почти все отказы — `LATTICE_BLOCKED_BY_HARD_RULES` на шагах `VI`, `D`, `T`, `T6`: это не «плохие мелодии», это систематическая несовместимость правил/словаря.

### 1.18. 108 из 108 «успешных» решений — музыкальный мусор с оценкой 5
Агент прогнал 108 успешных решений через тот же `/api/grade` (`.redteam/evidence/quality_audit.json`):
- **92.6%** (100/108) — унисон `S=A`;
- **20.4%** (22/108) — унисон `T=B`;
- **100%** (108/108) — неполные трезвучия (нет квинты или нет терции);
- **108/108** — `grade="5 (Отлично / Без замечаний)"`, `hard_violations_count=0`.
То есть «консерваторский инспектор» не просто слепой — он **систематически сертифицирует трёхголосные огрызки как эталон**.

## 2. Карта багов

| # | Severity | Где | Что сломано | Доказательство |
|---|---|---|---|---|
| 1 | **BLOCKER** | `solver/state_generator.py:88,137`; `rules/spacing.py:57-94`; `rules/doubling.py:101-175` | Унисоны соседних голосов и отсутствие терции не запрещены; топ-1 — 3-голосный кадавр | §1.4; `generate_candidate_voicings(64, T)` → `(64,60,48,48)`, `(64,60,60,60)` |
| 2 | **BLOCKER** | `solver/state_generator.py:88`; `rules/non_chord_tones.py` | Нет NCT: каждая нота сопрано обязана быть тоном аккорда; модуль NCT мёртв | §1.2; `C5-B4-A4-G4` → 0 планов |
| 3 | **BLOCKER** | `state_generator.py:99-105`; `resolutions.py:67-123` | `D43` смоделирован как `D2`: бас — септима F, а не квинта D | `bass pcs D43 = [5]`, `D2 = [5]`; канон: бас V4/3 = 2̂ (D) |
| 4 | **BLOCKER** | `backend/api.py:229`; `pipeline.py:160` | «Топ-3» = первые 3 успешных плана, не глобальный топ; 1-best на плане, не K-best | §1.6 |
| 5 | **BLOCKER** | `solver/viterbi.py:111-118`; `rules/engine.py:104-137`; `grammar.py:361-393` | Нет восстановления при недопустимости: fallback обходит финальную каденцию и метрику K64, затем solver отбрасывает | K64 первым; финал `S` в 12-нотной мелодии |
| 6 | **BLOCKER** | `rules/doubling.py:101-175`; `rules/spacing.py:57-94` | Нет проверки «терция обязательна»; нет запрета унисонов; `VII7` с удвоенным вводным тоном проходит | §1.4; `check_seventh_chord_doubling(VII7)` → `[]` |
| 7 | **BLOCKER** | `api.py:243`; `frontend/App.tsx:113-115` | Одна generic-ошибка на все причины; диагностика `SolverResult.message` выбрасывается; старые кандидаты не очищаются | §1.2, скриншот |
| 8 | **HIGH** | `core/types.py:426-499`; `export/musicxml.py:121-295` | Нет разрезания нот по тактам; нет валидации суммы такта; экспорт переполняет такты | §1.9 |
| 9 | **HIGH** | `api.py:142`; `pipeline.py`; `scripts/stress_test_harness.py:148-150`; `frontend/MelodyInput.tsx:97-106`; `grader.py:244` | Пять разных определений «сильной доли»; explicit `false` теряется | §1.7, §1.8 |
| 10 | **HIGH** | `doubling.py:101-175`; `get_triad_tones` | Нет проверки принадлежности всех голосов аккорду; неизвестная функция = тоника | §1.10; `V→(0,4,7)`, `III→(2,5,9)` |
| 11 | **HIGH** | `grammar.py:13-21`; `ALL_FUNCTIONS` | Нет `III`, `VII6`, `VII`, `II7`, `VII7`, `T64/S64`, обращений DD; заявленные правила VII7/II7 не генерируются | README §«Реализованные правила» vs `ALL_FUNCTIONS` |
| 12 | **HIGH** | `resolutions.py:21-64`; `grammar.py:146-208` | Дублирование и противоречие правил: `D43→T6/T` в грамматике vs только `T6` в движке; `D2→T6` vs `T` | §3.1 |
| 13 | **HIGH** | `frontend/App.tsx:75-121` | Нет `AbortController`/reqId; ответ старого запроса перетирает новый; `alert`; кнопка висит; старый score остаётся | скриншот |
| 14 | **HIGH** | `frontend/App.tsx:230-323` | Один общий `activeMusicXml/voicings/chords` на две вкладки; после grade гармонизатор показывает чужую партитуру | код |
| 15 | **HIGH** | `frontend/ExportBar.tsx:31,58-64` | Экспорт не передаёт `durations`; MIDI/XML получают все ноты как `half`; на вкладке grader нет `timeSignature` | §1.9; код |
| 16 | **HIGH** | `frontend/audio/synth.ts:215-218` | Плейбек считает каждый аккорд половиной (2 удара), игнорируя whole/dotted/метр | код |
| 17 | **HIGH** | `backend/grader.py:249-316` | Без `chords` все аккордовые правила пропускаются → grade 5; неверная римская цифра тоже пропускается | §1.10 |
| 18 | **HIGH** | `backend/key_detector.py:26-39,76-78`; `Key` | 24 «канонических» = 12 мажоров + 12 **гармонических** миноров; natural/melodic minor не поддержаны; половинная каденция на V уводит «Авто» в другую тональность | §1.3, §1.14; `C D E F G → G Major` |
| 19 | **HIGH** | `pyproject.toml:11`; `.venv` | `dependencies = []`; в `.venv` нет ни pytest, ни fastapi; проект запускается только на глобальном Python | `python -c "import fastapi"` в `.venv` → ModuleNotFoundError |
| 20 | **HIGH** | `README.md:234-262`; `scripts/stress_test_harness.py` | README: 127 тестов, 5×24/24, Bi-GRU. Факт: 515 тестов, harness 20/24, ML не подключён | §1.13, §1.16 |
| 21 | **HIGH** | `api.py:159-167` | `allow_secondary_dominants=false` при пустом фильтре молча берёт все планы; с F# выдаёт `DD7` | §1.12 |
| 22 | **MEDIUM** | `rules/voice_leading.py:79-130` | «Противоположные квинты» математически недостижимы при плавных шагах; `12→0` ложно трактуется как contrary octaves | §3.2 |
| 23 | **MEDIUM** | `rules/voice_leading.py:25-76` | Пропуск `ум.5→ч.5` (dim5→P5) — ложный negative | §3.2 |
| 24 | **MEDIUM** | `rules/voice_leading.py:265-337` | Не ловит ув.5 (8), ум.7 (9), ум.4 (4), два скачка подряд | §3.2 |
| 25 | **MEDIUM** | `rules/resolutions.py:21-64` | `D7→D65` с удержанием септимы блокируется, хотя это перестановка внутри доминанты | тест: delta 0/+2 → hard |
| 26 | **MEDIUM** | `rules/doubling.py:316-395` | `II6` без правила удвоения; `VII6` с удвоенным вводным тоном проходит | тест |
| 27 | **MEDIUM** | `rules/doubling.py:398-478` | Root-position `VII7` неполный (2 примы = 2 вводных тона) разрешён | тест |
| 28 | **MEDIUM** | `rules/engine.py:104-137` | `D→S` абсолютный запрет без метрики/цезур; в классике возможны проходящие/стыки предложений | §3.2 |
| 29 | **MEDIUM** | `export/musicxml.py:21-62` | Нет бемолей: Bb в F-dur пишется как `A#4` | тест |
| 30 | **MEDIUM** | `export/midi.py:52-57`; `exporters.py` | MIDI тоже получает дефолтные `half` от фронта | §1.9; код |
| 31 | **MEDIUM** | `frontend/ScoreDisplay.tsx:63-69` | При любом problem measure подсвечиваются **все** такты; обновление highlight не триггерится | код |
| 32 | **MEDIUM** | `frontend/ScoreDisplay.tsx:22-54` | Пустой `musicxml` не очищает старую партитуру; OSMD load race | код |
| 33 | **MEDIUM** | `frontend/MelodyInput.tsx:97-106` | Downbeat всегда считается по 4/4 (`%4`, offset 0/2); 3/4/6/8 игнорируются | код |
| 34 | **MEDIUM** | `frontend/ControlPanel.tsx:25,93-96` | API отдаёт `name`, фронт ждёт `title` → в селекте пустое имя, видно «(C мажор)» | скриншот + `/api/keys` |
| 35 | **MEDIUM** | `frontend/ControlPanel.tsx:82` | «24 канонических лада» — это 12 тональностей × 2 лада, а не 24 лада | текст |
| 36 | **MEDIUM** | `frontend/GraderPanel.tsx:92-100` | Не передаёт `time_signature`/`durations`; sample-задачи игнорируют свою тональность, берут текущую | код |
| 37 | **MEDIUM** | `backend/main.py:23-29` | CORS `*` + `allow_credentials=True` — невалидная комбинация; локальный сервис без лимитов | код |
| 38 | **MEDIUM** | `backend/api.py:44-50` | `max_plans`, длина мелодии, pitch не ограничены; `max_plans=10^6` → beam 4×10^6 | код |
| 39 | **LOW** | `frontend/ControlPanel.tsx:70-76` | Бейдж latency всегда «< 500 мс» | код |
| 40 | **LOW** | `frontend/src/App.tsx:329` | «И. И. Способин, И. В. Способин» — дубль и неверные инициалы | текст |
| 41 | **MEDIUM** | `rules/engine.py:53-72` | `docs/brigade_rules.json` грузится в `rules_registry`, но **ни одна проверка его не читает** — реестр декоративный | grep: `rules_registry` только запись |
| 42 | **MEDIUM** | `ml/model.py`; `models/style_weights.json` | «Bi-GRU / нейро-символический» скорер не подключён: `style_scorer=None` в pipeline; веса никто не загружает | grep: `StylePriorModel` только в тестах |
| 43 | **MEDIUM** | `run_app.py:39-45` | Порт 8000 фиксирован, нет проверки занятости; reload=False; нет graceful shutdown | код |
| 44 | **HIGH** | `pipeline.py:91`; `cli.py:87-88` | `Harmonizer`/CLI по умолчанию `max_plans=30` → дефолтная 6-нотная мелодия **не гармонизуется**; API спасает `max_plans=50` | §1.15 |
| 45 | **HIGH** | `grammar.py:395-408`; `api.py:229` | Успех зависит от порядка планов: нужные `S6`-планы стоят #40–43, ранние 30–39 отбраковываются; «топ» хрупок | §1.15 |
| 46 | **HIGH** | весь pipeline | 47% отказов на канонических мажорах/минорах, 42% на random diatonic; почти всё — hard-rule блокировки на `VI/D/T/T6` | §1.17 |
| 47 | **MEDIUM** | `voice_leading.py:25-76,133-171` | Параллели/скрытые 5/8 не знают про `prev_chord==curr_chord`: октавное перемещение одного и того же аккорда ложно режется | агентский `test_parallel.py` |
| 48 | **MEDIUM** | `doubling.py:177-212` | `check_k64_doubling` проверяет только «бас повторён», но не что бас = V ступень; K64 с басом C может пройти в grader | код |
| 49 | **MEDIUM** | `doubling.py:316-395` | Нет правил удвоения для `II6`/`VII6`; удвоенный вводный тон в `VII6` проходит | агентский тест |
| 50 | **HIGH** | `core/types.py:269-307`; `core/chord.py:21` | `parse_chord_symbol(ChordDefinition)` возвращает `"ChordFunction.T"`, и **все** проверки удвоения молча отключаются | `parse_chord_symbol(ChordDefinition(T)) → "ChordFunction.T"` |
| 51 | **MEDIUM** | `state_generator.py:99-105` | Ветка `"43"`/`"2"` для `II43`/`II2` тоже ставит F в бас (для `II43` нужен A, для `II2` — C) | код; грамматика пока не генерирует II7 |
| 52 | **MEDIUM** | `viterbi.py:35-37`; `docs/MATH_MODEL.md:102` | Заявлено `<10 ms`; фактические 15–173 мс (DP), 170–1077 мс (Harmonizer), 176–970 мс (HTTP) | `benchmark_results.json` |
| 53 | **MEDIUM** | `viterbi.py:127-145`; `engine.py:247-251` | Стоимость всех стартовых состояний `0.0`; нет штрафа за унисон/пустую квинту/дегенеративную фактуру | код |
| 54 | **MEDIUM** | `grammar.py:281-283` | «Закон» банит `S→D`, если сопрано идёт `1→2`, хотя параллельные октавы там даёт `4→5`; предикат не о том | `C E F G C`/`C D E F G C` → отказ |
| 55 | **BLOCKER** | `frontend/src/audio/midiInput.ts:121-141` | Новый `AudioContext` на **каждый** тик метронома → исчерпание аппаратных контекстов, краш вкладки, утечка | код |
| 56 | **HIGH** | `frontend/src/audio/midiInput.ts:114-117` | Запись MIDI считает сильную долю по `((beat-1)%4)+1` — снова хардкод 4/4 | код |
| 57 | **MEDIUM** | `frontend/src/App.tsx:12`; `dist/assets/index-B3v2zWUo.js` | OSMD весом >1 МБ в главном бандле; итог 1.65 МБ без code-splitting | размер файла |
| 58 | **LOW** | `frontend/src/components/ExportBar.tsx:43,76` | `revokeObjectURL` сразу после `a.click()` — в части браузеров скачивание обрывается | код |
| 59 | **BLOCKER** | `quality_audit.json` | 108/108 решений grader ставит 5; 92.6% содержат S=A, 20.4% T=B, 100% — неполные трезвучия | `.redteam/evidence/quality_audit.json` |
| 60 | **HIGH** | `grammar.py`; `resolutions.py` | Минимальный отказ — всего 3 ноты: `C5-B4-A4`; 8-нотная нисходящая гамма — 0/200 планов | `fuzz.md`; live API |
| 61 | **MEDIUM** | `backend/api.py:32-50`; `Key` | `{"tonic":"Z#","mode":"AlienMode"}` → HTTP 200, молча C-dur; нет валидации ключа | live API |
| 62 | **MEDIUM** | `backend/api.py:50` | `max_plans=0/-10` → HTTP 200 и 1 план; нет `ge=1, le=N` | live API |
| 63 | **HIGH** | `backend/main.py:23-29` | CORS `*` + credentials: `Origin: http://evil.com` отражается с `credentials: true` (CWE-942) | live API |
| 64 | **MEDIUM** | `backend/api.py` (все эндпоинты) | 0 строк логирования, нет exception handler; 500 без диагностики | grep |

## 3. Теория: где код врёт (с источниками)

### 3.1. `D43` — не терцквартаккорд, а второй секундаккорд
Канон: `V4/3` — бас — **квинта аккорда (2̂)**, разрешается в `I` (бас 2→1) или `I6` (2→3). `V2` — бас — **септима (4̂)**, разрешается в `I6` (4→3) [MIT chord table](https://web.stanford.edu/~kimth/www-mit/21M.301/chord_table.pdf), [Aldwell/Schachter](https://sfcm.edu/study/majors/academics/music-theory-and-musicianship/sfcm-theory/online-materials/harmony-supplements/aldwell-schachter-chapter-9).

Код:
```python
# state_generator.py:101-105
elif "43" in sym_clean:
    # Per Brigade D43 convention in this engine, 7th in bass
    required_bass_pc = (tonic_pc + 5) % 12   # F, а не D
```
Факт: `D43` и `D2` генерируют один и тот же бас `[5]` (F). `resolutions.py:67-123` требует `D43 → T6` с басом вниз, т.е. описывает `D2`. Настоящий `D43` (бас D) движок сгенерировать не может, а каноническое `D43 → T` объявляет ошибкой. Это **BLOCKER**.
Хуже: баг **закреплён тестами и документацией** — `tests/test_solver_fuzzing.py:372-376` прямо требует `D43` с септимой F в басу, `tests/test_rules.py:174-198` проверяет, что `D43 → T` невалиден, а `docs/MATH_MODEL.md:73-75` торжественно объявляет `B_{t-1} = IV` для `D43`. То есть 515 зелёных тестов и «математическая модель» — это не защита, а консервация ошибки.

### 3.2. Правила, которые либо мертвы, либо стреляют не туда
- **Contrary 5/8** (`voice_leading.py:79-130`): при плавных шагах `(|d1|+|d2|) ≤ 8 < 12`, поэтому условие `int_prev == int_curr` невыполнимо; проверка срабатывает только на взаимных скачках ≥ октавы. Плюс `%12` путает `12` и `0` — сход октавы в унисон противоположным движением ложно называется «противоположной октавой». В каноне такого отдельного запрета нет; либо удалить, либо переписать.
- **Parallel 5/8** (`voice_leading.py:25-76`): `ум.5 → ч.5` не ловится (сравнение `== 7`), хотя это классический запрещённый ход (dim5→P5) в похожем движении.
- **Hidden 5/8** (`voice_leading.py:133-170`): реализовано **правильно** — только S/B и скачок сопрано; это единственная теоретически чистая проверка в файле.
- **Melodic intervals** (`voice_leading.py:265-337`): нет ув.5 (8), ум.7 (9), ум.4 (4), двух скачков подряд; тритон (6) режется всегда, хотя ум.5 в басу иногда допустима. Слишком грубо и одновременно дыряво.
- **D→S** (`engine.py:104-115`): запрет на любом шаге, без учёта цезур; в упражнениях `D→S` действительно избегается, но на стыке предложений/в проходящем обороте это не абсолют. Как минимум нужен контекст «внутри фразы/на цезуре».
- **D7→D65** (`resolutions.py:21-64`): септима, удержанная при перестановке внутри доминанты, карается; это ложное срабатывание.
- **VII7 с удвоенным вводным тоном** (`doubling.py:398-478`): root-position incomplete разрешает 2 примы; для `VII7` прима = вводный тон → удвоение вводного тона. `check_seventh_chord_doubling` возвращает `[]` (проверено).
- **II6/VII6**: отдельных правил удвоения нет; `VII6` с удвоенным вводным тоном проходит.
- **NCT**: `non_chord_tones.py` не вызывается из `engine.py`/`state_generator.py`; `state_generator.py:88` требует, чтобы сопрано было тоном аккорда. Поэтому движок **не умеет держать один аккорд под проходящей/вспомогательной нотой**: он либо меняет гармонию на каждой ноте (`C-D-E` → `T-D-T`, что формально валидно, но гармонически бессмысленно), либо отказывает, если ни один аккорд из словаря не содержит ноту. Это архитектурный тупик, а не «строгость».

### 3.3. Унисоны и полнота
- «No unisons; octaves are ok» — [Michael Adduci, Rules for Traditional Four-Part Vocal Writing](https://michaeladduci.com/_files/ugd/57518d_6a952fc192934674a3974496b9e4954e.pdf).
- «Never omit the 3rd… The 5th may be omitted, but not in 2nd inversion or diminished chords» — [My Music Theory, SATB Doubling/Omissions](https://mymusictheory.com/satb-harmony/satb-doubling-omissions-spacing), [SFCM Harmony Supplement ch. 5](https://sfcm.edu/sites/default/files/sfcm-theory/harmony_supplements/chap_05/chap_05.pdf).
- Каденционная тоника может иметь утроенную приму и опущенную квинту — но **терция обязана быть** [Smith College cadences](https://sophia.smith.edu/~ratlas/mus31/4pg.pdf).

Код:
```python
# spacing.py:64,74,84
if s < a: ...   # равенство разрешено
if a < t: ...
if t < b: ...
```
```python
# doubling.py:142-172
if counts[third] >= 2: ...  # терцию нельзя удваивать
if counts[root] < 2: ...    # приму надо удвоить
# про наличие терции/квинты — ни слова
```
Итог: `(64,60,60,60)` — «T» с сопрано E и тремя C — проходит все проверки. `(60,60,55,48)` — «T» без терции — тоже.

### 3.4. K64
Канон: только на сильной/относительно сильной доле, удваивается бас (V), разрешается в D/D7; ходы 6→5 и 4→3 [Open Music Theory, cadential 6/4](https://pressbooks.nebraska.edu/openmusictheory/chapter/cadential-64). Код проверяет downbeat и удвоение баса, но:
- не запрещает K64 первым/ранним аккордом (пример §1.5);
- не требует терцию (K64 без E);
- `T64` через `parse_chord_symbol` превращается в `K64`, хотя проходящий T64 — не кадансовый;
- `is_downbeat` в разных слоях разный.

### 3.5. Диапазоны/тесситура
Стандарт S C4–A5, A G3–D5, T C3–G4, B E2–C4 — [Wikipedia, Four-part harmony](https://en.wikipedia.org/wiki/Four-part_harmony). `EXTENDED_VOICE_RANGES` опускает бас до C2 (36) — это уже октавист/профундо, а не учебный хор; для «строгого классического SATB» сомнительно. `T-B ≤ 24` (две октавы) — акустически пусто; в Бригаде обычно ≤ дуодецимы (19), но это вариативно, помечено как medium.

### 3.6. NCT
Проходящие/вспомогательные/задержания/предъёмы — [Milne, Nonharmonic Tones](https://milnepublishing.geneseo.edu/fundamentals-function-form/chapter/15-nonharmonic-tones); гармонизация мелодии с NCT держит один аккорд на 2–4 ноты — [Iowa State, Harmonizing a Melody with NCT](https://iastate.pressbooks.pub/comprehensivemusicianship/chapter/11-5-harmonizing-a-melody-with-non-chord-tones-theory-exercises). В коде этого слоя нет.

---

## 4. Почему архитектура обречена (а не «просто баги»)

### 4.1. Два независимых источника правил
`HarmonicGrammar.is_valid_syntax_transition` (`grammar.py:146-208`) и `RuleEngine.check_syntax` (`engine.py:74-137`) — **разные** реализации одних и тех же запретов. Они уже разошлись:
- `D43 → T6/T` в грамматике, `D43 → T6` в движке (`resolutions.py:90`).
- `D2 → T6` в грамматике, `D2 → T/T6` в движке (`resolutions.py:147`).
- Fallback 2 (`grammar.py:373-385`) обходит метрический фильтр K64, fallback 3 (`:387-393`) обходит финальную каденцию.
Планы генерируются под одними правилами, а валятся под другими. Отсюда «50 планов, 46 отказов».

### 4.2. «Viterbi» — это 1-best на плане, а не поиск по планам
- `grammar.generate_plans` — эвристический beam с ручными «законами» (`S→D` запрет по терциям, «root-to-third octave law» и т.п.). Это не ограничения голосоведения, а **костыли**, компенсирующие отсутствие полноты/унисонов.
- `ViterbiSolver.solve` — честный 1-best DP для **фиксированного** плана.
- `api.py` берёт первые 3 успешных плана. Глобального K-best нет.
- Стоимость: `contrary_bass_bonus = -5`, поэтому «оптимум» — это не «лучшая гармония», а «наибольшая сумма бонусов». Отрицательные cost в UI («−7») — прямое следствие.

### 4.3. Нет модели гармонического ритма
Один аккорд на каждую ноту сопрано. В классике один аккорд держится 2–4 ноты, а NCT — проходящие/вспомогательные. Без сегментации мелодии движок вынужден либо менять гармонию на каждой ноте, либо отказывать. Это корень «all candidates rejected» на нормальных мелодиях.

### 4.4. Нет единой модели метра
Шесть разных реализаций:
1. `frontend/MelodyInput.tsx:97-106` — `%4`, offset 0/2.
2. `backend/api.py:142` — explicit true, false → auto.
3. `core/types.calculate_metric_structure` — offset 0/2 в 4/4, 1.5 в 6/8.
4. `viterbi.py:68` — `i % 2 == 0` для int-мелодий.
5. `stress_test_harness.py:148-150` — `idx % 2 == 0`.
6. `grader.py:244` — снова `calculate_metric_structure`.
Плюс экспорт не режет такты. Неудивительно, что счётчик тактов и K64 не сходятся.

### 4.5. Две несовместимые модели аккорда
В проекте живут `core.types.Chord` и `core.chord.ChordDefinition`. `parse_chord_symbol` для второго делает `str(chord.function)`, а `ChordFunction` — это `str, Enum`, поэтому получается `"ChordFunction.T"`, а не `"T"`. Дальше `check_main_triad_doubling` (`doubling.py:112-114`) не находит `"ChordFunction.T"` в списке `("T","S","D",...)` и **молча возвращает пустой список**. Любой путь, где в валидатор попадает `ChordDefinition`, отключает проверки удвоения целиком. Это не «редкий тип», это вторая публичная модель аккорда в том же ядре.

### 4.6. Диагностика выброшена
`SolverResult.message` знает, на каком шаге и сколько кандидатов заблокировано (`viterbi.py:199-206`), но `api.py:243` возвращает одну строку. Пользователь не узнает, что «на шаге 3 аккорд D не имеет ни одного допустимого voicing из-за hidden octaves». Это не UX-мелочь, это невозможность отладки.

### 4.7. Нет K-best/релаксации
Если hard-ограничения несовместимы, правильный движок либо находит **лучшее приближение** с явным списком нарушений (MaxSAT/CP-SAT/weighted CSP), либо объясняет, какое ограничение снять. Здесь — пустой список и generic alert.

---

## 5. Целевая архитектура (что строить вместо)

```
Melody
  │
  ▼
[1] MelodyAnalyzer
    - барлайны/доли по выбранному метру
    - harmonic rhythm: сегменты по 1–4 ноты
    - NCT: passing / neighbor / suspension / anticipation
    - cadence points (полу/полная, прерванная)
  │
  ▼
[2] ChordLatticeBuilder
    - функции: T, T6, S, S6, S64, D, D6, D7, D65, D43, D2, K64,
      II, II6, II7, VII, VII6, VII7, VI, III, DD*, N...
    - инверсии/септаккорды, проверка тональности
    - сегмент = один аккорд; NCT допускаются поверх
  │
  ▼
[3] VoicingLatticeBuilder
    - полный набор hard constraints: диапазоны, порядок, унисоны,
      терция обязательна, удвоения, параллели/скрытые, разрешения,
      K64-позиция, каденция
    - общий валидатор для state gen / grader / API (один источник истины)
  │
  ▼
[4] KBestSearch
    - beam / K-best Viterbi по состояниям (аккорд + voicing)
    - hard = маска, soft = неотрицательная стоимость
    - хранить K лучших путей, а не 1
  │
  ├──> [5a] InfeasibilityExplainer: какой шаг, какие правила, сколько кандидатов
  └──> [5b] Relaxation (CP-SAT/MaxSAT): best-effort с явными violations
  │
  ▼
[6] ScoreModel (такты, длительности, голоса, функции)
  ├── MusicXMLRenderer (резать ноты по барлайнам, корректные бемоли)
  ├── MIDIRenderer (durations из модели)
  └── ASCIIRenderer
```

Инварианты:
- Все проверки — **чистые функции** над `(prev, curr, context)`; никакой мутации `rule_engine.allow_extended_ranges`.
- Один `HarmonizationService` для API и CLI/pipeline; никаких двух `harmonize`.
- Стоимость ≥ 0; hard-нарушения не «штраф 100000», а отсечение/недопустимость.
- Любой ответ API содержит `diagnostics`: `step`, `chord`, `candidates`, `blocked_by`, `suggested_fix`.

---

## 6. План лечения

### P0 — остановить кровь (1–2 дня)
1. **Полнота трезвучия**: в `state_generator`/`doubling` требовать `third_pc in pcs`; для `T/S/D` root doubled; fifth optional (но не в обращениях/уменьшённых). Добавить `CHORD_THIRD_MISSING`.
2. **Унисоны**: `S > A > T > B` (строго) в `spacing`; добавить `VOICE_UNISON`. Исключение — только если стиль явно разрешает (не в этом проекте).
3. **D43**: `required_bass_pc = fifth_pc`; разрешение `D43 → T` (бас 2→1) или `T6` (2→3); `D2 → T6` (4→3). Развести тесты.
4. **K64**: запретить первым/не в каденции; требовать терцию; разрешать только в D/D7; `T64` не мапить в K64.
5. **Топ-3**: убрать `break`; решить все планы, собрать успешные, `nsmallest(3)`; или K-best по состояниям.
6. **Ошибки**: возвращать `error.code`, `step`, `blocked_by`, `candidates`; фронт — inline banner, не `alert`; очищать старые candidates/score; `AbortController`.
7. **Экспорт**: передавать `best.durations` и `time_signature`; на вкладке grader — тоже; резать такты; тест «сумма такта == размер».
8. **Grader**: требовать `chords`; валидировать, что все pcs ∈ chord tones и терция присутствует; неизвестная функция → ошибка, не «тоника»; добавить унисоны/полноту.

### P1 — убрать architectural debt (3–5 дней)
9. **NCT/гармонический ритм**: сегментация, `non_chord_tones` в pipeline; один аккорд на сегмент; тесты на `C-D-E` над T.
10. **Словарь функций**: `III`, `VII6`, `VII7`, `II7`, обращения DD; исправить `get_triad_tones` (никакого fallback-тоники, `III` не должен парситься как `II`); поддержать римские цифры `I/IV/V`.
11. **Единый RuleSet**: `HarmonyContext` + `RuleEngine.validate_state/transition`; грамматика использует те же предикаты, без дублей; fallback не обходит метрику/каденцию.
12. **Метр**: один `MetricGrid` (bar/beat/offset) для solver/grader/export/frontend; explicit downbeat не терять; 3/4/6/8 тесты.
13. **Фронт**: `k.name` вместо `k.title`; `timeSignature`/`durations` в экспорт; `ScoreDisplay` — подсвечивать только проблемные такты; `AudioEngine` — длительности из `durations`; cleanup при unmount.

### P2 — доверие и качество (1–2 недели)
14. **K-best/CP-SAT**: честный beam/K-best; при infeasible — weighted relaxation и отчёт.
15. **Корпус**: реальные задачи Бригадного учебника (не самосгенерированные), golden SATB; property-тесты на каждый выход (нет унисонов, есть терция, нет параллелей, такт полный).
16. **Упаковка/CI**: `fastapi`, `uvicorn`, `pydantic`, `python-multipart`, `pytest`; lock; CI; `run_app` checks port.
17. **ML**: либо подключить `StylePriorModel` (и назвать честно «n-gram prior»), либо убрать «Bi-GRU» из README.
18. **Доки**: 515 тестов, реальный статус harness, никаких «0 косяков».

---

## 7. Конкретные патчи (эскизы)

### 7.1. Унисоны + полнота
```python
# rules/spacing.py
def check_voice_unisons(voicing):
    s, a, t, b = to_satb(voicing)
    out = []
    if s <= a or a <= t or t <= b:
        out.append(RuleViolation("VOICE_UNISON", "hard_gate", 1e5,
            "Adjacent voices must be strictly ordered; no unisons/crossing"))
    return out
```
```python
# rules/doubling.py
def check_triad_completeness(voicing, chord, key):
    sym = parse_chord_symbol(chord)
    if sym not in {"T","S","D","VI","II","III"}: return []
    root, third, fifth = get_triad_tones(sym, *parse_key(key))
    pcs = {p % 12 for p in to_satb(voicing)}
    out = []
    if third not in pcs:
        out.append(RuleViolation("CHORD_THIRD_MISSING", "hard_gate", 1e5,
            f"Triad {sym}: third PC {third} is absent"))
    if root not in pcs:
        out.append(RuleViolation("CHORD_ROOT_MISSING", "hard_gate", 1e5,
            f"Triad {sym}: root PC {root} is absent"))
    return out
```
Вызывать в `RuleEngine.validate`, в `state_generator` (фильтр кандидатов) и в `grader`.

### 7.2. D43
```python
elif "43" in sym_clean:
    required_bass_pc = fifth_pc          # V4/3: bass = 5th of chord (2̂)
```
```python
# resolutions.py: D43 -> T (bass down step) or T6 (bass up step); D2 -> T6 only
```
Синхронизировать `grammar.is_valid_syntax_transition`.

### 7.3. Топ-3
```python
solutions = []
for plan in plans_to_try:
    res = solver.solve(...)
    if res.is_success:
        solutions.append(build_candidate(res))
solutions.sort(key=lambda s: s["cost"])
return {"candidates": solutions[:3], ...}
```
Убрать `if len(solutions) >= 3: break`.

### 7.4. Ошибка с диагностикой
```python
return {
  "is_success": False,
  "candidates": [],
  "error": {
    "code": "NO_FEASIBLE_PLAN",
    "message": "Не удалось построить ни одного допустимого SATB-пути",
    "diagnostics": [d.__dict__ for d in last_diagnostics],
    "blocked_by": top_blocking_rules,
    "hint": "Проверьте диапазон сопрано/мелодию или включите расширенный диапазон"
  }
}
```

### 7.5. Фронт: без alert и без гонок
```tsx
const abortRef = useRef<AbortController | null>(null);
async function harmonize() {
  abortRef.current?.abort();
  const ac = new AbortController();
  abortRef.current = ac;
  setError(null); setCandidates([]); setSelectedCandidate(null);
  try {
    const resp = await fetch("/api/harmonize", { ..., signal: ac.signal });
    const data = await resp.json();
    if (!resp.ok || !data.is_success) throw new Error(data?.error?.message ?? data?.message);
    ...
  } catch (e) {
    if ((e as Error).name !== "AbortError") setError(String(e));
  }
}
```

### 7.6. Метр
```python
# один источник: (measure, offset, is_downbeat) по сетке
# note, пересекающая барлайн, режется на tied notes
# export группирует по measure из модели, а не по накоплению
```

---

## 8. Что проверять после починки

1. Для **каждого** кандидата: `S > A > T > B`; терция присутствует; все pcs принадлежат аккорду; нет параллельных 5/8; нет скрытых 5/8; K64 не первый и разрешается в D.
2. `pytest` + новый property-тест на 10 000 сгенерированных решений.
3. 24 тональности × 5 метров × 4 длины: доля отказов на **заведомо гармонизуемых** мелодиях = 0.
4. MusicXML: сумма `<duration>` в такте == `beats * divisions * 4 / beat_type`; MuseScore/OSMD открывают без переполнений.
5. `POST /api/grade`:
   - без `chords` → 400/422, не 5;
   - `V`/`I`/`IV` → корректная функция или 422;
   - унисон/нет терции → hard.
6. `POST /api/export/*` с `durations` из кандидата → ритм совпадает с экраном.
7. Harness: 5×24/24 с **тем же** определением downbeat, что у solver/grader.

---

## 9. Артефакты аудита

- [REPORT.md](.redteam/REPORT.md) — этот отчёт.
- [theory-research.md](.redteam/theory-research.md) — академический свод правил и расхождений (теоретик-агент).
- [rules-audit.md](.redteam/rules-audit.md) — детальный разбор `rules/*` (rules-агент).
- [solver-audit.md](.redteam/solver-audit.md) — солвер, унисоны, `D43`, типы (solver-агент).
- [frontend-audit.md](.redteam/frontend-audit.md) — React/OSMD/Audio/MIDI (frontend-агент).
- [architecture-audit.md](.redteam/architecture-audit.md) — архитектура, альтернативы, CP-SAT (arch-агент).
- [fuzz.md](.redteam/fuzz.md) — фаззинг, 108 решений, минимальные repro (fuzz-агент).
- [quality_audit.json](.redteam/evidence/quality_audit.json) — 92.6% S=A, 100% неполных трезвучий, 108/108 grade 5.
- [backend-audit.md](.redteam/backend-audit.md) — API, CORS, MusicXML, key/mode, max_plans (backend-агент).
- [category_stats.json](.redteam/evidence/category_stats.json) — агрегированные результаты фаззинга (47% отказов на канонических ладах).
- [core_fuzz_results.json](.redteam/evidence/core_fuzz_results.json) — сырые результаты по каждой мелодии.
- `D:\aitraining\.redteam\scratch\lead\` — скрипты лида, которыми воспроизведены §1.4–1.15.

Все семь агентских отчётов (solver, rules, backend, frontend, theory, fuzz, architecture) собраны; их ключевые факты перепроверены лидом.

## 10. Ограничения этого аудита

- Часть агентских отчётов (solver/rules/backend/frontend/arch/fuzz) может уточнить детали; базовые факты §1 воспроизведены лидом независимо.
- «Канон» местами вариативен (например, допустимость унисонов, `T-B` до двух октав, `D43→T` vs `T6`). В спорных местах это помечено; блокерами названы только однозначные расхождения.
- Я не менял код приложения; все патчи — эскизы. `.redteam/` и `scratch/` — артефакты аудита.

---

## 11. Источники (ключевые)

- [Hidden fifths/octaves — Music StackExchange](https://music.stackexchange.com/questions/58615/voice-leading-rule-hidden-fifths-octaves/58621)
- [Smith College, Cadences (hidden 5/8, doubling)](https://sophia.smith.edu/~ratlas/mus31/4pg.pdf)
- [Michael Adduci, Rules for Traditional Four-Part Vocal Writing](https://michaeladduci.com/_files/ugd/57518d_6a952fc192934674a3974496b9e4954e.pdf)
- [SFCM Harmony Supplement, ch. 5 (incomplete chords, never omit 3rd)](https://sfcm.edu/sites/default/files/sfcm-theory/harmony_supplements/chap_05/chap_05.pdf)
- [My Music Theory, SATB Doubling/Omissions/Spacing](https://mymusictheory.com/satb-harmony/satb-doubling-omissions-spacing)
- [Open Music Theory, Cadential 6/4](https://pressbooks.nebraska.edu/openmusictheory/chapter/cadential-64)
- [MIT 21M.301 chord table (V4/3 bass = 2)](https://web.stanford.edu/~kimth/www-mit/21M.301/chord_table.pdf)
- [Deceptive cadence doubling — Music StackExchange](https://music.stackexchange.com/a/118726)
- [LibreTexts, Objectionable Parallels](https://human.libretexts.org/Bookshelves/Music/Music_Theory/Music_Theory_for_the_21st-Century_Classroom_(Hutchinson)/26%3A_Voice_Leading_Triads/26.03%3A_Objectionable_Parallels)
- [Milne, Nonharmonic Tones](https://milnepublishing.geneseo.edu/fundamentals-function-form/chapter/15-nonharmonic-tones)
- [Iowa State, Harmonizing a Melody with NCT](https://iastate.pressbooks.pub/comprehensivemusicianship/chapter/11-5-harmonizing-a-melody-with-non-chord-tones-theory-exercises)
- [Wikipedia, Four-part harmony](https://en.wikipedia.org/wiki/Four-part_harmony)
- [Aldwell/Schachter, ch. 9 (V4/3, V4/2)](https://sfcm.edu/study/majors/academics/music-theory-and-musicianship/sfcm-theory/online-materials/harmony-supplements/aldwell-schachter-chapter-9)

---

**Вердикт:** движок не готов называться «консерваторским инспектором» и «строгой гармонизацией». Это прототип с сильной математической оболочкой и дырявой музыкальной семантикой. Пока не исправлены P0, любой зелёный тест — это тест на то, что баг воспроизводится стабильно.
