# HANDOFF — «Бригадное Ядро Гармонизации» (D:\aitraining)

> Точка входа для следующей сессии. Обновлено 2026-11-12 ~01:50 (Asia/Yekaterinburg).
> Полный план рефакторинга и статусы волн — [REMEDIATION_PLAN.md](REMEDIATION_PLAN.md).
> Независимый аудит критика — [scratch/critic/AUDIT.md](scratch/critic/AUDIT.md).
> Метрики выживаемости планов — [scratch/grammar_metrics/REPORT.md](scratch/grammar_metrics/REPORT.md).

## 1. Снимок состояния

| Параметр | Значение |
|---|---|
| Рабочая папка | `D:\aitraining` |
| Ветка | `redteam-p2` (remote: `https://github.com/nolekek/harmony-engine.git`) |
| Последний коммит | `0b2134e` + локальный коммит с `service.py` prefer-strict (см. git log) |
| Тесты | **824 собрано**, полный прогон `pytest -q` → exit 0 |
| Сервис | `http://127.0.0.1:8000` (backend/uvicorn, PID см. `Win32_Process`), `/api/health` → 200 |
| Python | `C:\Users\Admin\AppData\Local\Python\pythoncore-3.14-64\python.exe` |
| Node/фронт | `frontend/` React 19 + Vite; прод-сборка в `frontend/dist` (в .gitignore) |

## 2. Быстрый старт

```powershell
cd D:\aitraining

# тесты (обязательный гейт перед коммитом)
& 'C:\Users\Admin\AppData\Local\Python\pythoncore-3.14-64\python.exe' -m pytest -q

# скрипты из .redteam/scratch запускать с PYTHONPATH
$env:PYTHONPATH='D:\aitraining'

# приёмка волн (exit 0 = ок)
python .redteam/scratch/lead/verify_p0.py
python .redteam/scratch/lead/verify_p1.py
python .redteam/scratch/lead/verify_p2.py

# перезапуск сервиса (порт занят старым процессом — убить по PID)
Get-CimInstance Win32_Process -Filter "Name like '%python%'" |
  Where-Object { $_.CommandLine -like '*run_app.py*' } |
  ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
$env:PYTHONIOENCODING='utf-8'
Start-Process -FilePath 'C:\Users\Admin\AppData\Local\Python\pythoncore-3.14-64\python.exe' `
  -ArgumentList 'run_app.py','--port','8000','--no-browser' -WorkingDirectory 'D:\aitraining' `
  -WindowStyle Hidden -RedirectStandardOutput '.redteam\scratch\lead\server.out.log' `
  -RedirectStandardError '.redteam\scratch\lead\server.err.log'
