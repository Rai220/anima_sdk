# Benchmark Validation Example

Пример долгой агентской задачи: не запускать бенчмарк как чёрный ящик, а
последовательно валидировать его задачи. Для каждой задачи агент должен
разобрать постановку, самостоятельно решить её в отдельной рабочей директории,
проверить своё решение verifier-ом, проверить `gold`-решение тем же verifier-ом
и только после этого переходить к следующей задаче.

Локальная копия бенчмарка лежит в `source/bench/harness_bench/`. Она взята из
соседнего репозитория `../deepagents-gigachat/harness_bench/` (в исходном
репозитории директория называется `harness_bench`, хотя в задаче она была
названа `bench`).

Важно: в этой локальной копии несколько ошибок в `gold`-ответах внесены
специально. Это сделано как проверка, что агент действительно валидирует задачи,
а не просто переписывает ожидаемые ответы и не доверяет `gold` без анализа.

## Что внутри

- `MAIN_GOAL.md` — главная постановка задачи для агента.
- `AGENTS.md` — рабочие правила: проверять задачи строго по одной, вести
  журнал, не делать массовый прогон вместо анализа.
- `source/bench/harness_bench/` — локальная копия бенчмарка.
- `tools/bench_task.py` — небольшой помощник для списка задач, подготовки
  workspace, проверки `gold` и проверки ручного решения.
- `STATE.md`, `TODO.md`, `VALIDATION_REPORT.md` — стартовая файловая память.

## Как использовать

Запустить один ход из корня SDK:

```bash
ANIMA_TASK_DIR=examples/benchmark-validation bash run.sh
```

Запустить цикл с поколениями:

```bash
ANIMA_TASK_DIR=examples/benchmark-validation bash meta_loop.sh
```

Полезные команды внутри примера:

```bash
python3 tools/bench_task.py list
python3 tools/bench_task.py show task_01_create_hello
python3 tools/bench_task.py prepare task_01_create_hello --kind setup
python3 tools/bench_task.py verify task_01_create_hello work/tasks/task_01_create_hello/solution
python3 tools/bench_task.py verify-gold task_01_create_hello
```

Финальный результат работы агента должен быть в `VALIDATION_REPORT.md`: какие
задачи проверены, какие признаны корректными, где найдены ошибки, почему это
именно ошибка и какие доказательства были собраны.
