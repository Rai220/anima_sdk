# Lessons

## Процесс

- Валидация 221 задачи поштучно вручную слишком медленна. Эффективный шаблон:
  для каждой задачи внимательно читаешь `prompt`/`setup_files`/`verifier`/`gold`,
  но независимое решение для большинства одинаковых по форме задач удобно
  кодировать как строку в JSON-файле `work/solutions_*.json` и применять через
  `work/run_independent.py`. Verifier при этом запускается из стандартного
  setup, поэтому проверка остаётся честной.
- Для задач с бинарными артефактами (xlsx, sqlite, zip, gzip, tar) JSON-строка
  не подходит — решение пишется как Python-функция в `work/run_binary_solutions.py`.
- Массовая проверка `work/check_gold_all.py` (запускает `setup + apply_gold +
  verify` для каждой задачи) — дешёвый, но полезный фильтр для несоответствий
  между verifier и gold. FAIL в этом скане — кандидат на BUG, но требует
  персонального разбора.
- Прохождение «независимое решение PASS + gold PASS» — самый строгий критерий
  согласованности. Если независимое решение PASS, а gold FAIL — однозначно BUG
  в gold.

## API бенчмарка

- `Task.setup(ws)` сначала применяет `setup_files` (строки/None), потом
  `setup_callback` (произвольная подготовка, например запись sqlite, xlsx, tar).
- `Task.apply_gold(ws)` сначала применяет `gold_files` (значения `None` удаляют
  файл), потом `gold_callback`. Поэтому gold может содержать бинарные файлы
  только через `gold_callback`.
- Verifier — функция `Path -> VerifyResult`. Удобные комбинаторы:
  `all_of(...)`, `file_text_equals`, `file_lines_equal`, `file_matches_regex`,
  `file_contains`, `file_not_contains`, `json_file_has`, `python_runs`,
  `python_callable_returns`, `pytest_passes`, `xlsx_cell_equals`,
  `sqlite_query_returns`.
- В `tasks_diagnostic.py` есть свой кастомный `_json_file_matches_loose`,
  который сравнивает JSON-структуры с возможной нечувствительностью к порядку
  элементов в списке словарей.

## Полезные команды

```
python3 tools/bench_task.py list
python3 tools/bench_task.py show <task_id>
python3 tools/bench_task.py prepare <task_id> --kind setup --out work/tasks/<task_id>/setup --force
python3 tools/bench_task.py prepare <task_id> --kind gold  --out work/tasks/<task_id>/gold  --force
python3 tools/bench_task.py verify <task_id> work/tasks/<task_id>/solution
python3 tools/bench_task.py verify-gold <task_id>

python3 work/run_independent.py work/solutions_206_221.json
python3 work/run_binary_solutions.py
python3 work/check_gold_all.py
```

## Особенности конкретных задач

- `pytest_passes("tests")` запускает `pytest` в подкаталоге `tests`, поэтому
  тестируемый код должен импортироваться из текущего рабочего каталога
  (например, `from intervals import merge_intervals` работает только если
  `intervals.py` лежит в корне рабочей директории).
- В `task_148_csv_to_xlsx` верификатор требует, чтобы числовые значения в xlsx
  были целыми (`int`), а не строками. Поэтому при чтении CSV нужно делать
  `int(row[1])` перед `sh.append(...)`.
- `task_154_jsonl_into_sqlite` проверяет конкретный порядок столбцов
  `id, kind, value` и наличие именно колонки `id INTEGER PRIMARY KEY`. Для
  фиксированного порядка `id` достаточно `ORDER BY id`.
- `task_220_python_import_migration` использует `pytest_passes("tests")`, и в
  setup тестовый файл импортирует `src.utils.math`; решение должно одновременно
  переписать `tests/test_main.py` под новый путь и удалить `src/utils/math.py`,
  иначе pytest найдёт старую цепочку импортов и тесты упадут.

## Найденные BUG-шаблоны

- gold-таблица, собранная вручную, расходится с генератором ожидаемых строк в
  verifier (`task_206`: `300.00` vs `310.00`; `task_219`: порядок `dave,carol`).
- gold забывает часть условий из prompt (`task_213`: «или localhost» —
  забыли); проверка через verifier ловит это сразу.
- gold забывает учесть строки/дубликаты при подсчёте (`task_214`: `row_count:
  5` вместо 6).
- gold содержит лишнюю инкрементацию или другую опечатку (`task_02`: `version: 4`).

## Что НЕ помогло

- Полностью полагаться на gold как на эталон: в 5 случаях gold ошибочен.
  Эталон — это «prompt → verifier». Если они согласованы, а gold им
  противоречит, значит баг в gold.
- Запускать `python3 run.sh` / полный benchmark в надежде, что он подскажет
  ошибку: он бы сначала позвал модель, а уже потом проверял. Гораздо быстрее
  читать `tasks_*.py` и сравнивать gold с verifier напрямую.
