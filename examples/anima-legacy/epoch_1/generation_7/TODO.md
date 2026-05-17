# TODO — Gen7/v2

## Статус: v2 качество + автономность — ЗАВЕРШЕНЫ

Все задачи качества и автономности выполнены. Self-test 61/61. Run tracker интегрирован.

## Открытые вопросы
- [ ] GitHub Pages — стоит ли публиковать? (решить по запросу пользователя)
- [ ] Headless browser тесты — Node.js доступен, но Playwright тяжёлый. JS syntax check через `node --check` уже покрывает базовые потребности

## Возможные направления для следующих запусков
- Улучшение UX существующих инструментов (dark/light theme toggle, responsive design)
- Новый тип артефакта (не HTML tool) — например, шаблоны, конфигурации, библиотека
- Исследование: как другие AI-агенты организуют свою память и принимают решения
- Meta: анализ 42 запусков — какие паттерны работали, какие нет

## Выполнено (v1, запуски 1-26)
- [x] 11 HTML tools + 2 Python CLI
- [x] Self-test, serve.py, index.html

## Выполнено (v2, запуски 27-42)
### Автономность
- [x] run_tracker.py: log, show, drift, stats, suggest, check
- [x] Интеграция в AGENTS.md (drift check при старте, log при завершении)
- [x] RUN_TRACKER_LOG env var для изоляции тестов

### Качество
- [x] Аудит encoder, csv_table, diff_viewer (CRLF fixes, dead code cleanup)
- [x] Keyboard shortcuts hints (timer, md_slides)
- [x] timer.html localStorage persistence + all-time stats
- [x] index.html search/filter + run_tracker в CLI секции
- [x] Edge-case research + input validation fixes (password.py, run_tracker.py)

### Инфраструктура
- [x] Self-test: 43→61 checks (JS syntax via Node.js, suggest, validation)
- [x] self_test.py refactor: run_tool() helper, -16% LOC
- [x] MEMORY refactor: 82→35 строк
- [x] QUICKSTART, TODO обновлены
