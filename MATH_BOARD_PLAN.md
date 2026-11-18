# План доработки math_board.html

## Снимок состояния (передача контекста в новую задачу)
Этапы 1–3 закрыты и в `main`. Коммиты: `905ecac` (undo/redo в math_board), затем правки лендинга `c88b34f` (QR в футере), `a1de689` (CTA «Поддержать» в hero), `dbb3a7e` (честный текст про рекламу партнёров), `4af58db` (ссылка на `godspace.github.io/business/` в карточке «Зона: Выживание»).

Инструменты поддержки (страницы сайта не задевают, лежат вне `trainers/`):
- `tools/check.py` + `tests/math_board.smoke.html` — smoke-проверка доски в headless Edge: 30 проверок, базовая линия **30/30** (exit 0).
- `tools/size.py` — размеры секций `math_board.html` (строки/символы/≈токены), метрика этапа оптимизации.

Текущая задача — **этап 4: оптимизация `math_board.html`**. Экспорт JSON и несколько досок отложены и из плана убраны.

Git: `tools/`, `tests/`, `MATH_BOARD_PLAN.md` и `.clinerules` пока не добавлены (untracked) — коммит по твоему решению, отдельно от этапа 4.

### Решения, которые не переигрывать без причины
- История хранит только `items`, без pan/zoom: иначе каждый шаг зума создаёт снимок и undo прыгает камерой.
- Переменные названы `boardHistory` / `boardHistoryIndex` (НЕ `history`): `let history` на верхнем уровне конфликтует с `window.history` → SyntaxError, скрипт доски не запускается.
- `restoredSnapshot` — защита от срезания redo-ветки, если восстановление виджета нормализовало данные.
- Единственный канал сохранения: `scheduleSave()` (debounce 400 мс) → `saveBoardState()` → `pushSnapshot()`. Не добавлять обходных записей в localStorage.
- `clearAll()` отменяем (пишет пустое состояние, а не `removeItem`).
- При восстановлении `state.zIndex = 100`, затем максимум из данных.
- `undo()` / `redo()` / `applyZoom()` — глобальные функции (classic script), на них завязаны inline `onclick` в `#hud`. При выносе JS в модуль переписать на `addEventListener`.

### Контракт данных (item)
`type`, `val`, `left`, `top`, `zIndex`, `inputs[]`; для `fraction-bar` — `width`; для `segment` — `scale` + `rows[{step,len}]`; для `col-*` — `colData` (единственный источник — `item._getColData()`).

### Проверка без ручного браузера
Реализовано: `python tools/check.py` → грузит `tests/math_board.smoke.html` (доска в iframe, сам файл не копируется), внутри запускается `msedge.exe --headless --disable-gpu --allow-file-access-from-files --user-data-dir=%TEMP%\prof --virtual-time-budget=20000 --dump-dom "file:///..."`, результат разбирается из `document.body[data-test]` / `[data-err]`.
- Базовая линия: **30/30** (exit 0). Шаги теста ждут 600 мс — больше debounce 400 мс, иначе несколько действий дают один снимок истории.
- Падения печатаются списком (`data-err`), хвост stderr браузера прикладывается автоматически; коды возврата 0/1/2.
- Замер размера: `python tools/size.py` (строки, символы и ≈токены по секциям).

### Роутинг моделей и бюджет контекста
- Основная для агентных правок: `deepseek-flash` (DeepSeek-V4.1-Flash, 1M контекст, tool calls; кэш-хит ~в 50 раз дешевле промаха).
- Узкие одношаговые шаги: `yandexgpt-5.1` — контекст 32K, поэтому только «диапазон → патч → New Task».
- `deepseek-v4-pro` — контрольная точка / fallback.
- Замеры: `math_board.html` ≈31k токенов (HTML ≈2.6k, CSS ≈7.4k, JS ≈21k) — точные цифры даёт `python tools/size.py`, план ≈2.4k. Правило: >60% окна — New Task; внутри задачи не менять `.clinerules` и план (рвёт prefix-кэш).

