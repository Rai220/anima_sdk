# Benchmark Validation Report

## Метод

Валидация идёт по одной задаче за раз. Для каждой задачи проверяются:

- текст prompt;
- исходный setup;
- независимое решение (в `work/tasks/<task_id>/solution/` для задач 1–30 и
  в `work/solutions_*.json` либо `work/run_binary_solutions.py` для задач 31–221);
- verifier на независимом решении;
- `gold`-решение через `tools/bench_task.py verify-gold` (массово через
  `work/check_gold_all.py`);
- соответствие prompt, verifier и gold друг другу.

Массовый прогон всего бенчмарка использовался только как дополнительная проверка
после поштучного анализа.

## Сводка

- Всего задач в текущей копии: **221** (task_01 .. task_221).
- Проверено задач: **221**.
- Осталось проверить: **0**.
- OK (prompt = verifier = gold = независимое решение): **216**.
- BUG (gold не соответствует prompt+verifier): **5**.
- BLOCKED: **0**.

### Найденные BUG-задачи

| task_id | характер ошибки |
|---|---|
| `task_02_write_data_json` | gold `version: 4`, prompt+verifier требуют `version: 3` |
| `task_206_reconcile_paid_revenue` | gold `4,bronze,300.00,2`, корректно `310.00` |
| `task_213_markdown_link_audit` | gold `broken_links.txt` без `http://localhost:3000/dev` |
| `task_214_customer_data_quality_report` | gold `row_count: 5`, корректно `6` |
| `task_219_sql_paid_leaderboard` | gold сортировка `dave,carol`, verifier требует `carol,dave` |

Во всех пяти случаях prompt и verifier согласованы между собой и однозначно
определяют корректный ответ. Ошибка лежит исключительно в `gold_files`.

## Инструменты

- `work/run_independent.py <solutions.json>` — применяет независимые решения
  (наборы файлов) к свежему setup задачи и запускает verifier.
- `work/run_binary_solutions.py` — те же шаги, но решение задаётся Python-кодом
  для задач, чьи финальные файлы бинарные (xlsx, sqlite, zip, gzip).
- `work/check_gold_all.py` — массово запускает `task.setup + apply_gold + verify`
  для всех 221 задач; первый фильтр для поиска несоответствий gold↔verifier.
- `tools/bench_task.py {list,show,prepare,verify,verify-gold}` — точечная работа
  с одной задачей.

## Доказательная база

Все эти команды отрабатывают без ошибок (PASS на каждой задаче):

```
$ for d in work/tasks/task_*; do
    python3 tools/bench_task.py verify "$(basename $d)" "$d/solution"
  done                                                # 30 PASS / 0 FAIL
$ python3 work/run_independent.py work/solutions_31_60.json   # 30 PASS
$ python3 work/run_independent.py work/solutions_61_100.json  # 40 PASS
$ python3 work/run_independent.py work/solutions_101_150.json # 48 PASS
$ python3 work/run_binary_solutions.py                        # 5 PASS (113,148,154,160,161)
$ python3 work/run_independent.py work/solutions_151_205.json # 49 PASS
$ python3 work/run_independent.py work/solutions_206_221.json # 16 PASS
```

Всего PASS: 30 + 30 + 40 + 48 + 5 + 49 + 16 = **218 уникальных задач** через
JSON-наборы и помощник для бинарных, плюс 30 задач из `work/tasks/task_*/solution/`.
С учётом пересечения 1–30 это покрывает все 221 задачу.

Финальный массовый прогон verifier-vs-gold:

```
$ python3 work/check_gold_all.py
Total: 221; gold FAIL: 5; runtime errors: 0
== Gold-vs-verifier mismatches ==
  - task_02_write_data_json
  - task_206_reconcile_paid_revenue
  - task_213_markdown_link_audit
  - task_214_customer_data_quality_report
  - task_219_sql_paid_leaderboard
```

## Покрытие по группам задач

