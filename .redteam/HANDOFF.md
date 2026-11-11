# HANDOFF — «Бригадное Ядро Гармонизации» (D:\aitraining)

> Точка входа для следующей сессии. Обновлено 2026-11-12 ~03:55 (Asia/Yekaterinburg) после волны P2-фиксов.
> Полный план рефакторинга и статусы волн — [REMEDIATION_PLAN.md](REMEDIATION_PLAN.md).
> Независимый аудит критика — [scratch/critic/AUDIT.md](scratch/critic/AUDIT.md).
> Метрики выживаемости планов: старый снапшот — [scratch/grammar_metrics/REPORT.md](scratch/grammar_metrics/REPORT.md),
> актуальные после P2-фиксов — [scratch/grammar_metrics/REPORT_P2_FIX.md](scratch/grammar_metrics/REPORT_P2_FIX.md).

> ⚠️ История: предыдущая версия этого файла врала (последний коммит `c6ef64d` вместо `cfbb8a0`,
> «824 теста» при другом состоянии, статусы дефектов #1/#4 как OPEN уже после фикса). Сверяйтесь с
> `git log -1` и реальным прогоном, а не с таблицами ниже, если они расходятся.

## 1. Снимок состояния (проверено)

| Параметр | Значение |
|---|---|
| Рабочая папка | `D:\aitraining` |
| Ветка | `master` (единственная рабочая; `redteam-p0/p1/p2` влиты и удалены локально и на origin) |
| Remote | `https://github.com/nolekek/harmony-engine.git` |
| Последний коммит | `814ca5f` — `fix(grammar,engine,pipeline): plagal last-resort final + auto-extended ranges` (запушен) |
| Тесты | **830 собрано/проходит**, `pytest -q` → exit 0 (базовые 824 + 6 новых) |
| Python | `C:\Users\Admin\AppData\Local\Python\pythoncore-3.14-64\python.exe` (единственный рабочий; `.venv` битый) |
| Node/фронт | `frontend/` React 19 + Vite; прод-сборка в `frontend/dist` (в .gitignore) |

## 2. Быстрый старт

```powershell
cd D:\aitraining

# тесты (обязательный гейт перед коммитом)
& 'C:\Users\Admin\AppData\Local\Python\pythoncore-3.14-64\python.exe' -m pytest -q

# скрипты из .redteam/scratch запускать с PYTHONPATH
$env:PYTHONPATH='D:\aitraining'
$env:PYTHONIOENCODING='utf-8'

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

Волны P0/P1/P2 закрыты: унисоны/неполные трезвучия, канонический D43/D2/K64, честный топ-3,
структурные ошибки API (`error.code`, 422/400/413), NCT, MetricGrid, словарь III/VII6/VII7/II7,
Krumhansl-Schmuckler, единый `RuleEngine`, `HarmonizationService`, изоляция вкладок фронта,
MIDI Format 1, MusicXML с бемолями по `fifths`, OSMD в lazy-чанке.

**Последняя волна (коммит `814ca5f`, сделана Lead+Coder+Critic через two-stage gate):**
1. **Плагальный last-resort финал** для нетонической сопрано. Раньше `harmonize([60,64,62,65])`
   (финал F4, IV ступень) отбивался в трёх слоях: `grammar.get_compatible_chords_for_pitch:122-128`
   → дубль фильтра в `generate_plans` → `engine.py:477-509` (финальный аккорд только root T/D/VI).
   Теперь: при пустом пуле разрешены root `S/s/II/ii`; `engine.py` даёт hard-gate только если
   pc сопрано покрывается T/D/VI, иначе soft-штраф (50 для S/s, 70 для II/ii); финальный `S/s`
   получает +12.0 в beam-скоринге, чтобы консонантный F-A-C выигрывал у уменьшённого ii (D-F-Ab).
2. **Та же мина в replanning:** `pipeline._replan:*` хардкодил финальные альтернативы ("D","d","VI","vi")
   в двух местах — синхронизировано с плагальным fallback, иначе репланнинг на IV-ступени слеп.
3. **B3 / суб-C4 сопрано:** вместо ломки `STANDARD_VOICE_RANGES` (роняет `tests/unit/test_spacing.py`)
   в `pipeline.harmonize` автоматически включается `allow_extended_ranges`, когда мелодия выходит
   за `[60,81]`; флаг прокинут в solver и `_replan`, в результате выставлен `auto_extended_ranges=True`.
4. **Две замены soprano-`continue` на штрафы −6.0:** VI после D при сопрано на корне VI (было по всей
   пьесе, не только в финале) и `D6/D65 → T` при скачке >2 вверх на V. `Fallback 3` больше не сустейнит
   аккорд, не содержащий финальную ноту сопрано (раньше рождал фантомный план `['T','T','D','D']`).
5. **Новые тесты:** `tests/test_plagal_final_and_ranges.py` (6 шт.) — финал S консонантен (F-A-C-F),
   B3-мелодия проходит с `auto_extended_ranges=True`, полукаденция остаётся на D, контракт
   `get_compatible_chords_for_pitch` и стандартные диапазоны не тронуты. Существующие тесты не менялись.
6. **Метрики:** корпус `scripts/grammar_metrics.py` расширен двумя мелодиями; отчёт
   `scratch/grammar_metrics/REPORT_P2_FIX.md`.

## 4. Метрики выживаемости планов (после P2-фиксов)

Полная таблица — [scratch/grammar_metrics/REPORT_P2_FIX.md](scratch/grammar_metrics/REPORT_P2_FIX.md).
Ключевое:

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
поэтому колонка survival для B3 остаётся 0 — сквозной `harmonize()` при этом PASSED. Это осознанный
артефакт измерения, а не регрессия.

**Вывод неизменен:** план-генератор сам по себе выдаёт жизнеспособный план редко; UI держится на
bounded replanning. Главный архитектурный долг — диверсификация планов / K-best Viterbi, а не
дальнейшее размягчение синтаксиса. Снятие двух soprano-фильтров дало ноль прироста survival на
корпусе (честный отрицательный результат: фильтры срабатывали редко, а горлышко было в финальных
каденционных фильтрах и отказе Viterbi по диапазонам).

## 5. Статусы дефектов (после 814ca5f)

| # | Дефект | Статус |
|---|---|---|
| 1 | Финальный аккорд жёстко T/VI/D при нетонической сопрано → 0 решений | **CLOSED** — плагальный last-resort S, `harmonize([60,64,62,65])` → True, финал F-A-C-F |
| 2 | Финальный `T -> VI` как «прерванная каденция» (софт +15) — музыкальный мусор | **OPEN** — `harmonize([60,62,64,65,67,69])` → `T,II6,T,S6,T,VI`; нужен hard-gate/больший штраф после T |
| 3 | Monkey-patching: `doubling.py:64-65` перезаписывает `chromatic.check_false_relation` и `validate_chromatic_rules` | **OPEN** (подтверждено) — архитектурный долг P1 |
| 4 | Сопрано B3 (59) вне диапазона → неаполитанский оборот падал | **CLOSED** — авто-включение extended, `auto_extended_ranges=True` |
| 5 | Перф-пороги тестов подняты (16 нот 2500 мс, 32/длинные 6000 мс) вместо профилирования | **OPEN** (подтверждено) — фактические тайминги: 16 нот ~157 мс, 32 ноты ~420 мс, 64 ноты ~942 мс |
| 6 | Мёртвый/декоративный код в `RuleEngine` | **OPEN** (не перепроверялось в этой волне) |
| 7 | Незастаженный хак в рабочей копии | **CLOSED** — дерево чистое, всё в коммитах |
| 8 | `chromatic 5` `[60,63,64,62,60]` → FAILED (`FALSE_RELATION_PERECHENIE`, тенор E3 vs альтерированное сопрано Eb4) | **OPEN** — вне скоупа P2-фиксов, нужен отдельный разбор |

## 5.1 Статус фиче-флагов (проверено в `cad006b`)

| Флаг | Дефолт | Где реализован | Семантика |
|---|---|---|---|
| `allow_adjacent_unisons` | `False` | `viterbi.py:72`, `pipeline.py:115,279`, `backend/service.py:68`, `backend/api.py:178` | thread-local `set_unisons_allowed`, снимает hard-`VOICE_UNISON` в state_generator; в API — opt-in |
| `relax_hard_gates` | `False` | `viterbi.py:73`, `pipeline.py:116,280`, `backend/service.py:69`, `backend/api.py:179` | last-resort escape hatch: hard-нарушение получает штраф 10000, метаданные `relaxed_rule_ids` / `had_relaxed_violations`; **строгий план всегда предпочтительнее релаксации** — повторный strict-прогон в `Harmonizer.harmonize` и `HarmonizationService` (`service.py:160` принудительно ставит `relax_hard_gates=False` для strict-прохода) |

Оба флага прокинуты до API и не включаются молча; `allow_extended_ranges` тоже `False` по умолчанию,
но с P2-фикса автоматически включается для мелодий вне `[60,81]` (факт виден в `auto_extended_ranges`).

## 6. Известные ограничения (не блокеры)

- Хроматика (N/bVI/альтерации) абсорбируется не полностью: `[60,63,64,62,60]` → отказ.
- `brigade_rules.json` подключён, но часть правил всё ещё захардкожена в `RuleEngine`.
- Grader API принимает только канонические символы функций.
- UI-каталог тональностей: 12 мажоров и 12 гармонических миноров (natural/melodic — P3).
- K-best/CP-SAT и «объяснение неразрешимости» — P3 (см. план, T24).
- Плагальный финал `S/s` — только last-resort и только для ступеней, физически не покрываемых
  T/D/VI (в мажоре это IV ступень и альтерации). В обычных каденциях он не выбирается (штраф 50/70 +
  hard-gate, если сопрано покрывается T/D/VI).

## 7. Грабли окружения и агентов (личный опыт, не повторять)

- **Диагностика pytest:** смотреть хвост `pytest -q` и опираться на exit code; `--co -q` для числа тестов.
- **Параллельные агенты ломают прогон:** правка `.py` во время `pytest` даёт ложные фейлы.
  На этой волне Coder и Critic работали строго последовательно (two-stage gate).
- **`agy_ask(mode="plan")` в этой сборке моста падает с `unknown error`** — используйте дефолтный режим
  и дисциплину «только чтение» в промпте; `agx`/agy model slug: `gemini-3.8-flash` (не `flash`).
- **Медленные модели:** high-effort прогон Critic ~9-10 мин, упирается в 15-минутный кап инструмента —
  длинный аудит дробить на два параллельных вызова.
- **`git status` после работы субагента проверять обязательно** — агент мог не заметить лишние правки.
- Windows: `$env:PYTHONIOENCODING='utf-8'` для скриптов с русским выводом, иначе `UnicodeEncodeError`.
- `run_app.py` убивать строго по PID из `Win32_Process` (иначе плодятся сервисы на 8000).

## 8. Что дальше (рекомендуемый порядок)

1. **P1:** закрыть дефект #2 — финальный `T -> VI` после тоники (hard-gate или штраф >> 15), тест на
   `harmonize([60,62,64,65,67,69])`; проверить, что легальная прерванная каденция `D -> VI` не задета.
2. **P1:** вынести уточнённую логику ложных перечений из `doubling.py` в `chromatic.py`, убрать
   monkey-patch (строки 64-65), прогнать `tests/test_chromatic_layer.py`.
3. **P1:** `chromatic 5` — разобрать `FALSE_RELATION_PERECHENIE` (почему отклоняется консонансный вариант).
4. **P1:** профилирование/честный перф-бюджет и возврат порогов тестов к 1200/3000 мс.
5. **P2:** K-best / диверсификация луча — главный драйвер survival (см. RFC-обсуждение в отчёте метрик).
6. **P2:** survival-метрики в CI (`scripts/grammar_metrics.py` уже готов, нужен job).
