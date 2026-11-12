# WAVE 2 — UI/UX REDESIGN: CONTINUATION HANDOFF

> Состояние на 2026-11-12 ~22:15 (Asia/Yekaterinburg). Владелец переключил клиент, реализация
> прервана посреди Фазы 4. Master зелёный, WIP лежит в отдельной ветке.
> Читать вместе с [HANDOFF.md](HANDOFF.md) (основной контекст проекта).

## 1. Где что лежит

| Что | Где |
|---|---|
| `master` | `27dd5ac` — Wave 1 (desktop shell) завершена, 848 тестов зелёные, всё запушено |
| WIP редизайна | ветка **`wip/wave2-ui-redesign`**, коммит `352b499` |
| Задача на таскборде | `task-2` (пока `pending`, описание обновлено под WIP) |
| exe | `dist/HarmonyEngine/HarmonyEngine.exe` — собран из **старого** фронта (до редизайна); после редизайна пересобрать |

Продолжать так:

```powershell
cd D:\aitraining
git checkout wip/wave2-ui-redesign
cd frontend
pnpm install            # если node_modules не на месте
pnpm lint ; pnpm build  # сейчас build КРАСНЫЙ — см. §3
```

## 2. Что уже сделано в WIP (не потерять)

- **Дизайн-токены**: `frontend/src/index.css` (`@theme`, CSS-переменные, `[data-theme="light|dark"]`),
  тёмная тема по умолчанию; **anti-FOUC** инлайн-скрипт в `frontend/index.html`.
- **UI-примитивы**: `components/ui/{Button,Card,Badge}.tsx` с focus-visible и токенами.
  **НЕ хватает**: `Input.tsx`, `Select.tsx`, `Tabs.tsx` (по RFC они нужны для ControlPanel/Header).
- **Распил мелодии**: `components/melody/{PianoKeyboard,NoteList,MidiInputBar,MelodyFileUpload}.tsx`,
  `utils/durationUtils.ts`; `MelodyInput.tsx` сокращён до ~5 КБ.
- **Распил грейдера**: `components/grader/{GraderScoreMatrix,GraderViolationsList}.tsx`;
  `GraderPanel.tsx` сокращён до ~11 КБ.
- **Хуки**: `hooks/useTheme.ts`, `hooks/useHarmonizer.ts`; `types/harmony.ts`.
- **Layout/Header**: `components/layout/Header.tsx` (бренд, статус, табы, переключатель темы).
- **App.tsx** переписан под workstation-layout (24.7 КБ → ~8 КБ, точный размер см. в ветке).
- **ScoreDisplay.tsx** обновлён (стилизация партитуры), но фикс Критика №1 (без blanket-invert)
  надо проверить глазами по диффу — в ветке он частично.

## 3. БЛОКЕР: билд красный (12 ошибок TS)

`pnpm --dir frontend build` → `src/...`:

1. `MelodyInput.tsx(2,24)` TS6133: `Sparkles` импортирован и не используется.
2. `melody/MidiInputBar.tsx`: TS2339 ×4 — используются несуществующие методы `WebMidiManager`:
   `isSupported`, `getDevices`, `selectDevice`, `onNoteOn`; плюс TS7006 (param `note` implicit any).
   → Открыть `frontend/src/audio/midiInput.ts` и привести вызовы к РЕАЛЬНОМУ API класса
   (проверь текущие имена методов/сигнатуры; возможно часть логики жила в старом MelodyInput inline).
3. `melody/NoteList.tsx(39,17)` и `melody/PianoKeyboard.tsx(24,17)` TS2339: `AudioEngine.playSingleTone`
   не существует → сверить с `frontend/src/audio/synth.ts`, использовать реальный метод
   (там есть playNote/… — проверить).
4. `melody/PianoKeyboard.tsx(94,41)`, `(96,29)` TS2304: `END_PITCH` не определён → добавить константу
   диапазона (в старом коде были START/END_PITCH для C3–C6).
5. `ui/Card.tsx(3,18)` TS2430: `CardProps extends HTMLAttributes<HTMLDivElement>` конфликт по `title`
   (ReactNode vs string) → `Omit<HTMLAttributes<HTMLDivElement>, "title">`.

`pnpm --dir frontend lint` → 6 warnings (0 errors): неиспользуемый `Sparkles`, неиспользуемые catch-`e` ×2,
`react(set-state-in-effect)` ×1, `react-hooks(exhaustive-deps)` ×2 (App.tsx ref cleanup). Довести до 0.

## 4. Что осталось по плану (Фазы 3.5–5)