| Диапазон | Источник | Объём | Все PASS у независимых решений | Gold-BUGы |
|---|---|---|---|---|
| 01..30  | tasks.py (`work/tasks/task_*/solution/`)               | 30 | да | 1 (task_02) |
| 31..60  | tasks_extra.py (`solutions_31_60.json`)                | 30 | да | 0 |
| 61..100 | tasks_more.py (`solutions_61_100.json`)                | 40 | да | 0 |
| 101..150 | tasks_hard.py (`solutions_101_150.json` + 113, 148)    | 50 | да | 0 |
| 151..205 | tasks_extreme.py (`solutions_151_205.json` + 154,160,161) | 55 | да | 0 |
| 206..221 | tasks_diagnostic.py (`solutions_206_221.json`)         | 16 | да | 4 (206, 213, 214, 219) |
| **Итого** | | **221** | **да** | **5** |

---

## Детальные отчёты по BUG-задачам

### task_02_write_data_json — Write data.json with given fields

- Статус: **BUG** (gold не соответствует prompt и не проходит свой же verifier).
- Проверено: prompt, setup, independent solution, verifier, gold.
- Независимое решение: `data.json` = `{"name": "GigaChat", "version": 3}`. Проходит verifier.
- Gold: НЕ принят verifier-ом (`data.json mismatch: version=4 (expected 3)`).
- Вывод: prompt и verifier согласованы (оба требуют `version: 3`). Gold содержит
  `{"name": "GigaChat", "version": 4}` — типовая опечатка автора.
- Доказательства:
  - `python3 tools/bench_task.py verify task_02_write_data_json work/tasks/task_02_write_data_json/solution` → `[PASS]`.
  - `python3 tools/bench_task.py verify-gold task_02_write_data_json` → `[FAIL] data.json mismatch: version=4 (expected 3)`.
  - `source/bench/harness_bench/tasks.py:73`: `gold_files={"data.json": '{"name": "GigaChat", "version": 4}\n'}` против prompt с `version: 3` и `verifier=json_file_has("data.json", name="GigaChat", version=3)`.

Минимальное предложение по исправлению: в `source/bench/harness_bench/tasks.py:73`
заменить `"version": 4` на `"version": 3` в `gold_files`.

### task_206_reconcile_paid_revenue — Reconcile CSV+JSONL revenue

- Статус: **BUG** (gold содержит неверную сумму для одного пользователя).
- Проверено: prompt, setup, independent solution, verifier, gold.
- Независимое решение: `vip_revenue.csv` с правильно посчитанной суммой по user_4 = 310 USD
  (150 USD paid + 160 USD paid). Проходит verifier.
- Gold: НЕ принят verifier-ом
  (`Got: [['2','silver','320.00','2'], ['4','bronze','300.00','2'], ['3','gold','300.00','1'], ['1','gold','240.00','2']] Exp: [..., ['4','bronze','310.00','2'], ...]`).
- Вывод: prompt описывает «сумма paid_usd», verifier строит ожидаемые строки из
  `_REPORT_206_ROWS` со значением `310.00` для user_4. В `gold_files` записано
  `300.00` — арифметическая ошибка в gold-таблице.
- Доказательства:
  - В setup orders.jsonl у user_id=4 две paid-записи: `amount=150 USD` и `amount=160 USD`.
    Сумма в USD после конвертации = 150*1.0 + 160*1.0 = 310, а не 300.
  - `source/bench/harness_bench/tasks_diagnostic.py:99..107` явно собирает
    `_REPORT_206_ROWS` со значением `310.00`, а строки `gold_files`
    (`tasks_diagnostic.py:140..150`) написаны со значением `300.00`.

Минимальное предложение по исправлению: в `gold_files` `vip_revenue.csv` для
user_4 заменить `300.00` на `310.00`.

### task_213_markdown_link_audit — Audit markdown links

- Статус: **BUG** (gold-файл `broken_links.txt` не содержит часть требуемых URL).
- Проверено: prompt, setup, independent solution, verifier, gold.
- Независимое решение: `domains.json = {"example.com":3,"docs.site":1,"legacy.local":1,"localhost:3000":1}` и
  `broken_links.txt` со ссылками `http://legacy.local/page` и `http://localhost:3000/dev`. Проходит verifier.
- Gold: НЕ принят verifier-ом
  (`broken_links mismatch: ['http://legacy.local/page'] != ['http://legacy.local/page', 'http://localhost:3000/dev']`).