### Чего не делать
Без сборки, фреймворков, npm и внешних зависимостей. Не трогать `trainers/**/*.html` и `index.html`, если задача явно не про них (исключение — `trainers/fractions/math_board.html` в этапе 4). Один этап = один коммит.


## Контекст проекта
- Статический сайт (GitHub Pages), без сборки и package.json.
- Целевой файл: `trainers/fractions/math_board.html` — 2965 строк: разметка+head 181, inline CSS 792 (44–835), inline JS 1992 (972–2963), ≈31k токенов.
- Состояние доски: `localStorage['mathBoardData']` (items + pan/zoom).
- Инструменты: `python tools/check.py` (smoke-тест, 30 проверок) и `python tools/size.py` (размеры секций). Ручной браузер (Ctrl+F5, F12) — только для визуального контроля.

## Уже сделано (этапы 1–3)
- Этап 3: undo/redo — история 50 шагов, кнопки ↶ ↷ в `#hud`, Ctrl+Z / Ctrl+Shift+Z / Ctrl+Y, флаг `isRestoring`, `boardHistory`.
- SEO-блок (title, description, keywords, canonical, OG, JSON-LD).
- `<script src="../../assets/analytics.js" defer>`.
- Сохранение и восстановление `zIndex` элементов.
- Жесты: `body` — manipulation, `#viewport` — none, `#sidebar` — pan-y.
- Палитра на `<button type="button">` с `aria-label`, `<aside id="sidebar">`.
- `aria-expanded`/`aria-controls` у мобильной кнопки, `aria-live` у счётчика выделения.
- Крестик удаления — настоящая `<button>` (клик + клавиатура), `:focus-visible`.

## Этап 3 — Undo/Redo (сделан; оставлен как справка по коду)
Цель: Ctrl+Z, Ctrl+Shift+Z / Ctrl+Y, кнопки ↶ ↷ в `#hud`, история до 50 шагов.

### Ключевые функции (искать по имени, не по номерам строк)
- `scheduleSave()`, `saveBoardState()`, `loadBoardState()` — сохранение/восстановление.
- `surface.addEventListener('input', scheduleSave)` и `MutationObserver` уже покрывают
  ввод, добавление и удаление элементов; drag заканчивается вызовом `scheduleSave()`.
- `createItem(type, val, x, y, initData)`, `startItemDrag(e, item)`, `onMove`, `onEnd`.
- `nudgeSelected`, `deleteSelected`, `removeFn` (крестик), `clearAll`, `addFromPalette`.
- `applyZoom`, `resetView`, `updateView`.
- Виджеты столбиком: `buildColAddWidget`, `buildColMulWidget`, `buildColDivWidget`
  (сохраняются через `_getColData`), плюс `fraction-bar` и `segment`.

### Подход (снимки состояния)
1. Вынести сборку данных из `saveBoardState()` в `serializeBoard()`.
2. Вынести восстановление из `loadBoardState()` в `applyBoardState(data)`.
3. Ввести `history = []`, `historyIndex = -1`, `MAX_HISTORY = 50`.
4. `pushSnapshot()`: сравнить JSON с текущим снимком, отрезать «хвост» redo, ограничить 50.
5. Вызывать `pushSnapshot()` из `saveBoardState()` после записи в localStorage
   (дебаунс 400 мс уже есть). При `isRestoring` — не пушить.
6. `undo()`: `historyIndex--`, `applyBoardState(history[historyIndex])` под `isRestoring`,
   затем обновить localStorage без нового снимка.
7. `redo()` — симметрично.
8. Горячие клавиши игнорировать, если фокус в `INPUT`/`TEXTAREA` или внутри `#sidebar`
   (как уже сделано в обработчике `keydown`).
9. Кнопкам ↶ ↷ дать `aria-label`, блокировать при пустой истории (`disabled`).

