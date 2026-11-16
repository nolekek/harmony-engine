# DECISIONS.md — Brigade Harmony Engine

Формат записи: контекст → решение → последствия. Поле `Alternatives` приводится, когда рассматривались
существенные альтернативы; его отсутствие означает, что выбор был однозначным в рамках подтверждённого контракта.

---

## D-001. Pure Python symbolic solver вместо нейросетевого генератора

**Дата:** 2026-11-09  
**Контекст:** Нужна воспроизводимая гармонизация по строгим правилам Brigade.

**Alternatives:**

1. N-gram / ML генерация.
2. Constraint programming solver.
3. Grammar + Viterbi DP.

**Decision:** Выбрана связка `HarmonicGrammar + StateGenerator + ViterbiSolver`.

**Consequences:**

- плюсы: deterministic ranking, объяснимость, тесты, отсутствие C/ML runtime;
- минусы: качество сильно зависит от качества планов и survival rate plan generator;
- ML n-gram остаётся experimental stub, не production.

---

## D-002. Hard constraints как `+∞`, soft cost неотрицательна

**Дата:** 2026-11-09  
**Контекст:** Учебные правила нельзя заменять штрафами по умолчанию.

**Alternatives:**

1. Заменить hard rules крупными штрафами.
2. Отказываться даже в явном relaxed-режиме.
3. Разделить hard-feasibility и soft-стоимость.

**Decision:** В strict mode hard violation делает переход недопустимым; мягкая стоимость отдельно и всегда `>=0`.

**Consequences:**

- strict решение не «маскирует» нарушения дешёвой эвристикой;
- relaxed path возможен только по явного флага;
- тесты могут проверять отсутствие hidden relaxed-побед.

---

## D-003. Strict-first fallback к relaxed only через opt-in

**Дата:** 2026-11-14  
**Контекст:** Дефект #8 `[60,63,64,62,60]` требовал объяснимой неразрешимости, а не ослабления правила.

**Alternatives:**

1. Снизить penalty или изменить rule.
2. Возвращать невалидный результат.
3. Строгий отказ + diagnostics; отдельный relaxed escape.

**Decision:** Правило не ослабляется. Strict path возвращает отказ; relaxed path маркирует violations и `relaxed_rule_ids`.

**Consequences:**

- сохраняется учебная строгость;
- пользователь получает причину отказа;
- API-клиент обязан понимать diagnostics.

---

## D-004. Bounded replanning вместо неограниченного повторного поиска

**Дата:** 2026-11-12/13  
**Контекст:** План-генератор даёт низкую survival rate; UI нужен отказоустойчивый результат.

**Alternatives:**

1. Бесконечный retry.
2. Randomized plan restart.
3. Ограниченный replanning.

**Decision:** Replanning ограничен итерациями и временем; при исчерпании лимита возвращается честный отказ.

**Consequences:**

- плюсы: больше успешных ответов без hang;
- минусы: UI держится на replanning, это architectural debt;
- future: K-best / CP-SAT / diversification.

---

## D-005. Единый whitelist функций из grammar

**Дата:** волна 3, commit `7888455`, 2026-11-14  
**Контекст:** Backend `VALID_CHORD_FUNCTIONS` мог расходиться с grammar и давать ложные 422.

**Alternatives:**

1. Продолжить поддерживать отдельную ручную копию словаря.
2. Генерировать API-whitelist из grammar и добавить только явно легальные aliases.
3. Убрать historical aliases и сломать обратную совместимость.

**Decision:** Backend whitelist = `grammar.ALL_FUNCTIONS` union historical aliases.

**Consequences:**

- новые функции добавляются в одном месте;
- legacy aliases принимаются API, но не генерируются grammar;
- тесты должны контролировать расхождение grammar/API.

---

## D-006. Удалить monkey-patching

**Дата:** P1, commit `06c4437`, 2026-11-13  
**Контекст:** `doubling.py` перезаписывал chromatic functions на импорте; это ломало тестируемость и причинность.

**Alternatives:**

1. Оставить patch и документировать скрытый эффект импорта.
2. Перенести ответственную логику в `chromatic.py` и удалить патч.
3. Внедрить полный DI-контейнер для валидаторов.

**Decision:** Логика mode-aware false relation перенесена в `chromatic.py`; monkey patch удалён.

**Consequences:**

- поведение модулей явно;
- regression test проверяет отсутствие патча;
- меньше hidden side effects при import.

---

## D-007. Single source of truth для удвоения баса

**Дата:** волна 5, commit `fe8f942`, 2026-11-14  
**Контекст:** BASS_INVERSION_MISMATCH и FOREIGN_TONE требовали одинакового вычисления required bass pitch class.

**Alternatives:**

1. Держать отдельные реализации в state generator и rule engine.
2. Вынести общее вычисление в одну helper-функцию.
3. Переработать contracts solver и grader целиком.

**Decision:** Единая функция `required_bass_pc_for` используется state generator и rule engine.

**Consequences:**

