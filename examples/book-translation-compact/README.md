# Compact Article Translation Example

Минимальный пример долгой агентской задачи: перевести длинную HTML-статью на
русский язык и получить читаемый HTML с переведёнными иллюстрациями, не публикуя
рабочие логи и тяжёлые промежуточные артефакты.

Этот пример сделан как компактная версия `examples/whats-our-problem-translate`.
В большом примере накопились реальные поколения, отчёты, сборки и логи; здесь
оставлен шаблон, который удобно положить в публичный репозиторий.

## Готовый перевод

В репозитории сохранена завершённая `generation_1/` с переводом двух постов
Тима Урбана Wait But Why («От 1 до 1 000 000» и «От 1 000 000 до числа Грэма»).

**Читать онлайн:** [От 1 до числа Грэма — сводный перевод](https://rai220.github.io/anima_sdk/waitbutwhy-numbers-combined.ru.html)

Исходник: `source/waitbutwhy-numbers-combined.html` и `source/images/`.
Итог в репозитории: `generation_1/out/waitbutwhy-numbers-combined.ru.html` и
`generation_1/out/images/`. Публикация на GitHub Pages обновляется workflow
`.github/workflows/book-translation-compact-pages.yml` при пуше в `main`.

В начале HTML есть краткий дисклеймер «От переводчика» с ссылками на оригиналы
на waitbutwhy.com.

## Что внутри

- `MAIN_GOAL.md` — основная задача для агента.
- `AGENTS.md` — рабочие правила: как переводить, что проверять, куда писать
  состояние.
- `source/` — исходный HTML и картинки (не менять).
- `generation_1/` — завершённое поколение с переводом, скриптами и памятью
  (`STATE.md`, `TRANSLATION_NOTES.md`, `work/translate_image_caption.py`).
- `STATE.md`, `TODO.md` — шаблоны памяти в корне примера (для новых запусков).
- `TRANSLATION_NOTES.md` — один компактный файл вместо отдельных
  `GLOSSARY.md`, `STYLE_GUIDE.md`, `STRUCTURE.md` и `FIGURES.md`.
- `.gitignore` — защита от случайной публикации логов, `INBOX.md`, `STOP` и
  лишних `generation_*` (кроме явно разрешённой `generation_1/`).

## Как использовать

1. Исходник уже лежит в `source/`. Для своей статьи замените HTML и картинки и
   обновите `MAIN_GOAL.md`.

2. Запустите один агентский ход из корня SDK:

   ```bash
   ANIMA_TASK_DIR=examples/book-translation-compact bash run.sh
   ```

3. Или запустите цикл с поколениями:

   ```bash
   ANIMA_TASK_DIR=examples/book-translation-compact bash meta_loop.sh
   ```

Агент читает исходный HTML из `source/`, пишет промежуточные файлы в `work/`,
результаты в `out/`, а решения и состояние — в markdown-файлы. Логи
`.free-code-logs/` и локальные `INBOX.md` / `STOP` в git не попадают.

После завершения работы создайте файл `STOP` в директории поколения, чтобы
`loop.sh` не крутился бесконечно.

## Как адаптировать

Замените в `MAIN_GOAL.md` исходный файл, язык перевода, формат результата и
требования к качеству. Если статья сложная, можно позже разделить
`TRANSLATION_NOTES.md` на несколько файлов, но стартовый пример специально
держит память компактной.
