# Red-Team Аудит Ядра SATB-Гармонизации и Последних Коммитов (Ветка redteam-p2)

**Дата ревизии:** 12 ноября 2026 г.  
**Ревизор:** critic (reviewer, команда `harmony-critic`)  
**Рабочая директория:** `D:\aitraining`  
**Базовый коммит:** `30f527a fix(grammar): unstick chromatic deceptive cadence, deterministic replan window, perf thresholds`  
**Статус тестов на начало аудита:** 783 passed in ~300s  

---

## 🎯 Топ-5 самых критических находок (Краткая выжимка для Капитана)

1. **[CRITICAL] Мертвый клин каденции на мелодиях с окончанием на IV ступень и хроматику**
   - **Файл:** `src/harmony/syntax/grammar.py:122-128, 474, 492-496, 946-949`
   - **Суть:** В грамматике финальный аккорд захардкожен строго как `T`, `D` или `VI`. Если мелодия заканчивается на IV ступень (F в C-dur) или хроматические звуки (Db, Eb, F#, Ab, Bb), ни один из этих трех аккордов физически не содержит ноту сопрано. Кандидаты вырождаются в пустой список `[]`, фоллбек дублирует предпоследний аккорд, а Витерби падает с 0 кандидатов. Плагальные каденции (на S) и хроматические финалы убиты на 100%.

2. **[HIGH] Музыкальный суррогат: «прерванная каденция» через T -> VI и III -> VI**
   - **Файл:** `src/harmony/rules/engine.py:510-538`, `src/harmony/syntax/grammar.py:523-537`
   - **Суть:** В `RuleEngine` финальный аккорд `VI` запрещен после субдоминанты хард-гейтом, но если предшественник — `T` или `III`, навешивается лишь слабый софт-штраф `+15.0`. В итоге на мелодии, оканчивающейся на VI ступень (A4 в C-dur), гармонизатор на полном серьезе выдает каденцию `T -> VI` или `III -> VI` вместо классического прерванного оборота `D -> VI` / `D7 -> VI`. А коммит `30f527a` сверху налепил костыль `bVI -> VI`, назвав его «хроматической прерванной каденцией», хотя bVI — это субдоминанта, а не доминанта.

3. **[HIGH] Архитектурное скотство: Monkey-patching в `doubling.py`, перетирающий `chromatic.py`**
   - **Файл:** `src/harmony/rules/doubling.py:21-65`
   - **Суть:** Модуль удвоений при импорте втихую подменяет функцию валидации переченья `_chromatic.check_false_relation = _refined_check_false_relation` и сносит мастер-валидатор `validate_chromatic_rules = lambda p, c, key=None: ...`. Вместо исправления бага в `chromatic.py`, его замазали манки-патчем в совершенно постороннем файле. Любой вызов `chromatic.py` напрямую до импорта `doubling` работает со старым багом.

4. **[MEDIUM] Выбивание легальных сопрано-нот ниже C4 (B3 / нота 59)**
   - **Файл:** `src/harmony/rules/spacing.py:25`, `src/harmony/solver/state_generator.py:85`, `backend/service.py:175`
   - **Суть:** Диапазон сопрано `STANDARD_VOICE_RANGES[0]` зажат рамками `(60, 81)` (C4 - A5). В хоровой практике сопрано регулярно берет си малой октавы (B3 = 59). При `allow_extended_ranges=False` (дефолт везде в API и пайплайне) нота 59 мгновенно крашит гармонизацию с ошибкой `no candidate voicings found for soprano pitch 59`.

5. **[MEDIUM] Регрессия производительности, замазанная ослаблением ассертов в тестах**
   - **Файл:** `tests/test_long_lines.py:25-45`, `src/harmony/pipeline.py:48`
   - **Суть:** В коммите `30f527a` пороги времени выполнения тестов для 16-тактовых линий были тупо подняты с 1200 мс до 2500 мс, для длинных — с 3000 мс до 6000 мс, а таймаут репланнинга в пайплайне раздут с 2 с до 10 с. Из-за комбинаторного взрыва лучей в грамматике движок просел по скорости более чем в 2 раза, но вместо оптимизации и прунинга авторы просто ослабили ассерты в CI.

---

## 🔍 Подробный реестр дефектов и находок

### 1. Hard-Gate Deadlock финальной каденции на IV ступени и альтерированных тонах
- **Severity:** `blocker`
- **Location:** `src/harmony/syntax/grammar.py:122-128, 474, 492-496`
- **Repro:**
  ```bash
  python -c "from src.harmony.pipeline import Harmonizer; h = Harmonizer(); print(h.harmonize([60, 64, 62, 65], key='C Major').is_success)"
  ```
- **Expected:** `True` (Гармонизация с плагальным кадансом S -> S, II -> S, или T -> S).
- **Actual:** `False` (0 решений, полный отказ).
- **Механизм бага:**
  В `get_compatible_chords_for_pitch`:
  ```python
  if is_final_cadence:
      if pc in tonic_tones:
          if fn not in ("T", "t"):
              continue
      else:
          if fn not in ("D", "d", "VI", "vi"):
              continue
  ```
  Для IV ступени (нота F, pc=5):
  - 5 не входит в `tonic_tones` (`{0, 4, 7}`).
  - Функция обязана быть в `("D", "d", "VI", "vi")`.
  - Звуки трезвучия D: `{7, 11, 2}`. F там нет.
  - Звуки трезвучия VI: `{9, 0, 4}`. F там нет.
  - Список совместимых аккордов `cands` становится пустым (`[]`).
  - Фоллбек 3 тупо повторяет предпоследний аккорд (например, `D6`), в котором тоже нет ноты F.
  - Генератор состояний Витерби падает с 0 состояний для сопрано 65.
  - Аналогичный крах происходит для любых альтераций: bII (Db), bVI (Ab), #IV (F#), bVII (Bb).

---

### 2. Музыкальное убожество: T -> VI и III -> VI вместо прерванного каданса
- **Severity:** `high`
- **Location:** `src/harmony/rules/engine.py:510-538`, `src/harmony/syntax/grammar.py:523-537`
- **Repro:**
  ```bash
  python -c "from src.harmony.pipeline import Harmonizer; h = Harmonizer(); sol = h.harmonize([60, 62, 64, 65, 67, 69], key='C Major').best_solution; print([c.function for c in sol.chords])"
  ```
- **Expected:** Прерванная каденция строго вида `D -> VI` или `D7 -> VI`.
- **Actual:** `['T', 'II6', 'T', 'S6', 'T', 'VI']` — тоника скачет прямо в субмедианту `T -> VI` на каденции!
- **Механизм бага:**
  В `RuleEngine`:
  ```python
  elif curr_sym in ("VI", "vi"):
      ...
      elif prev_sym not in allowed_deceptive_preds:
          soft_cost += 15.0
  ```
  Если `prev_sym == 'T'`, хард-гейт НЕ срабатывает, начисляется жалкий штраф +15.0. Поскольку другие ходы в beam search были отсечены, алгоритм выбирает дикий переход `T -> VI`.
  Более того, коммит `30f527a` прописал:
  ```python
  if prev_sym in ("bVI", "bVI6", "BVI", "BVI6", "bvi", "bvi6"):
      # Chromatic deceptive cadence...
      soft_cost += 12.0
  ```
  В классической гармонии (Бригадный учебник, гл. 22) прерванная каденция — это ВСЕГДА разрешение **доминанты** в VI ступень (`D -> VI`). Разрешение субдоминанты `bVI -> VI` прерванной каденцией не является в принципе. Это хроматическое сползание с полутоновым переченьем баса (Ab -> A).

---

### 3. Скрытый манки-патчинг модуля хроматики из `doubling.py`
- **Severity:** `high`
- **Location:** `src/harmony/rules/doubling.py:21-65`
- **Repro:**
  ```python
  import src.harmony.rules.chromatic as chr_mod
  # До импорта doubling.py chr_mod.check_false_relation имеет одну реализацию
  # После import src.harmony.rules.doubling она мутирует глобально!
  ```
- **Expected:** Чистая модульная архитектура: правила хроматики живут в `chromatic.py`, правила удвоения — в `doubling.py`.
- **Actual:** `doubling.py` нагло перезаписывает:
  `_chromatic.check_false_relation = _refined_check_false_relation`
  `_chromatic.validate_chromatic_rules = lambda p, c, key=None: _refined_check_false_relation(p, c, key=key)`
- **Почему это костыль:** Разработчики обнаружили ложные срабатывания переченья на диатонических полутонах (I <-> bII, V <-> bVI). Вместо того чтобы по-человечески исправить `chromatic.py` и его тесты, они засунули функцию `_refined_check_false_relation` в файл удвоений (`doubling.py`) и манки-патчнули модуль при импорте. Это мина замедленного действия при рефакторинге и многопоточности.

---

### 4. Недоступность B3 (59) для хорового сопрано при дефолтных настройках
- **Severity:** `medium`
- **Location:** `src/harmony/rules/spacing.py:24-29`, `src/harmony/solver/state_generator.py:85`, `backend/service.py:175`
- **Repro:**
  ```bash
  python -c "from src.harmony.pipeline import Harmonizer; h = Harmonizer(); print(h.harmonize([65, 61, 59, 60], key='C Major').is_success)"
  ```
- **Expected:** `True` (Мелодия F4 -> Db4 -> B3 -> C4 гармонизуется через `S -> N6 -> D -> T`).
- **Actual:** `False` (`Step 2 (D): no candidate voicings found for soprano pitch 59`).
- **Механизм бага:**
  Нижняя граница диапазона сопрано в `STANDARD_VOICE_RANGES[0]` равна 60 (C4). B3 (нота 59) отнесена к `EXTENDED_VOICE_RANGES[0]`. Однако ни в CLI, ни в `Harmonizer`, ни в REST API флаг `allow_extended_ranges` по умолчанию не включен. В результате любая классическая хоровая мелодия, касающаяся вводного тона малой октавы (B3), мгновенно отваливается с фатальной ошибкой.

---

### 5. Деградация производительности и заметание мусора под ковер в `test_long_lines.py`
- **Severity:** `medium`
- **Location:** `tests/test_long_lines.py:37-39`, `src/harmony/pipeline.py:26`
- **Коммит-виновник:** `30f527a` (скрипты `.redteam/scratch/lead/patch_bvi_vi.py`, `patch_cadence_unstick.py`)
- **Механизм:**
  Из-за добавления шаблонов каденций, фоллбеков и разрастания beam search без профилирования время гармонизации 16-тактовых линий удвоилось.
  Вместо профилирования и оптимизации:
  - порог 16-тактовой мелодии поднят с 1200 мс до 2500 мс;
  - порог длинных линий поднят с 3000 мс до 6000 мс;
  - дефолтный таймаут репланнинга в `pipeline.py` увеличен с 2.0 с до 10.0 с.
  Тесты позеленели, но производительность ядра деградировала в 2.1 раза.

---

### 6. Несрабатывающий мусорный код в `RuleEngine`
- **Severity:** `low`
- **Location:** `src/harmony/rules/engine.py:519-528`
- **Код:**
  ```python
  if prev_sym in ("bVI", "bVI6", "BVI", "BVI6", "bvi", "bvi6"):
      soft_cost += 12.0
  elif prev_sym in forbidden_subdom or prev_sym.upper().startswith("BVI") or prev_sym in SUBDOMINANT_GROUP:
      violations.append(...)
  ```
  В кортеже `forbidden_subdom` (строка 512) первыми элементами идут `"bVI", "bVI6", "BVI", "BVI6"`. Но ветка `elif prev_sym in forbidden_subdom` для аккордов bVI **никогда не выполнится**, потому что предыдущий `if` уже перехватил их все и превратил в софт-пенальти! Автор написал мертвый код в правилах валидации.

---

### 7. Нестажированный сомнительный хак в рабочей копии (`git status`)
- **Severity:** `medium`
- **Location:** `src/harmony/syntax/grammar.py:333`
- **Дифф:**
  ```diff
  - "BVI", "BVI6", "D53", "T53", "T-6",
  + "BVI", "BVI6", "D53", "T53", "T-6", "VII", "VII6", "VII7",
  ```
- **Суть:** В локальной рабочей копии оставлено незакоммиченное изменение, разрешающее переход из неаполитанского аккорда (`N`, `N6`) в седьмую ступень (`VII`, `VII6`, `VII7`). В теории классической гармонии неаполитанский аккорд (bII) разрешается в доминанту (D, D7, K64) или тонику, но никогда не скачет в уменьшенное трезвучие/септаккорд VII ступени (образуя запрещенные тритоновые ходы и переченья между Db и D).

---

## 🎼 Результаты прогона гармонизатора на тестовой сюите из 15 мелодий

| № | Мелодия | Тональность | Результат | Последовательность | Стоимость | Замечания |
|---|---------|-------------|-----------|-------------------|-----------|-----------|
| 1 | C major scale up (C4-C5) | C Major | SUCCESS | T -> II6 -> T -> S6 -> T6 -> S6 -> D7 -> T | 33.0 | Корректно |
| 2 | C major scale down (C5-C4) | C Major | SUCCESS | T -> VII6 -> VI -> T -> S6 -> T -> D -> T | 30.6 | Корректно |
| 3 | A minor scale up (A4-A5) | A minor | SUCCESS | T -> II6 -> T -> S6 -> T -> S6 -> D7 -> T | 31.9 | Корректно |
| 4 | A minor scale down (A5-A4) | A minor | SUCCESS | T -> III -> S6 -> T6 -> S6 -> T -> D6 -> T | 33.1 | Корректно |
| 5 | C major arpeggio | C Major | SUCCESS | T -> VI -> D2 -> T6 -> D6 -> T -> T | 45.0 | Стазис T-T в финале |
| 6 | A minor arpeggio | A minor | SUCCESS | T6 -> VI -> T6 -> S6 -> T6 -> III6 -> T | 33.2 | **Дефект:** III6 -> T в финале без D |
| 7 | Neapolitan line (F4-Db4-B3-C4) | C Major | **FAILED** | None | Inf | **Крах:** нота B3 выбита рейнджем |
| 8 | Neapolitan line high (F5-Db5-B4-C5) | C Major | SUCCESS | II6 -> N6 -> D7 -> T | 11.2 | Корректно в высоком регистре |
| 9 | Chromatic bVI line (G4-Ab4-G4-C4) | C Major | SUCCESS | T -> bVI6 -> D6 -> T | 14.2 | Корректно |
| 10 | Repeated notes stasis (C4-C4-C4-C4) | C Major | SUCCESS | T -> T -> T -> T | 6.0 | Однообразие гармонии |
| 11 | Half-cadence on deg 2 (E4-F4-G4-D4) | C Major | SUCCESS | T -> S6 -> T6 -> D | 6.9 | Корректно |
| 12 | Deceptive cadence on 6 (E4-F4-G4-A4) | C Major | **DEFECT** | T -> S6 -> III -> VI | 49.4 | **Дефект:** III -> VI вместо D -> VI |
| 13 | Leap-heavy melody with B3 | C Major | **FAILED** | None | Inf | **Крах:** нота B3 выбита рейнджем |
| 14 | Melody ending on deg 4 (C4-E4-D4-F4) | C Major | **FAILED** | None | Inf | **Крах:** IV ступень заблокирована в финале |
| 15 | Melody ending on bVI (E4-F4-G4-Ab4) | C Major | **FAILED** | None | Inf | **Крах:** bVI ступень заблокирована в финале |

**Итог:** Из 15 мелодий 4 завершились полным отказом гармонизации (27%), а 2 выдали грубые музыкальные дефекты каденции (13%). Совокупный процент брака на естественных мелодиях составляет **40%**.

---

## 🧪 Анализ тестового покрытия и слабых мест в `tests/`

1. **`tests/test_cadence_finals.py`**:
   - Тестирует только степени 1, 2, 5, 7.
   - Ступени 3, 4, 6 и альтерации полностью проигнорированы.
   - Ассерты вида `assert final_chord in ("T", "D", "VI")` на 5 ступени — фикция, так как аккорд `VI` в C-dur не содержит ноты G (5 ступени).
2. **`tests/test_scale_matrix.py`**:
   - Проверяет только флаг `res.is_success is True`. Никакой проверки голосоведения, параллелизмов и чистоты каденций нет.
3. **`tests/test_chromatic_layer.py`**:
   - Покрывает синтетические связки аккордов из 2-3 нот, но не проверяет интеграцию хроматики в сквозные каденционные фразы реальных мелодий.

---

## 🛠️ Рекомендации к исправлению

1. **Разблокировать финальные каденции в грамматике:**
   - Если сопрано оканчивается на IV ступень, разрешить плагальную каденцию (`S`, `S6` -> `T` или полукаденцию на `S`).
   - Добавить явную поддержку плагального завершения и полукаденций на субдоминанте.
2. **Ужесточить прерванный оборот:**
   - Превратить `CADENCE_FINAL_VI_REQUIRES_DOMINANT` в безусловный hard-gate, если аккорду `VI` не предшествует доминанта (`D`, `D7`, `D6`, `D65`, `VII7`).
   - Искоренить бред с «хроматической прерванной каденцией `bVI -> VI`».
3. **Ликвидировать манки-патч в `doubling.py`:**
   - Перенести `_refined_check_false_relation` непосредственно в `src/harmony/rules/chromatic.py` и убрать костыльные присваивания из тела `doubling.py`.
4. **Скорректировать дефолтный диапазон сопрано:**
   - Расширить нижнюю границу сопрано по умолчанию до B3 (59) или включать `allow_extended_ranges` для граничных вводных тонов.
5. **Откатить незастажированный хак `N -> VII` в `grammar.py:333`.**