# проверка: Invoke-WebRequest http://127.0.0.1:8000/api/health
```

**Важно:** системный `python` — единственный рабочий интерпретатор. `.venv` пустой/битый (задача T22),
`uv sync` не проверялся. `run_app.py` форсит UTF-8 на stdout — без этого cp1251 ломает логи.

## 3. Что сделано (сжато)

Волны P0/P1/P2 из плана закрыты: убраны униисоны и неполные трезвучия, канонический D43/D2/K64,
честный топ-3, структурные ошибки API (`error.code`, 422/400/413), NCT, MetricGrid, словарь
III/VII6/VII7/II7, Krumhansl-Schmuckler, единый `RuleEngine`, `HarmonizationService`, изоляция
вкладок фронта, MIDI Format 1, MusicXML с бемолями по `fifths`, OSMD в lazy-чанке.

Последний коммит `0b2134e`:
1. **Каденционные хард-гейты** — предпоследний аккорд обязан быть доминантой (D/D7/D65/D43/D2/D6/VII7)
   либо плагальной подготовкой S/II; `T6 → T` и финальный `VI` без доминанты запрещены;
   разрешён хроматический маршрут `N6 → VII7 → VI`.
2. **Фильтры грамматики по высотам сопрано** (`same_triad_scalar`, пары квинт корневых трезвучий,
   запреты S→D / D→T по высоте) переведены из `continue` в мягкие `-6.0` штрафы + счётчик
   `beam_starvations`; `is_valid_syntax_transition` обёрнут в `lru_cache(4096)`.
3. **Опциональные флаги решателя** `allow_adjacent_unisons` и `relax_hard_gates`
   (штраф 10000 за hard-нарушение, метаданные `relaxed_rule_ids` / `had_relaxed_violations`),
   прокинуты в pipeline, `HarmonizationService` и Pydantic-модель API.
   **Семантика: строгий план всегда предпочтительнее релаксации** — повторный strict-прогон
   в `Harmonizer.harmonize` и `HarmonizationService.harmonize`.
4. Новые тесты: `tests/test_final_approach.py` (20), `tests/test_relaxed_flags.py` (7),
   `tests/test_relaxed_modes.py`; `scripts/grammar_metrics.py`.

## 4. Метрики выживаемости планов (до/после снятия фильтров)

Отчёт: `.redteam/scratch/grammar_metrics/REPORT.md`, скрипт: `scripts/grammar_metrics.py`
(сравнивает текущую грамматику с сохранённым снапшотом `grammar_before.py`).

| Мелодия | Планов | Решено | Survival | NO_FEASIBLE | Harmonize |
|---|---:|---:|---:|---:|---|
| default (6) | 61 | 13 | 21.3% | 78.7% | PASSED |
| a-moll desc (8) | 61 | 0 | **0.0%** | 100% | PASSED (replanning) |
| 16-note scale | 60 | 27 | 45.0% | 55.0% | PASSED |
| 32-note arch | 60 | 0 | **0.0%** | 100% | PASSED (replanning) |
| chromatic 1 `[60,61,64,67,60]` | 60 | 4 | 6.7% | 93.3% | PASSED |
| chromatic 2 `[60,64,68,69,72,60]` | 60 | 3 | 5.0% | 95.0% | PASSED |
| chromatic 3 `[64,65,68,69]` | 12 | 1 | 8.3% | 91.7% | PASSED |
| chromatic 4 `[64,68,67,62,60]` | 61 | 0 | 0.0% | 100% | PASSED |
| chromatic 5 `[60,63,64,62,60]` | 61 | 0 | 0.0% | 100% | **FAILED** |
| same_triad `[60,64,62,60]` | 48→56 | 20→22 | 41.7→39.3% | 58.3→60.7% | PASSED |
| s_to_d_leap `[65,67,60]` | 20→23 | 5→6 | 25.0→26.1% | 75.0→73.9% | PASSED |

**Вывод:** сам по себе план-генератор выдаёт «жизнеспособный» план лишь в 0–45% случаев; всё, что
работает в UI, держится на bounded replanning. Это главный архитектурный долг: повышать survival
(диверсификация планов + K-best), а не наращивать репланнинг.

## 5. Открытые дефекты (из аудита критика, репро подтверждены Lead'ом)

Источник: `.redteam/scratch/critic/AUDIT.md`. Проверено вручную на текущем коде
(`.redteam/scratch/lead/repro_critic.py`):

| # | Дефект | Репро | Статус |
|---|---|---|---|
| 1 | Финальный аккорд жёстко T/VI/D при нетонической сопрано → мелодия, кончающаяся на IV ступени или альтерации, падает с 0 решений | `Harmonizer().harmonize([60,64,62,65], 'C Major').is_success` → **False** | OPEN, P0 |
| 2 | Финальный `T → VI` / `III → VI` как «прерванная каденция» (софт-штраф +15) — музыкальный мусор | `harmonize([60,62,64,65,67,69])` → `T,II6,T,S6,T,VI` | OPEN, P0 (частично: hard-гейт только после S/II) |
| 3 | Monkey-patching: `doubling.py` перезаписывает `chromatic.check_false_relation` и весь `validate_chromatic_rules` | `src/harmony/rules/doubling.py:21-65` | OPEN, P1 (архитектура) |
| 4 | Сопрано B3 (59) вне стандартного диапазона `(60,81)` → неаполитанский оборот `F4→Db4→B3→C4` падает | `harmonize([65,61,59,60])` → **False** | OPEN, P0 (одна строка) |
| 5 | Перфоманс: пороги тестов подняты (16 нот 1200→2500 мс, длинные 3000→6000 мс, replan timeout 2→10 с) вместо профилирования | `tests/test_long_lines.py` | OPEN, P1 |
| 6 | Мёртвый/декоративный код в `RuleEngine` | AUDIT §6 | OPEN, P2 |
| 7 | Незастаженный хак в рабочей копии — **снят**, всё в `0b2134e` | — | CLOSED |

Рекомендуемый порядок следующей волны:
1. **P0:** финальная каденция при нетонической/альтерированной сопрано — плагальный выход (S/II),
   либо явный `error.code = FINAL_DEGREE_UNSUPPORTED` вместо пустого списка кандидатов; правило
   `grammar.py:474, 491-496` + хард-гейты `RuleEngine`.
2. **P0:** B3 в стандартном диапазоне сопрано (`spacing.py:24-29`) + тест на `[65,61,59,60]`.
3. **P0:** запретить финальный `T → VI` / `III → VI`; прерванная каденция — только из доминанты.
4. **P1:** вынести уточнённую логику ложных перечений из `doubling.py` в `chromatic.py`,
   удалить monkey-patch; прогнать `tests/test_chromatic_layer.py`.
5. **P1:** профилирование генератора планов (цель — вернуть 1200 мс на 16 нотах), или честно
   задокументировать перф-бюджет.
6. **P1:** survival-метрики в CI (`scripts/grammar_metrics.py`), K-best Viterbi (P3-остаток).

## 6. Известные ограничения (не блокеры)

- Хроматика (N/bVI/альтерации) абсорбируется не полностью: `[60,63,64,62,60]` → отказ; поглощение ~86.7%.
- `brigade_rules.json` подключён, но часть правил всё ещё захардкожена в `RuleEngine`.
- Grader API принимает только канонические символы функций (римские `I/IV/V` нормализуются на входе парсера,
  но не в `GradeRequest`).
- UI-каталог тональностей: только 12 мажоров и 12 гармонических миноров (natural/melodic — P3).
- K-best/CP-SAT и «объяснение неразрешимости» — P3 (см. план, T24).

## 7. Грабли окружения и агентов (личный опыт, не повторять)

- **Диагностика pytest:** `Select-String -Pattern 'passed'` по выхлопу иногда не ловит строку итога
  (CR/цвет); надёжнее `pytest -q 2>&1 | Out-String` и смотреть хвост, либо опираться на `exit code 0`.
  Количество тестов: `pytest --co -q` и суммировать `file.py: N`.
- **Параллельные агенты ломают прогон:** правка `.py` во время `pytest` даёт ложные фейлы
  (`TypeError`, обрезанные импорты). Перед финальным прогоном дождаться тишины по mtime.
- **Субагенты:** после рестарта сессии их id мёртв (`active teammate ... not found`).
  Реестр и правила: `.redteam/agents/subagent_registry.json` (сначала reuse, иначе один агент на роль,
  максимум 3).
- **AgentTeams** (`agent_teams_*`) в этой сессии после перезапуска плагина исчез из инструментов;
  команда `harmony-critic` и её задачи восстановлению не подлежат — отчёт критика сохранён в git.
- **pwsh** в песочнице иногда падает по ACL; файловая политика сейчас `danger-full-access`.
- `run_app.py` убивать строго по PID из `Win32_Process` (иначе плодятся сервисы на 8000).
- Windows: `$env:PYTHONIOENCODING='utf-8'` для скриптов с русским выводом, иначе `UnicodeEncodeError`.

## 8. Что не доделано в последнем шаге

- `relax_hard_gates` на уровне сервиса теперь тоже предпочитает strict (правка в `service.py`),
  но соответствующий коммит/тест — в рабочем дереве; проверить `git status` при старте.
- Survival-метрики не интегрированы в CI, только ручной скрипт.
- 15-мелодийная сюита критика лежит в `.redteam/scratch/critic/test_audit_melodies.py` — её стоит
  превратить в честный параметризованный тест с фиксацией допустимого процента отказов.
