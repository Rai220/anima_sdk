# anima_sdk

`anima_sdk` - минимальный runtime для долгих автономных экспериментов с
агентами. Он помогает запускать агента короткими ходами, сохранять состояние в
файлах и переходить к новой генерации, когда текущий ход завершился.

SDK выделен из эксперимента [Rai220/anima](https://github.com/Rai220/anima).
В отличие от исходного эксперимента, здесь нет старых поколений, истории
`epoch_5` и демонстрационных артефактов. Это маленький набор скриптов, который
можно скопировать в любую новую задачу.

## Для чего это нужно

Обычный цикл работы:

1. Вы описываете долгую задачу в `MAIN_GOAL.md`.
2. Вы задаете правила поведения агента в `AGENTS.md`.
3. `run.sh` запускает один агентский ход.
4. `loop.sh` повторяет ходы в текущей директории, пока не появится `STOP`.
5. `meta_loop.sh` создает `generation_N` директории и переносит задачу между
   поколениями.

Агент должен оставлять важное состояние в файлах: `NOTES.md`, `TODO.md`,
`STATE.md`, `REPORT.md`, код, тесты, черновики или другие артефакты задачи.

## Требования

- Bash.
- Один из поддерживаемых agent CLI: `free-code`, `claude`, `codex`,
  `deepagents` или свой CLI через `ANIMA_HARNESS_CMD`.
- `jq` опционален, но полезен для читаемого вывода `free-code` и `claude`.

## Быстрый старт

Скопируйте SDK в отдельную директорию эксперимента:

```bash
cp -R anima_sdk my_experiment
cd my_experiment
```

Заполните `MAIN_GOAL.md`:

```markdown
## Режим
research

## Задача
Исследовать тему, собрать источники, сравнить подходы и написать отчет.

## Артефакты
`NOTES.md`, `SOURCES.md`, `REPORT.md`.

## Ограничения
Не запускать тяжелые задачи без необходимости. Проверять факты по источникам.

## Критерий готовности
Есть список источников и связный отчет с выводами.
```

При необходимости настройте `AGENTS.md`: язык, стиль работы, ограничения,
правила проверки результата и формат памяти.

Дальше выберите один из двух способов запуска. Они независимы — нужно
запустить что-то одно, а не оба сразу.

Простой непрерывный цикл в текущей директории, без поколений:

```bash
bash loop.sh
```

`loop.sh` повторяет ходы агента в той же папке, пока агент сам не создаст
файл `STOP`. Подходит для коротких задач, когда поколения не нужны и
достаточно одной рабочей директории.

Мета-цикл с поколениями `generation_N/`:

```bash
bash meta_loop.sh
```

На первом запуске `meta_loop.sh` создаст `generation_1/`, скопирует туда
`MAIN_GOAL.md`, `AGENTS.md`, `run.sh`, `loop.sh`, `harnesses/` и запустит
`loop.sh`. Если внутри поколения появится файл `STOP`, следующий цикл создаст
`generation_2/` и так далее. Подходит для долгих задач, в которых полезно
начинать каждое поколение с чистого рабочего состояния, но с накопленным
`AGENTS.md` из прошлого поколения.

## Способы запуска

Один агентский ход в текущей директории:

```bash
bash run.sh
```

Непрерывные ходы в текущей директории до появления `STOP`:

```bash
bash loop.sh
```

Полный режим с поколениями:

```bash
bash meta_loop.sh
```

Остановить текущую генерацию:

```bash
printf 'done\n' > STOP
```

Передать уточнение человеку в работающий эксперимент можно через `INBOX.md`.
Агентские инструкции в этом репозитории требуют читать `INBOX.md` в начале
хода, если файл существует.

## Настройка harness

Скопируйте пример окружения:

```bash
cp anima.env.example anima.env
```

Выберите CLI:

```bash
ANIMA_HARNESS=codex
ANIMA_MODEL=gpt-5.5
```

или запустите без файла окружения:

```bash
ANIMA_HARNESS=codex ANIMA_MODEL=gpt-5.5 bash meta_loop.sh
ANIMA_HARNESS=claude ANIMA_MODEL=claude-opus-4-7 bash meta_loop.sh
ANIMA_HARNESS=free_code bash meta_loop.sh
ANIMA_HARNESS=deepagents ANIMA_MODEL=openai:gpt-4o bash meta_loop.sh
ANIMA_HARNESS=deepagents ANIMA_MODEL=gigachat:GigaChat-3-Ultra bash meta_loop.sh
```

Для `deepagents` модель **обязательно** указывайте в формате
`provider:model` (`openai:gpt-4o`, `anthropic:claude-opus-4-7`,
`gigachat:GigaChat-3-Ultra`). В неинтерактивном режиме CLI не подхватывает
глобальный `default-model` и без префикса завершается с ошибкой
`Unable to infer a model provider for '<name>'`. В интерактивном запуске
`deepagents` префикс не нужен, потому что используется сохранённая
дефолтная модель.

Переопределить бинарь:

```bash
ANIMA_CODEX_BIN=/path/to/codex bash run.sh
ANIMA_CLAUDE_BIN=/path/to/claude bash run.sh
ANIMA_FREE_CODE_BIN=/path/to/free-code bash run.sh
ANIMA_DEEPAGENTS_BIN=/path/to/deepagents bash run.sh
```

Передать дополнительные аргументы:

```bash
ANIMA_CODEX_ARGS='--full-auto' bash run.sh
ANIMA_CLAUDE_ARGS='--permission-mode bypassPermissions' bash run.sh
ANIMA_DEEPAGENTS_ARGS='--mcp-config ./mcp.json' bash run.sh
```

Специфичные настройки `deepagents` (все опциональны):

```bash
ANIMA_DEEPAGENTS_AGENT=coder           # имя агента (-a)
ANIMA_DEEPAGENTS_SHELL_ALLOW=all       # список разрешённых shell-команд (-S)
ANIMA_DEEPAGENTS_AUTO_APPROVE=1        # авто-одобрение тулзов (-y), по умолчанию включено
ANIMA_DEEPAGENTS_MAX_TURNS=20          # лимит ходов (--max-turns)
ANIMA_DEEPAGENTS_QUIET=0               # 1 — чистый вывод для пайпа (--quiet)
```

Использовать произвольный CLI:

```bash
ANIMA_HARNESS_CMD='my-agent --task-file "$ANIMA_PROMPT_FILE"' bash run.sh
ANIMA_HARNESS_CMD='my-agent --stdin' bash run.sh
```

Команда из `ANIMA_HARNESS_CMD` запускается через `bash -lc` из директории
задачи. Текст задачи доступен как stdin и как путь в `$ANIMA_PROMPT_FILE`.

## Как запустить свой эксперимент

1. Создайте чистую директорию под эксперимент.
2. Скопируйте туда файлы SDK:

```bash
mkdir my_experiment
cp MAIN_GOAL.md AGENTS.md run.sh loop.sh meta_loop.sh anima.env.example my_experiment/
cp -R harnesses my_experiment/
cd my_experiment
```

3. Запишите задачу в `MAIN_GOAL.md`.
4. При необходимости создайте `anima.env` и выберите `ANIMA_HARNESS`.
5. Запустите один из режимов (что-то одно):

```bash
bash loop.sh        # непрерывные ходы в текущей директории, без поколений
bash meta_loop.sh   # поколения generation_N/ с переходом между ними
```

6. Если выбрали `meta_loop.sh`, смотрите результаты в `generation_1/`, затем
   в следующих `generation_N/`. Если выбрали `loop.sh`, всё происходит прямо
   в текущей директории.
7. Для ручных уточнений пишите в `INBOX.md` (в текущей директории для
   `loop.sh` или в `generation_N/INBOX.md` для `meta_loop.sh`).
8. Для остановки создайте файл `STOP` рядом с `loop.sh` (для `meta_loop.sh`
   — внутри текущего `generation_N/`).

Runtime-артефакты `STOP`, `INBOX.md`, `.free-code-logs/` и локальный
`anima.env` не предназначены для коммита в SDK. Директории `generation_N/`
можно коммитить, если нужно сохранить результаты эксперимента.

## Пример проекта

Публичный пример долгого эксперимента: [Rai220/anima](https://github.com/Rai220/anima).

Текущая рабочая ветка примера:
[Rai220/anima/tree/epoch_5](https://github.com/Rai220/anima/tree/epoch_5).

Этот репозиторий показывает исходный сценарий, из которого был выделен SDK:
автономный агент решает одну тестовую задачу из `MAIN_GOAL.md` и сохраняет
результаты по поколениям. Для новых экспериментов лучше использовать
`anima_sdk`, потому что он отделяет runtime от истории конкретного опыта.

## Структура

- `MAIN_GOAL.md` - шаблон долгой задачи.
- `AGENTS.md` - правила поведения агента.
- `run.sh` - один запуск агента.
- `loop.sh` - повторяет `run.sh` до появления `STOP`.
- `meta_loop.sh` - управляет директориями `generation_N`.
- `harnesses/` - адаптеры для конкретных agent CLI.
- `anima.env.example` - пример локальной настройки.
- `LICENSE` - лицензия MIT.

## Контракт harness

Любой harness должен:

- запускаться из директории задачи или поколения;
- читать путь к prompt из `ANIMA_PROMPT_FILE`;
- читать директорию задачи из `ANIMA_TASK_DIR`;
- опционально читать модель из `ANIMA_MODEL`;
- писать обычный вывод в stdout/stderr;
- завершаться с ненулевым кодом, если запуск агента упал.

Чтобы добавить свой переиспользуемый harness, создайте
`harnesses/name.sh`, сделайте его исполняемым и запускайте так:

```bash
ANIMA_HARNESS=name bash meta_loop.sh
```

## Релизная проверка

Перед публикацией полезно выполнить:

```bash
bash -n run.sh loop.sh meta_loop.sh harnesses/*.sh
find . -maxdepth 2 -type f | sort
```

Проверьте, что в релиз не попали локальные артефакты:

- `STOP`
- `INBOX.md`
- `.free-code-logs/`
- `anima.env`
- `.DS_Store`

## Лицензия

MIT. См. `LICENSE`.
