# Red Team Security & Architecture Audit: Frontend (React 19 + TypeScript + OSMD)

## Краткий вердикт
Фронтенд представляет собой классический «демо-костыль», наспех слепленный поверх тяжеловесной библиотеки OpenSheetMusicDisplay без базового понимания жизненного цикла React, Web Audio API и асинхронной изоляции состояния. В кодовой базе зияют архитектурные дыры: блокирующий `window.alert` замораживает UI с вечным спиннером и грязным стейтом, мутации вкладок приводят к загрязнению партитуры чужими данными, экспорт молча калечит ритмику мелодии (все ноты вырождаются в половинные), Web MIDI плодит по новому `AudioContext` на каждый удар метронома (гарантированный краш вкладки браузера), а монолитный бандл весом 1.72 МБ грузится без какого-либо code-splitting.

---

## Сводная таблица дефектов

| ID | Область | Severity | Файл:Строка | Суть дефекта |
|---|---|---|---|---|
| F-01 | UI / State | **BLOCKER** | `App.tsx:113-120` | Блокирующий `alert()` вешает UI в вечном спиннере, старые кандидаты и ноты не очищаются при ошибке. |
| F-02 | Web Audio | **BLOCKER** | `midiInput.ts:121-140` | `new AudioContext()` инстанциируется на КАЖДЫЙ тик метронома. Исчерпание аппаратных аудио-контекстов браузера. |
| F-03 | Export | **HIGH** | `ExportBar.tsx:31,63`, `App.tsx:280` | `ExportBar` не передает `durations` в `/api/export/*`. Ритмика уничтожается, все ноты становятся половинными. |
| F-04 | State Leak | **HIGH** | `App.tsx:161-170, 264, 303` | Общий стейт между вкладками «Гармонизатор» и «Инспектор». Проверка чужого задания подменяет партитуру и ломает экспорт. |
| F-05 | Web Audio | **HIGH** | `synth.ts:242-248` | `stop()` сбрасывает только таймер, но оставляет звучать текущие осцилляторы; нет сброса при переключении кандидатов. |
| F-06 | Async / Race | **HIGH** | `App.tsx:75-121, 124-126` | Отсутствие `AbortController` и requestId. Гонка ответов при повторных кликах и двойной маунт React StrictMode. |
| F-07 | Rendering | **HIGH** | `ScoreDisplay.tsx:63-70` | Подсветка ошибок инспектора вешает красный дроп-шадоу на ВСЕ такты подряд без разбора и не обновляется при клике на ошибку. |
| F-08 | API Contract | **MEDIUM** | `ControlPanel.tsx:94`, `App.tsx:35` | Ожидание поля `k.title`, в то время как бэкенд возвращает `name`. В селекторе отображаются пустые имена ладов. |
| F-09 | Music Theory | **MEDIUM** | `MelodyInput.tsx:98-106` | Расчет сильных долей (`is_downbeat`) захардкожен под 4/4; удаление ноты не пересчитывает доли оставшихся нот. |
| F-10 | Performance | **MEDIUM** | `App.tsx:12`, `package.json:14` | Монолитный бандл 1.72 МБ: `OpenSheetMusicDisplay` импортируется синхронно в корневой бандл без `React.lazy()`. |
| F-11 | UX / Logic | **LOW** | `ControlPanel.tsx:177, 226-234` | Кнопка активна при пустой мелодии; отрицательная стоимость («Стоимость: -7») вводит пользователя в заблуждение. |
| F-12 | a11y / Clean | **LOW** | `App.css:1-184`, `GraderPanel.tsx:269` | 184 строки мусорного Vite-CSS; полное отсутствие `aria-*` в интерактивных матрицах аккордов и карточках. |

---

## Детальный разбор находок