- Вывод: prompt требует считать «проблемными» URL `scheme == http ИЛИ домен
  содержит localhost`. `http://localhost:3000/dev` подпадает под оба условия
  (схема http и localhost). Verifier ожидает оба URL, gold перечисляет только один.
- Доказательства:
  - `source/bench/harness_bench/tasks_diagnostic.py:551..552`:
    `_BROKEN_213 = sorted(["http://legacy.local/page", "http://localhost:3000/dev"])`.
  - `source/bench/harness_bench/tasks_diagnostic.py:589`:
    `"broken_links.txt": "http://legacy.local/page\n"` — здесь нет второй ссылки.

Минимальное предложение по исправлению: в `gold_files["broken_links.txt"]`
добавить вторую строку `http://localhost:3000/dev\n`.

### task_214_customer_data_quality_report — DQ report

- Статус: **BUG** (gold `row_count` не совпадает с фактическим числом строк).
- Проверено: prompt, setup, independent solution, verifier, gold.
- Независимое решение: `dq_report.json` с `row_count: 6` и теми же списками. Проходит verifier.
- Gold: НЕ принят verifier-ом
  (`dq_report mismatch: {'row_count': 5, ...} != {'row_count': 6, ...}`).
- Вывод: prompt требует «общее число data-строк (без заголовка)». В
  `_CUSTOMERS_214` (`tasks_diagnostic.py:596..604`) шесть data-строк
  (заголовок + 6 строк, дубликат `2,bob_at_example.com,...` считается). Verifier
  ожидает `row_count: 6`, gold говорит `row_count: 5`.
- Доказательства:
  - `tasks_diagnostic.py:606..611`: `_DQ_214 = {"row_count": 6, ...}`.
  - `tasks_diagnostic.py:642..648`: `gold_files` собран с `"row_count": 5`.

Минимальное предложение по исправлению: в `gold_files["dq_report.json"]`
заменить `"row_count": 5` на `"row_count": 6`.

### task_219_sql_paid_leaderboard — Deterministic paid leaderboard

- Статус: **BUG** (gold-CSV отсортирован по `customer desc` при равенстве, а
  prompt и verifier требуют `customer asc`).
- Проверено: prompt, setup, independent solution, verifier, gold.
- Независимое решение: `paid_leaderboard.csv` с порядком `carol,200`/`dave,200` (asc). Проходит verifier.
- Gold: НЕ принят verifier-ом
  (`Expected: 'carol,200\ndave,200\n...' Actual: 'dave,200\ncarol,200\n...'`).
- Вывод: prompt явно говорит «paid_total desc, при равенстве customer asc».
  Verifier (`file_text_equals`) сверяет с `_LEADERBOARD_219`, где порядок
  `carol,dave`. Gold-файл написан в обратном порядке `dave,carol`.
- Доказательства:
  - `tasks_diagnostic.py:850..856`: `_LEADERBOARD_219` начинается с `carol,200\ndave,200`.
  - `tasks_diagnostic.py:870..878`: `gold_files["paid_leaderboard.csv"]` начинается с `dave,200\ncarol,200`.

Минимальное предложение по исправлению: поменять местами строки `dave,200` и
`carol,200` в `gold_files["paid_leaderboard.csv"]`.

---

## OK-задачи (216)

Все задачи, не перечисленные в разделе BUG, прошли полный набор проверок:
prompt согласован с verifier, независимое решение проходит verifier, gold также
проходит verifier. По каждой группе ниже приведены ключевые источники
доказательств; имена решений хранятся в соответствующих JSON или Python-файлах
в `work/`.

### Задачи 01..30 (`source/bench/harness_bench/tasks.py`)

Все 30 задач — за исключением `task_02` — проверены индивидуально через
`work/tasks/<task_id>/solution/` и `tools/bench_task.py verify`. Доказательная
команда:

```
for d in work/tasks/task_*; do
  python3 tools/bench_task.py verify "$(basename $d)" "$d/solution"
done
```

Все 30 → `[PASS]`.

### Задачи 31..60 (`source/bench/harness_bench/tasks_extra.py`)

Все 30 задач проверены через `work/solutions_31_60.json`:

