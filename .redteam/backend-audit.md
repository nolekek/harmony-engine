# 🩸 Red-Team Audit Report: Backend, Harmonic Grammar & API Gateway
**Репозиторий:** `D:\aitraining`  
**Дата аудита:** 11.11.2026  
**Объект:** Бригадное Ядро Гармонизации SATB (FastAPI, CFG Grammar, Viterbi Solver, Grader, Exporters)

---

## 1. Краткий вердикт

Движок декларирует «0 косяков», «нейро-символический Bi-GRU» и «строгий Бригадный учебник», но на деле представляет собой хрупкую конструкцию с критическими дырами в музыкальной теории и программной архитектуре. В ядре перепутаны базовые обращения септаккордов (у D43 бас прописан на септиме вместо квинты, дублируя D2), тактовая сетка ломается на дефолтной мелодии (в такт 4/4 заталкивается 6 четвертей с `backup=24` и целой нотой на 3-й доле), 80% планов грамматики — мертворожденный мусор из-за параллельных октав в $S \to D$, а отбор «топ-3» тупо берет первые три попавшихся плана до ранжирования по стоимости. «Bi-GRU» оказался тривиальным счетчиком n-грамм со сглаживанием Лапласа, а валидация API пропускает марсианские тональности и отрицательные лимиты.

---

## 2. Сводный реестр находок

| ID | Уязвимость / Дефект | Файл:Строка | Severity |
|---|---|---|---|
| **BK-01** | Теоретический крах: D43 реализован с септимой в басу (путаница D43 и D2) | `src/harmony/solver/state_generator.py:101`, `src/harmony/rules/resolutions.py:75` | **BLOCKER** |
| **BK-02** | Дефолтный `Harmonizer` падает на канонической мелодии (мусорный префикс $S \to D$) | `src/harmony/pipeline.py:91`, `src/harmony/syntax/grammar.py:278` | **BLOCKER** |
| **BK-03** | Ломаная тактовая сетка MusicXML: 6 четвертей в 4/4, `backup=24`, баг `is_downbeat` | `src/harmony/core/types.py:471`, `backend/api.py:142`, `frontend/src/App.tsx:26` | **BLOCKER** |
| **BK-04** | Фальшивый «Топ-3»: ранний `break` до сортировки по стоимости Viterbi | `backend/api.py:229-233`, `src/harmony/pipeline.py:160` | **HIGH** |
| **BK-05** | Игнорирование флага `allow_secondary_dominants=false` через fallback | `backend/api.py:165` | **HIGH** |
| **BK-06** | Слепота API: уничтожение диагностики `SolverResult` и generic alert | `backend/api.py:189, 243` | **HIGH** |
| **BK-07** | Grader пропускает унисоны и отсутствие квинты, ставя «5» кривому решению | `src/harmony/rules/spacing.py:63`, `src/harmony/rules/doubling.py:159`, `backend/grader.py:324` | **HIGH** |
| **BK-08** | Дыры валидации API: мусорные тональности, `max_plans<=0`, читерство в `/grade` | `backend/api.py:44-70`, `src/harmony/core/types.py:122`, `backend/grader.py:300` | **HIGH** |
| **BK-09** | Небезопасная конфигурация CORS: `allow_origins=["*"]` + `allow_credentials=True` | `backend/main.py:24-29` | **HIGH** |
| **BK-10** | Ложные маркетинговые заявления: фейковый «Bi-GRU», устаревшие бейджи | `src/harmony/ml/model.py:18`, `README.md:3, 46` | **MEDIUM** |
| **BK-11** | Неполный каталог 24 тональностей, отсутствие Cis-dur/es-moll, ошибки детектора | `backend/key_detector.py:11-39, 77`, `FIFTHS_TABLE` | **MEDIUM** |
| **BK-12** | Архитектурная неспособность работать с неаккордовыми звуками (NCT) | `src/harmony/solver/state_generator.py:88` | **MEDIUM** |
| **BK-13** | Примитивный экспорт/импорт MIDI: Format 0, моноканал, потеря длительностей | `src/harmony/export/midi.py:88`, `backend/importers.py:373` | **LOW** |

