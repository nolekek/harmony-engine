# Red-Team Core Audit Findings: SATB Harmonization Engine

Дата: 11.11.2026  
Интерпретатор: `C:\Users\Admin\AppData\Local\Python\pythoncore-3.14-64\python.exe`  
Рабочая директория: `D:\aitraining`  
Область проверки: Core (`src/harmony/pipeline.py`, `src/harmony/solver/`, `src/harmony/rules/`, `src/harmony/syntax/`, `src/harmony/core/`).

---

## 1. Сводная таблица подтвержденных дефектов

| Severity | Файл:строка | Что не так | Repro | Ожидаемое vs Фактическое |
|---|---|---|---|---|
| **CRITICAL** | `src/harmony/core/metric.py:127-129` | Бесконечный цикл и зависание процесса на нулевом или отрицательном размере такта (`time_signature="0/4"`, `"-1/4"`). `measure_duration` равен `0.0`, условие `while curr_offset >= -1e-4` крутится бесконечно. | `python -c "import sys; sys.path.insert(0, '.'); from src.harmony.pipeline import Harmonizer; Harmonizer().harmonize([60, 62], 'C Major', time_signature='0/4')"` | **Ожидалось:** Graceful validation error или fallback на 4/4.<br>**Фактически:** Полное зависание потока CPU (100% core spin). |
| **HIGH** | `src/harmony/pipeline.py:296-304` | Механизм `_replan` сливает `ALL_FUNCTIONS` в список альтернатив для финального шага, приводя к гармонизациям с финальным аккордом на обращении доминанты (`D6`, `D65`, `D43`) вместо `T` или `D`. | `python -c "import sys; sys.path.insert(0, '.'); from src.harmony.pipeline import Harmonizer; res = Harmonizer().harmonize([71, 67], 'C Major', time_signature='6/8'); print([c.function for c in res.best_solution.chords])"` | **Ожидалось:** Финальный аккорд классической каденции только `T`/`t` (автентический) или `D`/`d` (половинный).<br>**Фактически:** Решение завершается на `['D', 'D6']` или `D43` / `D65` (14 подтвержденных случаев в фаззинге). |
| **HIGH** | `src/harmony/pipeline.py:163` | Контрактный байпас `allow_extended_ranges=False`. Флаг принудительно перетирается в `True`, если включен `allow_replanning=True` (по умолчанию) и сопрано выходит за пределы 60..81. | `python -c "import sys; sys.path.insert(0, '.'); from src.harmony.pipeline import Harmonizer; h = Harmonizer(); print('rep=F:', h.harmonize([59, 60], 'C Major', allow_extended_ranges=False, allow_replanning=False).is_success); print('rep=T:', h.harmonize([59, 60], 'C Major', allow_extended_ranges=False, allow_replanning=True).is_success)"` | **Ожидалось:** При `allow_extended_ranges=False` мелодия с нотой 59 отклоняется.<br>**Фактически:** `allow_extended_ranges=False` молча игнорируется при первой же попытке `solver.solve` (`effective_extended=True`). |
| **MEDIUM** | `src/harmony/rules/doubling.py:115-166`, `550-563` | Неполные секстаккорды (`T6`, `S6`, `II6`, `III6`) без квинты. Разрешено удвоение терции и основного тона одновременно без наличия квинты (`pcs = [4, 0, 0, 4]` для T6). | `python -c "import sys; sys.path.insert(0, '.'); from src.harmony.pipeline import Harmonizer; res = Harmonizer().harmonize([64, 60, 60, 64], 'C Major'); print([v.pitch_classes() for v in res.best_solution.voicings])"` | **Ожидалось:** В 4-голосии секстаккорды трезвучий обязаны содержать квинту (удваивается прима или квинта).<br>**Фактически:** В фаззинге 66 раз зафиксированы секстаккорды без квинты с пустым звучанием (удвоена прима и терция). |
| **MEDIUM** | `src/harmony/solver/state_generator.py:77-79` | Для аккорда `VII7` в натуральном мажоре безусловно генерируется пониженная VI ступень гармонического мажора (Eb в G-dur, F в A-dur), загрязняя фактуру недиатоническими нотами в альте/теноре. | `python -c "import sys; sys.path.insert(0, '.'); from src.harmony.solver.state_generator import generate_candidate_voicings; from src.harmony.core.types import Key, Chord; vs = generate_candidate_voicings(78, Chord('VII7'), Key('G', 'Major')); print(set(v.alto % 12 for v in vs))"` | **Ожидалось:** В чистом натуральном мажоре VII7 полууменьшенный (септима E, PC 4).<br>**Фактически:** В список допустимых тонов жестко зашит PC 3 (Eb), формируя уменьшенный септаккорд гармонического мажора. |
| **LOW** | `src/harmony/syntax/grammar.py:513-524` | Грамматика допускает генерацию планов, начинающихся не с тоники (`T`/`t`), а с субдоминанты `S`, `II` или `T6`. | `python -c "import sys; sys.path.insert(0, '.'); from src.harmony.pipeline import Harmonizer; res = Harmonizer().harmonize([67, 69, 71, 74, 72, 71, 69, 67], 'G Major', time_signature='3/4'); print([c.function for c in res.best_solution.chords])"` | **Ожидалось:** Учебная гармонизация начинается строго с тонического трезвучия в основном виде `T`.<br>**Фактически:** План начинается с `S`: `['S', 'II', 'T', 'T', 'S', 'T', 'D7', 'T']`. |
| **LOW** | `src/harmony/rules/engine.py:317-327` | Слабый штраф за половинчатую каденцию на секстаккорде доминанты `D6 -> T` позволяет алгоритму выбирать неавтентическую каденцию вместо `D -> T` / `D7 -> T`. | `python -c "import sys; sys.path.insert(0, '.'); from src.harmony.pipeline import Harmonizer; res = Harmonizer().harmonize([60, 64, 67, 72, 71, 69, 67, 60], 'C Major'); print([c.function for c in res.best_solution.chords])"` | **Ожидалось:** Заключительная каденция подготавливается основным видом доминанты `D` или `D7`.<br>**Фактически:** Финальная пара аккордов `D6 -> T` (штраф всего 0.8 в `compute_functional_cost`). |