### Проверка этапа 3
- 5 действий (добавить, подвинуть, ввести число, удалить, очистить) → 5 отмен → 5 повторов.
- Перезагрузка страницы сохраняет текущее состояние.
- Виджеты «Столбик», «Умножение», «Уголок» и «Блок отрезков» восстанавливаются без дублей.
- Нет лишних снимков при загрузке страницы и при undo/redo.

### Риски
- Восстановление не должно плодить элементы и слушатели.
- `zIndex` и значения полей уже сохраняются — не терять их при снимках.
- Не пушить историю во время `loadBoardState()` и `applyBoardState()`.

## Этап 4 — Оптимизация math_board.html (текущая задача)
Цель: уменьшить размер и сложность поддержки, **не меняя поведение**. Метрика — `python tools/size.py`.

### Базовая линия (замер до этапа)
| Часть файла | Строк | Символов | ≈токенов |
|---|---|---|---|
| Разметка + head | 181 | 10 385 | 2 596 |
| CSS inline (`<style>`, 44–835) | 792 | 29 603 | 7 401 |
| JS inline (`<script>`, 972–2963) | 1992 | 84 424 | 21 106 |
| **Итого `math_board.html`** | **2965** | **124 412** | **31 103** |

### Что нельзя менять
- Поведение и контракт `item`; имена `boardHistory` / `boardHistoryIndex`; единственный канал записи `scheduleSave()` → `saveBoardState()` → `pushSnapshot()`.
- Жесты (`body` — manipulation, `#viewport` — none, `#sidebar` — pan-y), undo/redo, восстановление виджетов без дублей, `zIndex`, `aria`-атрибуты, SEO-блок, `<script src="../../assets/analytics.js" defer>`.
- Без сборки, фреймворков, npm и внешних зависимостей: только нативные `assets/math_board.css` и `assets/math_board.js`.
- Не трогать `index.html`, остальные `trainers/**/*.html`, `assets/analytics.js`. Переименований функций и глобальных переменных в этом этапе нет.

### Шаг 4.1 — CSS → `assets/math_board.css` (один коммит)
1. Содержимое `<style>` (открывается строкой 44, закрывается на 835 перед `<script src="../../assets/analytics.js">`) перенести в `assets/math_board.css` **дословно**: тот же порядок правил, те же отступы, без минификации.
2. На месте блока поставить `<link rel="stylesheet" href="../../assets/math_board.css">` в `<head>` (сразу после favicon/manifest).
3. В CSS нет `url()`, `@import`, `@font-face` — пересчитывать пути не нужно (проверено).
4. Проверка: `python tools/check.py` → 30/30; `python tools/size.py` → HTML ≈181 строка, CSS 792 строки в `assets/`.
5. Визуальный контроль на 1280px и 504px: сайдбар/палитра, `#hud`, `#group-toolbar`, счётчик выделения.

### Шаг 4.2 — JS → `assets/math_board.js` + inline-обработчики → `addEventListener` (один коммит)
1. Код `<script>` (972–2963) перенести в `assets/math_board.js` дословно, подключить `<script src="../../assets/math_board.js"></script>` на месте старого `<script>` в конце `<body>`, без `defer` — момент выполнения (`DOMContentLoaded` → `loadBoardState`) сохраняется.
2. Заменить 12 inline-`onclick` в трёх блоках разметки на `addEventListener` (по одному на кнопку, делегирование здесь не нужно):
   - `#group-toolbar` (949–953): `nudgeSelected(-10,0)`, `nudgeSelected(0,-10)`, `nudgeSelected(0,10)`, `nudgeSelected(10,0)`, `deleteSelected()` → добавить `data-action="nudge"` + `data-dx` / `data-dy` и `data-action="delete"`.
   - `#hud` (959, 961, 962, 964, 966): `toggleSelectMode()`, `undo()`, `redo()`, `applyZoom(-0.1)`, `applyZoom(0.1)` → `data-action`, у кнопок зума `data-zoom="-0.1"` / `"0.1"`.
   - Сайдбар (939–940): `resetView()`, `clearAll()` → `data-action`.