### 1. Блокирующий `alert` и сохранение тухлого стейта (Главный баг со скриншота)
- **Severity**: **BLOCKER**
- **Файл**: `frontend/src/App.tsx:113-120`
- **Суть**: 
  Пользователь нажимает «Гармонизовать мелодию». Вызывается `handleHarmonize()`, взводится флаг `setIsHarmonizing(true)`. При получении от бэкенда `is_success: false` (например, «Все кандидаты отклонены жесткими правилами голосоведения.») фронтенд вызывает синхронный модальный `alert(data.message)`.
  1. Вызов `alert()` полностью блокирует стек выполнения JS в браузере ДО блока `finally { setIsHarmonizing(false); }`.
  2. Из-за этого кнопка «Гармонизовать» находится в заблокированном спиннер-состоянии («Математический синтез (Viterbi)...») ровно столько времени, сколько открыто окно alert.
  3. В ветке `else` отсутствует вызов очистки стейта: `setCandidates([])`, `setSelectedCandidate(null)`, `setActiveMusicXml("")`, `setLatencyMs(null)`. В результате под модальным окном красуются СТАРЫЕ кандидаты от предыдущей успешной гармонизации (#1 Оптимум, cost -7) и старая партитура.
  4. Код полностью игнорирует проверку `resp.ok`. Если сервер выбросит HTTP 422 (валидация Pydantic) или 500 (Unhandled Python Exception), фронтенд попытается прочитать `data.message` (которого нет в 422 `{"detail": ...}`) и выбросит дефолтный алерт `alert("Не удалось найти решений...")`, скрывая истинную причину аварии.
- **Доказательство**:
  ```ts
  // frontend/src/App.tsx:99-120
  const data = await resp.json();
  setLatencyMs(data.latency_ms); // При 422 тут undefined

  if (data.is_success && data.candidates && data.candidates.length > 0) {
    // ...
  } else {
    // Синхронная блокировка потока! candidates и activeMusicXml НЕ очищаются!
    alert(data.message || "Не удалось найти решений для данной мелодии.");
  }
  // finally выполнится ТОЛЬКО после того, как юзер нажмет ОК в alert:
  finally {
    setIsHarmonizing(false);
  }
  ```
- **Фикс**: 
  Заменить `alert()` на inline-баннер об ошибке (`errorMessage` в React state). Проверять `resp.ok` с парсингом `data.detail`. В случае неудачи явно сбрасывать `setCandidates([])`, `setActiveMusicXml("")`, `setSelectedCandidate(null)`.

---

### 2. Утечка AudioContext при записи с метрономом (Web MIDI)
- **Severity**: **BLOCKER**
- **Файл**: `frontend/src/audio/midiInput.ts:121-141`
- **Суть**:
  В методе `playClick(isDownbeat: boolean)` на КАЖДЫЙ тик метронома вызывается `new AudioCtxClass()`. Браузеры (Chrome, Firefox, Safari) имеют жесткое ограничение на количество одновременно открытых `AudioContext` (обычно от 6 до 32). По достижении лимита браузер начинает бросать исключения `DOMException: The number of hardware contexts provided has reached its maximum`, звук клика отваливается, память течет, а в мобильных браузерах вкладка крашится.
  Кроме того, в `connectDevice()` слушатель `onmidimessage` вешается заново, но нигде не отвязывается при отключении устройства или размонтировании компонента.
- **Доказательство**:
  ```ts
  // frontend/src/audio/midiInput.ts:121-127
  private playClick(isDownbeat: boolean) {
    try {
      const AudioCtxClass = window.AudioContext || ...;
      const ctx = new AudioCtxClass(); // <--- ДИЧЬ: новый контекст КАЖДЫЕ 500 мс!
      const osc = ctx.createOscillator();
  ```
- **Фикс**: 
  Использовать единственный разделяемый экземпляр `AudioContext` из `audioEngine` либо синглтон-контекст класса. Добавить корректный метод `cleanup()`.

---

### 3. Экспорт решений ломает длительности нот (Durations Omission)
- **Severity**: **HIGH**
- **Файл**: `frontend/src/components/ExportBar.tsx:28-34, 55-66`, `frontend/src/App.tsx:279-286`
- **Суть**:
  Бэкенд-эндпоинты `/api/export/midi` и `/api/export/musicxml` принимают в теле запроса опциональный массив `durations: list[str]`. Если массив не передан, бэкенд (`backend/api.py:377, 399`) берет фоллбэк: все ноты по умолчанию становятся половинными (`half`).
  В `ExportBar.tsx` при формировании payload для скачивания MIDI и MusicXML поле `durations` ВООБЩЕ НЕ ОТПРАВЛЯЕТСЯ. Более того, `App.tsx` даже не передает актуальные `durations` в пропсы компонента `ExportBar`!
  Если в мелодии были целые (`whole`) ноты (как последняя нота в `INITIAL_MELODY`) или четверти, скачанный файл MusicXML и MIDI будет содержать изуродованную ритмику, где ВСЕ ноты насильно превращены в половинные.
  Дополнительно: в строках 43 и 76 `window.URL.revokeObjectURL(url)` вызывается синхронно сразу после `a.click()`, из-за чего в Firefox и Safari загрузка блоба обрывается до передачи в менеджер закачек.
- **Доказательство**:
  ```ts
  // frontend/src/components/ExportBar.tsx:58-64
  body: JSON.stringify({
    voicings,
    chords,
    key: keyObj,
    title: `Гармонизация в ${keyObj.tonic} ${keyObj.mode}`,
    time_signature: timeSignature,
    // DURATIONS ОТСУТСТВУЕТ!
  })
  ```
  Проверено скриптом `verify_frontend_flaws.py`: в экспортированном MusicXML все элементы `<type>` равны `'half'`.
- **Фикс**: 
  Добавить `durations` в состояние `App.tsx` и пропсы `ExportBarProps`, прокидывать `durations: activeDurations` в JSON payload. Отзыв Object URL завернуть в `setTimeout(() => URL.revokeObjectURL(url), 1000)`.

---

### 4. Взаимное загрязнение стейта между вкладками «Гармонизация» и «Инспектор»
- **Severity**: **HIGH**
- **Файл**: `frontend/src/App.tsx:55-63, 161-170, 279-286, 316-322`
- **Суть**:
  В `App.tsx` состояние партитуры (`activeMusicXml`, `activeVoicings`, `activeChords`, `asciiScore`, `problemMeasures`) объявлено как единый глобальный набор стейтов для обеих вкладок («Гармонизация» и «Консерваторский инспектор»).
  При переключении на вкладку «Инспектор» и проверке студенческой задачи:
  1. `handleGradeComplete()` перезаписывает `activeMusicXml` и `activeVoicings`, но НЕ трогает `activeChords` и `asciiScore`.
  2. Пользователь возвращается на вкладку «Гармонизация»: в партитуре отображается чужая студенческая работа с двойками инспектора, в селекторе кандидатов выбран `#1 Оптимум`, а `ExportBar` отправляет на сервер адскую смесь из аккордов авто-гармонизатора и голосоведения студента!
  3. Ошибки `problemMeasures` не сбрасываются при переключении вкладок и подсвечивают такты в основном гармонизаторе.
  4. На вкладке инспектора в `ExportBar` не передается `timeSignature`, из-за чего экспорт всегда насильно уходит в 4/4.
- **Доказательство**:
  `App.tsx:161-170`:
  ```ts
  const handleGradeComplete = (report, musicxml, voicings) => {
    setActiveMusicXml(musicxml);
    setActiveVoicings(voicings);
    setProblemMeasures(report.problem_measures);
    setScoreTitle(`Инспектор: ${report.grade}`);
    // activeChords и asciiScore остаются от гармонизатора!
  };
  ```
- **Фикс**: 
  Изолировать состояние гармонизатора и инспектора в два независимых объекта состояния или раздельные контексты/редьюсеры.

---

### 5. Аудиодвижок: утечка звучащих нот и рассинхронизация при смене кандидата
- **Severity**: **HIGH**
- **Файл**: `frontend/src/audio/synth.ts:203-248`, `frontend/src/App.tsx:149-158`
- **Суть**:
  1. `audioEngine.stop()` сбрасывает только `playbackTimer = window.setTimeout(...)`, но не останавливает уже запущенные узлы `OscillatorNode` и `GainNode`. Текущий звучащий аккорд продолжает звучать до истечения `now + durationSec`. При быстром нажатии Стоп -> Старт происходит наложение аккордов с клиппингом громкости.
  2. В `synth.ts:216-218` длительность каждого аккорда жестко захардкожена: `const chordDurationSec = beatDurationSec * 2` (половинная нота). Любые четверти, целые или точки в мелодии игнорируются синтезатором.
  3. Планирование воспроизведения через `window.setTimeout` вместо `AudioContext.currentTime` приводит к тайминг-джиттеру (10-40 мс на аккорд) и сползанию темпа при смене фокуса окна.
  4. В `App.tsx:149-158` клик по карточке другого кандидата (`handleSelectCandidate`) НЕ вызывает `audioEngine.stop()`. Если пользователь переключает кандидаты на лету во время воспроизведения, синтезатор продолжает доигрывать старый массив `voicings` из замыкания `playSequence`, пока глаза видят новую партитуру.
  5. В `updateGains()` переключение `mute/solo` выполняется через мгновенный `setValueAtTime`, что вызывает слышимые цифровые щелчки (clicks/pops).
- **Фикс**: 
  Сохранять активные генераторы в массив `activeNodes` и вызывать `.stop()` / сбрасывать `gain.cancelScheduledValues` в методе `stop()`. В `handleSelectCandidate` вызывать `audioEngine.stop()`. Заменить `setTimeout` на Web Audio lookahead scheduler.

---

### 6. Состояние гонки (Race Condition) и двойной вызов в React StrictMode
- **Severity**: **HIGH**
- **Файл**: `frontend/src/App.tsx:75-121, 124-126`
- **Суть**:
  В `handleHarmonize()` сетевой запрос `fetch("/api/harmonize")` не имеет привязки к `AbortController` и не версионируется идентификатором запроса (`reqId`). Если пользователь меняет параметры мелодии или отправляет повторные запросы, ответы могут прийти не в порядке отправки, и медленный старый ответ перезапишет актуальный результат.
  Кроме того, авто-гармонизация на маунте:
  ```ts
  useEffect(() => {
    handleHarmonize();
  }, []);
  ```
  В React 18/19 при `StrictMode` (стандарт для dev-сборки) вызывает эффект дважды. На бэкенд улетают два параллельных тяжелых расчета Viterbi, создавая гонку прямо на старте приложения. При этом функция `handleHarmonize` не обернута в `useCallback` и не передана в deps.
- **Фикс**: 
  Использовать `AbortController` в `useRef`, прерывая предыдущий запрос перед отправкой нового: `signal: abortControllerRef.current.signal`.

---

### 7. Фиктивная подсветка проблемных тактов в ScoreDisplay (OSMD)
- **Severity**: **HIGH**
- **Файл**: `frontend/src/components/ScoreDisplay.tsx:57-71, 54`
- **Суть**:
  Метод `applyVoiceColoringAndMeasureHighlights()` пытается подсветить проблемные такты:
  ```ts
  if (problemMeasures && problemMeasures.length > 0) {
    const measureBoxes = svg.querySelectorAll("g[id*='Measure'], g.vf-measure");
    measureBoxes.forEach((m) => {
      (m as SVGGraphicsElement).style.filter = "drop-shadow(0 0 6px rgba(239, 68, 68, 0.6))";
    });
  }
  ```
  1. Селектор выбирает ВСЕ элементы тактов в SVG и окрашивает ВСЕ такты без оглядки на номера из `problemMeasures`. Ошибка в такте 2 приведет к тому, что подсветится вся партитура от первого до последнего такта.
  2. Очистка стиля (`style.filter = ""`) отсутствует, если `problemMeasures` становится пустым.
  3. `useEffect` зависит только от `[musicxml]` (строка 54). Пропс `problemMeasures` вообще не включен в массив зависимостей! При клике на ошибку в отчете инспектора (`onHighlightMeasure`) меняется стейт `problemMeasures`, но `ScoreDisplay` ДАЖЕ НЕ ПЫТАЕТСЯ перерисоваться.
- **Фикс**: 
  Вычислять `measureIndex` для каждого SVG-узла, сопоставлять с `problemMeasures`, очищать фильтры при сбросе и вынести подсветку в отдельный `useEffect(() => { ... }, [problemMeasures, isRendered])`.

---

### 8. Несоответствие контракта API: пустые имена ладов в ControlPanel
- **Severity**: **MEDIUM**
- **Файл**: `frontend/src/components/ControlPanel.tsx:94`, `frontend/src/App.tsx:34-36`
- **Суть**:
  Бэкенд `/api/keys` возвращает массив объектов:
  `[{"tonic": "C", "mode": "Major", "name": "C-dur (До мажор)", "fifths": 0}, ...]`
  Однако типы и разметка фронтенда ожидают поле `title`:
  ```tsx
  // ControlPanel.tsx:94
  <option key={`${k.tonic}:${k.mode}`} value={`${k.tonic}:${k.mode}`}>
    {k.title} ({k.tonic} {k.mode === "Major" ? "мажор" : "гарм. минор"})
  </option>
  ```
  Поскольку `k.title === undefined`, React рендерит пустоту вместо названия тональности. В селекторе пользователь видит нелепый текст: ` (C мажор)` вместо `C-dur (До мажор) (C мажор)`.
- **Доказательство**:
  Подтверждено тестом в `verify_frontend_flaws.py`. В ответе `/api/keys` ключа `title` нет вовсе, есть ключ `name`.
- **Фикс**: 
  Заменить `k.title` на `k.name || k.title` в `ControlPanel.tsx` и обновить интерфейс в `App.tsx`.

---

### 9. Кривая логика расчета сильных долей в MelodyInput
- **Severity**: **MEDIUM**
- **Файл**: `frontend/src/components/MelodyInput.tsx:98-106, 120-125, 173-176`
- **Суть**:
  1. `calculateDownbeatForIndex` жестко вычисляет `beatInMeasure = totalBeats % 4`. При выборе размеров 3/4, 2/4 или 6/8 в `ControlPanel` ввод нот в `MelodyInput` продолжает считать доли по сетке 4/4, потому что компонент даже не принимает `timeSignature` в качестве пропа!
  2. При удалении ноты из середины последовательности (`removeNote(idx)`) метрическая сетка сдвигается, однако атрибуты `is_downbeat` у последующих нот НЕ пересчитываются и остаются привязаны к устаревшим позициям.
  3. Ввод по MIDI (`toggleMidiRecording`, строки 173-175) намертво зашивает длительность `"half"` для всех сыгранных нот, игнорируя реальное время удержания клавиши и переключатель длительностей.
- **Фикс**: 
  Передавать `timeSignature` в `MelodyInput`, пересчитывать `is_downbeat` для всего массива мелодии декларативно при любых изменениях (добавление, удаление, смена размера).

---

### 10. Монолитный бандл 1.72 МБ без Code Splitting
- **Severity**: **MEDIUM**
- **Файл**: `frontend/vite.config.ts`, `frontend/package.json:14`, `frontend/src/App.tsx:12`
- **Суть**:
  Библиотека `opensheetmusicdisplay` весит свыше 1.2 МБ minified. В проекте отсутствует разделение чанков (code splitting) в `vite.config.ts`. Компонент `ScoreDisplay` импортируется синхронно на верхнем уровне. В итоге `dist/assets/index-B3v2zWUo.js` раздут до 1 726 493 байт (~1.65 МБ чистого JS).
  Пользователь вынужден выкачивать полуторамигабайтный монолит до первого полезного рендера (LCP > 3.5 сек на 3G/медленном Wi-Fi).
- **Доказательство**:
  `Get-ChildItem frontend/dist/assets`: файл `index-B3v2zWUo.js` имеет длину 1 726 493 байт.
- **Фикс**: 
  Использовать `const ScoreDisplay = React.lazy(() => import('./components/ScoreDisplay'))` с оберткой в `Suspense`, а также настроить `manualChunks` в Rollup-конфигурации Vite для выноса OSMD в отдельный кэшируемый чанк.

---

### 11. UX-дефекты: пустая мелодия, отрицательная стоимость и побочные доминанты
- **Severity**: **LOW**
- **Файл**: `ControlPanel.tsx:177, 226-234`, `App.tsx:76`
- **Суть**:
  1. Кнопка «Гармонизовать мелодию» имеет условие `disabled={isHarmonizing}`. Если мелодия очищена (`melody.length === 0`), кнопка кликабельна. При клике `handleHarmonize` молча выходит по `if (!melody.length) return;` — юзер кликает, но ничего не происходит, валидационных сообщений нет.
  2. Значение `Стоимость: -7` в карточках кандидатов сбивает с толку пользователей-музыкантов. В Viterbi штрафы складываются с бонусами (например, за красивую каденцию и бас), уходя в минус. Для пользователя непонятно, почему «стоимость» отрицательная и почему -7 лучше, чем -5.
  3. Чекбокс «Побочные доминанты»: бэкенд (`backend/api.py:159-167`) при снятом чекбоксе в случае отсутствия чистых диатонических планов молча берет все планы (`filtered_plans or all_plans`), игнорируя волю пользователя.
- **Фикс**: 
  Дизейблить кнопку при `melody.length === 0`, нормализовать отображение стоимости (например, «Оценка гармонии: 95/100» или «Штраф: 0»).

---

### 12. Недоступность (a11y) и мертвый CSS
- **Severity**: **LOW**
- **Файл**: `frontend/src/App.css:1-184`, `frontend/src/components/GraderPanel.tsx:269-328`
- **Суть**:
  1. Файл `App.css` целиком состоит из 184 строк дефолтного бойлерплейта Vite (`#hero`, `#next-steps`, `.ticks`), который нигде не используется, так как стилизация построена на Tailwind CSS v4.
  2. В таблице ввода аккордов инспектора (`GraderPanel.tsx`) десятки числовых полей `<input type="number">` не снабжены атрибутами `aria-label`, `aria-describedby` или `<label>`. Для скринридера это бессмысленный набор спиннеров без указания голоса и номера такта.
  3. Карточки решений в `ControlPanel.tsx` и плашки ошибок в `GraderPanel.tsx` реализованы как `div` с `onClick` без `role="button"`, `tabIndex={0}` и обработчиков клавиш `Enter` / `Space`. Навигация с клавиатуры невозможна.
- **Фикс**: 
  Удалить `App.css`, добавить `aria-label` к инпутам голосоведения, снабдить интерактивные элементы семантическими кнопками или role="button" с tabindex.

---

## Проверенные гипотезы, которые НЕ подтвердились

1. **Гипотеза о сбое переключения партитуры при клике на кандидата**:
   *Проверка*: предполагалось, что клик на карточку #2 или #3 не меняет партитуру в OSMD.
   *Результат*: Не подтвердилось. `handleSelectCandidate` корректно передает `cand.musicxml` в `activeMusicXml`, и OSMD перерисовывает ноты (если нет зависшего промиса). Однако при этом не глушится звук (что зафиксировано в F-05).
2. **Гипотеза о падении OSMD при пустом MusicXML**:
   *Проверка*: предполагалось, что пустая строка вызывает необработанный `throw` внутри библиотеки.
   *Результат*: Не подтвердилось. В `ScoreDisplay.tsx:40` стоит гарда `if (!musicxml.trim()) return;`, предотвращающая вызов `osmd.load("")`.
3. **Гипотеза о несовместимости Tailwind v4 с Vite**:
   *Проверка*: в `package.json` указаны `@tailwindcss/vite` 4.3.5 и `tailwindcss` 4.3.5.
   *Результат*: Сборка в `dist` проходит успешно, стили Tailwind корректно компилируются в `index-CVP-rBDc.css` (45 КБ).

---

## Ссылки на стандарты и документацию
- W3C Web Audio API (AudioContext lifecycle & limits): https://www.w3.org/TR/webaudio/
- W3C Web MIDI API: https://www.w3.org/TR/webmidi/
- OpenSheetMusicDisplay Documentation: https://opensheetmusicdisplay.org/
- MusicXML 3.1 Specification: https://www.w3.org/2021/06/musicxml31/
- WCAG 2.2 Guidelines (Non-text Contrast & Keyboard Accessibility): https://www.w3.org/WAI/standards-guidelines/wcag/
- React 19 Docs (Synchronous Alert Blocking & StrictMode Lifecycle): https://react.dev/