1. Доделать `ui/Input.tsx`, `ui/Select.tsx`, `ui/Tabs.tsx` и перевести на них `ControlPanel.tsx`
   (`frontend/src/components/ControlPanel.tsx`, 11.7 КБ — ещё на старых классах), `ExportBar.tsx`,
   `AudioControls.tsx`, `GraderPanel`-обёртку.
2. Проверить/доделать workstation layout:
   - левая панель 380–440 px с **единым `overflow-y-auto`** (фикс Критика №2, на 1080p иначе
     «Гармонизовать» уезжает за экран);
   - один вертикальный скролл, без вложенных скроллбоксов; партитура — центральная зона.
3. ScoreDisplay (фикс Критика №1): **никакой blanket-инверсии** SVG (`invert+hue-rotate` перекрашивает
   маркеры ошибок #ef4444). Тёмная тема = матовая пергаментная бумага в тёмной раме ИЛИ селективная
   стилизация `svg path, svg text` через CSS-переменные, не трогая цветные rect-маркеры.
4. Сохранить `React.lazy` для ScoreDisplay + `manualChunks` (фикс №4); OSMD должен остаться отдельным
   чанком ~1.44 МБ, не попасть в main.
5. Верификация (фикс №5 и acceptance):
   - `pnpm --dir frontend lint` → 0 errors / 0 warnings;
   - `pnpm --dir frontend build` → exit 0; показать размеры чанков (index/osmd/ScoreDisplay);
   - grep: все 8 API-эндпоинтов на месте (`/api/keys`, `/api/detect-key`, `/api/harmonize`,
     `/api/grade`, `/api/import-file`, `/api/parse-text`, `/api/export/midi`, `/api/export/musicxml`);
   - zero-regression чек-лист: Web MIDI, пианино, авто-сильные доли, аудио-транспорт (BPM 40–200,
     шаг вперёд/назад), топ-3 кандидатов, relaxed-флаги (ranges, secondary dominants), подсветка
     проблемных тактов в OSMD, grader-матрица, экспорт MIDI/MusicXML;
   - все распилы <300 строк;
   - бэкенд не трогали: `pytest -q` → 848 passed, exit 0;
   - визуальная приёмка: запустить `python run_app.py --no-browser` и/или `python -m desktop`,
     снять скриншоты (доступен skill `webapp-testing`/`browser`, Playwright) — три экрана:
     пустое состояние, гармонизация, оценка.
6. После зелёного билда: `pnpm --dir frontend build` → пересобрать exe
   (`python -m PyInstaller desktop.spec --noconfirm`) → smoke-запуск exe.
7. Коммит в master только после аудита Критика (`[ДИФФ ОДОБРЕН]`), затем handoff-док обновить.

## 5. Критерии приёмки Wave 2 (из аудита Критика)

- [ ] Дизайн-токены, тёмная/светлая тема, без FOUC, без хардкодных hex/прозрачностей в компонентах.
- [ ] Workstation layout без вложенных скроллов; левая панель скроллится целиком.
- [ ] Партитура не «выжигает глаза», цвета SATB/ошибок узнаваемы.
- [ ] Все фичи сохранены (чек-лист §4), API не переименованы.
- [ ] A11y: focus-visible, `role=tablist/tab/aria-selected`, `aria-live` для ошибок, контраст AA,
      клавиатурная навигация по пианино.
- [ ] `lint` 0/0, `build` exit 0, чанк OSMD отдельный, `pytest -q` 848.
- [ ] exe пересобран и запускается.

## 6. Команда и окружение (важно для следующего клиента)

- Команда живёт в DSH agent-teams. Продуктивные члены: `coder-agy` и `critic-agy`
  (модель `antigravity/gemini-3.8-flash` — включена патчем харнесса, см. HANDOFF §7).
  Остальные 4 члена — inactive/старые, удалить нельзя (API removal нет).
- Регламент: Coder пишет только по одобренному RFC; Critic аудирует план ДО кода и дифф ДО коммита;
  Lead коммитит. `send_message` у agy-членов на `"lead"` не работает — они сдают отчёт в closing message.
- Не запускать `pytest`/`pnpm build` параллельно с правками агента — ложные фейлы.
- `dist/` и `frontend/dist/` гитигнорятся; exe не в репе.
- Python: `C:\Users\Admin\AppData\Local\Python\pythoncore-3.14-64\python.exe`, `PYTHONPATH=D:\aitraining`,
  `PYTHONIOENCODING=utf-8`. Node: v26, pnpm 12.