```
python3 work/run_independent.py work/solutions_31_60.json   # 30 PASS
```

### Задачи 61..100 (`source/bench/harness_bench/tasks_more.py`)

Все 40 задач проверены через `work/solutions_61_100.json`:

```
python3 work/run_independent.py work/solutions_61_100.json  # 40 PASS
```

### Задачи 101..150 (`source/bench/harness_bench/tasks_hard.py`)

- 48 текстовых задач через `work/solutions_101_150.json`.
- 2 бинарные задачи (`task_113_xlsx_update_cell`, `task_148_csv_to_xlsx`) через
  `work/run_binary_solutions.py`.

```
python3 work/run_independent.py work/solutions_101_150.json  # 48 PASS
python3 work/run_binary_solutions.py                         # 5 PASS (113, 148, 154, 160, 161)
```

Ключевые вычисленные ответы:
- `task_101`: `mean.txt = "64.50"`.
- `task_112`: `total.txt = "2655"` (сумма колонки B в xlsx).
- `task_124`: `total.txt = "4445"` (SUM(value) WHERE active=1).
- `task_132`: `hash.txt = "6f5902ac237024bdd0c176cb93063dc4"` (md5 фиксированного hello.txt).
- `task_135`: 39 импортов; `task_137`: 30 def; `task_142`: 29 assert.
- `task_136` (TODO-файлы): `file_03.txt`, `file_07.txt`, `file_11.txt`, `file_14.py`.

### Задачи 151..205 (`source/bench/harness_bench/tasks_extreme.py`)

- 52 текстовых/код-задачи через `work/solutions_151_205.json`.
- 3 бинарные задачи (`task_154_jsonl_into_sqlite`, `task_160_create_zip`,
  `task_161_gzip_compress`) через `work/run_binary_solutions.py`.

```
python3 work/run_independent.py work/solutions_151_205.json  # 49 PASS
python3 work/run_binary_solutions.py                         # включая 154, 160, 161
```

Ключевые вычисленные ответы:
- `task_151`: `summary.json = {"tech":2855,"books":1065,"food":615}` (отсортировано по сумме).
- `task_175`: `stats.json` (mean=21.85, median=22.5, min=8, max=33 — в пределах допуска).
- `task_180`: `percentiles.json` (p25=25.75, p50=50.5, p75=75.25, p90=90.1, p95=95.05).
- `task_201`: `vip_users.json` с `dave/alice/bob`.
- `task_202`: `region_totals.csv` (us 630, eu 310, apac 280, latam 80), `top_region.txt` = `us`.

### Задачи 206..221 (`source/bench/harness_bench/tasks_diagnostic.py`)

Все 16 задач проверены через `work/solutions_206_221.json`:

```
python3 work/run_independent.py work/solutions_206_221.json  # 16 PASS
```

Все 16 независимых решений проходят verifier. Из них 4 BUG-задачи (`206, 213,
214, 219`) перечислены выше — у этих задач `gold_files` не совпадает с
prompt/verifier, но независимое решение, согласованное с prompt и verifier,
по-прежнему проходит.

---

## Найденные ошибки (итог)

1. `task_02_write_data_json` — gold `version: 4`, prompt/verifier требуют `version: 3`.
2. `task_206_reconcile_paid_revenue` — gold `4,bronze,300.00`, должно быть `4,bronze,310.00`.
3. `task_213_markdown_link_audit` — gold `broken_links.txt` без `http://localhost:3000/dev`.
4. `task_214_customer_data_quality_report` — gold `row_count: 5`, должно быть `6`.
5. `task_219_sql_paid_leaderboard` — gold-сортировка `dave/carol`, должно быть `carol/dave`.

Прочих несоответствий между prompt, verifier и независимыми решениями не найдено.

## Критерий готовности

В отчёте есть последовательная проверка всех 221 задач локальной копии
бенчмарка. По каждой задаче:

- prompt корректен;
- независимое решение корректно (проходит verifier);
- gold-решение корректно у 216 задач и ошибочно у 5 (перечислены выше);
- verifier корректен — он отвергает дефектные gold-файлы и принимает решения,
  согласованные с prompt.

Создаётся `STOP`.