- меньше расхождений solver vs grader;
- новые правила опираются на один контракт;
- изменение правила требует только одной правки.

---

## D-008. CADENCE_FINAL_VI_REQUIRES_DOMINANT

**Дата:** P1, commit `06c4437`  
**Контекст:** Финальный переход `T → VI` ошибочно принимался как легальный кадансовый оборот.

**Decision:** VI после T/T6/S/II/bVI запрещён как hard gate; разрешённые предшественники перечислены.

**Consequences:**

- короткие неразрешимые кадры возвращают `is_success=False`;
- поведение объявлено осознанным, не баг;
- grader выдаёт педагогический diagnostic.

---

## D-009. D43 бас трактуется как квинта доминанты

**Дата:** волна 5  
**Контекст:** Внешний аудит/ошибочный список ожидал трактовку, не совпадающую с HEAD-реализацией.

**Decision:** Для D43 baseline трактовка оставлена согласно internal rule и тесту `test_d43_d2`; внешние расхождения не применяются без цитаты учебника.

**Consequences:**

- защита от opportunistic fixes;
- KNOWN_ISSUES фиксирует внешний review mismatch;
- изменение требует явного user approval и источника.

---

## D-010. LRU + TTL кэш для гармонизации

**Дата:** волна 3, commit `7888455`  
**Контекст:** Growable request cache мог хранить полные response-payloads и вести к memory pressure.

**Alternatives:**

1. Убрать кэш целиком.
2. Оставить неограниченный кэш и наблюдать потребление памяти.
3. Ввести LRU с ограничением entries и TTL.

**Decision:** Кэш ограничен `CACHE_MAX_ENTRIES = 128`, TTL `CACHE_TTL_SEC = 300`.

**Consequences:**

- desktop/web repeated requests быстрее;
- память имеет верхнюю границу;
- TTL требует учитывать stale cache в dev.

---

## D-011. Import-file ошибки как 400, не 500

**Дата:** волна 3  
**Контекст:** Invalid base64/JSON/XML/MIDI мог вызывать internal server error.

**Alternatives:**

1. Пробрасывать исключения в generic global 500 handler.
2. Возвращать неструктурированный текстовый 400.
3. Валидировать input на границе и возвращать structured 400 detail.

**Decision:** Все malformed input paths возвращают structured 400 detail.

**Consequences:**

- API контракты стабильны;
- frontend/DAW clients лучше обрабатывают ошибки;
- OpenAPI/schema должен описывать error semantics.

---

## D-012. Desktop single instance через file lock, не named mutex

**Дата:** desktop wave, commit `29b5a5f`  
**Контекст:** Named mutex оставлялся занятым после force kill из-за handle inheritance; второй запуск не мог стартовать.

**Decision:** Эксклюзивный byte-range file lock + atomic instance state.

**Consequences:**

- stale lock снимается при смерти процесса;
- повторный запуск активирует существующее окно;
- desktop lifecycle тесты проверяют lock и discovery.

---

## D-013. Frontend как React SPA, backend как единственный источник правил

**Дата:** initial architecture  
**Контекст:** UI нужен интерактивный, правила — проверяемые и тестируемые.

**Alternatives:**

1. Реализовать правила отдельно в TypeScript для мгновенной проверки в UI.
2. Использовать server-rendered UI вместо SPA.
3. Оставить единый rule engine в Python-бэкенде для web и desktop.

**Decision:** React frontend вызывает REST backend; UI не дублирует rule engine.

**Consequences:**

- единая truth source правил;
- desktop и web используют один backend;
- UI-ошибки отдельно от solver-ошибок.

---

## D-014. Packaging mismatch не исправлять без отдельного approval

**Дата:** аудит 2026-11-13  
**Контекст:** `pyproject.toml` описывает package `harmony`, а код и README используют `src.harmony.*`.

**Alternatives:**

1. Немедленно переписать packaging и импорты.
2. Добавить path hacks, не меняя public package contract.
3. Зафиксировать расхождение и вынести исправление в отдельную approved wave.

**Decision:** Зафиксировать как KNOWN_ISSUES; не менять packaging в docs-wave без пользователя.

**Consequences:**

- installed wheel остаётся потенциально несовместимым;
- pytest path workaround работает;
- отдельная packaging wave нужна для fix.

---

## D-015. Docs wave: создать canonical governance docs и обновить stale counts

**Дата:** 2026-11-16  
**Контекст:** AGENTS.md требует полный набор типовых документов; live QA показал 901 passed, README и PROJECT_MAP содержали старые цифры.

**Decision:** Создать отсутствующие `ARCHITECTURE.md`, `SPECIFICATION.md`, `DECISIONS.md`, `KNOWN_ISSUES.md`, `TASK_LOG.md`; обновить factual status в `PROJECT_MAP.md` и `README.md`, не трогая code.

**Consequences:**

- документы становятся навигируемыми;
- Repomix body `PROJECT_MAP.md` остаётся историческим snapshot;
- дальнейшие изменения кода требуют docs sync.
