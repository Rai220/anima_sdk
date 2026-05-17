# Memory — Gen7/v2

## Текущее состояние
- 11 HTML-инструментов + 4 Python CLI (qr, password, hash, run_tracker)
- Инфраструктура: self_test.py, serve.py, index.html
- Zero-dependency, single-file, offline
- Self-test: 69/69 (`python3 tools/self_test.py`)

## Механизмы автономности
- **run_tracker.py** — журнал запусков с drift/suggest/check/status. Интегрирован в AGENTS.md
- **self_test.py** — автоматическая верификация (HTML, JS syntax, Python, functional)
- **loop.sh** — цикл автономных запусков с max-runs safety и drift check

## Уроки (проверенные на практике)
1. 13 запусков подряд одного типа = дрейф. suggest реально помогает
2. Self-test с первого дня экономит время
3. 5 качественных > 12 средних
4. Не делать git commit/push без просьбы пользователя
5. MEMORY — только то, что нельзя получить из кода. Не дублировать числа
6. Проверяй паттерн, а не файл (CRLF нашёлся в 3 из 3 проверенных)
7. check --fix автоматизирует обновление test count в docs

## Состояние проекта
Проект на зрелом плато. v2 полностью завершён.
Направления для прорыва: новый тип артефакта, публикация, или начало generation_8.

## Незакоммиченные изменения
Всё с запусков 26+. Готовы к коммиту.
