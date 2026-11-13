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