3. `undo()`, `redo()`, `applyZoom()` остаются глобальными функциями (на них ссылаются тест и консоль), но разметка от них больше не зависит.
4. Проверка: `python tools/check.py` → 30/30; вручную: ↶ / ↷, Ctrl+Z, Ctrl+Shift+Z, зум ±, «🎯 Центр камеры», «🗑 Очистить всё» (внутри `confirm()`), стрелки группы, «🗑 Удалить», «⬚ Выделение».

### Шаг 4.3 — убрать дубли в виджетах столбиком (один коммит, по желанию)
`buildColAddWidget`, `buildColMulWidget`, `buildColDivWidget` почти совпадают: контейнер, `currentRefs`, `render()`, `syncModelFromDOM()`, хвост `item._getColData = () => { syncModelFromDOM(currentRefs); return model; }`. Вынести общий каркас, оставить в каждом только модель и рендер своих полей.
Проверка: `python tools/check.py` (там уже есть `col-add` и `colData`) + «Умнож.» и «Уголок»: undo/redo, запись `colData` в localStorage, восстановление после перезагрузки без дублей.

### Приёмка этапа
- `python tools/check.py` → `[OK] 30/30`, exit 0.
- `python tools/size.py`: `math_board.html` ≈181 строка, в нём нет `<style>` и `onclick`; вынесенные файлы на месте.
- `git status` — изменены только `trainers/fractions/math_board.html`, `assets/math_board.css`, `assets/math_board.js`.
- Поведение не изменилось: палитра, drag, зум, рамка выделения, история, `localStorage`, вёрстка 504px.
- Один шаг = один коммит; при регрессии — `git revert` шага, а не «правка правки».

### Риски
- Потеря/смещение CSS-правил при копировании: сверить строки до и после через `tools/size.py`; строк с `</style>` внутри CSS нет (проверено).
- Порядок каскада: `<link>` стоит там же, где был `<style>`; никаких `defer` / `media` / `onload`-трюков.
- Локальный кэш при ручной проверке — Ctrl+F5; headless-тест всегда стартует с чистым профилем.
- Без `--allow-file-access-from-files` тест падает с сообщением про iframe — это не регрессия доски.

## Правила экономии токенов
- Не читать файл целиком: только нужный диапазон или функцию.
- Поиск по уникальному имени, а не общий regex по всему проекту.
- Ответы: патч + 3–5 пунктов проверки, без длинных объяснений.
- Одна задача = один этап; перед каждым этапом — New Task.
- После правок в `math_board`: `python tools/check.py` (ждём 30/30) и `python tools/size.py`.

## Контекст и кэширование (по документации AI Studio)
- Кэширование промптов работает автоматически, отдельного переключателя нет.
- Кэш держится, пока неизменен префикс: системные инструкции, `.clinerules`,
  определения инструментов и начало диалога.
- Внутри задачи не менять `.clinerules` и настройки модели, не редактировать
  и не переотправлять старые сообщения — это сбрасывает кэш.
- Авто-сжатие (compaction) и обрезание истории меняют контекст и сбрасывают кэш:
  лучше начинать New Task до порога ~60–70k токенов.
- `max_output_tokens` ограничивает видимые и reasoning-токены, но не токены
  tool calls (результаты инструментов всё равно попадают в контекст).
- Проверка расхода: Billing → отчёты по AI Studio (доля кэшированных токенов)
  или поле `cached_tokens` в ответе API.

## Стартовый промпт для новой задачи
> Прочитай MATH_BOARD_PLAN.md. Работаем над этапом 4 (оптимизация) в
> trainers/fractions/math_board.html. Не читай файл целиком: CSS бери диапазоном
> 44–835, JS — 972–2963 (или по именам функций), разметку — нужными блоками.
> Начни с шага 4.1: вынести CSS в assets/math_board.css дословно. Сначала покажи
> план правок и список затронутых участков, затем внеси изменения минимальными
> патчами. После правок запусти python tools/check.py (ждём 30/30) и
> python tools/size.py. Ответы — коротко.