---

## 3. Детальный разбор дефектов

### BK-01 [BLOCKER]: Теоретическая безграмотность: D43 реализован с септимой в басу (путаница D43 и D2)
- **Файл:Строка:** [`src/harmony/solver/state_generator.py:101-105`](file:///D:/aitraining/src/harmony/solver/state_generator.py#L101-L105), [`src/harmony/rules/resolutions.py:74-78`](file:///D:/aitraining/src/harmony/rules/resolutions.py#L74-L78)
- **Суть:** В классической гармонии (Бригадный учебник, гл. 27):
  - $D_7$ — прима в басу (V ступень).
  - $D_{65}$ (квинтсекстаккорд) — терция в басу (VII ступень).
  - $D_{43}$ (терцквартаккорд) — **КВИНТА В БАСУ (II ступень)**. Разрешается в $T_{53}$ с удвоением тоники или в $T_6$.
  - $D_2$ (секундаккорд) — **СЕПТИМА В БАСУ (IV ступень)**. Разрешается строго в $T_6$.
  В коде генератора состояний написано:
  ```python
  elif "43" in sym_clean:
      # Per Brigade D43 convention in this engine, 7th in bass
      required_bass_pc = (tonic_pc % 12) if sym_clean.startswith("DD") else (tonic_pc + 5) % 12
  elif sym_clean.endswith("2") or sym_clean in ("D2", "DD2", "II2", "VII2"):
      required_bass_pc = (tonic_pc % 12) if sym_clean.startswith("DD") else (tonic_pc + 5) % 12
  ```
  Автор приписал терцквартаккорду $D_{43}$ септиму в басу (`tonic_pc + 5` = IV ступень), сделав его математическим клоном секундаккорда $D_2$! В `resolutions.py:75` комментарий прямо подтверждает эту галлюцинацию: *"D43 has the seventh in the bass (scale degree IV). It MUST resolve strictly to T6..."*.
- **Доказательство:** В C-мажоре для $D_{43}$ генератор требует ноту `F` (IV ступень) в басу. Нота `D` (II ступень, квинта аккорда $G-B-D-F$) отвергается.
- **Как чинить:** Для $D_{43}$ бас обязан быть квинтой аккорда (`(tonic_pc + 2) % 12` в мажоре/миноре, для $DD_{43}$ — `(tonic_pc + 9) % 12`). Разрешение $D_{43}$ должно вести бас шагом вниз в $T$ (II $\to$ I) или шагом вверх в $T_6$ (II $\to$ III).

---

### BK-02 [BLOCKER]: Дефолтный пайплайн `Harmonizer` падает на стандартной мелодии из-за мусорных планов грамматики
- **Файл:Строка:** [`src/harmony/pipeline.py:91, 122`](file:///D:/aitraining/src/harmony/pipeline.py#L91), [`src/harmony/syntax/grammar.py:278-284`](file:///D:/aitraining/src/harmony/syntax/grammar.py#L278-L284)
- **Суть:** В базовом классе `Harmonizer.harmonize()` параметр `max_plans` равен 30. При гармонизации дефолтной мелодии учебника `E4, F4, G4, E4, D4, C4` грамматика генерирует первые 40 планов с гармонией $T \to S \to D$.
  На шаге 1 $\to$ 2 сопрано идет $F4 \to G4$ (IV $\to$ V ступень). В основном трезвучии $S$ бас стоит на IV ступени ($F$), а в основном трезвучии $D$ бас обязан идти на V ступень ($G$). Движение $F \to G$ одновременно в сопрано и басу физически порождает **параллельные октавы**!
  Грамматика содержит эвристику для сопрано $1 \to 2$ (`grammar.py:282`), но забыла про запрет $4 \to 5$ при $S \to D$. В итоге первые 40 планов — заведомо неразрешимый мусор, убиваемый Viterbi на шаге 2. Планы с секстаккордом $S_6 \to D$ появляются только начиная с 41-го места.
- **Доказательство:**
  Запуск скрипта `test_harmonizer_pipeline.py`:
  ```python
  from src.harmony.pipeline import Harmonizer
  res = Harmonizer().harmonize([64, 65, 67, 64, 62, 60], key="C Major")
  print(res.is_success, res.message)
  # Вывод: False All candidate plans were rejected by hard voice-leading constraints.
  ```
  При `max_plans=30` отсекаются все 30 планов, и движок возвращает полный отказ.
- **Как чинить:**
  1. В `grammar.py` запретить переход $S \to D$ в основных видах, если сопрано идет на секунду вверх из IV в V ступень:
     ```python
     if prev_fn in ("S", "s") and cand in ("D", "d", "D7"):
         if (notes[i-1].pitch % 12) == (tonic_pc + 5) % 12 and (notes[i].pitch % 12) == (tonic_pc + 7) % 12:
             continue
     ```
  2. Поднять дефолтный `max_plans` в `pipeline.py` минимум до 60.

---

### BK-03 [BLOCKER]: Рассинхрон тактовой сетки: 6 четвертей в 4/4, `backup=24`, баг `is_downbeat`
- **Файл:Строка:** [`src/harmony/core/types.py:471`](file:///D:/aitraining/src/harmony/core/types.py#L471), [`backend/api.py:142`](file:///D:/aitraining/backend/api.py#L142), [`frontend/src/App.tsx:26`](file:///D:/aitraining/frontend/src/App.tsx#L26)
- **Суть:**
  1. В `frontend/src/App.tsx` дефолтная мелодия `INITIAL_MELODY` содержит длительности: `half, half, half, half, half, whole` в размере 4/4.
     - Такт 1: 2 + 2 = 4 четверти (норма).
     - Такт 2: 2 + 2 = 4 четверти (норма).
     - Такт 3: 2 + 4 = **6 четвертей**! Целая нота падает на 3-ю долю такта.
  2. `calculate_metric_structure` проверяет переполнение такта только по условию `curr_offset >= 4.0 - 1e-4` в начале ноты. Поскольку 5-я нота начинается на оффсете 2.0, она заталкивается в такт 3. Итого такт 3 имеет длительность 6.0 четвертей (24 divisions).
  3. Экспортер MusicXML генерирует в 3-м такте `<type>whole</type>` (целую ноту) на 3-й доле и тег `<backup><duration>24</duration></backup>`. В нотаторах (MuseScore, Sibelius) и в OSMD на фронтенде это вызывает визуальный разрыв сетки тактов.
  4. В `backend/api.py:142` допущен глупейший баг проброса метрики:
     `"is_downbeat": m.is_downbeat if m.is_downbeat else None`
     Если клиент передал `is_downbeat: False`, тернарный оператор превращает `False` в `None`. Затем `calculate_metric_structure` видит `None` и вычисляет `is_downbeat` по формуле оффсета, где для 4/4 оффсет 2.0 считается сильной долей! В итоге **все половинные ноты в 4/4 принудительно получают `is_downbeat: True`**, полностью отключая метрический контроль кадансового квартсекстаккорда K64!
- **Доказательство:**
  Вывод `test_metric_xml.py`:
  ```
  Measure 3: notes=8, durations=['8', '16', '8', '16'], types=['half', 'whole', 'half', 'whole'], backups=['24', '24', '24']
  ```
- **Как чинить:**
  - В `backend/api.py:142`: пробрасывать булево значение напрямую без зануления: `"is_downbeat": m.is_downbeat`.
  - В `calculate_metric_structure`: валидировать сумму длительностей в такте. Если нота пересекает тактовую черту, либо дробить ее лигой (tie), либо выбрасывать ошибку валидации 400 Bad Request.
  - В `frontend/src/App.tsx`: исправить последнюю ноту на `half` или предпоследнюю на `whole`.

---

### BK-04 [HIGH]: Ложный «Топ-3»: ранний `break` до сортировки по стоимости Viterbi
- **Файл:Строка:** [`backend/api.py:229-233`](file:///D:/aitraining/backend/api.py#L229-L233), [`src/harmony/pipeline.py:160`](file:///D:/aitraining/pipeline.py#L160)
- **Суть:** В цикле перебора синтезированных планов стоит проверка:
  ```python
  if len(solutions) >= 3:
      break
  # Sort solutions by ascending cost
  solutions.sort(key=lambda s: s["cost"])
  ```
  Бэкенд прерывает перебор, как только накопил **первые три попавшихся** успешных плана. Сортировка `solutions.sort()` применяется постфактум ТОЛЬКО к этой тройке! Если 4-й или 10-й план имел стоимость `-15.0` (идеальное голосоведение), а первые три имели стоимость `+40.0`, `+50.0`, `+60.0`, то лучшее решение никогда не будет вычислено. Называть результат «топ-3 математически оптимальных решений» — чистый обман пользователя.
- **Доказательство:** При генерации 50 планов планы оцениваются строго в порядке выдачи генератором, а не по глобальной функции стоимости.
- **Как чинить:**
  Использовать очередь с приоритетом (min-heap / `heapq`) размера $K=3$ по всей совокупности допустимых планов, либо оценивать все синтезированные планы (их всего 30-50, Viterbi занимает < 1 мс на план) и брать `sorted(solutions, key=...)[:3]`.

---

### BK-05 [HIGH]: Игнорирование настройки `allow_secondary_dominants=false`
- **Файл:Строка:** [`backend/api.py:165`](file:///D:/aitraining/backend/api.py#L165)
- **Суть:** В коде фильтрации побочных доминант:
  ```python
  if not req.allow_secondary_dominants:
      filtered_plans = []
      for plan in all_plans:
          fns = [c.function for c in plan]
          if not any(f.startswith("DD") for f in fns):
              filtered_plans.append(plan)
      plans_to_try = filtered_plans or all_plans
  ```
  Конструкция `plans_to_try = filtered_plans or all_plans` означает: если пользователь снял чекбокс «Побочные доминанты», но грамматика сгенерировала только планы с $DD$ (например, на мелодии с альтерацией $\#IV$), бэкенд молча забивает на запрет пользователя и скармливает солверу `all_plans`!
- **Доказательство:**
  Вызов API с хроматической нотой $F\#4$ (pitch 66) в C-dur и `allow_secondary_dominants: false`:
  ```bash
  POST /api/harmonize -> {"allow_secondary_dominants": false, "melody": [64, 66, 67, 64, 62, 60]}
  Ответ: is_success: true, candidates: [['T', 'DD7', 'D', 'T', 'D', 'T']]
  ```
  В ответе клиенту вернулись аккорды $DD7$, несмотря на явный запрет.
- **Как чинить:**
  Заменить fallback на честную ошибку:
  ```python
  plans_to_try = filtered_plans
  if not plans_to_try:
      return {
          "is_success": False,
          "candidates": [],
          "message": "Без побочных доминант невозможно гармонизовать заданную мелодию.",
      }
  ```

---

### BK-06 [HIGH]: Слепота API: уничтожение диагностики `SolverResult` и generic alert
- **Файл:Строка:** [`backend/api.py:189, 243`](file:///D:/aitraining/backend/api.py#L189), [`frontend/src/App.tsx:114`](file:///D:/aitraining/frontend/src/App.tsx#L114)
- **Суть:** Объект `SolverResult` в Viterbi формирует богатейшую пошаговую диагностику: на каком шаге $t$, для какого аккорда, сколько кандидатов было найдено и какое именно правило заблокировало переходы (`res.message`, `res.diagnostics`).
  В `backend/api.py` при `not res.is_success` вся диагностика выбрасывается в мусорку. В финальном JSON возвращается дежурная заглушка:
  `"message": "Все кандидаты отклонены жесткими правилами голосоведения."`
  Фронтенд вешает браузер модальным `alert()`, не очищая старые кандидаты. Пользователь видит старую партитуру, зависшую кнопку «Синтез...» и не понимает, в каком такте и почему произошел сбой.
- **Доказательство:** Воспроизведено на живом API `http://127.0.0.1:8000/api/harmonize`.
- **Как чинить:** Возвращать в ответе поле `"diagnostics": [{"step": t, "chord": fn, "error": res.message}]`, а на фронтенде отображать внятный баннер с указанием проблемной ноты.

---

### BK-07 [HIGH]: Grader пропускает унисоны и отсутствие квинты, ставя «5» дефектному решению
- **Файл:Строка:** [`src/harmony/rules/spacing.py:63`](file:///D:/aitraining/src/harmony/rules/spacing.py#L63), [`src/harmony/rules/doubling.py:159`](file:///D:/aitraining/src/harmony/rules/doubling.py#L159), [`backend/grader.py:324`](file:///D:/aitraining/backend/grader.py#L324)
- **Суть:**
  1. В `spacing.py` проверка перекрещивания `check_voice_crossing` использует нестрогие неравенства: `if s < a: ... if a < t: ... if t < b: ...`. УНИСОНЫ СОСЕДНИХ ГОЛОСОВ ($S=A$, $A=T$, $T=B$) РАЗРЕШЕНЫ.
  2. В `doubling.py` проверка `check_main_triad_doubling` проверяет `counts[root] >= 2` и `counts[third] < 2`, но ВООБЩЕ НЕ ПРОВЕРЯЕТ НАЛИЧИЕ КВИНТЫ (`counts[fifth]`).
  3. В результате Топ-1 решение движка для дефолтной мелодии содержит:
     - Такт 1: $S=64 (E4), A=60 (C4), T=48 (C3), B=48 (C3)$. **Унисон тенора и баса**, квинта $G$ отсутствует напрочь (три тоники и одна терция в начальном аккорде построения!).
     - Финальный аккорд: $S=60 (C4), A=60 (C4), T=55 (G3), B=48 (C3)$. **Унисон сопрано и альта**.
  4. При отправке этого Топ-1 кандидата в инспектор `/api/grade` Grader радостно рапортует:
     `Grade: "5 (Отлично / Без замечаний)"`, `Verdict: "Безупречное голосоведение!"`, `hard_violations: 0`.
- **Доказательство:** Скрипт `test_grade_top1.py` подтвердил получение оценки «5» на партитуре с пустыми унисонами.
- **Как чинить:**
  - В `spacing.py` запретить унисоны между соседними голосами (кроме финального аккорда или явных разрешений): `if s <= a: ...`.
  - В `doubling.py` для полных трезвучий требовать `counts[fifth] >= 1`. Неполные трезвучия (без квинты с утроенной примой) разрешать только в заключительной тонике.

---

### BK-08 [HIGH]: Дыры валидации API: мусорные тональности, `max_plans<=0`, читерство в `/grade`
- **Файл:Строка:** [`backend/api.py:44-70`](file:///D:/aitraining/backend/api.py#L44-L70), [`src/harmony/core/types.py:122`](file:///D:/aitraining/src/harmony/core/types.py#L122), [`backend/grader.py:300`](file:///D:/aitraining/backend/grader.py#L300)
- **Суть:**
  1. `KeyRequest` не валидирует тональность. Если передать `{"tonic": "Z#", "mode": "AlienMode"}`, метод `Key.parse` молча возвращает тонику C и лад Major. API отвечает HTTP 200 и генерирует C-мажор.
  2. `HarmonizeRequest.max_plans` не имеет валидации `Field(ge=1, le=100)`. Запросы с `max_plans: 0` или `max_plans: -10` возвращают HTTP 200, порождая 1 кандидат из-за `max(max_plans * 4, 16)` в beam search.
  3. В эндпоинте `/api/grade` отсутствует проверка равенства длин массивов `voicings` и `chords`. Если передать 6 аккордов и 1 символ функции `chords: ["T"]`, то для остальных 5 аккордов `curr_chord` становится `None`, отключая все функциональные проверки удвоений и разрешений. Любое студенческое решение получает оценку «5».
  4. Отсутствует ограничение на длину массива `melody`. Отправка мелодии из 10 000 нот повесит Viterbi и сожрет память воркера (DoS).
- **Доказательство:** Вывод `test_api_edge_cases.py` показал HTTP 200 на всех некорректных пейлоадах.
- **Как чинить:** Добавить жесткую Pydantic-валидацию полей: `Field(ge=1, le=100)`, проверку тональностей по белому списку, проверку `len(voicings) == len(chords)` в `/grade`.

---

### BK-09 [HIGH]: Небезопасная конфигурация CORS: `allow_origins=["*"]` + `allow_credentials=True`
- **Файл:Строка:** [`backend/main.py:24-29`](file:///D:/aitraining/backend/main.py#L24-L29)
- **Суть:**
  ```python
  app.add_middleware(
      CORSMiddleware,
      allow_origins=["*"],
      allow_credentials=True,
      allow_methods=["*"],
      allow_headers=["*"],
  )
  ```
  В спецификации W3C CORS и реализации Starlette комбинация `allow_origins=["*"]` и `allow_credentials=True` заставляет middleware динамически отражать любой заголовок `Origin`, присланный клиентом. Запрос с заголовком `Origin: http://evil.com` получает ответ:
  `access-control-allow-origin: http://evil.com`  
  `access-control-allow-credentials: true`  
  Это классическая уязвимость CWE-942, позволяющая сторонним сайтам красть данные и слать аутентифицированные запросы в локальный сервис.
- **Доказательство:** Проверено запросом к `/api/health` с `Origin: http://evil.com`.
- **Как чинить:** Задать строгий белый список доверенных источников: `allow_origins=["http://127.0.0.1:8000", "http://localhost:5173"]`.

---

### BK-10 [MEDIUM]: Маркетинговые мифы: фейковый «Bi-GRU», устаревшие бейджи
- **Файл:Строка:** [`src/harmony/ml/model.py:18-55`](file:///D:/aitraining/src/harmony/ml/model.py#L18-L55), [`README.md:3, 46`](file:///D:/aitraining/README.md#L3)
- **Суть:** В README на самом видном месте красуется:
  - *«Soft Cost / Style Priors: Bi-GRU нейро-символический оценщик стиля (models/style_weights.json)»*
  - Бейджик *«pytest 127 passed»*.
  По факту:
  1. В `src/harmony/ml/model.py` класс `StylePriorModel` — это **150 строк чистого Python со словарем `dict[str, int]`**, считающим n-граммы перемещений 4 голосов и логарифмирующим их вероятность по формуле Лапласа. Никакого PyTorch, нейросетей, рекуррентных слоев и тем более «Bi-GRU» в проекте НЕТ.
  2. В репозитории уже 515 тестов, а бейджик «127 passed» захардкожен вручную в markdown.
- **Доказательство:** Инспекция `src/harmony/ml/model.py` и вывод `pytest` (515 passed).
- **Как чинить:** Удалить ложные термины «Bi-GRU» и «нейро-символический» из документации, заменив на честное «n-gram statistical style prior». Обновить бейджики на динамические.

---

### BK-11 [MEDIUM]: Неполный каталог 24 тональностей, отсутствие Cis-dur/es-moll, ошибки автодетектора
- **Файл:Строка:** [`backend/key_detector.py:11-39, 77`](file:///D:/aitraining/backend/key_detector.py#L11-L39), [`src/harmony/export/musicxml.py:24-35`](file:///D:/aitraining/src/harmony/export/musicxml.py#L24-L35)
- **Суть:**
  1. В `CANONICAL_KEYS` включено 24 тональности, но выборка сделана безграмотно: включен Ре-диез минор (dis-moll, 6 диезов), но полностью отсутствует Ми-бемоль минор (es-moll, 6 бемолей) — одна из самых употребительных тональностей романтической литературы (Шопен, Брамс). В мажорах есть Des-dur, но нет Cis-dur.
  2. UI и документация называют этот список «24 канонических лада». В музыковедении мажор и минор — это лады (их 2 основных), а 24 — это тональности кварто-квинтового круга.
  3. В `detect_key_from_melody` за совпадение последней ноты с тоникой начисляется гигантский бонус (+60 очков). Мелодия в До-мажоре с половинным кадансом, оканчивающаяся на ноту Соль (`C D E F G`), безапелляционно определяется алгоритмом как Соль-мажор.
- **Доказательство:** Запуск `test_key_detector.py`.
- **Как чинить:** Расширить каталог тональностей до полных 30 энгармонических пар (с Cis/Des, Fis/Ges, H/Ces, dis/es, gis/as, ais/b). В детекторе учитывать вес гармонического кадансового оборота, а не только последнюю ноту.

---

### BK-12 [MEDIUM]: Полная неспособность работать с неаккордовыми звуками (NCT)
- **Файл:Строка:** [`src/harmony/solver/state_generator.py:88`](file:///D:/aitraining/src/harmony/solver/state_generator.py#L88)
- **Суть:** Строка `if soprano_pitch % 12 not in allowed_pcs: return []` требует, чтобы абсолютно каждая нота сопрано являлась аккордовым тоном вертикали. Если в мелодии на слабой доле встречается проходящий звук (passing tone), задержание (suspension) или вспомогательный звук (auxiliary), движок либо крашится с ошибкой «No candidate voicings found», либо пытается натянуть на проходящую ноту бессмысленный диссонирующий аккорд, ломая гармонический ритм.
- **Как чинить:** Ввести классификацию метрических нот: сильные доли гармонизовать аккордами, слабые доли с плавным поступенным движением помечать как NCT без смены гармонии.

---

### BK-13 [LOW]: Примитивный экспорт и импорт MIDI: моноканал, потеря длительностей
- **Файл:Строка:** [`src/harmony/export/midi.py:88`](file:///D:/aitraining/src/harmony/export/midi.py#L88), [`backend/importers.py:373`](file:///D:/aitraining/backend/importers.py#L373)
- **Суть:**
  1. В `src/harmony/export/midi.py` все 4 голоса SATB записываются на один канал 0 (`0x90`) в один трек (MIDI Format 0). В секвенсорах (Reaper, Cubase, Logic) голоса сливаются в один неразделимый аккордовый поток.
  2. В `backend/importers.py:373` при импорте MIDI длительность каждой ноты тупо хардкодится как `"half"`, а сильные доли — как `i % 2 == 0`. Вся ритмическая структура исходного файла уничтожается.
- **Как чинить:** Экспортировать 4 трека (Format 1) на каналах 0, 1, 2, 3 с назначением хор-патчей General MIDI (`Program Change 52 Choir Aahs`). При импорте парсить реальные `delta_time` из MIDI-событий.

---

## 4. Проверенные гипотезы, которые НЕ подтвердились

1. **Гипотеза о мертвом коде противоположных квинт и октав:**
   - *Предположение из BRIEF:* Функция `check_contrary_fifths_and_octaves` математически недостижима при обычных шагах ($d_2 - d_1 \equiv 0 \pmod{12}$).
   - *Проверка:* В тесте `test_s_to_d_block.py` на переходах $S \to D$ правило `CONTRARY_OCTAVES` сработало 66 раз, а `CONTRARY_FIFTHS` — 17 раз при встречном движении голосов в чистые октавы и квинты. Код живой и рабочий.
2. **Гипотеза о сбое детектора тональностей на дефолтной мелодии:**
   - *Предположение:* Детектор может путать C Major дефолтной мелодии.
   - *Проверка:* Дефолтная мелодия `E4 F4 G4 E4 D4 C4` уверенно и безошибочно распознается как `C Major (До мажор)`.

---

## 5. Внешние авторитетные источники

- **Бригадный учебник:** *И. Дубовский, С. Евсеев, И. Способин, В. Соколов. «Учебник гармонии»* — Глава 20 («Гармонизация мелодии»), Глава 27 («Обращения доминантсептаккорда. Терцквартаккорд D43»). [Классика теории музыки](https://ale07.ru/music/notes/profile.php?name=dubovsky_harmony).
- **MusicXML 3.1 Specification:** W3C / MakeMusic Standard — [Partwise Structure, Divisions & Backup](https://www.w3.org/2021/06/musicxml31/).
- **CWE-942:** Permissive Cross-domain Policy with Untrusted Domains — [MITRE CWE-942](https://cwe.mitre.org/data/definitions/942.html).
- **MDN Web Docs:** Cross-Origin Resource Sharing (CORS) with credentials — [MDN CORS Credentialed Requests](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS#credentialed_requests_and_wildcards).