---

## 2. Проверено и НЕ подтвердилось (Clean Invariants)

1. **Голосоведение: строгий порядок S > A > T > B (никаких унисонов и перекрещиваний):**
   - Проверено на 360 сгенерированных мелодиях (191 успешное решение, >1200 срезов аккордов).
   - **Результат:** 0 нарушений. Во всех решениях `v.soprano > v.alto > v.tenor > v.bass`. Хард-гейты `check_voice_crossing` и `check_voice_unison` работают безотказно.

2. **Параллельные и противоположные квинты и октавы:**
   - Проверены все 6 пар голосов (S-A, S-T, S-B, A-T, A-B, T-B) по модулю 12 и в прямых интервалах (7, 12, 19, 24).
   - **Результат:** 0 нарушений. Правило `check_parallel_fifths_and_octaves` и `check_contrary_fifths_and_octaves` на 100% отсекает параллелизмы в решетке Viterbi.

3. **Скрытые квинты и октавы в крайних голосах (Soprano - Bass):**
   - Проверено движение крайних голосов в одном направлении в чистую квинту/октаву со скачком сопрано > 2 полутонов.
   - **Результат:** 0 нарушений. Хард-гейт `check_hidden_fifths_and_octaves` соблюдается.

4. **Стоимость пути (Cost Non-Negativity):**
   - Проверена стоимость `sol.cost >= 0.0`.
   - **Результат:** 0 нарушений. Все стоимости строго неотрицательны.

5. **Детерминизм вычислений:**
   - Проверены повторные запуски на идентичных входах.
   - **Результат:** 100% идентичность последовательностей функций и голосов между прогонами.

6. **12 гармонических миноров (вверх и вниз):**
   - Проверены 24 гаммы (A, E, B, F#, C#, G#, D, G, C, F, Bb, Eb minor harmonic, ascending & descending).
   - **Результат:** 24 из 24 успешно гармонизованы без падений (`0 failures out of 24`).

7. **Replanning timeout & iteration bounds:**
   - Измерен метод `_replan`: строго прерывается по истечении `timeout_sec=2.0` (фактически 2.017с при ~109 попытках решения).
   - *Нюанс:* Общий тайминг `harmonize()` может достигать 3.2с, так как начальный прогон Viterbi по `max_plans=60` (~1.1с) выполняется до входа в `_replan`.

8. **Граничные размеры такта и длительности:**
   - Пустой ввод `[]`: возвращает `is_success=False`, не падает.
   - 1 нота `[60]`: корректно гармонизуется в `T`.
   - 128 нот: решается за 0.24с без переполнения стека.
   - Питчи 0 и 127: корректно отклоняются хард-гейтами без `IndexError`.
   - Длительность `"whole"` в размере `3/8`: корректно рассчитывается через `quarters_to_xml_type_and_dots`.
   - Размеры `"7/8"`, `"abc"`: работают стабильно (`"abc"` fallback в 4/4).
   - `is_downbeat=True` на всех нотах: успешно обрабатывается.
