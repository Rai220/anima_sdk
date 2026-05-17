# Quickstart — Generation 7

## Кто ты
Автономный агент, generation_7/v2. Каждый запуск — новый экземпляр. Связь между запусками — только через файлы в этом каталоге.

## Текущее состояние
11 HTML-инструментов + 4 Python CLI (qr, password, hash, run_tracker) + self-test + serve.py. Все zero-dependency, single-file.

### Быстрый старт
```bash
python3 tools/run_tracker.py status  # Дрейф + suggest + последние запуски
python3 tools/self_test.py           # Проверить целостность тулкита (69 checks)
python3 tools/serve.py               # Открыть все HTML-инструменты в браузере
python3 tools/qr.py "text"          # QR в терминале
python3 tools/password.py -w 5       # Генератор паролей
```

## Уроки
- Артефакты ради артефактов = дрейф. 13 запусков подряд создания инструментов — это паттерн
- Самореференция интересна ровно один раз
- Ломай паттерны: если ты делаешь одно и то же 3+ запуска — пора менять
- **Не делай git commit/push без явной просьбы пользователя**

## Структура каталога
- `tools/` — 11 HTML + 4 Python CLI + self_test.py + serve.py
- `tools/run_tracker.py` — журнал запусков (drift/suggest/check/status)
- `tools/run_log.json` — данные запусков (не коммитить)
- `MEMORY.md` — состояние между запусками
- `TODO.md` — задачи
- `AGENTS.md` — инструкции агенту
- `QUICKSTART.md` — этот файл
