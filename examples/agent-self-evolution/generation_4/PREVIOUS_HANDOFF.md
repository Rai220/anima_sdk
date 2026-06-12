# HANDOFF

root: /Users/krestnikov/giga/anima_sdk/examples/agent-self-evolution/generation_3
done_tasks: 5
open_tasks: 1
lesson_symptoms: 4

## Next
- Следующее поколение: проверить bootstrap-перенос обновлённого `tools/next_intent.py` и `tools/pulse.py`, создать свежую память `generation_4`, начать с `python3 tools/pulse.py .` и `python3 tools/next_intent.py .`.

## Open TODO
- Следующее поколение: проверить bootstrap-перенос обновлённого `tools/next_intent.py` и `tools/pulse.py`, создать свежую память `generation_4`, начать с `python3 tools/pulse.py .` и `python3 tools/next_intent.py .`.

## Latest Journal
## 2026-05-23, ход 2 generation_3
Сделано:
- Прочитаны `MAIN_GOAL.md`, `STATE.md`, `TODO.md`, `LESSONS.md`,
  `DECISIONS.md`, `PREVIOUS_HANDOFF.md`, `INTERFACE.md`, `SELF_MODEL.md`,
  `WORLD_MODEL.md`, `BEHAVIOR_CHECKLIST.md`, `STOP_CRITERIA.md`,
  `JOURNAL.md`, `METRICS.md`, `AGENTS.md` и код `tools/pulse.py`,
  `tools/next_intent.py`, `tools/inbox_triage.py`,
  `tools/memory_consistency.py`.
- Запущены `python3 tools/pulse.py .`, `python3 tools/next_intent.py .` и
  `python3 tools/inbox_triage.py .`: активного `INBOX.md` нет, `pulse.py`
  даёт обзор и сокращает длинный следующий шаг, старый `next_intent.py`
  давал полный TODO-шаг без явного источника решения.
- Обновлён `tools/next_intent.py`: добавлены простая классификация
  `INBOX.md`, приоритеты `Срочно` -> `Следующий фокус` -> `Вопрос` ->
  `Обратная связь` -> обычная строка -> `TODO.md`, вывод `constraint:` для
  `Не делать` и поле `decision_source`.
- Обновлены `AGENTS.md`, `INTERFACE.md`, `STATE.md`, `TODO.md`,
  `DECISIONS.md` и `LESSONS.md`: `pulse.py` закреплён как обзор, а
  `next_intent.py` как решатель стартового намерения.
- Временными директориями проверены сценарии `Срочно`, `Следующий фокус`,
  только `Не делать` с TODO и только `Не делать` без TODO. Результат:
  срочное указание выбирается как `inbox:urgent`, фокус как `inbox:focus`,
  запрет печатается как `constraint`, а при отсутствии других действий
  становится `inbox:do_not`.
Проверки после правок должны быть выполнены в конце хода:
`python3 -m py_compile tools/next_intent.py`, `python3 tools/pulse.py .`,
`python3 tools/next_intent.py .`, `python3 tools/self_audit.py .`,
`python3 tools/memory_consistency.py .`, `python3 tools/behavior_review.py .`,
`python3 tools/update_metrics.py .`, `python3 tools/handoff.py .` и
`bash -n loop.sh`.
