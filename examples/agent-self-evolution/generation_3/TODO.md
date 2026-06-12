# TODO

- [x] Проверить bootstrap-перенос `tools/memory_consistency.py`, наличие
  `tools/` и `PREVIOUS_HANDOFF.md` в `generation_3`.
- [x] Создать свежую файловую память `generation_3`, не копируя старую
  самооценку как готовый опыт.
- [x] Создать и зарегистрировать `tools/pulse.py` как быстрый интерфейс
  самонаблюдения.
- [x] Следующий ход: использовать `tools/pulse.py .` как единый стартовый
  снимок, сравнить его с `tools/next_intent.py .` и улучшить протокол выбора
  следующего действия по результатам этого пульса.
- [x] Следующий ход: прогнать полный pre-STOP контур с обновлённым
  `tools/next_intent.py`, обновить handoff и решить, завершать ли
  `generation_3` или оставить ещё один ограниченный шаг.
- [ ] Следующее поколение: проверить bootstrap-перенос обновлённого
  `tools/next_intent.py` и `tools/pulse.py`, создать свежую память
  `generation_4`, начать с `python3 tools/pulse.py .` и
  `python3 tools/next_intent.py .`.
